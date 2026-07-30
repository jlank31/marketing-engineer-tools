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
from .corpus import STAT_MIN_SHARED, analyze, load_corpus, render
from .corpus import to_dict as corpus_to_dict
from .profiles import PRESETS, dump, load, to_dict
from .repetition import find_verbatim_runs, opener_echo, opening_line, stat_fingerprint

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
    """Cross-document findings for ONE draft against a corpus.

    Signatures here are easy to get wrong, and getting them wrong crashes rather
    than degrades: find_verbatim_runs returns (snippet, source) in that order,
    opener_echo takes an opener STRING plus a list of other openers (not raw
    texts) and returns a single match or None, and stat_fingerprint takes one text
    and returns a set. An earlier version of this function got all three wrong and
    the --siblings path raised TypeError. Hence the explicit test coverage.
    """
    out: list[str] = []

    for snippet, source in find_verbatim_runs(text, corpus):
        out.append(f'verbatim run shared with {source}: "{snippet}"')

    openers = {label: opening_line(body) for label, body in corpus.items()}
    echoed = opener_echo(opening_line(text), list(openers.values()))
    if echoed:
        match = next((k for k, v in openers.items() if v == echoed), "another draft")
        out.append(f"opening line echoes {match}")

    mine = stat_fingerprint(text)
    for label, body in corpus.items():
        shared = mine & stat_fingerprint(body)
        if len(shared) >= STAT_MIN_SHARED:
            out.append(f"recycled stat block with {label} ({len(shared)} shared figures)")

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


def _corpus_cmd(args) -> int:
    """Read a whole archive and report where it repeats itself.

    Always exits 0. Repetition is a finding for a human to judge, not a failure:
    some of it is a positioning line you want consistent, some is a rut, and no
    threshold can tell those apart.
    """
    root = Path(args.dir)
    if not root.is_dir():
        print(f"prose-tells: not a directory: {root}", file=sys.stderr)
        return 2

    corpus = load_corpus(root, pattern=args.pattern,
                         exclude_section=args.exclude_section)
    if not corpus:
        print(f"prose-tells: no files matching {args.pattern!r} under {root}",
              file=sys.stderr)
        return 2

    report = analyze(corpus, min_run=args.min_run)
    if args.json:
        json.dump({"version": __version__, **corpus_to_dict(report)},
                  sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        print(render(report))
    return 0


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

    c = sub.add_parser(
        "corpus",
        help="read a whole archive and report where it repeats itself",
        description="Cross-document analysis: verbatim reuse, echoed openers, "
                    "recycled stat blocks, and phrases that recur across many "
                    "pieces. Findings, not verdicts — always exits 0.",
    )
    c.add_argument("dir", help="directory of published work")
    c.add_argument("--pattern", default="*.md",
                   help="glob for files to include (default: *.md)")
    c.add_argument("--exclude-section", default="", metavar="REGEX",
                   help="drop markdown sections whose heading matches, e.g. "
                        "'image prompt|schema' — production metadata repeats "
                        "across every file and swamps real findings")
    c.add_argument("--min-run", type=int, default=8, metavar="N",
                   help="word-run length that counts as verbatim reuse (default: 8)")
    c.add_argument("--json", action="store_true", help="machine-readable output")
    c.set_defaults(func=_corpus_cmd)

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
