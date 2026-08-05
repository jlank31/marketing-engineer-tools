"""Shared post-text validators used by humanizer and qc.

Single source of truth for content checks that need identical behavior in
multiple agents — duplicating regexes across files is what caused the 2026-05
"Thursday URL got dropped" bug. Both humanizer and qc had the same too-greedy
bare-URL regex that flagged perfectly good `"Full breakdown:\\n\\nhttps://..."`
patterns as bare URLs, which caused the audit_and_fix LLM pass to rewrite
the post and drop the URL entirely.
"""

from __future__ import annotations

import re

# Canonical URL extraction pattern for social-post bodies. Stops at whitespace,
# closing bracket/paren/quote — terminators that commonly appear after a URL
# in a sentence ("...Full breakdown: https://example.com/page).") but never
# inside one. This was previously copy-pasted in 5 places (qc.py x2,
# sheet_publisher.py x2, x_writer.py x1) — same regex, no variation.
#
# Note: newsletter_qc / newsletter_drafter use a slightly different pattern
# (also excludes `<` for HTML safety) and utm.py uses yet another (excludes
# `>` and `'`). Those are intentionally different and NOT consolidated here.
URL_PATTERN = re.compile(r'https?://[^\s\)\]"]+')

# Bland filler phrases that signal AI-generated content. Catches both the
# "thoughtful pause" tells (`let that sink in`) and the LinkedIn-essay
# openers (`let's dive in`). Used by humanizer.py (rewrite trigger),
# qc.py (issue flag), and newsletter_qc.py (issue flag) — these were
# three separately-maintained lists that drifted (humanizer said
# "think about that"; qc said "think about that for a second"; same idea,
# different reach). One canonical list as of 2026-05-03.
BANNED_PHRASES = (
    "that's a signal",
    "here's the thing",
    "here's what i mean",
    "the reality is",
    "let that sink in",
    "think about that",
    "read that again",
    "full stop",
    "spoiler alert",
    "let's dive in",
    # Faux-profound "that's the whole X" closers that read as AI throat-clearing.
    # Banned as a FAMILY (Jared, 2026-06-26): "that's the whole game" and every
    # near-clone. Replace with a specific observation or the concrete stakes,
    # never a stock "this is the essential thing" tag. Both contracted and
    # expanded forms are listed (the contraction rule turns "that is" -> "that's",
    # but a draft can arrive either way); find_banned_phrases also normalizes
    # curly apostrophes so smart-quote drafts still match.
    "that's the whole game",
    "that is the whole game",
    "that's the entire game",
    "that is the entire game",
    "that's the whole ballgame",
    "that is the whole ballgame",
    "that's the ballgame",
    "that is the ballgame",
    "that's the name of the game",
    "that is the name of the game",
    "that's the whole point",
    "that is the whole point",
    "that's the secret",
    "that is the secret",
    "that's the magic",
    "that is the magic",
    # Manufactured-stakes fixed clichés (2026-07-21, prompted by a viral
    # LinkedIn post on "tension cosplay"). The inflecting families ("quietly
    # kills", "silent failure") live in find_manufactured_stakes below; these
    # are the frozen forms that recurred in live copy and don't fit those
    # regexes. "silent qualifier" was a campaign coinage, retired 2026-07-21.
    "does less than nothing",
    "silent qualifier",
    "the buyer assumes the worst",
)


def find_banned_phrases(text: str) -> list[str]:
    """Return all BANNED_PHRASES that appear in `text` (case-insensitive).

    Returns the matched phrases in BANNED_PHRASES declaration order so
    callers get a stable result for logging/tests.
    """
    # Normalize curly apostrophes to straight so smart-quote drafts ("that’s")
    # still match the straight-quote phrases in BANNED_PHRASES.
    text_lower = text.lower().replace("’", "'")
    return [p for p in BANNED_PHRASES if p in text_lower]


# The "negate then assert" reversal: "The gap isn't talent. It's distance...",
# "It's not X. It's Y." A strong AI-writing tell Jared bans across ALL content
# (social + articles). The humanizer rewrites it for pipeline posts, but
# hand/subagent-authored articles bypass that — scan them with this. Targets the
# punchy two-sentence form (short negated clause, then It's/That's/They're).
#
# The `["'”’)\]]*` after the sentence-ender catches the QUOTE-MASKED form, where
# the negated clause ends inside quotation marks: `isn't "avoid AI." It's keep a
# human in the loop`. Without it the closing quote between the period and the
# space slipped past (a real #22 blog miss, 2026-06-29). `norm` already folds the
# curly apostrophe to a straight one; the class also allows the curly close quote.
# The negation half of the period form. `'s not` / `'re not` were added
# 2026-07-29: the list spelled out "is not" and "are not" as two words, so the
# contracted-auxiliary form slipped through entirely —
#   "It's not a tooling problem. It's a distance problem."   MISSED
#   "It isn't a tooling problem. It's a distance problem."   caught
# Same construction, and the first is the more common way to write it. CLAUDE.md
# names "It's not X. It's Y." as banned explicitly, so this was a real hole in
# live-copy protection. The inconsistency is the argument for the fix: "There
# isn't much time. It's fine." already flagged, so this adds no new class of
# false positive — it just stops the detector depending on which way the writer
# punctuated "is".
_REVERSAL_NEG = (
    r"isn't|aren't|wasn't|weren't|is not|are not|was not|were not"
    r"|'s not|'re not"
)

_REVERSAL_RE = re.compile(
    rf"(?i)\b({_REVERSAL_NEG})\b"
    r"[^.!?|]{0,45}[.!?]+[\"'”’)\]]*\s+(it's|it is|that's|that is|they're|they are)\b"
)

# The COMMA-form contrast, the most-flagged AI formula on LinkedIn in 2026
# (~-9% reach per the Search Engine Land AI-tics study, 2026). The period-form
# _REVERSAL_RE above requires a sentence-ender between the halves, so it MISSES
# the far more common comma join:
#   "It's not just speed, it's efficiency."   ("not just/only/about ..., it's Y")
#   "More than a tool, it's a system."         ("more than a/an/just ..., it's Y")
# Both are the same negate-then-assert elevation move, just punctuated softer.
# Kept as a SEPARATE pattern (not folded into _REVERSAL_RE) because the trigger
# words differ ("not just" / "more than" vs the auxiliary-negation of the period
# form). find_reversal_patterns runs both so every caller inherits the coverage.
_REVERSAL_COMMA_RE = re.compile(
    r"(?i)\b(?:not (?:just|only|about)|more than (?:a|an|just))\b"
    r"[^.!?|]{0,45}[,;]\s+(it's|it is|that's|that is|they're|they are)\b"
)


# The BARE comma reversal: "The gap isn't talent, it's proximity."
#
# Deliberately SEPARATE from find_reversal_patterns and reported SOFT, because
# unlike "not just X, it's Y" this shape overlaps ordinary speech — "it isn't
# broken, it's just slow" is a normal sentence. The AI version is the same
# negate-then-assert elevation move, so it's worth surfacing; it is NOT worth
# failing a publish over. Callers should warn, never block.
_REVERSAL_COMMA_BARE_RE = re.compile(
    rf"(?i)\b({_REVERSAL_NEG})\b"
    r"[^.!?|]{0,45}[,;]\s+(it's|it is|that's|that is|they're|they are)\b"
)


