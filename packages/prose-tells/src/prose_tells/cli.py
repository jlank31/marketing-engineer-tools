"""prose-tells command line interface.

    prose-tells scan draft.md
    prose-tells scan posts/*.md --preset social
    cat draft.md | prose-tells scan -
    prose-tells scan article.md --preset blog --siblings ./published --json
    prose-tells profile --preset blog > profile.json

Exit codes are chosen so this is usable as a CI gate:

    0  no issues (warnings may still be printed)
    1  at least one issue
    2  bad usage / unreadable input

Warnings never fail the run. That is deliberate: a linter that blocks a publish
on a soft signal gets switched off within a week, and then it protects nothing.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .content_quality import Profile, check_text, read_siblings
from .profiles import PRESETS, dump, load, to_dict
from .repetition import find_verbatim_runs, opener_echo, stat_fingerprint

STDIN = "-"


def _read(target: str) -> tuple[str, str]:
    """Return (label, text). `-` reads stdin."""
    if target == STDIN:
        return "<stdin>", sys.stdin.read()
    p = Path(target)
    return str(p), p.read_text()


def _resolve_profile(args) -> Profile:
    if args.profile:
        return load(args.profile, base=args.preset)
    return PRESETS[args.preset]


def _corpus_report(text: str, corpus: dict[str, str]) -> list[str]:
    """Cross-document findings: reuse a per-text scan structurally cannot see."""
    out: list[str] = []
    for other, snippet in find_verbatim_runs(text, corpus):
        out.append(f"verbatim run shared with {other}: {snippet!r}")
    for other in opener_echo(text, corpus):
        out.append(f"opening line echoes {other}")
    for other, shared in stat_fingerprint(text, corpus):
        out.append(f"recycled stat block with {other} ({shared} shared figures)")
    return out


def _scan(args) -> int:
    profile = _resolve_profile(args)
    corpus: dict[str, str] = {}
    if args.siblings:
        corpus = read_siblings(Path(args.siblings))

    reports = []
    worst = 0
    for target in args.paths:
        try:
            label, text = _read(target)
        except OSError as e:
            print(f"prose-tells: cannot read {target}: {e}", file=sys.stderr)
            worst = max(worst, 2)
            continue

        result = check_text(text, profile)
        # Exclude the file being scanned from its own comparison corpus.
        peers = {k: v for k, v in corpus.items() if Path(k).name != Path(label).name}
        repeats = _corpus_report(text, peers) if peers else []

        reports.append(
            {
                "file": label,
                "passed": result.passed and not result.issues,
                "issues": result.issues,
                "warnings": result.warnings,
                "repetition": repeats,
                "stats": result.stats,
            }
        )
        if result.issues:
            worst = max(worst, 1)

    if args.json:
        json.dump({"version": __version__, "profile": profile.name, "results": reports},
                  sys.stdout, indent=2)
        sys.stdout.write("\n")
        return worst

    for r in reports:
        n_i, n_w, n_r = len(r["issues"]), len(r["warnings"]), len(r["repetition"])
        mark = "PASS" if not n_i else "FAIL"
        print(f"\n{mark}  {r['file']}  ({n_i} issue{'s' * (n_i != 1)}, "
              f"{n_w} warning{'s' * (n_w != 1)}"
              + (f", {n_r} repetition" if n_r else "") + ")")
        for label, rows in (("issue", r["issues"]), ("warning", r["warnings"]),
                            ("repetition", r["repetition"])):
            for row in rows:
                print(f"    [{label}] {row}")

    if not reports:
        return max(worst, 2)
    if worst == 0:
        print("\nNo issues. Worth remembering this checks for tells, not for quality —")
        print("clean output is a floor, not a finished piece.")
    return worst


def _profile_cmd(args) -> int:
    if args.out:
        dump(PRESETS[args.preset], args.out)
        print(f"wrote {args.out}", file=sys.stderr)
        return 0
    json.dump(to_dict(PRESETS[args.preset]), sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="prose-tells",
        description="Find the lines that make copy read as machine-written.",
    )
    ap.add_argument("--version", action="version", version=f"prose-tells {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("scan", help="scan one or more files (use - for stdin)")
    s.add_argument("paths", nargs="+", help="files to scan, or - for stdin")
    s.add_argument("--preset", choices=sorted(PRESETS), default="generic",
                   help="starting profile (default: generic)")
    s.add_argument("--profile", metavar="FILE",
                   help="JSON profile; overrides matching --preset values")
    s.add_argument("--siblings", metavar="DIR",
                   help="directory of earlier work to compare against for reuse")
    s.add_argument("--json", action="store_true", help="machine-readable output")
    s.set_defaults(func=_scan)

    p = sub.add_parser("profile", help="print a starter profile as JSON")
    p.add_argument("--preset", choices=sorted(PRESETS), default="generic")
    p.add_argument("--out", metavar="FILE", help="write to FILE instead of stdout")
    p.set_defaults(func=_profile_cmd)

    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except ValueError as e:
        print(f"prose-tells: {e}", file=sys.stderr)
        return 2
    except BrokenPipeError:
        return 0


if __name__ == "__main__":
    sys.exit(main())
