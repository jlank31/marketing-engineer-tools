"""edit-digest — turn a pile of redlines into rules your AI prompt can use.

    edit-digest edits.jsonl
    edit-digest edits.csv --min-count 2 --prompt-block > rules.md
    edit-digest edits.jsonl --json

Input is any file with a before and an after column. See loaders.py for the
column names it recognizes.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .digest import compute, render_prompt_block, render_report, to_dict
from .loaders import load


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="edit-digest",
        description="Learn an editor's style from before/after pairs. No model, no API calls.",
    )
    ap.add_argument("path", help="edits file: .jsonl, .json, or .csv")
    ap.add_argument("--min-count", type=int, default=3, metavar="N",
                    help="times a pattern must recur to count (default: 3)")
    ap.add_argument("--prompt-block", action="store_true",
                    help="print only the block to paste into your AI prompt")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--out", metavar="FILE", help="write to FILE instead of stdout")
    ap.add_argument("--version", action="version", version=f"edit-digest {__version__}")
    args = ap.parse_args(argv)

    try:
        edits = load(args.path)
    except (OSError, ValueError) as e:
        print(f"edit-digest: {e}", file=sys.stderr)
        return 2

    if not edits:
        print(
            f"edit-digest: no usable pairs in {args.path}.\n"
            "  Each row needs a before and an after. Recognized column names:\n"
            "  original_text/edited_text, before/after, old/new.",
            file=sys.stderr,
        )
        return 2

    digest = compute(edits, min_count=args.min_count)

    if args.json:
        text = json.dumps(to_dict(digest), indent=2) + "\n"
    elif args.prompt_block:
        text = render_prompt_block(digest)
        if not text:
            print(
                "edit-digest: nothing survived the prompt filter.\n"
                "  That's the right answer for a thin corpus. An empty block\n"
                "  beats a wrong one. Try --min-count 2, or come back with more edits.",
                file=sys.stderr,
            )
            return 1
    else:
        text = render_report(digest)

    if args.out:
        Path(args.out).write_text(text)
        print(f"wrote {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
