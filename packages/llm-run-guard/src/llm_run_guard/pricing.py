"""What a call actually costs, including the parts most trackers miss.

Three things make naive cost tracking wrong, and all three are quiet:

1. CACHE TOKENS ARE ADDITIVE. The API reports `cache_creation_input_tokens` and
   `cache_read_input_tokens` SEPARATELY from `input_tokens`. They are not a
   subset. Bill them at 1.25x and 0.10x of the input rate, on top. Skip them and
   every cached call is understated.

2. SERVER-SIDE TOOLS COST MONEY. Web search is billed per request on top of
   tokens, and it doesn't show up in the token counts at all.

3. UNKNOWN MODELS. The common implementation returns 0.0 for a model ID it
   doesn't recognize. That is the dangerous one: a new model version silently
   becomes free, which means it is also invisible to any budget cap built on
   these numbers. This module falls back to the most expensive tier instead.
   Overstate, never understate.

Prices are a DATED SNAPSHOT, not live data. See PRICES_LAST_REVIEWED. Verify
against the vendor's pricing page before trusting a number that matters, and
send a PR when one is stale.
"""

from __future__ import annotations

import logging
import os
from datetime import date, datetime

logger = logging.getLogger(__name__)

# Bump this when you touch the table below. `staleness_warning()` reads it.
PRICES_LAST_REVIEWED = "2026-07-30"
PRICES_SOURCE_URL = "https://www.anthropic.com/pricing"

# USD per million tokens. Sticker rates, deliberately: promotional or
# introductory pricing gets tracked at sticker so costs are never understated
# when the promo ends and nobody remembers to update this.
TOKEN_PRICES: dict[str, dict[str, float]] = {
    "claude-opus-5": {"input": 5.00, "output": 25.00},
    "claude-opus-4-8": {"input": 5.00, "output": 25.00},
    "claude-opus-4-7": {"input": 5.00, "output": 25.00},
    "claude-opus-4-6": {"input": 15.00, "output": 75.00},
    "claude-sonnet-5": {"input": 3.00, "output": 15.00},
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "claude-fable-5": {"input": 1.50, "output": 7.50},
    "claude-haiku-4-5": {"input": 0.80, "output": 4.00},
}

# Unknown models price as the most expensive tier. This is the single most
# important line in the file: the alternative (returning 0.0) means a model you
# haven't added is free, and therefore invisible to your cost cap.
FALLBACK_MODEL = "claude-opus-4-6"

# Anthropic cache billing multipliers, applied to the model's INPUT rate.
CACHE_WRITE_MULTIPLIER = 1.25
CACHE_READ_MULTIPLIER = 0.10

# Server-side web_search: $10 per 1,000 requests, on top of tokens.
WEB_SEARCH_COST_PER_REQUEST = 0.01

_warned_unknown: set[str] = set()


def price_for(model: str) -> dict[str, float] | None:
    """Look up prices, tolerating dated model IDs.

    The API reports IDs like `claude-opus-5-20260814` while the table keys on the
    family. Returns None when nothing matches so the caller can choose between
    the conservative fallback and skipping the row.
    """
    if model in TOKEN_PRICES:
        return TOKEN_PRICES[model]
    for known, prices in TOKEN_PRICES.items():
        if model.startswith(known) or known.startswith(model):
            return prices
    return None


def calculate_cost(
    model: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cache_creation_tokens: int = 0,
    cache_read_tokens: int = 0,
    web_search_requests: int = 0,
) -> float:
    """USD for one call. Cache tokens are ADDITIVE to input_tokens, not a subset.

    An unrecognized model warns ONCE PER PROCESS and prices as the most expensive
    tier. Once-per-process matters: a single run can make 80+ calls, and a warning
    per call trains you to ignore the log.
    """
    prices = price_for(model)
    if prices is None:
        if model not in _warned_unknown:
            _warned_unknown.add(model)
            logger.warning(
                "llm-run-guard: unknown model %r, pricing as %s (the most "
                "expensive tier) so cost is overstated rather than hidden from "
                "your cap. Add it to TOKEN_PRICES.",
                model, FALLBACK_MODEL,
            )
        prices = TOKEN_PRICES[FALLBACK_MODEL]

    rate_in = prices["input"] / 1_000_000
    rate_out = prices["output"] / 1_000_000

    return round(
        input_tokens * rate_in
        + output_tokens * rate_out
        + cache_creation_tokens * rate_in * CACHE_WRITE_MULTIPLIER
        + cache_read_tokens * rate_in * CACHE_READ_MULTIPLIER
        + web_search_requests * WEB_SEARCH_COST_PER_REQUEST,
        6,
    )


def cost_from_usage(model: str, usage) -> float:
    """Cost straight from an Anthropic SDK `response.usage` object or a dict.

    Reads every field that carries a charge, including the two cache fields that
    are easy to miss because they sit outside `input_tokens`.
    """
    def get(name: str) -> int:
        if isinstance(usage, dict):
            return int(usage.get(name) or 0)
        return int(getattr(usage, name, 0) or 0)

    searches = 0
    server_tool = (
        usage.get("server_tool_use") if isinstance(usage, dict)
        else getattr(usage, "server_tool_use", None)
    )
    if server_tool is not None:
        searches = (
            int(server_tool.get("web_search_requests") or 0)
            if isinstance(server_tool, dict)
            else int(getattr(server_tool, "web_search_requests", 0) or 0)
        )

    return calculate_cost(
        model,
        input_tokens=get("input_tokens"),
        output_tokens=get("output_tokens"),
        cache_creation_tokens=get("cache_creation_input_tokens"),
        cache_read_tokens=get("cache_read_input_tokens"),
        web_search_requests=searches,
    )


def staleness_warning(today: date | None = None, max_age_days: int = 120) -> str | None:
    """Return a warning if the price table is older than `max_age_days`.

    A cost tool reporting stale numbers is worse than no cost tool, because you
    trust the output. Surfaced by the CLI and callable from your own startup.
    """
    reviewed = datetime.strptime(PRICES_LAST_REVIEWED, "%Y-%m-%d").date()
    now = today or date.today()
    age = (now - reviewed).days
    if age <= max_age_days:
        return None
    return (
        f"llm-run-guard price table is {age} days old (reviewed "
        f"{PRICES_LAST_REVIEWED}). Verify against {PRICES_SOURCE_URL}. "
        f"Corrections are the one contribution actively wanted."
    )


def _env_float(name: str, default: float | None = None) -> float | None:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError:
        logger.warning("llm-run-guard: %s=%r is not a number, ignoring", name, raw)
        return default