def find_soft_reversal_comma(text: str) -> list[str]:
    """Bare comma-form reversal ("X isn't A, it's B"). SOFT — warn, don't block.

    find_reversal_patterns covers the shapes confident enough to fail on. This
    covers the one that shades into ordinary English, so it exists to be
    surfaced for a human rather than enforced.
    """
    norm = text.replace("\u2019", "'")
    # Compare by OVERLAP, not equality: the hard and soft patterns anchor at
    # different offsets, so the same sentence yields two differently-trimmed
    # fragments and an equality check reported it twice.
    hard = [h.lower() for h in find_reversal_patterns(text)]
    out, seen = [], set()
    for m in _REVERSAL_COMMA_BARE_RE.finditer(norm):
        frag = m.group(0).strip()
        low = frag.lower()
        if low in seen:
            continue
        if any(low in h or h in low for h in hard):
            continue
        seen.add(low)
        out.append(frag)
    return out


def find_reversal_patterns(text: str) -> list[str]:
    """Return 'negate then assert' reversal snippets ('X isn't A. It's B.').

    Covers both the period form ("X isn't A. It's B.") and the comma-join form
    ("It's not just A, it's B." / "More than a tool, it's a system."). Jared
    bans this construction everywhere. Use in article/copy QC; the humanizer
    BANNED_PATTERNS prompt covers it for the social pipeline.
    """
    norm = text.replace("’", "'")
    matches = [m.group(0).strip() for m in _REVERSAL_RE.finditer(norm)]
    matches += [m.group(0).strip() for m in _REVERSAL_COMMA_RE.finditer(norm)]
    return matches


# Empty emphasis/descriptor words that read as an AI tell. "actually", "actual",
# "literally", and "genuinely" almost never add information — they're verbal
# throat-clearing that the brand team edits out in favor of direct copy ("the
# actual cost is X" → "the cost is X"; "what actually works" → "what works";
# "literally doubled" → "doubled"; "genuinely useful" → "useful"). Jared kept
# stripping these from weekly drafts (2026-06), so they're caught at every copy
# layer: drafter prompt (avoid at generation), humanizer (rewrite trigger so the
# fix happens before human review), qc and newsletter_qc (flag survivors), and
# the deterministic no-rewrite copy paths. Word-boundary matched so stems are
# safe — "factual", "actualize", "actuality", "actuator", "literal", "literary",
# "genuine" (adjective: "genuine interest") never hit. Scoped on purpose; Jared
# is fine with "really"/"very"/"just"/"simply" depending on use, so those are
# intentionally NOT here. Add more only when a specific word recurs. "truly" and
# "seamlessly" were added 2026-07 from the AI-tells refresh — both are empty
# adverbs that ChatGPT overuses ("seamlessly" is one of the top AI tells) and
# strip cleanly ("seamlessly integrates" → "integrates", "truly useful" →
# "useful"). "seamless"/"true" as adjectives are unaffected (word-boundary).


# ---------------------------------------------------------------------------
# 2026-07-29 refresh, ported from the shared engine (utils/content_quality.py).
# The patterns are lifted verbatim so the blog path and the social/newsletter
# path cannot disagree about what a tell is — a rule caught on one and missed on
# the other is the drift this whole arrangement exists to prevent.
# ---------------------------------------------------------------------------
# 2026-07-29 refresh. Six families the word-level detectors structurally miss,
# because each one is a SHAPE rather than a vocabulary choice. A draft can pass
# every banned-word check and still be obviously generated if it keeps doing
# these. Sources: the 2026 AI-tell literature (Forbes' Feb-2026 giveaway-signs
# piece, the contentbeta/oliviacal blacklists, Peter Yang's no-ai-slop skill) plus
# what the models observably overuse.
#
# All six use CLOSED lists, matching the rest of this module: an open-ended
# "noun + ?" or "any reassurance" pattern would false-positive on ordinary prose,
# and a detector that cries wolf gets switched off.
# ---------------------------------------------------------------------------

# The single most consistent cross-model tell in the 2026 literature: the
# reassurance opener. Claude, ChatGPT, and Gemini all reach for it to manufacture
# rapport before saying anything. "You're not wrong" is deliberately EXCLUDED —
# it's ordinary conversational English, unlike the fixed comfort phrases below.
_REASSURANCE_OPENER_RE = re.compile(
    r"(?i)\b(?:"
    r"(?:you'?re|you are) not (?:alone|imagining (?:it|this)|crazy|broken"
    r"|the only one|losing your mind)"
    r"|it'?s not just you|it is not just you"
    r"|if (?:this|that) (?:sounds|feels) familiar"
    r")\b"
)

# Noun-phrase question used as a fake-punchy transition ("The result? A 40% lift.").
# The rhythm is distinctive: a two-word question, then the answer as a fragment.
#
# This one is matched per line and anchored, not searched loosely, after three
# false positives on live content:
#   "## How do buyers ... tell the difference?"  a heading that happens to END
#                                               in a listed noun
#   "What is the reason?"                        an ordinary question
#   "### The catch?"                             a legitimate H2 structure
# The tell is a SHORT STANDALONE question, so it must start a line or follow
# sentence-ending punctuation, and heading lines are skipped entirely. A loose
# search matches the same words inside perfectly good prose.
_INTERROGATIVE_FRAGMENT_RE = re.compile(
    r"(?:^|(?<=[.!?])\s+)(?:the|their|our|my)\s+"
    r"(?:result|catch|problem|kicker|twist|upside|downside|difference|reason"
    r"|point|best part|worst part|reality|takeaway|fix|answer|issue|payoff)\?",
    re.IGNORECASE,
)

# Throat-clearing that claims candor instead of delivering it. If the next line
# were genuinely blunt it wouldn't need the warm-up.
_FALSE_CANDOR_RE = re.compile(
    r"(?i)\b(?:"
    r"let'?s be honest|let us be honest|let me be (?:honest|blunt|clear)|to be honest"
    r"|truth be told|here'?s the truth|here is the truth|the truth is"
    r"|if we'?re (?:being )?honest|if we are (?:being )?honest"
    r"|here'?s what nobody (?:tells|talks about|will tell)"
    r"|i'?ll be honest|real talk"
    r")\b"
)

# Asserting importance rather than demonstrating it. Always replaceable with the
# specific consequence, which is the actual information.
_OVERSTATEMENT_FORMULA_RE = re.compile(
    r"(?i)\b(?:"
    r"cannot be overstated|can'?t be overstated|speaks volumes|no small feat"
    r"|worth its weight in gold|needs no introduction|goes without saying"
    r"|it'?s no exaggeration|it is no exaggeration|more important than ever"
    r")\b"
)

