#!/usr/bin/env python3
"""Copy mirrored files from the private upstream into this public repo.

Run from the public repo:

    python3 tools/promote.py --private ~/Documents/<private-repo>
    make promote PRIVATE=~/Documents/<private-repo>     # preferred

Design constraints, both load-bearing:

1. NOTHING PRIVATE EVER IMPORTS THIS REPO. The public copy is strictly
   downstream. That is what makes it safe to skip a promote for three weeks —
   and, more importantly, what means an 11pm fix to a detector that just let
   something bad through never waits on a PyPI publish.

2. SUBSTITUTIONS ARE DECLARED, ORDERED, AND LITERAL. No regex transforms of
   docstrings, no "strip the header" magic. A generated docstring is not
   reviewable; a literal find/replace pair is. If a file needs more than
   MAX_SUBS substitutions it is a FORK, not a mirror, and belongs in FORKS
   below with a note — silently maintaining a heavily-transformed copy is how
   the two versions quietly diverge.

This script never commits and never pushes. It copies, verifies, prints a diff
summary, and stops. A human reads the diff. That is the whole safety model.
"""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "packages/prose-tells/src/prose_tells"

MAX_SUBS = 5


class Sub:
    """One declared literal substitution. `required` means its absence is a bug.

    A substitution that silently matches nothing is the failure mode this class
    exists to prevent: the upstream comment gets reworded, the rule stops firing,
    and a private module path ships in a public docstring.
    """

    def __init__(self, find: str, replace: str, required: bool = True):
        self.find, self.replace, self.required = find, replace, required


class Mirror:
    def __init__(self, private_rel: str, public_path: Path, subs: list[Sub] | None = None):
        self.private_rel = private_rel
        self.public_path = public_path
        self.subs = subs or []


# ---------------------------------------------------------------------------
# The manifest.
#
# content_quality.py and repetition.py are stdlib-only and brand-clean upstream
# (enforced there by test_vendor_sync.py), so they copy essentially verbatim. The
# only rewrites are docstring references to private module paths, which would be
# dangling pointers in a published package.
# ---------------------------------------------------------------------------

MIRRORS: list[Mirror] = [
    Mirror("utils/content_quality.py", PKG / "content_quality.py"),
    Mirror(
        "utils/repetition.py",
        PKG / "repetition.py",
        subs=[
            Sub("`utils.post_validators`", "`prose_tells.post_validators`"),
            # Names a private module with no public counterpart. Rewritten to
            # describe the distinction rather than point at a file nobody has.
            Sub(
                "Deliberately separate from\n`agents.angle_diversity` — that gate dedupes angle TITLES/summaries at\nideation; this one compares finished BODY COPY.",
                "Deliberately separate from\nan idea-dedup gate — that compares angle TITLES at planning time;\nthis one compares finished BODY COPY.",
            ),
            # Consumer list: three private file paths that don't exist here.
            Sub(
                "No pipeline deps (importable from scripts, QC, and skills). Consumers:\n`scripts/lint_week.py` (cross-week + intra-week report), `agents/blog_qc.py`\n(sibling stat-fingerprint), `scripts/scan_worn_phrases.py` (--suggest corpus\ncounting). All findings are SOFT — the human review gate decides.",
                "No dependencies at all, so this imports cleanly from a CLI, a QC gate, or\na notebook. All findings are SOFT by design — they surface candidates for a\nhuman to judge, and none of them should ever block a publish on their own.",
            ),
        ],
    ),
    # Drop 3 (Aug 17). Blocked upstream until find_stale_event_reference takes an
    # `events=` parameter instead of lazily importing the registry loader — see
    # the DEBT note in the private test_vendor_sync.py MIRRORS table.
    # Mirror("utils/post_validators.py", PKG / "post_validators.py"),
]

# Files deliberately NOT mirrored, recorded so the reason survives.
FORKS = {
    "tracker.py": "Public UsageRecord dataclass vs the private pydantic row type. "
                  "60 lines of accumulator plumbing — drift here costs nothing, "
                  "unlike the detector engine where drift is a correctness bug.",
}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def promote_one(m: Mirror, private_root: Path) -> tuple[bool, list[str]]:
    src = private_root / m.private_rel
    notes: list[str] = []
    if not src.exists():
        return False, [f"  MISSING upstream: {src}"]

    text = src.read_text()
    if len(m.subs) > MAX_SUBS:
        return False, [
            f"  {m.private_rel}: {len(m.subs)} substitutions exceeds MAX_SUBS={MAX_SUBS}."
            " Treat this as a FORK, not a mirror."
        ]

    for s in m.subs:
        if s.find not in text:
            if s.required:
                return False, [
                    f"  {m.private_rel}: required substitution did not match.",
                    f"    looked for: {s.find[:70]!r}",
                    "    The upstream text changed. Update the manifest — do NOT"
                    " publish with a stale rule, or a private reference ships.",
                ]
            notes.append(f"  {m.private_rel}: optional substitution skipped (no match)")
            continue
        text = text.replace(s.find, s.replace)

    m.public_path.parent.mkdir(parents=True, exist_ok=True)
    changed = not m.public_path.exists() or m.public_path.read_text() != text
    if changed:
        m.public_path.write_text(text)
    notes.append(
        f"  {'UPDATED' if changed else 'unchanged'}  {m.private_rel}"
        f" -> {m.public_path.relative_to(ROOT)}"
        f" ({len(m.subs)} sub{'s' if len(m.subs) != 1 else ''})"
    )
    return True, notes


def write_hashes() -> Path:
    """Record public-copy hashes so CI can detect a direct edit to a mirrored file."""
    out = ROOT / "packages/prose-tells/VENDORED.sha256"
    lines = [
        "# Mirrored from a private upstream. Do not edit these files here —",
        "# see CONTRIBUTING.md. Regenerated by tools/promote.py.",
    ]
    for m in MIRRORS:
        if m.public_path.exists():
            lines.append(f"{sha(m.public_path)}  {m.public_path.relative_to(ROOT)}")
    out.write_text("\n".join(lines) + "\n")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--private", required=True, help="path to the private upstream repo")
    args = ap.parse_args()

    private_root = Path(args.private).expanduser().resolve()
    if not private_root.is_dir():
        print(f"  FAIL: --private is not a directory: {private_root}")
        return 1

    print(f"  upstream: {private_root}\n")
    ok = True
    for m in MIRRORS:
        good, notes = promote_one(m, private_root)
        ok &= good
        for n in notes:
            print(n)
    if not ok:
        print("\n  PROMOTE FAILED — nothing further was run.")
        return 1

    h = write_hashes()
    print(f"\n  wrote {h.relative_to(ROOT)}")
    if FORKS:
        print("\n  not mirrored (forks):")
        for name, why in FORKS.items():
            print(f"    {name}: {why}")

    print("\n  --- git diff --stat ---")
    subprocess.run(["git", "diff", "--stat"], cwd=ROOT, check=False)
    print(
        "\n  Nothing was committed or pushed. Read the diff, run `make check`,"
        "\n  then commit yourself."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
