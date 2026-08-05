"""Keep a pipeline running unattended, and measure whether that's worth paying for.

Three pieces, in order of how often they save you:

1. `response_text()` — get the text out of a response, correctly.
2. `safe_parse_json()` — get structured data out, tolerating the ways models
   wrap it.
3. `@with_healing` — retry with backoff, and optionally escalate to a model to
   diagnose what went wrong.

THE PART WORTH READING TWICE is the instrumentation, not the healing. The
escalation path calls a bigger model to diagnose a failure, which costs real
money. `metrics()` counts how often it fires and how often the failure was a
transient error that plain retry would have fixed for free. Most people add the
expensive rescue path and never check whether it earns its keep. Check yours.
"""

from __future__ import annotations

import functools
import json
import logging
import random
import re
import threading
import time
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_metrics = {
    "attempts": 0,
    "retries": 0,
    "retry_succeeded": 0,
    "json_repairs": 0,
    "json_repairs_local": 0,
    "diagnoses": 0,
    "failures": 0,
}


def metrics() -> dict:
    """Counters for the healing layer. The honest version of "it works".

    `retry_succeeded` against `diagnoses` is the ratio that matters: if plain
    retry is fixing nearly everything, the expensive diagnosis path is costing
    you money for nothing and should be turned off.
    """
    with _lock:
        m = dict(_metrics)
    if m["diagnoses"]:
        m["retry_fixed_share"] = round(
            m["retry_succeeded"] / (m["retry_succeeded"] + m["diagnoses"]), 3
        )
    return m


def reset_metrics() -> None:
    with _lock:
        for k in _metrics:
            _metrics[k] = 0


def _bump(key: str, n: int = 1) -> None:
    with _lock:
        _metrics[key] = _metrics.get(key, 0) + n


# ---------------------------------------------------------------------------
# 1. Reading the response
# ---------------------------------------------------------------------------

def response_text(response: Any) -> str:
    """Return the text of a response, whatever else is in the content array.

    THIS EXISTS BECAUSE OF A REAL OUTAGE. Extended-thinking models return a
    thinking block as `content[0]`, so every pipeline written as
    `response.content[0].text` started raising the day that shipped. It isn't a
    graceful degradation; it's a hard stop, mid-run.

    The fix is to stop assuming position 0 and walk the array for the first block
    that actually carries text. Cheap, and it makes your code forward-compatible
    with whatever block type gets added next.
    """
    if response is None:
        return ""
    content = getattr(response, "content", None)
    if content is None:
        return str(response)
    if isinstance(content, str):
        return content

    parts: list[str] = []
    for block in content:
        btype = getattr(block, "type", None)
        if btype in ("thinking", "redacted_thinking"):
            continue
        text = getattr(block, "text", None)
        if text:
            parts.append(text)
    if parts:
        return "\n".join(parts)

    # Nothing text-shaped: a pure tool_use response, most likely.
    for block in content:
        if getattr(block, "type", None) == "tool_use":
            return json.dumps(getattr(block, "input", {}))
    return ""


def tool_input(response: Any, name: str | None = None) -> dict | None:
    """Return the input of the first tool_use block, optionally matching a name."""
    for block in getattr(response, "content", None) or []:
        if getattr(block, "type", None) != "tool_use":
            continue
        if name is None or getattr(block, "name", None) == name:
            return getattr(block, "input", None)
    return None


# ---------------------------------------------------------------------------
# 2. Getting structured data out
# ---------------------------------------------------------------------------

_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.S)