# The pivot-to-product cliché. Nearly every AI-written marketing page contains
# one. "Enter <Product>." is the same move but deliberately NOT matched — "enter"
# has too many literal uses to catch safely.
_PRODUCT_PIVOT_RE = re.compile(
    # Both contracted and expanded auxiliaries. Listing only "that's" would
    # repeat the exact bug that hid "It's not X. It's Y." for months: a draft
    # can arrive either way, and the contraction pass runs later.
    r"(?i)\b(?:that'?s|that is|this is|here'?s|here is) where\b[^.!?]{1,45}?\bcomes? in\b"
)

# Correlative scaffolding and audience-hedging. Both are legitimate English, which
# is why they're SOFT by default — the tell is frequency, not any single use.
_CORRELATIVE_HEDGE_RE = re.compile(
    # "but also" is usually split by a pronoun ("but IT also", "but THEY also"),
    # so allow a short gap rather than requiring adjacency.
    r"(?i)\bnot only\b[^.!?]{0,70}\bbut\b[^.!?]{0,15}\balso\b"
    r"|\bwhether you'?re\b[^.!?]{0,45}\bor\b"
)

# Era-framing: manufactured historical momentum standing in for a real reason.
_ERA_FRAME_RE = re.compile(
    r"(?i)\b(?:gone are the days|in an era where|in the age of"
    r"|as we (?:move|head|step) into|in this new era|now more than ever)\b"
)

# Metaphorical "navigate". Literal navigation is fine, so this requires an
# abstract object — you can navigate a harbor, but "navigating the complexities"
# is filler for "dealing with".
_METAPHORICAL_NAVIGATE_RE = re.compile(
    r"(?i)\bnavigat(?:e|ing|es)\s+(?:the\s+|this\s+|these\s+)?"
    r"(?:complexit|ever-|challeng|nuance|intricac|landscape|waters|maze|minefield|terrain)"
)

_FILLER_INTENSIFIER_RE = re.compile(
    r"\b(actually|actual|literally|genuinely|truly|seamlessly)\b", re.IGNORECASE
)


# Expanded verb forms that should be contracted. This is conversational B2B
# social writing, and the contracted form is wanted everywhere ("are not" →
# "aren't"). Enforced at the same layers as the filler intensifiers: drafter
# prompt + humanizer rewrite + QC flag for social/newsletter copy (the LLM
# handles context), and apply_contractions() as the deterministic pass for copy
# paths that have no rewrite layer to lean on.
# Ordered longest-first so multi-word forms match before any substring could.
# Negatives are always safe ("not" after an auxiliary is unambiguous); the
# pronoun+be/will forms are safe in conversational copy. The human review gate
# is the backstop for the rare idiom where the expansion was intentional
# (e.g. "leave it as it is").
_CONTRACTIONS: tuple[tuple[str, str], ...] = (
    ("are not", "aren't"),
    ("is not", "isn't"),
    ("was not", "wasn't"),
    ("were not", "weren't"),
    ("does not", "doesn't"),
    ("do not", "don't"),
    ("did not", "didn't"),
    ("have not", "haven't"),
    ("has not", "hasn't"),
    ("had not", "hadn't"),
    ("would not", "wouldn't"),
    ("should not", "shouldn't"),
    ("could not", "couldn't"),
    ("will not", "won't"),
    ("must not", "mustn't"),
    ("cannot", "can't"),
    ("can not", "can't"),
    ("you are", "you're"),
    ("we are", "we're"),
    ("they are", "they're"),
    ("i am", "i'm"),
    ("it is", "it's"),
    ("that is", "that's"),
    ("there is", "there's"),
    ("here is", "here's"),
    ("what is", "what's"),
    ("who is", "who's"),
    ("he is", "he's"),
    ("she is", "she's"),
    ("i will", "i'll"),
    ("you will", "you'll"),
    ("we will", "we'll"),
    ("they will", "they'll"),
    ("it will", "it'll"),
    ("he will", "he'll"),
    ("she will", "she'll"),
)

# (expanded form, compiled \b-bounded pattern, contracted form).
_CONTRACTION_RES: tuple[tuple[str, re.Pattern, str], ...] = tuple(
    (expanded, re.compile(rf"\b{re.escape(expanded)}\b", re.IGNORECASE), contracted)
    for expanded, contracted in _CONTRACTIONS
)


def find_uncontracted_forms(text: str) -> list[str]:
    """Return expanded verb forms that should be contracted ("are not", "you
    are", ...), in first-appearance order, de-duplicated.

    Shared by qc.py / newsletter_qc.py (flag) and the humanizer (rewrite
    trigger) so generation, rewrite, and gate layers never drift on the
    contractions rule.
    """
    seen: list[str] = []
    for expanded, pattern, _ in _CONTRACTION_RES:
        if expanded not in seen and pattern.search(text):
            seen.append(expanded)
    return seen


def apply_contractions(text: str) -> str:
    """Deterministically contract expanded verb forms, preserving the case of
    the first letter ("Are not" → "Aren't").

    The counterpart to `find_uncontracted_forms` for copy paths with no
    downstream LLM rewrite — specifically on-image card text. Social /
    newsletter copy relies on the humanizer's context-aware rewrite instead.
    """
    if not text:
        return text

    def _replace(contracted: str):
        def _sub(m: re.Match) -> str:
            return contracted[0].upper() + contracted[1:] if m.group(0)[:1].isupper() else contracted
        return _sub

    for _, pattern, contracted in _CONTRACTION_RES:
        text = pattern.sub(_replace(contracted), text)
    return text


def find_filler_intensifiers(text: str) -> list[str]:
    """Return empty emphasis words ("actually"/"actual"/"literally") in `text`.

    Returns each distinct match (lowercased) in first-appearance order, so a
    post with two "actually"s reports it once. These descriptors rarely earn
    their space — prefer direct copy. Shared by drafter.py (prompt rule),
    humanizer.py (rewrite trigger) and qc.py (Needs Attention flag) so the
    three layers can never drift.
    """
    seen: list[str] = []
    for match in _FILLER_INTENSIFIER_RE.findall(text):
        lowered = match.lower()
        if lowered not in seen:
            seen.append(lowered)
    return seen


def strip_filler_intensifiers(text: str) -> str:
    """Remove empty emphasis words from `text` and tidy the seam.

    A deterministic counterpart to `find_filler_intensifiers` for copy paths
    with NO downstream LLM rewrite to lean on — specifically on-image card
    text, which goes straight from a cheap model to the human review gate.
    Social/newsletter copy uses the humanizer's smarter
    rewrite instead, so they call `find_filler_intensifiers` (flag) not this.

    Removal is conservative: drop the word, collapse the doubled space it
    leaves, repair a space-before-punctuation seam, and drop a now-orphaned
    leading comma at a sentence start ("Actually, the cost" → "The cost").
    Re-capitalizes the first letter if stripping a sentence-initial word
    lowercased it. Errs toward a clean cut; the human gate catches the rare
    case where "actual" was load-bearing ("actual vs projected").
    """
    if not text:
        return text
    cleaned = _FILLER_INTENSIFIER_RE.sub("", text)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)          # collapse doubled spaces
    cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned)    # " ," → ","
    cleaned = re.sub(r"[,;:]+([.!?])", r"\1", cleaned)    # "works,." → "works."
    cleaned = re.sub(r"(^|[.!?]\s+)[,;:]\s*", r"\1", cleaned)  # drop orphaned leading comma
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned).strip()
    if cleaned and text[:1].isupper() and cleaned[0].islower():
        cleaned = cleaned[0].upper() + cleaned[1:]
    return cleaned


