"""Corpus-level analysis: what your whole archive reveals that no single file does.

The per-text detectors in `content_quality` read one piece at a time, which means
they structurally cannot see the failure mode that matters most once you've been
publishing for a while: every piece passes on its own while the library slowly
converges into one voice, telling one anecdote, citing one set of numbers.

That convergence is invisible from inside any single draft. You only see it by
reading everything at once, which nobody does. Hence this module.

Four findings, each answering a question you can't ask of one file:

    verbatim runs     which exact sentences have you published more than once
    opener echoes     how many pieces start the same way
    stat blocks       which statistics you keep recycling together
    worn phrases      which distinctive phrasings recur across many pieces

All of it is descriptive. Nothing here is a pass/fail — repetition is sometimes
deliberate (a positioning line you *want* consistent) and sometimes a rut. The
tool finds it; you decide which is which.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from .repetition import (
    find_verbatim_runs,
    opener_echo,
    opening_line,
    shingles,
    stat_fingerprint,
)

# A phrase must appear in at least this many documents before it counts as worn.
# Two is just a pair; three is a habit.
WORN_MIN_DOCS = 3

# Shared percentage stats before a pair counts as a recycled stat block. Tuned to
# match the upstream pipeline's threshold.
STAT_MIN_SHARED = 4


@dataclass
class CorpusReport:
    files: list[str] = field(default_factory=list)
    verbatim: list[tuple[str, str, str]] = field(default_factory=list)   # (a, b, snippet)
    openers: list[tuple[str, str]] = field(default_factory=list)         # (a, b)
    stat_blocks: list[tuple[str, str, int]] = field(default_factory=list)  # (a, b, shared)
    worn: list[tuple[str, int]] = field(default_factory=list)            # (phrase, doc count)

    @property
    def clean(self) -> bool:
        return not (self.verbatim or self.openers or self.stat_blocks or self.worn)


def drop_sections(text: str, heading_re: str) -> str:
    """Remove markdown sections whose heading matches, up to the next heading.

    Real archives carry production metadata in-band: cover-image prompts, schema
    dumps, changelogs. Those are templates, so they repeat across every file and
    swamp the genuine prose findings — on a 10-document archive an image-prompt
    boilerplate block produced three of the top verbatim hits.
    """
    if not heading_re:
        return text
    rx = re.compile(heading_re, re.IGNORECASE)
    out, skipping, skip_depth = [], False, 0
    for line in text.splitlines():
        m = re.match(r"^(#+)\s*(.*)$", line)
        if m:
            depth, title = len(m.group(1)), m.group(2)
            if skipping and depth <= skip_depth:
                skipping = False
            if not skipping and rx.search(title):
                skipping, skip_depth = True, depth
                continue
        if not skipping:
            out.append(line)
    return "\n".join(out)


def load_corpus(
    path: Path, pattern: str = "*.md", exclude_section: str = ""
) -> dict[str, str]:
    """Read every matching file under `path` into {label: text}.

    Labels are paths relative to `path`, so output stays readable when the
    directory is deep. Unreadable files are skipped rather than fatal — a corpus
    scan over someone's blog folder shouldn't die on one bad encoding.

    `exclude_section` is a regex matched against markdown headings; matching
    sections are dropped before analysis.
    """
    out: dict[str, str] = {}
    root = Path(path)
    for f in sorted(root.rglob(pattern)):
        if not f.is_file():
            continue
        try:
            body = f.read_text(errors="replace")
        except OSError:
            continue
        out[str(f.relative_to(root))] = drop_sections(body, exclude_section)
    return out


def _pair_key(a: str, b: str) -> tuple[str, str]:
    """Order-independent pair key, so A-vs-B and B-vs-A report once."""
    return (a, b) if a <= b else (b, a)


def analyze(corpus: dict[str, str], min_run: int = 8) -> CorpusReport:
    """Compare every document against every other. Returns findings, not verdicts."""
    report = CorpusReport(files=sorted(corpus))
    labels = report.files

    # --- verbatim runs -----------------------------------------------------
    # find_verbatim_runs compares one text against a corpus and returns
    # (snippet, source_label). Feeding it one document at a time and excluding
    # self keeps the pairing honest.
    seen_pairs: set[tuple[str, str, str]] = set()
    for label in labels:
        peers = {k: v for k, v in corpus.items() if k != label}
        for snippet, source in find_verbatim_runs(corpus[label], peers, min_run=min_run):
            a, b = _pair_key(label, source)
            key = (a, b, snippet)
            if key not in seen_pairs:
                seen_pairs.add(key)
                report.verbatim.append((a, b, snippet))

    # --- opener echoes -----------------------------------------------------
    # opener_echo takes an opener STRING and a list of other openers, so build
    # the opener list first rather than passing raw texts.
    openers = {label: opening_line(corpus[label]) for label in labels}
    seen_op: set[tuple[str, str]] = set()
    for label in labels:
        others = [openers[k] for k in labels if k != label]
        echoed = opener_echo(openers[label], others)
        if not echoed:
            continue
        match = next((k for k in labels if k != label and openers[k] == echoed), None)
        if match:
            pair = _pair_key(label, match)
            if pair not in seen_op:
                seen_op.add(pair)
                report.openers.append(pair)

    # --- recycled stat blocks ----------------------------------------------
    prints = {label: stat_fingerprint(corpus[label]) for label in labels}
    for i, a in enumerate(labels):
        for b in labels[i + 1:]:
            shared = prints[a] & prints[b]
            if len(shared) >= STAT_MIN_SHARED:
                report.stat_blocks.append((a, b, len(shared)))

    # --- worn phrases ------------------------------------------------------
    # Count DOCUMENTS per phrase, not occurrences. A phrase used six times in one
    # essay is a stylistic choice; the same phrase in six separate pieces is a rut.
    doc_counts: Counter[str] = Counter()
    phrase_docs: dict[str, set[str]] = defaultdict(set)
    for label in labels:
        for sh in shingles(corpus[label]):
            phrase_docs[sh].add(label)
    for phrase, docs in phrase_docs.items():
        if len(docs) >= WORN_MIN_DOCS:
            doc_counts[phrase] = len(docs)
    report.worn = doc_counts.most_common(25)

    return report


def render(report: CorpusReport, limit: int = 12) -> str:
    """Human-readable report. Leads with the count so the headline is the number."""
    n = len(report.files)
    lines = [f"\nCorpus: {n} document{'s' if n != 1 else ''}"]

    if n < 2:
        lines.append(
            "\n  Need at least 2 documents to compare. Point --corpus at a folder"
            "\n  with more than one file."
        )
        return "\n".join(lines)

    if report.clean:
        lines.append(
            "\n  No cross-document repetition found."
            "\n  Worth noting this only looks for reuse, not for quality, and with a"
            "\n  small corpus there simply isn't much to find yet."
        )
        return "\n".join(lines)

    if report.verbatim:
        lines.append(f"\n  Verbatim reuse ({len(report.verbatim)}):")
        for a, b, snippet in report.verbatim[:limit]:
            lines.append(f"    {a}  ↔  {b}")
            lines.append(f"      \"{snippet}\"")
        if len(report.verbatim) > limit:
            lines.append(f"    ... and {len(report.verbatim) - limit} more")

    if report.openers:
        lines.append(f"\n  Echoed openers ({len(report.openers)}):")
        for a, b in report.openers[:limit]:
            lines.append(f"    {a}  ↔  {b}")

    if report.stat_blocks:
        lines.append(f"\n  Recycled stat blocks ({len(report.stat_blocks)}):")
        for a, b, shared in report.stat_blocks[:limit]:
            lines.append(f"    {a}  ↔  {b}   ({shared} shared figures)")

    if report.worn:
        lines.append(f"\n  Phrases appearing in {WORN_MIN_DOCS}+ documents:")
        for phrase, count in report.worn[:limit]:
            lines.append(f"    {count:>2} docs   \"{phrase}\"")
        lines.append(
            "\n  These are candidates, not violations. Some repetition is your"
            "\n  positioning working. Promote the ones you want to retire to a"
            "\n  banned list yourself. Nothing here should graduate automatically."
        )

    return "\n".join(lines)


def to_dict(report: CorpusReport) -> dict:
    return {
        "files": report.files,
        "verbatim": [{"a": a, "b": b, "snippet": s} for a, b, s in report.verbatim],
        "openers": [{"a": a, "b": b} for a, b in report.openers],
        "stat_blocks": [{"a": a, "b": b, "shared": n} for a, b, n in report.stat_blocks],
        "worn": [{"phrase": p, "documents": n} for p, n in report.worn],
    }
