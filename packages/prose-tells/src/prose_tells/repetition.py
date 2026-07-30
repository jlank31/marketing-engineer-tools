"""Cross-output repetition detection — the variety layer.

Written after 2026-07-21 feedback: as the pipeline produced more content, "the
writing is just less varied and interesting" — the same phrases, openers, and
stat blocks recur across weeks. The per-text AI-tell detectors in
`prose_tells.post_validators` can't see this: each piece passes alone while the
corpus converges. (Evidence at the time: one anecdote told 3x nearly verbatim
across the email campaigns, "human review gate" in 5 of 6 blogs, one sentence
verbatim in 2 blogs, the same 5-stat block pasted across 4+ pieces, and
"Most founders..." opening 7 posts in one export.)

This module is the deterministic counterpart: pure text functions that compare
a NEW draft against a corpus of recent output. Deliberately separate from
an idea-dedup gate — that compares angle TITLES at planning time;
this one compares finished BODY COPY. Different granularity,
different job (shingle overlap vs distinctive-bigram topics), so a shared
implementation would serve neither well.

No dependencies at all, so this imports cleanly from a CLI, a QC gate, or
a notebook. All findings are SOFT by design — they surface candidates for a
human to judge, and none of them should ever block a publish on their own.
"""

from __future__ import annotations

import re

# Words too common to signal reuse on their own. Small on purpose — shingles
# are 4-5 words long, so one stopword inside a shared shingle doesn't matter;
# we only need to drop shingles made ENTIRELY of glue.
_STOPWORDS = frozenset(
    (
        "a an and are as at be but by for from has have if in into is it its of on "
        "or that the their there this to was were will with you your we our they"
    ).split()
)

_WORD_RE = re.compile(r"[a-z0-9%$']+")
_URL_RE = re.compile(r"https?://\S+")
_STAT_RE = re.compile(r"\b\d[\d,]*(?:\.\d+)?%")


def normalize_tokens(text: str) -> list[str]:
    """Lowercase word tokens with URLs stripped and light suffix-folding.

    Folding is deliberately crude (plural/verb -s, -ing, -ed) — enough that
    "operators scan" and "operator scanning" share tokens, cheap enough to run
    over a 6-week corpus. Not a stemmer; don't grow it into one.
    """
    text = _URL_RE.sub(" ", text.replace("’", "'").lower())
    tokens = []
    for tok in _WORD_RE.findall(text):
        if len(tok) > 4:
            for suffix in ("ing", "ed", "es", "s"):
                if tok.endswith(suffix) and len(tok) - len(suffix) >= 3:
                    tok = tok[: -len(suffix)]
                    break
        tokens.append(tok)
    return tokens


def shingles(text: str, n: int = 5) -> set[str]:
    """Word n-gram shingles over normalized tokens, minus all-stopword grams."""
    tokens = normalize_tokens(text)
    out: set[str] = set()
    for i in range(len(tokens) - n + 1):
        gram = tokens[i : i + n]
        if all(t in _STOPWORDS for t in gram):
            continue
        out.add(" ".join(gram))
    return out


# Lines that are production metadata rather than prose: "SEO TITLE: ...",
# "META DESCRIPTION: ...", "SLUG: ...". An ALL-CAPS or Title-Case key followed by
# a colon, at the very start of a line.
_METADATA_LINE = re.compile(r"^[A-Z][A-Za-z ]{2,30}:\s")


def opening_line(text: str) -> str:
    """The draft's first line of actual prose — the hook a reader sees first.

    Skips markdown headings, horizontal rules, YAML frontmatter delimiters, and
    KEY: value metadata lines.

    This used to return the literal first non-empty line, which broke opener-echo
    detection on any format that front-loads metadata: every file beginning
    "SEO TITLE: ..." reported as echoing every other, because the compared
    "openers" were all the same metadata key. Six false pairs out of six on a real
    archive. The hook is what the reader meets, not what the CMS reads.
    """
    in_frontmatter = False
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line in ("---", "+++"):
            # Toggle: an opening delimiter starts frontmatter, the next ends it.
            in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter:
            continue
        if line.startswith("#") or set(line) <= set("-=*_ "):
            continue
        if _METADATA_LINE.match(line):
            continue
        return line
    return ""


def find_verbatim_runs(
    new_text: str, corpus: dict[str, str], min_run: int = 8
) -> list[tuple[str, str]]:
    """Return (snippet, source_label) for normalized word runs of >= min_run
    shared between `new_text` and any corpus entry.

    Catches the retold-anecdote / pasted-sentence failure ("They went
    heads-down for a quarter. Their LinkedIn went silent..." shipped 3x).
    A paraphrase that changes wording every few words never accumulates a run.
    Snippets are truncated to ~60 chars for readable reports.
    """
    new_tokens = normalize_tokens(new_text)
    if len(new_tokens) < min_run:
        return []
    new_runs = {
        " ".join(new_tokens[i : i + min_run]): i
        for i in range(len(new_tokens) - min_run + 1)
    }
    hits: list[tuple[str, str]] = []
    seen_snippets: set[str] = set()
    for label, old_text in corpus.items():
        old_tokens = normalize_tokens(old_text)
        old_runs = {
            " ".join(old_tokens[i : i + min_run])
            for i in range(len(old_tokens) - min_run + 1)
        }
        shared = new_runs.keys() & old_runs
        # Report each overlapping REGION once, not every offset of a long run:
        # consecutive start positions belong to the same reused passage.
        last_pos = -2
        for run in sorted(shared, key=new_runs.get):
            pos = new_runs[run]
            if pos == last_pos + 1:
                last_pos = pos
                continue
            last_pos = pos
            snippet = run if len(run) <= 60 else run[:57] + "..."
            if snippet not in seen_snippets:
                seen_snippets.add(snippet)
                hits.append((snippet, label))
    return hits


def phrasing_overlap(new_text: str, old_text: str, n: int = 5) -> int:
    """Count of shared n-word shingles between two texts. >= 3 against one
    prior piece reads as heavy phrasing reuse for social-length copy."""
    return len(shingles(new_text, n) & shingles(old_text, n))


def opener_echo(new_opener: str, recent_openers: list[str]) -> str | None:
    """Return the recent opener this one echoes, or None.

    Echo = same first 2 normalized tokens ("Most founders..." x7) OR any
    shared 3-shingle inside the opening line. First-2-token matching is
    aggressive by design: the opener is the single highest-repetition surface,
    and two posts starting identically read as a template even when the rest
    diverges.
    """
    new_tokens = normalize_tokens(new_opener)
    if len(new_tokens) < 2:
        return None
    new_head = tuple(new_tokens[:2])
    new_shingles = shingles(new_opener, 3)
    for old in recent_openers:
        old_tokens = normalize_tokens(old)
        if len(old_tokens) >= 2 and tuple(old_tokens[:2]) == new_head:
            return old
        if new_shingles & shingles(old, 3):
            return old
    return None


def stat_fingerprint(text: str) -> frozenset[str]:
    """The set of percentage stats a text cites ("52%", "45%", ...).

    Two pieces sharing >= 4 stats are running the same recycled stat block
    (the 52/86/82/45/64 cluster shipped in 4+ pieces). Percent stats only:
    they're the load-bearing citations in this corpus, and plain integers
    ("3 things", "14 days") false-positive too easily.
    """
    return frozenset(m.group(0).replace(",", "") for m in _STAT_RE.finditer(text or ""))