# Spelled-out "percent" after a number. Jared's rule: always render the symbol
# ("52 percent" → "52%"). The symbol is tighter and reads less like AI prose.
# Matches a number (with optional thousands commas / decimal) followed by
# optional whitespace and the word "percent". `\bpercent\b` so "percentage" and
# "percentile" never match. Case-insensitive for sentence-start "Percent".
#
_SPELLED_PERCENT_RE = re.compile(
    r"(?<![\w%])(\d[\d,]*(?:\.\d+)?)\s*percent\b",
    re.IGNORECASE,
)


def find_spelled_percent(text: str) -> list[str]:
    """Return number-plus-"percent" fragments that should use the "%" symbol.

    Each distinct match (lowercased, whitespace-normalized — e.g. "52 percent")
    in first-appearance order. Shared by qc.py / newsletter_qc.py / lint_week
    (flag) and drafter.py (prompt rule) so generation and gate layers stay in
    sync. The deterministic counterpart for no-rewrite copy paths is
    `apply_percent_symbol`.
    """
    seen: list[str] = []
    for m in _SPELLED_PERCENT_RE.finditer(text):
        frag = re.sub(r"\s+", " ", m.group(0).strip()).lower()
        if frag not in seen:
            seen.append(frag)
    return seen


def apply_percent_symbol(text: str) -> str:
    """Deterministically rewrite "52 percent" → "52%".

    The counterpart to `find_spelled_percent` for copy paths with no downstream
    LLM rewrite (on-image cards, profile_renderer, apply_copy_rules) and as a
    backstop in the humanizer. Drops the word and any space, attaching "%"
    directly to the number. "25 to 30 percent" becomes "25 to 30%", which is
    standard.
    """
    if not text:
        return text
    return _SPELLED_PERCENT_RE.sub(lambda m: f"{m.group(1)}%", text)


# Structural scaffold / placeholder tokens that must never survive into
# finished copy. Their presence means a template or prompt delimiter leaked
# through instead of being replaced with real text — e.g. the drafter's
# system prompt once instructed output as "[HEADLINE]...[/HEADLINE]
# [BODY]...[/BODY]", and those markers occasionally landed inside a field
# value (the 2026-06 Thursday "[HEADLINE]/[BODY] in the copy" bug). Matched
# case-insensitively with an optional closing-tag slash, so [HEADLINE],
# [/headline], and [Body] all hit. Scoped to known scaffold words (not any
# bracketed text) to avoid false positives on legitimate copy like "[2026]".
_PLACEHOLDER_TOKEN_RE = re.compile(
    r"\[/?(?:HEADLINE|BODY|SUBHEAD(?:LINE)?|EYEBROW|CTA|TITLE|CAPTION|"
    r"HOOK|INTRO|OUTRO|PLACEHOLDER|INSERT|TODO|TKTK|IMAGE|TEXT)\]",
    re.IGNORECASE,
)


def find_placeholder_tokens(text: str) -> list[str]:
    """Return any structural scaffold/placeholder tokens left in `text`.

    Catches the [HEADLINE]/[BODY] (and kin) delimiters that must be replaced
    with real copy, never shipped literally. Used by qc.py to fail the draft
    loudly (so it surfaces in "Needs Attention") and by drafter.py to trigger
    a heal/retry before a leak can persist. Returns matches in document order,
    de-duplicated, for stable logging/tests.
    """
    seen: list[str] = []
    for token in _PLACEHOLDER_TOKEN_RE.findall(text):
        if token not in seen:
            seen.append(token)
    return seen


def extract_urls(text: str) -> list[str]:
    """Return all URLs in `text` using the canonical social-post pattern.

    Centralizes the regex previously duplicated in qc.py, sheet_publisher.py,
    and x_writer.py. Trailing punctuation (`.,;:!?`) is NOT stripped here —
    callers that need clean URLs should `.rstrip(".,;:!?")` themselves
    (matches the pre-existing call-site behavior).
    """
    return URL_PATTERN.findall(text)


def count_dashes(text: str) -> tuple[int, int]:
    """Return (em_dash_count, double_dash_count) in `text`.

    Em dashes (—) and `--` are both banned in social content.
    Both qc.py and humanizer.py independently checked for these;
    this helper unifies the count so the same number reaches both code paths.
    qc uses both counts in its issue message; humanizer only cares about
    presence (>0). One source of truth, two consumers.
    """
    return text.count("—"), text.count("--")


# Em dash / double-dash surrounded by optional spaces. Captured so we can
# collapse the surrounding whitespace and replace with a single deterministic
# substitute (comma-space) that reads naturally mid-sentence.
_EM_DASH_RE = re.compile(r"\s*(?:—|--)\s*")


def strip_em_dashes(text: str) -> str:
    """Deterministically remove em dashes (—) and double dashes (--).

    The counterpart to `count_dashes` for copy paths with no downstream LLM
    rewrite to lean on: the humanizer's deterministic backstop and any no-rewrite
    finalizer. Em dashes are banned everywhere in this content, and
    the LLM rewrite doesn't reliably strip them, so this guarantees none ship.

    Replaces " — " / "--" with ", " (comma-space), which reads naturally for the
    parenthetical-clause use the em dash most often stands in for. A dash flush
    against the following word (start/end of line, or "word—word") collapses to a
    single space rather than a stray leading/trailing comma.

    NOT quote-aware — callers that may hold verbatim customer quotes (e.g. a
    testimonial with an attribution em dash) must decide separately whether to
    apply it. The scheduling gate deliberately does NOT auto-run this for that
    reason; it belongs in the generation path where the copy is model-authored.
    """
    if not text:
        return text

    def _sub(m: re.Match) -> str:
        start, end = m.start(), m.end()
        at_edge = start == 0 or end == len(text) or text[start - 1] == "\n" or text[end : end + 1] == "\n"
        return " " if at_edge else ", "

    return _EM_DASH_RE.sub(_sub, text)


# URL-only line: optional whitespace, http(s)://..., optional trailing whitespace.
_URL_LINE_RE = re.compile(r"^\s*https?://\S+\s*$", re.MULTILINE)

# Words on the line immediately before a standalone URL that mean "this URL is
# the CTA, not a bare drop." Includes the most common phrasings the drafter
# uses: "Full breakdown:", "Read more:", "Listen here:", "Watch:", "Link:",
# "Source:", "Story:", "Details:", "Sign up:", "Join:", "Learn more:".
_CTA_CONTEXT_WORDS = re.compile(
    r"\b(read|see|learn|listen|watch|read more|here|below|link|more|"
    r"breakdown|story|details|join|sign up|source|full|continues?|"
    r"thread|article|episode|recap|video|preview|context)\b",
    re.IGNORECASE,
)


