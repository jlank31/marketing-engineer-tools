"""llm-cost: price a call from the terminal, or check the price table.

    llm-cost price claude-opus-5 --in 50000 --out 2000 --cache-read 40000
    llm-cost models
    llm-cost check

`price` is the useful one when you're sizing a job before running it: plug in the
token counts you expect and see the number before you spend it.
"""

from __future__ import annotations

import argparse
import json
import sys

from . import __version__
from .pricing import (
    CACHE_READ_MULTIPLIER,
    CACHE_WRITE_MULTIPLIER,
    PRICES_LAST_REVIEWED,
    PRICES_SOURCE_URL,
    TOKEN_PRICES,
    WEB_SEARCH_COST_PER_REQUEST,
    calculate_cost,
    price_for,
    staleness_warning,
)


def _price(args) -> int:
    cost = calculate_cost(
        args.model,
        input_tokens=args.input_tokens,
        output_tokens=args.output_tokens,
        cache_creation_tokens=args.cache_write,
        cache_read_tokens=args.cache_read,
        web_search_requests=args.web_search,
    )
    known = price_for(args.model) is not None

    if args.json:
        json.dump({"model": args.model, "cost_usd": cost, "known_model": known},
                  sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    print(f"\n  {args.model}")
    if not known:
        print("  NOT in the price table. Priced at the most expensive tier so the")
        print("  number is overstated rather than hidden from your cap.")
    print(f"\n  input        {args.input_tokens:>12,}")
    print(f"  output       {args.output_tokens:>12,}")
    if args.cache_write:
        print(f"  cache write  {args.cache_write:>12,}   billed {CACHE_WRITE_MULTIPLIER}x input")
    if args.cache_read:
        print(f"  cache read   {args.cache_read:>12,}   billed {CACHE_READ_MULTIPLIER}x input")
    if args.web_search:
        print(f"  web search   {args.web_search:>12,}   ${WEB_SEARCH_COST_PER_REQUEST} each")
    print(f"\n  cost         ${cost:.6f}\n")

    if args.cache_read or args.cache_write:
        print("  Cache tokens are ADDITIVE to input_tokens, not a subset of them.")
        print("  A tracker that ignores them understates every cached call.\n")
    return 0


def _models(args) -> int:
    if args.json:
        json.dump(TOKEN_PRICES, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0
    print(f"\n  USD per million tokens (reviewed {PRICES_LAST_REVIEWED})\n")
    print(f"  {'model':<34}{'input':>10}{'output':>10}")
    for name, p in sorted(TOKEN_PRICES.items()):
        print(f"  {name:<34}{p['input']:>10.2f}{p['output']:>10.2f}")
    print(f"\n  Source: {PRICES_SOURCE_URL}")
    print("  These are a dated snapshot. Verify anything that matters.\n")
    return 0


def _check(args) -> int:
    warning = staleness_warning()
    if warning:
        print(f"\n  STALE: {warning}\n")
        return 1
    print(f"\n  Price table reviewed {PRICES_LAST_REVIEWED}, within the freshness window.\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="llm-cost",
        description="Price Anthropic API calls, including the parts most trackers miss.",
    )
    ap.add_argument("--version", action="version", version=f"llm-cost {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("price", help="cost of one call")
    p.add_argument("model")
    p.add_argument("--in", dest="input_tokens", type=int, default=0, metavar="N")
    p.add_argument("--out", dest="output_tokens", type=int, default=0, metavar="N")
    p.add_argument("--cache-write", type=int, default=0, metavar="N")
    p.add_argument("--cache-read", type=int, default=0, metavar="N")
    p.add_argument("--web-search", type=int, default=0, metavar="N",
                   help="server-side web_search requests")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=_price)

    m = sub.add_parser("models", help="show the price table")
    m.add_argument("--json", action="store_true")
    m.set_defaults(func=_models)

    c = sub.add_parser("check", help="warn if the price table is stale")
    c.set_defaults(func=_check)
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except BrokenPipeError:
        return 0


if __name__ == "__main__":
    sys.exit(main())
