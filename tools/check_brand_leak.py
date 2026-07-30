#!/usr/bin/env python3
"""Repo-wide pre-publication scan. The safety net under `make promote`.

Four families, ordered by how bad it is if one ships:

  CRITICAL  live credentials — anything that grants access
  IDENTITY  infra identifiers — project refs, service accounts, doc IDs, portal
            IDs, email addresses. Not credentials, but they let someone
            enumerate or target the private system.
  CLIENT    client / prospect / person names and internal codenames
  RECON     internal module paths, DB table names, env vars. Report-only: a
            public package legitimately names its own modules, so this family
            exists to be eyeballed, not to gate.

Why this runs repo-wide and not just over mirrored files: the mirrored files are
already guarded upstream by the private repo's test_vendor_sync.py. The leak risk
here is everything ELSE — a README example, a test fixture, a drop note written
in a hurry at 11pm.

Usage:
    check_brand_leak.py                 # scan the whole repo (git-tracked + untracked)
    check_brand_leak.py path [path ...] # scan specific paths

Exit 1 if anything in CRITICAL / IDENTITY / CLIENT hits.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", ".pytest_cache", ".ruff_cache", "dist", "build"}
SKIP_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".webp", ".ico", ".zip", ".woff", ".woff2"}

# This file necessarily contains every token it searches for. So does any doc
# explaining the policy. Both are exempt by path.
SELF_EXEMPT = {"tools/check_brand_leak.py", "tools/promote.py", "CONTRIBUTING.md"}

RULES: list[tuple[str, str, re.Pattern[str]]] = [
    # ---------------- CRITICAL ----------------
    ("anthropic key",       "CRITICAL", re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}")),
    ("openai key",          "CRITICAL", re.compile(r"sk-(?:proj-)?[A-Za-z0-9]{32,}")),
    ("github token",        "CRITICAL", re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}")),
    ("slack token",         "CRITICAL", re.compile(r"xox[baprs]-[A-Za-z0-9\-]{10,}")),
    ("slack webhook",       "CRITICAL", re.compile(r"hooks\.slack\.com/services/(?!YOUR|TEST|\.\.\.)\S+")),
    ("google api key",      "CRITICAL", re.compile(r"AIza[A-Za-z0-9_\-]{30,}")),
    ("aws key id",          "CRITICAL", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("private key block",   "CRITICAL", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY")),
    ("jwt",                 "CRITICAL", re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.")),
    ("db url with creds",   "CRITICAL", re.compile(r"(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)://[^\s:@/]+:[^\s@]+@")),
    ("perplexity key",      "CRITICAL", re.compile(r"\bpplx-[A-Za-z0-9]{20,}")),
    ("assigned secret",     "CRITICAL", re.compile(
        r"(?i)\b(?:api[_-]?key|secret|passwd|password|access[_-]?token|bearer)\b\s*[:=]\s*"
        r"['\"][A-Za-z0-9_\-]{16,}['\"]")),

    # ---------------- IDENTITY ----------------
    ("supabase project",    "IDENTITY", re.compile(r"\b(?!x{4})[a-z0-9]{15,}\.supabase\.(?:co|in)\b")),
    ("gcp service account", "IDENTITY", re.compile(r"[A-Za-z0-9._%-]+@[a-z0-9-]+\.iam\.gserviceaccount\.com")),
    ("google file id",      "IDENTITY", re.compile(r"\b1[A-Za-z0-9_\-]{32,}\b")),
    ("hubspot portal",      "IDENTITY", re.compile(r"\b44217588\b")),
    # Allow the LinkedIn/GitHub profile links that are deliberately public.
    ("email address",       "IDENTITY", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    ("scheduler host",      "IDENTITY", re.compile(r"(?i)\bdata\.postforme\.dev\b|\bpostforme\b|\bpost4me\b")),

    # ---------------- CLIENT ----------------
    # Removing a client's NAME is not enough. The incident story has to go too:
    # "the week a client's copy promoted a show that had already ended" is a
    # readable client report even with the name stripped. Reviewers: check the
    # sentence, not just the token.
    #
    # Deliberately NOT in this list: the publisher's own company name. It belongs
    # in LICENSE, NOTICE, and the README byline, and blocking it there was this
    # rule's first false positive. The distinction the list encodes is author vs
    # client — publishing your own name is the opposite of a leak. Internal
    # product and system codenames stay banned even though they're also "ours",
    # because those name commercial work the public repo has no business
    # describing.
    ("client / brand",      "CLIENT", re.compile(
        r"(?i)\b(?:popcorn|air\s?cover|aircover|opsage|one\s?goal|onegoal|ogc"
        r"|brand\s?os|molinari|haselhoff|freecandy|khumbu"
        r"|cap\s?energy|livelytics|onesource|bikky|marqii|ripplefeedback"
        r"|outlever|msmr)\b")),
    ("private doc pointer", "CLIENT", re.compile(r"feedback_[a-z_0-9]+\.md|\bclients/[a-z0-9-]+")),
    ("retired integration", "CLIENT", re.compile(r"(?i)\bcanva\b")),
    ("vertical event",      "CLIENT", re.compile(r"(?i)\b(?:nra\s+show|murtec|fstec|mufso)\b")),

    # ---------------- RECON (report only) ----------------
    ("absolute local path", "RECON", re.compile(r"/Users/[a-z]+|~/Documents/")),
    ("private module path", "RECON", re.compile(r"\b(?:utils|agents|scripts|models)\.[a-z_]{3,}")),
    ("private db table",    "RECON", re.compile(
        r"\b(?:content_drafts|human_edits|client_onboarding|qc_signals"
        r"|pipeline_dispatch|postforme_project_keys|site_pages)\b")),
    ("private env var",     "RECON", re.compile(r"\b(?:BRANDOS|POSTFORME|SUPABASE|HUBSPOT|SLACK)_[A-Z_]+\b")),
]

BLOCKING = {"CRITICAL", "IDENTITY", "CLIENT"}


def candidate_files(args: list[str]) -> list[Path]:
    if args:
        out: list[Path] = []
        for a in args:
            p = Path(a)
            out.extend(sorted(q for q in p.rglob("*") if q.is_file()) if p.is_dir() else [p])
        return out
    try:
        listed = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.split("\n")
        return [ROOT / f for f in listed if f]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return [p for p in ROOT.rglob("*") if p.is_file()]


def scannable(p: Path) -> bool:
    if not p.is_file():
        return False
    if any(part in SKIP_DIRS for part in p.parts):
        return False
    if p.suffix.lower() in SKIP_SUFFIXES:
        return False
    try:
        return str(p.resolve().relative_to(ROOT)) not in SELF_EXEMPT
    except ValueError:
        return True


def main(argv: list[str]) -> int:
    hits: dict[str, list[str]] = {}
    scanned = 0
    for path in candidate_files(argv):
        if not scannable(path):
            continue
        scanned += 1
        try:
            lines = path.read_text(errors="replace").splitlines()
        except OSError:
            continue
        try:
            shown = path.resolve().relative_to(ROOT)
        except ValueError:
            shown = path
        for i, line in enumerate(lines, 1):
            for label, family, rx in RULES:
                m = rx.search(line)
                if m:
                    hits.setdefault(family, []).append(
                        f"    {shown}:{i}  [{label}]  {m.group(0)[:60]!r}"
                    )

    print(f"  scanned {scanned} file(s)\n")
    rc = 0
    for family in ("CRITICAL", "IDENTITY", "CLIENT", "RECON"):
        rows = hits.get(family, [])
        if not rows:
            print(f"  {family:<9} clean")
            continue
        gate = "BLOCKING" if family in BLOCKING else "review only"
        print(f"  {family:<9} {len(rows)} hit(s)  ({gate})")
        for r in rows[:60]:
            print(r)
        if len(rows) > 60:
            print(f"    ... and {len(rows) - 60} more")
        print()
        if family in BLOCKING:
            rc = 1

    if rc:
        print("  BLOCKED. Fix the hits above, or add a deliberate exemption with a")
        print("  comment explaining why it is safe. Do not widen a rule to silence it.")
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