def has_bare_url(text: str) -> bool:
    """Return True if `text` contains a URL on its own line with no CTA context.

    A "bare URL" is a standalone URL line where the immediately preceding
    non-empty line provides no CTA context. URLs after CTA-style lines are
    fine — for example:

        Full breakdown, including the unit economics most vendors skip:

        https://example.com/article          ← NOT bare (colon + CTA word)

    But a URL with no preceding context IS bare:

        Some opening hook.

        https://example.com/article          ← bare (preceding line is just a sentence)

    The check looks at the line immediately before the URL line. It treats
    the URL as "has CTA context" if that prior line:
      - ends with `":"` (drafter's standard CTA pattern), OR
      - contains an action verb / CTA-indicator word (read, see, listen, etc.)

    This intentionally errs toward false-negative (letting a few real bare
    URLs slip through) rather than false-positive (flagging good content),
    because false-positive triggers a destructive audit_and_fix rewrite that
    can drop the URL — far worse than a slightly less polished post.
    """
    for match in _URL_LINE_RE.finditer(text):
        before = text[: match.start()].rstrip()
        if not before:
            # URL at very start of text with nothing before → truly bare.
            return True
        prev_line = before.split("\n")[-1].strip()
        if not prev_line:
            # Should be unreachable since we rstripped, but be defensive.
            return True
        if prev_line.endswith(":"):
            continue  # CTA pattern: "Full breakdown:" / "Read more:" / etc.
        if _CTA_CONTEXT_WORDS.search(prev_line):
            continue  # CTA-indicator word in the prior line.
        return True
    return False


# =============================================================================
# 2026 AI-tell refresh (added 2026-07). New deterministic detectors for tells
# that survived the original gates. All are SOFT (warning-level) in qc /
# newsletter_qc given false-positive risk; the human review gate is the backstop.
# Each returns distinct matches in
# first-appearance order (curly apostrophes normalized), like the detectors above.
# =============================================================================


def _distinct_matches(pattern: re.Pattern, text: str) -> list[str]:
    """Return distinct pattern matches in `text`, first-appearance order.

    Shared helper for the phrase-based AI-tell detectors below. Normalizes curly
    apostrophes so smart-quote drafts still match, and lowercases + collapses
    internal whitespace so "In  Today's" and "in today's" dedupe to one hit.
    """
    norm = text.replace("’", "'")
    seen: list[str] = []
    for m in pattern.finditer(norm):
        frag = re.sub(r"\s+", " ", m.group(0).strip()).lower()
        frag = re.sub(r"^[^\w]+", "", frag)  # drop any leading anchor punctuation (". ", etc.)
        if frag not in seen:
            seen.append(frag)
    return seen


# Clichéd openers. Anchored to post start or line start ((?:^|\n)\s*) so
# "here's how it works" mid-paragraph never false-positives — only the essay
# "Here's how ..." lead-in does. "Here's how" is the fastest-growing LinkedIn AI
# tell in 2026 (went from <3% to >16% of posts post-ChatGPT). Say the concrete
# thing directly instead of announcing it.
_HOLLOW_OPENER_RE = re.compile(
    r"(?im)(?:^|\n)\s*(?:"
    r"in the world of|in the realm of|"
    r"in today's (?:fast-paced|ever-changing|ever-evolving|digital|competitive)"
    r"\s+(?:landscape|world|environment|market)|"
    r"imagine (?:a|if|that)|picture (?:this|a)|"
    r"here's how|let's talk about"
    r")\b"
)


def find_hollow_openers(text: str) -> list[str]:
    """Return clichéd essay/opener phrases used at post or line start.

    Catches "In the world of ...", "Imagine a ...", "Picture this", "Here's how
    ...", and kin — hollow lead-ins that delay the concrete point. Anchored to
    line start so mid-sentence uses ("here's how it works") don't hit.
    """
    return _distinct_matches(_HOLLOW_OPENER_RE, text)


# Essay-scaffold connective tissue. "That said", "It's worth noting", the
# "In summary" family of conclusion-openers — connectors that announce structure
# instead of just saying the thing. "here's the thing" is deliberately absent
# (already in BANNED_PHRASES; dedupe rather than double-flag). Conclusion words
# ("ultimately"/"in short"/"in summary"/"in conclusion") are anchored to sentence
# start so "the ultimately responsible party" mid-sentence never hits.
_SCAFFOLD_TRANSITION_RE = re.compile(
    r"(?:"
    r"\bthat said\b|\bit'?s worth noting\b|\bit is worth noting\b|"
    r"\bneedless to say\b|\bat the end of the day\b|"
    r"\bhere's the part that surprises\b"
    r")"
    r"|(?:^|[.!?]\s+)(?:ultimately|in short|in summary|in conclusion)\b",
    re.IGNORECASE | re.MULTILINE,
)


def find_scaffold_transitions(text: str) -> list[str]:
    """Return essay-scaffold transitions ("That said", "In summary", ...).

    Connectors that announce structure rather than carry content. The
    conclusion-openers are anchored to sentence start; the mid-sentence
    connectors ("that said", "it's worth noting") match anywhere.
    """
    return _distinct_matches(_SCAFFOLD_TRANSITION_RE, text)


# Vague quantifiers-as-proof. "Countless", "a myriad of", "ever-evolving" — words
# that gesture at scale without a number. Anchor on specific figures instead. "in today's fast-paced landscape" is handled by the hollow
# opener; the standalone "fast-paced landscape" is caught here too.
_VAGUE_QUANTIFIER_RE = re.compile(
    r"(?i)\b(?:countless|a myriad of|myriad|ever-evolving|ever-changing|"
    r"fast-paced landscape|a plethora of|a wealth of|treasure trove)\b"
)


def find_vague_quantifiers(text: str) -> list[str]:
    """Return vague quantifiers-as-proof ("countless", "a myriad of", ...).

    These gesture at scale without committing to a number. Prefer a specific
    figure or drop the claim.
    """
    return _distinct_matches(_VAGUE_QUANTIFIER_RE, text)


# The "X is the difference between A and B" contrast formula — an insight-shaped
# frame that rarely earns the insight. Scoped to the DECLARATIVE predicate form
# ("<subject> is/are/was/were the difference between ...") so it flags the tell
# but NOT the legitimate interrogative "What's/What is the difference between X
# and Y?" (a real question the AEO blog format uses as FAQ headings — a false
# positive on published blog-02). The `(?<!what )` lookbehind drops the "What is
# the difference between ...?" question; the contracted "What's ..." form has no
# "is the difference" substring so it's excluded automatically. The contracted
# declarative ("That's the difference between ...") is left to the humanizer
# prompt — better to under-flag than false-positive on FAQ headings.
_CONTRAST_FORMULA_RE = re.compile(
    r"(?i)(?<!what )\b(?:is|are|was|were)\s+the difference between\b"
)


def find_contrast_formula(text: str) -> list[str]:
    """Return "X is the difference between A and B" contrast-formula hits.

    A twice-and-it's-a-tell rhetorical crutch. Rewrite as a plain statement.
    """
    return _distinct_matches(_CONTRAST_FORMULA_RE, text)