def safe_parse_json(raw: str | Any, default: Any = None) -> Any:
    """Parse JSON out of a model response, tolerating the usual wrappers.

    Handles: a plain object, a ```json fence, prose either side of the object,
    and trailing commas. Returns `default` rather than raising, because in a long
    unattended run one unparseable response should cost you one item, not the run.

    Deliberately does NOT call a model to repair the JSON. Every case above is
    fixable locally, and reaching for an API call here is how a cheap failure
    becomes an expensive one.
    """
    if not isinstance(raw, str):
        raw = response_text(raw)
    if not raw or not raw.strip():
        return default

    text = raw.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    fenced = _FENCE.search(text)
    if fenced:
        try:
            _bump("json_repairs_local")
            return json.loads(fenced.group(1).strip())
        except json.JSONDecodeError:
            text = fenced.group(1).strip()

    # Slice from the first opening brace/bracket to its matching close.
    for opener, closer in (("{", "}"), ("[", "]")):
        start = text.find(opener)
        end = text.rfind(closer)
        if start != -1 and end > start:
            candidate = text[start : end + 1]
            try:
                _bump("json_repairs_local")
                return json.loads(candidate)
            except json.JSONDecodeError:
                # Trailing commas are the most common remaining break.
                cleaned = re.sub(r",(\s*[}\]])", r"\1", candidate)
                try:
                    _bump("json_repairs")
                    return json.loads(cleaned)
                except json.JSONDecodeError:
                    continue
    return default


# ---------------------------------------------------------------------------
# 3. Retrying
# ---------------------------------------------------------------------------

# Errors where retrying is pointless: the same input will fail the same way.
# Retrying these wastes wall clock and, on an auth or credit failure, hides the
# real cause behind N identical stack traces.
NON_RETRYABLE = (TypeError, ValueError, KeyError, AttributeError, NotImplementedError)

# Substrings that mean "stop immediately and tell the human". A credit-balance
# failure retried 3 times just delays the message you actually needed.
FATAL_SUBSTRINGS = (
    "credit balance is too low",
    "authentication",
    "invalid x-api-key",
    "permission",
    "quota",
)


class HealingFailed(RuntimeError):
    """Every attempt failed. Carries the last exception as __cause__."""


def is_fatal(error: BaseException) -> bool:
    msg = str(error).lower()
    return any(s in msg for s in FATAL_SUBSTRINGS)


def with_healing(
    attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    retry_on: tuple[type[BaseException], ...] = (Exception,),
    diagnose: Callable[[BaseException, dict], str | None] | None = None,
):
    """Retry a step with exponential backoff and jitter.

    Jitter is not decoration: without it, a pipeline that fans out and hits a
    rate limit retries in lockstep and re-collides at exactly the same moment.

    `diagnose` is optional and OFF by default. Pass a callable to escalate a
    final failure somewhere expensive (a bigger model, an alerting hook). It runs
    only after every retry is exhausted, and `metrics()` counts how often that
    happened versus how often plain retry was enough.

        @with_healing(attempts=3)
        def summarize(doc):
            ...
    """
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            last: BaseException | None = None
            for attempt in range(attempts):
                _bump("attempts")
                try:
                    result = fn(*args, **kwargs)
                    if attempt:
                        _bump("retry_succeeded")
                    return result
                except NON_RETRYABLE:
                    # A bug in the caller. Retrying re-runs the same bug.
                    _bump("failures")
                    raise
                except retry_on as e:
                    last = e
                    if is_fatal(e):
                        _bump("failures")
                        logger.error("llm-cost: fatal, not retrying: %s", e)
                        raise
                    if attempt == attempts - 1:
                        break
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    delay += random.uniform(0, delay * 0.25)  # noqa: S311
                    _bump("retries")
                    logger.warning(
                        "llm-cost: %s failed (attempt %d/%d), retrying in %.1fs: %s",
                        getattr(fn, "__name__", "step"), attempt + 1, attempts, delay, e,
                    )
                    time.sleep(delay)

            _bump("failures")
            if diagnose is not None:
                _bump("diagnoses")
                try:
                    note = diagnose(last, {"step": getattr(fn, "__name__", "step")})
                    if note:
                        logger.error("llm-cost: diagnosis: %s", note)
                except Exception:  # noqa: BLE001
                    logger.debug("llm-cost: diagnosis hook failed", exc_info=True)

            raise HealingFailed(
                f"{getattr(fn, '__name__', 'step')} failed after {attempts} attempts"
            ) from last
        return wrapper
    return decorator
