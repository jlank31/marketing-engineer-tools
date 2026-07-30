"""Accumulate spend across a run, and stop the run when it blows its budget.

The cap is the point. Cost *reporting* tells you what happened yesterday; a cap
stops a runaway retry loop from spending a day's budget in twenty minutes while
you're at lunch.

Design notes worth knowing before you rely on this:

- **Thread-safe by lock, not by magic.** One process-global accumulator guarded
  by a lock. If you fan out across processes, each gets its own budget.
- **Tracking failures never break your pipeline.** `record()` swallows its own
  errors. A cost tracker that crashes the job it's measuring is worse than no
  cost tracker. The cap check is the deliberate exception: that one raises.
- **Records are plain dataclasses.** No pydantic, no ORM, no DB. Persist them
  yourself if you want history; `flush()` hands you the list.
"""

from __future__ import annotations

import logging
import threading
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field

from .pricing import calculate_cost, cost_from_usage

logger = logging.getLogger(__name__)


class RunCostExceeded(RuntimeError):
    """Accumulated cost passed the cap mid-run.

    Raised from inside `record()`, so it interrupts the loop that is spending
    rather than being noticed afterwards. This is what catches a runaway retry
    or a prompt-engineering mistake before it becomes a bill.
    """

    def __init__(self, spent: float, cap: float, label: str = ""):
        self.spent, self.cap, self.label = spent, cap, label
        where = f" in {label!r}" if label else ""
        super().__init__(
            f"run cost ${spent:.4f} exceeded cap ${cap:.2f}{where}. "
            f"Raise the cap or find what is looping."
        )


@dataclass(frozen=True)
class UsageRecord:
    """One billable call."""

    label: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0
    web_search_requests: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    started_at: float = 0.0

    @property
    def total_tokens(self) -> int:
        return (
            self.input_tokens + self.output_tokens
            + self.cache_creation_tokens + self.cache_read_tokens
        )

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class _RunState:
    name: str = ""
    cap_usd: float | None = None
    records: list[UsageRecord] = field(default_factory=list)

    @property
    def spent(self) -> float:
        return round(sum(r.cost_usd for r in self.records), 6)


_lock = threading.Lock()
_state = _RunState()


def init_run(name: str = "", cap_usd: float | None = None) -> None:
    """Start a fresh run. Clears any previous accumulation."""
    global _state
    with _lock:
        _state = _RunState(name=name, cap_usd=cap_usd)


def record(
    label: str,
    model: str,
    usage=None,
    *,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cache_creation_tokens: int = 0,
    cache_read_tokens: int = 0,
    web_search_requests: int = 0,
    latency_ms: int = 0,
) -> UsageRecord | None:
    """Record one call. Pass the SDK's `response.usage` or explicit counts.

    Raises RunCostExceeded if this call pushes the run past its cap. Every other
    failure in here is swallowed: measurement must not break the thing it
    measures.
    """
    try:
        if usage is not None:
            cost = cost_from_usage(model, usage)

            def _g(n):
                if isinstance(usage, dict):
                    return int(usage.get(n) or 0)
                return int(getattr(usage, n, 0) or 0)

            rec = UsageRecord(
                label=label, model=model,
                input_tokens=_g("input_tokens"),
                output_tokens=_g("output_tokens"),
                cache_creation_tokens=_g("cache_creation_input_tokens"),
                cache_read_tokens=_g("cache_read_input_tokens"),
                web_search_requests=web_search_requests,
                cost_usd=cost, latency_ms=latency_ms, started_at=time.time(),
            )
        else:
            cost = calculate_cost(
                model, input_tokens, output_tokens,
                cache_creation_tokens, cache_read_tokens, web_search_requests,
            )
            rec = UsageRecord(
                label=label, model=model,
                input_tokens=input_tokens, output_tokens=output_tokens,
                cache_creation_tokens=cache_creation_tokens,
                cache_read_tokens=cache_read_tokens,
                web_search_requests=web_search_requests,
                cost_usd=cost, latency_ms=latency_ms, started_at=time.time(),
            )
    except RunCostExceeded:
        raise
    except Exception:  # noqa: BLE001 - deliberate: never break the caller
        logger.debug("llm-run-guard: could not record usage", exc_info=True)
        return None

    with _lock:
        _state.records.append(rec)
        spent, cap, name = _state.spent, _state.cap_usd, _state.name

    if cap is not None and spent > cap:
        raise RunCostExceeded(spent, cap, name)
    return rec


def spent() -> float:
    with _lock:
        return _state.spent


def records() -> list[UsageRecord]:
    with _lock:
        return list(_state.records)


def summary() -> dict:
    """Totals for the current run, grouped by label and by model."""
    rows = records()
    by_label: dict[str, dict] = {}
    by_model: dict[str, dict] = {}
    for r in rows:
        for bucket, key in ((by_label, r.label), (by_model, r.model)):
            b = bucket.setdefault(key, {"calls": 0, "cost_usd": 0.0, "tokens": 0})
            b["calls"] += 1
            b["cost_usd"] = round(b["cost_usd"] + r.cost_usd, 6)
            b["tokens"] += r.total_tokens
    with _lock:
        name, cap = _state.name, _state.cap_usd
    return {
        "run": name,
        "calls": len(rows),
        "cost_usd": round(sum(r.cost_usd for r in rows), 6),
        "cap_usd": cap,
        "tokens": sum(r.total_tokens for r in rows),
        "cached_read_tokens": sum(r.cache_read_tokens for r in rows),
        "by_label": by_label,
        "by_model": by_model,
    }


def flush() -> list[UsageRecord]:
    """Return the records and clear them. Persist them yourself if you want."""
    global _state
    with _lock:
        rows = list(_state.records)
        _state = _RunState(name=_state.name, cap_usd=_state.cap_usd)
    return rows


@contextmanager
def tracked_run(name: str = "", cap_usd: float | None = None):
    """Scope a run and get its summary at the end.

        with tracked_run("nightly", cap_usd=5.00) as run:
            ...
        print(run.summary["cost_usd"])

    The summary is populated on exit, including when the block raises, so a run
    killed by its own cap still tells you what it spent.
    """
    class _Handle:
        summary: dict = {}

    init_run(name, cap_usd)
    handle = _Handle()
    try:
        yield handle
    finally:
        handle.summary = summary()