# Engagement-bait closing questions. The reflex "What about you?" ask, now so
# automatic on LinkedIn it reads as a script (and depresses reach). End on a
# specific observation or the concrete stakes instead.
_CLOSING_REFLEX_RE = re.compile(
    r"(?i)\b(?:what about you|what'?s your take|sound familiar|"
    r"who'?s with me|am i right|thoughts\?)\s*\??"
)


def find_closing_reflex_question(text: str) -> list[str]:
    """Return engagement-bait reflex questions ("What about you?", ...).

    The scripted comment-fishing close. Flagged wherever it appears (it's almost
    always at the end); rewrite to a concrete closing line.
    """
    return _distinct_matches(_CLOSING_REFLEX_RE, text)


# AI-tell verbs — CONSERVATIVE deterministic list. Only the words that are
# almost never used literally in B2B copy, so a hit is a real
# tell, not a false positive. Borderline words that have legitimate literal uses
# ("unlock", "leverage" (operating leverage), "elevate", "land", "surface",
# "drive") are deliberately EXCLUDED here and left to the humanizer BANNED_WORDS
# prompt, which is context-aware. Add a word here only if it's unambiguous.
_AI_TELL_VERB_RE = re.compile(
    r"(?i)\b(?:supercharg(?:e[sd]?|ing)|harness(?:e[sd]|ing)?|"
    r"revolutioni[sz]e[sd]?|revolutioni[sz]ing|spearhead(?:s|ed|ing)?|"
    r"delv(?:e[sd]?|ing))\b"
)


def find_ai_tell_verbs(text: str) -> list[str]:
    """Return unambiguous AI-tell verbs ("supercharge", "harness", "delve", ...).

    A conservative set — only verbs that rarely appear literally in this copy, so
    a match is a genuine tell. Replace with the plain verb.
    """
    return _distinct_matches(_AI_TELL_VERB_RE, text)


# "Manufactured stakes" / fake-drama framing (2026-07-21, prompted by a viral
# LinkedIn post on "tension cosplay"). Ominous music behind mundane advice —
# "this quietly kills your pipeline", "a silent failure", "slow trust leak",
# "while you're polishing decks, your competitors are shipping". If the insight
# were sharp, the copy wouldn't need to whisper ominously about what's
# "silently" happening. Three families, one public detector. Rewrite direction:
# state the plain cost with a number you can defend, or cut the line.
#
#
# False-positive guards (all deliberate — don't "fix" them):
# - The doom-verb list is CLOSED. "quietly launched / shipped / raised /
#   rolled out" are factual and never flag; "quietly reselling" (a real line in
#   _pending/blog-18) is a factual description, not manufactured doom, and is
#   intentionally not matched.
# - The window is [^.!?,\n]{0,40} — never crosses a sentence, line, or comma,
#   so "the team worked quietly. The pilot failed." never pairs, and neither
#   does "worked quietly, and costs fell 20%".
# - The stealth-noun list is CLOSED too: "silent mode", "silent auction",
#   "hidden menu", "hidden costs" (often literal in B2B) never flag.
# - The verb-first form allows only a 0-2 word gap ("fails quietly"), so
#   distant passives ("the leak was handled quietly by the team") under-flag
#   rather than over-flag — matching the repo's stated false-negative bias.
_STAKES_ADVERB_FIRST_RE = re.compile(
    r"(?i)\b(?:quietly|silently|slowly|invisibly)\b"
    r"[^.!?,\n]{0,40}?"
    r"\b(?:kill(?:s|ed|ing)?|fail(?:s|ed|ing|ures?)?|erode[sd]?|eroding|"
    r"bleed(?:s|ing)?|bled|leak(?:s|ed|ing)?|drain(?:s|ed|ing)?|"
    r"eat(?:s|ing)?|sabotages?|sabotaging|sabotaged|undermines?|undermining|"
    r"undermined|destroy(?:s|ed|ing)?|stall(?:s|ed|ing)?|rot(?:s|ted|ting)?|"
    r"cost(?:s|ing)?(?!-))\b"
)
_STAKES_VERB_FIRST_RE = re.compile(
    r"(?i)\b(?:kill(?:s|ed|ing)?|fail(?:s|ed|ing)?|erode[sd]?|eroding|"
    r"bleed(?:s|ing)?|leak(?:s|ed|ing)?|drain(?:s|ed|ing)?|sabotages?|"
    r"sabotaging|undermines?|undermining|stall(?:s|ed|ing)?|"
    r"rot(?:s|ted|ting)?)\s+(?:\w+\s+){0,2}?(?:quietly|silently|in silence)\b"
)
_STAKES_NOUN_RE = re.compile(
    r"(?i)\b(?:silent|quiet|invisible|slow)\s+(?:\w+[- ]){0,2}?"
    r"(?:killers?|failures?|leaks?|drains?|bleed|erosion|tax|death|rot|threats?)\b"
)
_STAKES_COMPETITOR_RE = re.compile(
    r"(?i)\bwhile (?:you'?re|you are|you)\b[^.!?\n]{0,50}?"
    r"\b(?:your competitors?|everyone else|the rest of the (?:market|industry))\b"
)


def find_manufactured_stakes(text: str) -> list[str]:
    """Return "manufactured stakes" / fake-drama fragments in `text`.

    Catches the ominous-framing tell in three forms: stealth adverb + doom verb
    ("quietly kills your pipeline", "fails silently"), stealth-noun phrases
    ("a silent failure", "slow trust leak"), and the competitor-dread frame
    ("while you're doing X, your competitors are Y"). Breathless tension around
    an ordinary observation is an AI tell — rewrite with the plain cost (a
    number or consequence you can defend) or cut the sentence. The frozen
    clichés from live copy ("does less than nothing", "silent qualifier") live
    in BANNED_PHRASES.
    """
    hits: list[str] = []
    for pattern in (
        _STAKES_ADVERB_FIRST_RE,
        _STAKES_VERB_FIRST_RE,
        _STAKES_NOUN_RE,
        _STAKES_COMPETITOR_RE,
    ):
        for frag in _distinct_matches(pattern, text):
            if frag not in hits:
                hits.append(frag)
    return hits


def find_worn_phrases(
    text: str, phrases: list[str], openers: list[str] = ()
) -> list[str]:
    """Return worn-out (overexposed) phrases present in `text`.

    Parameterized rather than a module constant on purpose: the worn list is
    DATA: a JSON list you maintain by hand without a code change, and it
    can differ from one project to the next.
    `phrases` match anywhere (case-insensitive substring, curly apostrophes
    normalized, like find_banned_phrases); `openers` match only when the
    text's first non-empty line starts with them — "most founders" is normal
    English mid-sentence and a burned template as a hook. These are the
    variety layer, not bans: SOFT everywhere, never a qc hard issue.
    """
    norm = text.lower().replace("’", "'")
    found = [p for p in phrases if p.lower().replace("’", "'") in norm]
    if openers:
        first_line = next(
            (ln.strip() for ln in norm.splitlines() if ln.strip()), ""
        )
        for opener in openers:
            o = opener.lower().replace("’", "'")
            if first_line.startswith(o) and opener not in found:
                found.append(f"{opener} (as opener)")
    return found


