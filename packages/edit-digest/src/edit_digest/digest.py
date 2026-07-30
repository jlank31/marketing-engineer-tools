"""Learn an editor's style from what they actually change.

Your editing history is training data you're already producing and almost
certainly throwing away. Every redline is someone telling you their preferences
in the clearest terms available, and most teams read each one once and bin it.

This reads before-and-after pairs and returns the patterns:

    Write "brands", not "vendors" (7x)
    Cut "very" (5x)

No model involved. It's `difflib` over word tokens, so it costs nothing to run
and gives the same answer every time.

THE ONE NON-OBVIOUS PART is the filter in `render_prompt_block()`. Raw word diffs
produce garbage on heavy rewrites: you get pairs like

    "aren't"  ->  "and founders are already"

which is an artifact of the alignment, not a preference. Feed that back into a
prompt and you've actively taught the model something false. So the prompt-facing
block only takes swaps where both sides are short AND the replacement is no
longer than the original. The human report keeps everything, because a person can
tell the difference and a prompt cannot.
"""

from __future__ import annotations

import difflib
import re
from collections import Counter
from dataclasses import dataclass, field

# A phrase this short is usually punctuation noise; this long is usually a
# rewrite rather than a preference.
MIN_PHRASE_CHARS = 4
MAX_DELETION_WORDS = 6
MAX_SUBSTITUTION_WORDS = 5

# The prompt-facing block is stricter still. See the module docstring.
MAX_PROMPT_WORDS = 3


@dataclass
class Digest:
    substitutions: list[tuple[str, str, int]] = field(default_factory=list)
    deletions: list[tuple[str, int]] = field(default_factory=list)
    pairs_analyzed: int = 0

    @property
    def empty(self) -> bool:
        return not (self.substitutions or self.deletions)


def _tokens(text: str) -> list[str]:
    return (text or "").split()


def _norm(phrase: str) -> str:
    """Trim punctuation and collapse whitespace, preserving inner apostrophes."""
    p = re.sub(r"\s+", " ", (phrase or "").strip())
    return p.strip(" ,.;:!?\"'()[]—-")


def compute(edits: list[dict], min_count: int = 3) -> Digest:
    """Find edits that recur at least `min_count` times.

    `edits` is a list of dicts with `original_text` and `edited_text`. Anything
    else on the dict is ignored, so you can pass rows straight from wherever you
    keep them.

    Deterministic: same input, same output, no network.
    """
    subs: Counter[tuple[str, str]] = Counter()
    dels: Counter[str] = Counter()
    analyzed = 0

    for e in edits:
        before = _tokens(e.get("original_text") or e.get("before") or "")
        after = _tokens(e.get("edited_text") or e.get("after") or "")
        if not before or not after:
            continue
        analyzed += 1
        for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, before, after).get_opcodes():
            if op == "delete":
                phrase = _norm(" ".join(before[i1:i2]))
                if len(phrase) >= MIN_PHRASE_CHARS and len(phrase.split()) <= MAX_DELETION_WORDS:
                    dels[phrase.lower()] += 1
            elif op == "replace":
                b = _norm(" ".join(before[i1:i2]))
                a = _norm(" ".join(after[j1:j2]))
                if (
                    b and a and b.lower() != a.lower()
                    and len(b.split()) <= MAX_SUBSTITUTION_WORDS
                    and len(a.split()) <= MAX_SUBSTITUTION_WORDS
                ):
                    subs[(b.lower(), a.lower())] += 1

    return Digest(
        substitutions=[(b, a, n) for (b, a), n in subs.most_common() if n >= min_count],
        deletions=[(p, n) for p, n in dels.most_common() if n >= min_count],
        pairs_analyzed=analyzed,
    )


def render_prompt_block(digest: Digest, max_rules: int = 20) -> str:
    """The block you paste into your AI prompt. Deliberately conservative.

    Only takes swaps where both sides are 3 words or fewer AND the replacement is
    no longer than the original. That second condition is doing the real work: it
    drops alignment artifacts from heavy rewrites, which read as confident
    instructions and would teach the model something false.

    Returns "" when nothing survives the filter, which is the correct outcome for
    a thin corpus. An empty block beats a wrong one.
    """
    clean = [
        (b, a, n) for b, a, n in digest.substitutions
        if len(b.split()) <= MAX_PROMPT_WORDS and len(a.split()) <= len(b.split())
    ]
    if not clean and not digest.deletions:
        return ""

    lines = [
        "## Apply these every time",
        "The exact swaps and cuts a human editor makes most often on this "
        "writing. Get them right in the first draft.",
        "",
    ]
    room = max_rules
    for before, after, n in clean[:room]:
        lines.append(f'- Write "{after}", not "{before}" ({n}x).')
        room -= 1
    for phrase, n in digest.deletions[: max(room, 0)]:
        lines.append(f'- Cut "{phrase}" ({n}x). The editor removes it every time.')
    lines.append("")
    return "\n".join(lines)


def render_report(digest: Digest, limit: int = 40) -> str:
    """The full human-readable report. Keeps what the prompt block filters out.

    A person can look at "aren't -> and founders are already" and see it's a diff
    artifact. That judgement is exactly what the prompt block can't make, which is
    why the two outputs differ.
    """
    if digest.empty:
        return (
            f"\nNo recurring patterns yet ({digest.pairs_analyzed} pairs analyzed).\n\n"
            "  A pattern needs to repeat before it's a pattern. Come back after\n"
            "  another few rounds of edits.\n"
        )

    out = [f"\nEdit digest: {digest.pairs_analyzed} before/after pairs\n"]
    if digest.substitutions:
        out.append(f"  Substitutions ({len(digest.substitutions)}):")
        for b, a, n in digest.substitutions[:limit]:
            survives = (
                len(b.split()) <= MAX_PROMPT_WORDS
                and len(a.split()) <= len(b.split())
            )
            note = "" if survives else "   (report only)"
            out.append(f'    {n:>3}x   "{b}" -> "{a}"{note}')
    if digest.deletions:
        out.append(f"\n  Deletions ({len(digest.deletions)}):")
        for p, n in digest.deletions[:limit]:
            out.append(f'    {n:>3}x   "{p}"')
    out.append(
        "\n  Rows marked (report only) are excluded from the prompt block:"
        "\n  they're long, or the replacement grew, which usually means a diff"
        "\n  artifact from a heavy rewrite rather than a preference."
    )
    return "\n".join(out) + "\n"


def to_dict(digest: Digest) -> dict:
    return {
        "pairs_analyzed": digest.pairs_analyzed,
        "substitutions": [
            {"before": b, "after": a, "count": n} for b, a, n in digest.substitutions
        ],
        "deletions": [{"phrase": p, "count": n} for p, n in digest.deletions],
    }
