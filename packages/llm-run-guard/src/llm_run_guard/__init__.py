"""llm-run-guard — know what a run costs, and stop it when it blows the budget.

    from llm_run_guard import TrackedClient, tracked_run

    with tracked_run("nightly", cap_usd=5.00) as run:
        client = TrackedClient("summarizer")
        client.messages.create(...)          # unchanged
    print(run.summary["cost_usd"])

Three things most cost tracking gets wrong, all quiet:

  cache tokens    billed 1.25x to write, 0.10x to read, and reported SEPARATELY
                  from input_tokens rather than included in them
  server tools    web search bills per request, invisible in token counts
  unknown models  the usual implementation returns $0, which silently switches
                  off any budget cap built on the number

Plus a healing layer for pipelines that run unattended, and the counters to tell
you whether its expensive escalation path is earning its keep.
"""

from .client import TrackedClient
from .healing import (
    HealingFailed,
    metrics,
    reset_metrics,
    response_text,
    safe_parse_json,
    tool_input,
    with_healing,
)
from .pricing import (
    TOKEN_PRICES,
    calculate_cost,
    cost_from_usage,
    price_for,
    staleness_warning,
)
from .tracker import (
    RunCostExceeded,
    UsageRecord,
    flush,
    init_run,
    record,
    records,
    spent,
    summary,
    tracked_run,
)

__version__ = "0.1.0"

__all__ = [
    "TrackedClient",
    "tracked_run",
    "RunCostExceeded",
    "UsageRecord",
    "init_run", "record", "records", "spent", "summary", "flush",
    "calculate_cost", "cost_from_usage", "price_for", "staleness_warning",
    "TOKEN_PRICES",
    "with_healing", "HealingFailed", "response_text", "safe_parse_json",
    "tool_input", "metrics", "reset_metrics",
    "__version__",
]