# Forward-looking cues that imply an event is upcoming/current rather than being
# referenced retrospectively. Paired with a PAST event's name below so a purely
# retrospective mention ("at the spring summit we saw…") does NOT false-positive.
_UPCOMING_EVENT_CUE_RE = re.compile(
    r"(?i)\b(?:"
    r"heading to|join us|see you|we'?ll be (?:at|there)|come by|stop by|"
    r"this year'?s|get ready for|gear(?:ing)? up|ahead of|before the|"
    r"game plan for|what to expect at|prep(?:ping)? for|register (?:now|for|today)|"
    r"don'?t miss|coming up|next (?:week|month)|skip the noise|"
    r"our booth|visit us"
    r")\b"
)


def find_stale_event_reference(
    text: str, today=None, events: list[dict] | None = None
) -> list[str]:
    """Flag copy that references an already-PASSED industry event as upcoming.

    For each event whose end_date is before `today`, if the copy names it AND
    carries a forward-looking cue ("game plan for", "heading to", "this year's",
    "skip the noise", …), it's flagged. Returns "<name> (ended YYYY-MM-DD)" per
    match.

    `events` is a list of dicts with `name`, `aliases`, `start_date`, `end_date`.
    It is INJECTED rather than imported. Until 2026-07-30 this function reached
    into the app's config loader, which was the single line contradicting this
    module's "stdlib only, no dependencies, ever" header — and it went unnoticed
    for months because the import sat inside the function body where nothing was
    looking. Callers now bind the registry explicitly (see utils/validators_bound).

    Passing no events returns [] rather than raising. That is a real trade-off:
    a caller that forgets to bind gets a silently disabled detector, which is the
    failure class this codebase otherwise bans. The mitigation is a wiring test
    asserting every consumer imports the BOUND wrapper, not this raw function.

    SOFT/warning-level. The human review gate is the backstop. This is the
    deterministic catch for the 2026-07 leak where a trade show that had already
    ended shipped as upcoming.
    """
    if not text or not events:
        return []
    from datetime import datetime

    now = (today or datetime.now())
    if hasattr(now, "hour"):
        now = now.replace(hour=0, minute=0, second=0, microsecond=0)
    norm = text.replace("’", "'")
    if not _UPCOMING_EVENT_CUE_RE.search(norm):
        return []

    hits: list[str] = []
    for ev in events:
        end_str = ev.get("end_date") or ev.get("start_date", "")
        try:
            end = datetime.strptime(end_str, "%Y-%m-%d")
        except ValueError:
            continue
        if end >= now:
            continue  # upcoming or current — fine
        name = ev.get("name") or (ev.get("aliases") or [""])[0]
        for alias in ev.get("aliases", []):
            if re.search(rf"(?i)\b{re.escape(alias)}\b", norm):
                frag = f"{name} (ended {end_str})"
                if frag not in hits:
                    hits.append(frag)
                break
    return hits


def _distinct_shape(pattern: re.Pattern, text: str) -> list[str]:
    """Dedupe helper for the shape detectors. Mirrors _distinct_matches."""
    seen, out = set(), []
    for m in pattern.finditer(text.replace("\u2019", "'")):
        frag = m.group(0).strip()
        if frag.lower() not in seen:
            seen.add(frag.lower())
            out.append(frag)
    return out


def find_reassurance_opener(text: str) -> list[str]:
    """Manufactured rapport: "You're not alone", "It's not just you".

    The most consistent cross-model tell in the 2026 literature — Claude, ChatGPT
    and Gemini all reach for it to build rapport before saying anything.
    """
    return _distinct_shape(_REASSURANCE_OPENER_RE, text)


def find_interrogative_fragment(text: str) -> list[str]:
    """Fake-punchy transitions: "The result?", "The catch?".

    Line-aware: markdown headings are skipped, because an H2 reading "The catch?"
    is a legitimate document structure rather than a prose tic.
    """
    seen, out = [], []
    for line in text.replace("\u2019", "'").splitlines():
        if line.lstrip().startswith("#"):
            continue
        for m in _INTERROGATIVE_FRAGMENT_RE.finditer(line):
            frag = m.group(0).strip()
            if frag.lower() not in seen:
                seen.append(frag.lower())
                out.append(frag)
    return out


def find_false_candor(text: str) -> list[str]:
    """Claimed bluntness used as throat-clearing: "Let's be honest"."""
    return _distinct_shape(_FALSE_CANDOR_RE, text)


def find_overstatement_formula(text: str) -> list[str]:
    """Asserted importance instead of the specific consequence."""
    return _distinct_shape(_OVERSTATEMENT_FORMULA_RE, text)


def find_product_pivot(text: str) -> list[str]:
    """The marketing-page pivot: "That's where <product> comes in"."""
    return _distinct_shape(_PRODUCT_PIVOT_RE, text)


def find_era_frame(text: str) -> list[str]:
    """Manufactured momentum: "Gone are the days", "in the age of"."""
    return _distinct_shape(_ERA_FRAME_RE, text)


def find_metaphorical_navigate(text: str) -> list[str]:
    """"Navigating the complexities" — filler for "dealing with"."""
    return _distinct_shape(_METAPHORICAL_NAVIGATE_RE, text)


def find_correlative_hedge(text: str) -> list[str]:
    """"Not only X but also Y" / "Whether you're X or Y". SOFT — real English."""
    return _distinct_shape(_CORRELATIVE_HEDGE_RE, text)


# ---------------------------------------------------------------------------
# Client-scoped detectors (added 2026-08-03)
#
# The five below take their word lists as ARGUMENTS rather than module
# constants, for the same reason find_worn_phrases does: the lists are DATA
# (clients/{slug}/config.json), differ per client, and a human must be able to
# tune them without a code change. Passing an empty list is a no-op, so a
# client that hasn't configured them is unaffected.
#
# All five come out of a 2026-08-03 client content review, where the client
# rejected a queued Monday post for two reasons no detector could see.
# ---------------------------------------------------------------------------

# "AI last" sequencing. Two shapes:
#   (a) an explicit ordering word tying infrastructure/hardware/fundamentals to
#       a position ahead of AI ("infrastructure first, AI second"),
#   (b) a before/until/then construction that gates AI behind other work.
# Deliberately NOT triggered by "AI" plus any nearby "first" — "the first AI
# tool an operator buys" is fine, and so is "AI-first" as a description of a
# company. The pattern requires the fundamentals noun AND the ordering claim.
_AI_SEQUENCING_FUNDAMENTAL = (
    r"(?:infrastructure|hardware|fundamentals?|basics|foundation|plumbing|"
    r"back ?of ?house|the boring (?:stuff|parts?))"
)
_AI_SEQUENCING_RES = (
    # "infrastructure first ... AI" / "hardware before AI"
    re.compile(
        r"(?i)\b" + _AI_SEQUENCING_FUNDAMENTAL +
        r"\b[^.!?\n]{0,60}?\b(?:first|before|ahead of|precede[sd]?|comes? first)\b"
        r"[^.!?\n]{0,60}?\bA\.?I\b"
    ),
    # "before you buy AI, fix the infrastructure" (reverse order, same claim)
    re.compile(
        r"(?i)\b(?:before|until|rather than)\b[^.!?\n]{0,40}?\bA\.?I\b"
        r"[^.!?\n]{0,80}?\b" + _AI_SEQUENCING_FUNDAMENTAL + r"\b"
    ),
    # "AI gets bolted on after" / "AI rides on top of it"
    re.compile(
        r"(?i)\bA\.?I\b[^.!?\n]{0,40}?"
        r"\b(?:(?:gets? |is |was )?bolted on|rides? on top|sits? on top|"
        r"layered on(?:to)?(?: top)?|comes? (?:later|last|after that))\b"
    ),
    # "the smart layer gets bolted on after" — same move, AI by euphemism
    re.compile(
        r"(?i)\b(?:smart|intelligent|AI) layer\b[^.!?\n]{0,40}?"
        r"\b(?:bolted on|on top|later|last|after)\b"
    ),
    # "missing the first step" / "skipping the first step" — the setup line
    re.compile(
        r"(?i)\b(?:missing|skipping|skipped|jump(?:ing|ed)? (?:past|over))\b"
        r"[^.!?\n]{0,30}?\bthe first step\b"
    ),
)


def find_ai_sequencing_claim(text: str) -> list[str]:
    """Return fragments that position AI as the wrong or later move.

    A client killed a post over this on 2026-08-03: "we don't want to say that
    because we have clients that are AI first." Any brand whose portfolio or
    customer base includes AI-forward companies cannot publish copy implying AI
    buyers got the order wrong, however reasonable the underlying advice.

    The approved reframe is a balance rather than a sequence: the pull of AI on
    one side, software and hardware fundamentals on the other, both real. So this
    fires on the ORDERING claim, not on mentioning AI and infrastructure in the
    same breath. Not client-scoped — the reasoning generalizes to any client with
    AI vendors in the mix — so it takes no argument.
    """
    hits: list[str] = []
    for pattern in _AI_SEQUENCING_RES:
        for frag in _distinct_matches(pattern, text):
            if frag not in hits:
                hits.append(frag)
    return hits


def find_unrepresented_category(text: str, categories: list[str]) -> list[str]:
    """Return technology categories named in `text` that the client can't place.

    `categories` is config.json#technology_categories.not_represented. A client
    checking its own portfolio live on 2026-08-03, against a draft that leaned on
    two hardware categories: "Do we have anybody in our vendor thing that's a
    ...? No. So, this doesn't work." Naming a category the client has no partner
    for promises a capability that doesn't exist.

    Word-boundary matched so a short category name doesn't fire inside a longer
    word, and case-insensitive so an acronym lands in either case. Configured
    lists should be multi-word wherever a bare noun would over-flag: "loyalty"
    appears legitimately inside approved vendor copy ("build guest loyalty"), so
    the entry to configure is "loyalty program" / "loyalty platform".
    """
    if not categories:
        return []
    norm = text.replace("’", "'")
    found: list[str] = []
    for cat in categories:
        if not cat:
            continue
        if re.search(r"(?i)(?<!\w)" + re.escape(cat) + r"(?:e?s)?(?!\w)", norm):
            if cat not in found:
                found.append(cat)
    return found


# How close a name has to sit to a figure to count as "attached to" it. One
# clause, roughly — wide enough for "<Vendor> trims your bill by up to 20%",
# narrow enough that a vendor named in paragraph 1 and a number in paragraph 4
# don't collide.
_FIGURE_PROXIMITY = 120
_FIGURE_RE = re.compile(
    r"(?:\$\s?[\d,]+(?:\.\d+)?[KkMm]?|\b\d+(?:\.\d+)?\s?%|\b\d+(?:\.\d+)?\s?percent\b)"
)


def _names_near_figures(text: str, names: list[str], window: int) -> list[str]:
    """Names from `names` that appear within `window` chars of a $/% figure."""
    if not names:
        return []
    norm = text.replace("’", "'")
    spans = [m.span() for m in _FIGURE_RE.finditer(norm)]
    if not spans:
        return []
    found: list[str] = []
    for name in names:
        if not name:
            continue
        for nm in re.finditer(r"(?i)(?<!\w)" + re.escape(name) + r"(?!\w)", norm):
            ns, ne = nm.span()
            if any(ns - window <= fe and ne + window >= fs for fs, fe in spans):
                if name not in found:
                    found.append(name)
                break
    return found


def find_vendor_named_with_figure(
    text: str, vendors: list[str], exempt: list[str] = ()
) -> list[str]:
    """Return vendors named within one clause of a $ or % figure.

    Narrowing agreed 2026-08-03. Naming a vendor while teaching a category stays
    fine; naming one while quoting a savings number is not, because it hands the
    buyer everything needed to go around the client. The client, whose whole
    business is being the intermediary: "let's not necessarily divulge who those
    vendors are ... we'd much rather them go through you."

    `exempt` carries the vendors whose numbers are published on the client's own
    site and are therefore already public. Naming one beside that figure is the
    required citation rather than a leak, so it must not flag.
    """
    live = [v for v in vendors if v and v not in (exempt or ())]
    return _names_near_figures(text, live, _FIGURE_PROXIMITY)


def find_client_brand_with_figure(text: str, brands: list[str]) -> list[str]:
    """Return customer brand names sitting next to a $ or % figure.

    `brands` is config.json#proof_points.never_name_with_results. The distinction
    matters and is narrower than a flat ban: a client's named customers are often
    already public on its own site and stay claimable as a ROSTER. What was banned
    on 2026-08-03 is attaching a specific savings figure to a named customer — one
    founder, on a draft: "I don't want to list [a named chain]", answered with
    "you don't have to mention names." The roster and the receipts must not appear
    in the same sentence.
    """
    return _names_near_figures(text, list(brands), _FIGURE_PROXIMITY)


# A quoted sentence attributed to a person or brand. Requires real quote marks
# around >=4 words plus an attribution cue, so a quoted phrase ("the 'quiet
# months'") and a scare-quoted term don't fire.
_TESTIMONIAL_RE = re.compile(
    r"(?:[“\"][^”\"\n]{20,400}[”\"]\s*(?:[-–—~]{1,2}\s*\w|"
    r"(?:said|says|told us|according to)\b)|"
    r"(?:said|says|told us)\s*[,:]?\s*[“\"][^”\"\n]{20,400}[”\"])"
)


def find_testimonial_quote(text: str) -> list[str]:
    """Return attributed customer-quote constructions. SOFT.

    From a 2026-08-03 client review, on the testimonial-forward LinkedIn style:
    "That's not working ... That pisses everybody off." Customer quotes belong on
    the website as trust verification. Proof-point NUMBERS are welcome in social
    copy; testimonial quotes are not. Soft because a quote from a cited news
    source in a blog body is legitimate — this flags for a human, it doesn't
    block.
    """
    return [m.group(0).strip()[:90] for m in _TESTIMONIAL_RE.finditer(text)][:5]
