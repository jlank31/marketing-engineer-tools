#!/usr/bin/env python3
"""Unified content-quality detectors. One shared engine for every consumer.

SYNC CONTRACT: this file is vendored byte-identical into every consumer. Each
consumer runs a sha256 guard (test_vendor_sync.py). Edit in one place, fan out in
the same pass, or the guard fails.

Why one module: two pipelines each caught tells the other missed. One had the
statistical and link-graph checks (rhythm variance, distinct-domain citations,
cross-file duplication) and none of the lexical depth. The other had 13 lexical
detector families and none of the statistical ones. Neither was a superset. This
is the union, so a tell learned in one place is caught everywhere.

Design rules:
  - Stdlib only. No dependencies, ever. Both repos import this directly.
  - Pure functions. No I/O except the explicit corpus helpers at the bottom.
  - Brand-specific values (banned words, own host, thresholds) arrive via a
    Profile. Nothing brand-specific is hardcoded here.
  - Every detector returns a list of matched snippets, never a bool, so callers
    can quote the offending line back to the writer.

Spec: content/strategy/blog-engine-spec.md sections 2 and 6.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

def normalize(text: str) -> str:
    """Fold curly quotes to straight. Run before ANY pattern match.

    Half the reversal tells slip through on smart-quote drafts otherwise: a
    draft pasted from Google Docs arrives with "isn’t", and `isn'?t` misses it.
    """
    return (
        text.replace("’", "'")
        .replace("‘", "'")
        .replace("“", '"')
        .replace("”", '"')
    )


def strip_links(text: str) -> str:
    """Remove markdown link targets and bare URLs, leaving anchor text.

    Run before banned-word scanning so a banned word inside a *cited source's*
    URL slug (".../scalable-content-marketing") doesn't fail the draft. Citing a
    source is the behavior we want; punishing its slug is a false positive.
    """
    out = re.sub(r"\]\((https?://[^)]+)\)", "]", text)
    return re.sub(r"https?://\S+", "", out)


def body_of(text: str) -> str:
    """Strip YAML frontmatter, return the body."""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
    return m.group(2) if m else text


def _distinct(pattern: re.Pattern, text: str) -> list[str]:
    seen, out = set(), []
    for m in pattern.finditer(normalize(text)):
        frag = m.group(0).strip()
        key = frag.lower()
        if key not in seen:
            seen.add(key)
            out.append(frag)
    return out


# ---------------------------------------------------------------------------
# Universal lexicon (brand-neutral). Brand additions arrive via Profile.
# ---------------------------------------------------------------------------

BANNED_WORDS: tuple[str, ...] = (
    # Core AI slop
    "delve", "crucial", "tapestry", "leverage", "synergy", "game-changer",
    "transformative", "cutting-edge", "robust", "seamless", "holistic",
    "landscape", "spearhead", "pioneering", "revolutionize", "unlock", "empower",
    # Significance inflation
    "pivotal", "testament", "indelible", "enduring", "groundbreaking",
    "profound", "instrumental",
    # Promotional puff
    "vibrant", "breathtaking", "stunning", "nestled", "renowned", "must-visit",
    # AI-frequency vocabulary
    "underscore", "interplay", "intricate", "intricacies", "foster", "fostering",
    "garner", "showcase", "showcasing", "encompassing", "cultivating",
    "exemplifies",
    # Corporate jargon LLMs overuse
    "align", "alignment", "elevate", "ideate", "scalable", "streamline",
    "optimize", "synergize", "operationalize",
    # Added from a second brand's lexicon
    "innovative", "paradigm", "thought leader", "hustle", "fast-paced",
    "unpack", "circle back",
)

BANNED_PHRASES: tuple[str, ...] = (
    "that's a signal", "here's the thing", "here's what i mean",
    "the reality is", "let that sink in", "think about that",
    "read that again", "full stop", "spoiler alert", "let's dive in",
    "in today's fast-paced", "it's no secret that", "let's dive deep",
    "let's explore", "the key takeaway", "it's important to note",
    "it's worth mentioning", "one might argue",
    # 2026-07-29 additions: dead metaphors and inflation that survive a
    # word-level pass because each word is individually ordinary.
    "double-edged sword", "paradigm shift", "a beacon of", "a testament to",
    "the perfect storm", "a game of inches", "moving the goalposts",
    # Faux-profound "that's the whole X" closers, banned as a FAMILY.
    # Both contracted and expanded forms: a draft can arrive either way.
    "that's the whole game", "that is the whole game",
    "that's the entire game", "that is the entire game",
    "that's the whole ballgame", "that is the whole ballgame",
    "that's the ballgame", "that is the ballgame",
    "that's the name of the game", "that is the name of the game",
    "that's the whole point", "that is the whole point",
    "that's the secret", "that is the secret",
    "that's the magic", "that is the magic",
)

INFLATION_PHRASES: tuple[str, ...] = (
    "stands as", "serves as a testament", "a pivotal moment", "marking a shift",
    "setting the stage", "reflects broader trends", "underscores the importance",
    "marks a pivotal",
)

CHATBOT_ARTIFACTS: tuple[str, ...] = (
    "i hope this helps", "of course!", "certainly!", "let me know if",
    "great question", "you're absolutely right", "that's an excellent point",
    "would you like me to",
)

FILLER_CONSTRUCTIONS: tuple[tuple[str, str], ...] = (
    ("in order to", "to"),
    ("due to the fact that", "because"),
    ("at this point in time", "now"),
    ("it is important to note that", "[cut entirely]"),
    ("has the ability to", "can"),
)

LONGFORM_TERMS: tuple[tuple[str, str], ...] = (
    ("year-over-year", "YoY"), ("year over year", "YoY"),
    ("quarter-over-quarter", "QoQ"), ("quarter over quarter", "QoQ"),
    ("month-over-month", "MoM"), ("month over month", "MoM"),
)

COMMON_ACRONYMS = {
    "AI", "GTM", "B2B", "SaaS", "API", "CTA", "YoY", "QoQ", "MoM", "ARR", "MRR",
    "ACV", "CAC", "LTV", "CEO", "VP", "CMO", "CRO", "ROI", "KPI", "SQL", "MQL",
    "SEO", "AEO", "GEO", "PPC", "RAG", "URL", "DM", "FAQ", "TLDR", "POS", "HR",
    "NOT", "AND", "OR", "MAX", "COGS", "P&L", "ONE", "LLM", "PLG", "ICP",
}

# ---------------------------------------------------------------------------
# Compiled detectors
# ---------------------------------------------------------------------------

# The #1 AI tell, in both shapes. The comma form is the most-flagged AI formula
# on LinkedIn as of 2026 and is the one period-only regexes miss.
# The negation half of the period form. `'?s not` / `'?re not` were added
# 2026-07-29: the list spelled out "is not" and "are not" as two words, so the
# contracted-auxiliary form slipped through entirely —
#   "It's not a tooling problem. It's a distance problem."   MISSED
#   "It isn't a tooling problem. It's a distance problem."   caught
# Same construction, and the first one is the more common way to write it. The
# inconsistency is the real argument for the fix: "There isn't much time. It's
# fine." already flagged, so this adds no new class of false positive, it just
# stops the detector depending on which way the writer punctuated "is".
_REVERSAL_NEG = (
    r"isn'?t|aren'?t|wasn'?t|weren'?t|is not|are not|was not|were not"
    r"|'?s not|'?re not"
)

REVERSAL_PERIOD = re.compile(
    rf"\b({_REVERSAL_NEG})\b"
    r"[^.!?|]{0,45}[.!?]+[\"')\]]*\s+"
    r"(it'?s|it is|that'?s|that is|they'?re|they are)\b",
    re.IGNORECASE,
)
REVERSAL_COMMA = re.compile(
    r"\b(?:not (?:just|only|about)|more than (?:a|an|just))\b"
    r"[^.!?|]{0,45}[,;]\s+"
    r"(it'?s|it is|that'?s|that is|they'?re|they are)\b",
    re.IGNORECASE,
)
REVERSAL_DASH = re.compile(
    r"\b(?:that'?s|this|it'?s|the \w+) (?:isn'?t|is not|not) .{2,40}[—\-:]\s*it'?s ",
    re.IGNORECASE,
)

# "X is the difference between A and B". Lookbehind spares the question form
# ("what is the difference between X and Y"), which is legitimate.
CONTRAST_FORMULA = re.compile(
    r"(?<!what )\b(?:is|are|was|were)\s+the difference between\b", re.IGNORECASE
)

CLOSING_REFLEX = re.compile(
    r"\b(?:what about you|what'?s your take|sound familiar|who'?s with me|"
    r"am i right|thoughts\?)\s*\??",
    re.IGNORECASE,
)

HOLLOW_OPENER = re.compile(
    r"(?im)(?:^|\n)\s*(?:"
    r"in the world of|in the realm of|"
    r"in today's (?:fast-paced|ever-changing|ever-evolving|digital|competitive)"
    r"\s+(?:landscape|world|environment|market)|"
    r"imagine (?:a|if|that)|picture (?:this|a)|"
    r"here's how|let's talk about"
    r")\b"
)

SCAFFOLD_TRANSITION = re.compile(
    r"(?:\bthat said\b|\bit'?s worth noting\b|\bit is worth noting\b|"
    r"\bneedless to say\b|\bat the end of the day\b|"
    r"\bhere's the part that surprises\b|"
    # 2026-07-29 additions. Same job as the above: connective tissue that
    # announces structure. "the bottom line" is included but "bottom line"
    # alone is not, since it's a real finance term.
    r"\bsimply put\b|\bat its core\b|\bthe bottom line\b|"
    r"\bmake no mistake\b|\bthat being said\b|\bwhen all is said\b)"
    r"|(?:^|[.!?]\s+)(?:ultimately|in short|in summary|in conclusion)\b",
    re.IGNORECASE | re.MULTILINE,
)

VAGUE_QUANTIFIER = re.compile(
    r"(?i)\b(?:countless|a myriad of|myriad|ever-evolving|ever-changing|"
    r"fast-paced landscape|a plethora of|a wealth of|treasure trove)\b"
)

AI_TELL_VERB = re.compile(
    r"(?i)\b(?:supercharg(?:e[sd]?|ing)|harness(?:e[sd]|ing)?|"
    r"revolutioni[sz]e[sd]?|revolutioni[sz]ing|spearhead(?:s|ed|ing)?|"
    r"delv(?:e[sd]?|ing))\b"
)

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
REASSURANCE_OPENER = re.compile(
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
INTERROGATIVE_FRAGMENT = re.compile(
    r"(?:^|(?<=[.!?])\s+)(?:the|their|our|my)\s+"
    r"(?:result|catch|problem|kicker|twist|upside|downside|difference|reason"
    r"|point|best part|worst part|reality|takeaway|fix|answer|issue|payoff)\?",
    re.IGNORECASE,
)

# Throat-clearing that claims candor instead of delivering it. If the next line
# were genuinely blunt it wouldn't need the warm-up.
FALSE_CANDOR = re.compile(
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
OVERSTATEMENT_FORMULA = re.compile(
    r"(?i)\b(?:"
    r"cannot be overstated|can'?t be overstated|speaks volumes|no small feat"
    r"|worth its weight in gold|needs no introduction|goes without saying"
    r"|it'?s no exaggeration|it is no exaggeration|more important than ever"
    r")\b"
)

# The pivot-to-product cliché. Nearly every AI-written marketing page contains
# one. "Enter <Product>." is the same move but deliberately NOT matched — "enter"
# has too many literal uses to catch safely.
PRODUCT_PIVOT = re.compile(
    # Both contracted and expanded auxiliaries. Listing only "that's" would
    # repeat the exact bug that hid "It's not X. It's Y." for months: a draft
    # can arrive either way, and the contraction pass runs later.
    r"(?i)\b(?:that'?s|that is|this is|here'?s|here is) where\b[^.!?]{1,45}?\bcomes? in\b"
)

# Correlative scaffolding and audience-hedging. Both are legitimate English, which
# is why they're SOFT by default — the tell is frequency, not any single use.
CORRELATIVE_HEDGE = re.compile(
    # "but also" is usually split by a pronoun ("but IT also", "but THEY also"),
    # so allow a short gap rather than requiring adjacency.
    r"(?i)\bnot only\b[^.!?]{0,70}\bbut\b[^.!?]{0,15}\balso\b"
    r"|\bwhether you'?re\b[^.!?]{0,45}\bor\b"
)

# Era-framing: manufactured historical momentum standing in for a real reason.
ERA_FRAME = re.compile(
    r"(?i)\b(?:gone are the days|in an era where|in the age of"
    r"|as we (?:move|head|step) into|in this new era|now more than ever)\b"
)

# Metaphorical "navigate". Literal navigation is fine, so this requires an
# abstract object — you can navigate a harbor, but "navigating the complexities"
# is filler for "dealing with".
METAPHORICAL_NAVIGATE = re.compile(
    r"(?i)\bnavigat(?:e|ing|es)\s+(?:the\s+|this\s+|these\s+)?"
    r"(?:complexit|ever-|challeng|nuance|intricac|landscape|waters|maze|minefield|terrain)"
)

FILLER_INTENSIFIER = re.compile(
    r"\b(actually|actual|literally|genuinely|truly|seamlessly)\b", re.IGNORECASE
)

SPELLED_PERCENT = re.compile(r"(?<![\w%])(\d[\d,]*(?:\.\d+)?)\s*percent\b", re.IGNORECASE)

# RECOVERED 2026-07-16. These two lived only in a shell script that was
# deprecated 2026-07-08. No Python detector module picked them up, so one
# consumer silently lost both detectors. They belong here — which is the whole
# argument for a single vendored engine over per-consumer scripts.
#
# Widened the same day after the first real sweep found two misses the original
# shell regex would also have missed:
#   "what this data rewards"   — determiner was hardcoded to "the"
#   "The algorithm punishes"   — subject matched, verb wasn't in the list
# Determiners and verbs are now enumerated separately so a new subject or verb
# is a one-word edit rather than a new alternation branch.
#
# Deliberately EXCLUDED, because data legitimately does these: shows, suggests,
# indicates, says, points to, reflects, confirms. "The data shows a 12% lift" is
# correct writing. The tell is agency (wanting, deciding, rewarding), not
# reporting.
_FA_DET = r"(?:the|this|that|these|those)"
_FA_SUBJ = (
    r"(?:data|market|algorithm|conversation|culture|decision|industry|numbers|"
    r"research|content|platform|feed)"
)
# Verbs of AGENCY only: wanting, judging, deciding. No noun-homographs.
#
# `moves`, `shifts`, `drives`, `emerges`, `becomes` were in the original shell
# regex and are removed here. With an optional -s they match noun phrases: "the
# platform shift is real" is correct writing, and the old pattern flagged it.
# The homograph risk is not worth it — those were weak tells anyway.
#
# The trailing -s is MANDATORY, not optional. These subjects are singular, so a
# real predicate agrees with them ("the algorithm punishes"). A bare verb after
# the noun means the noun is not its subject — the case that caught this out was
# "would an operator who lives in this industry care about this story", where
# `care` belongs to `an operator` and `this industry` is just the object of
# `lives in`. Optional -s flagged it. Mandatory -s does not.
_FA_VERB = (
    r"(?:tells|rewards|punishes|penali[sz]es|favou?rs|prefers|wants|decides|"
    r"thinks|knows|cares|likes|hates|demands|requires|notices|"
    r"understands|learns)"
)
# "let the numbers decide" / "let the data decide" are established business
# idioms, not slop. The lookbehind spares them without weakening the rule.
FALSE_AGENCY = re.compile(rf"(?i)(?<!let )\b{_FA_DET}\s+{_FA_SUBJ}\s+{_FA_VERB}\b")
COPULA_AVOIDANCE = re.compile(
    r"(?i)\b(serves|stands|functions|acts|operates)\s+as\b"
)

META_COMMENTARY = re.compile(
    r"(?i)(?:this (?:article|post|blog|piece) (?:is about|will|covers|explores)|"
    r"in this (?:article|post|blog|piece)(?:,| we| I)|"
    r"by the end of this (?:article|post|read)|"
    r"let's dive in|let's get started|we'll explore)"
)

EM_DASH = re.compile(r"—")
CURLY_QUOTE = re.compile(r"[“”‘’]")
BARE_URL_LINE = re.compile(r"(?:^|\n)\s*https?://\S+\s*(?:\n|$)")
MD_LINK = re.compile(r"\]\((https?://[^)\s]+)\)")
BOLD_SPAN = re.compile(r"\*\*[^*]+\*\*")
ALLCAPS = re.compile(r"\b[A-Z]{2,}\b")
PLACEHOLDER_TOKEN = re.compile(
    r"(?:\{\{[^}]+\}\}|\[(?:TODO|TBD|INSERT|XX+|PLACEHOLDER)[^\]]*\]|"
    r"\bLorem ipsum\b|<[A-Z_]{3,}>)"
)


# ---------------------------------------------------------------------------
# Detector functions
# ---------------------------------------------------------------------------

def find_reversal_patterns(text: str) -> list[str]:
    """Negate-then-assert, all three shapes. The #1 AI tell."""
    n = normalize(text)

    out: list[str] = []
    for pat in (REVERSAL_PERIOD, REVERSAL_COMMA, REVERSAL_DASH):
        out += [m.group(0).strip() for m in pat.finditer(n)]
    return out


def find_contrast_formula(text: str) -> list[str]:
    return _distinct(CONTRAST_FORMULA, text)


def find_closing_reflex(text: str) -> list[str]:
    return _distinct(CLOSING_REFLEX, text)


def find_hollow_openers(text: str) -> list[str]:
    return _distinct(HOLLOW_OPENER, text)


def find_scaffold_transitions(text: str) -> list[str]:
    return _distinct(SCAFFOLD_TRANSITION, text)


def find_vague_quantifiers(text: str) -> list[str]:
    return _distinct(VAGUE_QUANTIFIER, text)


def find_ai_tell_verbs(text: str) -> list[str]:
    return _distinct(AI_TELL_VERB, text)


# --- 2026-07-29 refresh: shape-level tells (see the pattern block above) -----

def find_reassurance_opener(text: str) -> list[str]:
    """Manufactured rapport: "You're not alone", "It's not just you"."""
    return _distinct(REASSURANCE_OPENER, text)


def find_interrogative_fragment(text: str) -> list[str]:
    """Fake-punchy transitions: "The result?", "The catch?".

    Line-aware on purpose: markdown headings are skipped, because an H2 reading
    "The catch?" is a legitimate document structure rather than a prose tic.
    """
    seen, out = set(), []
    for line in normalize(text).splitlines():
        if line.lstrip().startswith("#"):
            continue
        for m in INTERROGATIVE_FRAGMENT.finditer(line):
            frag = m.group(0).strip()
            if frag.lower() not in seen:
                seen.add(frag.lower())
                out.append(frag)
    return out


def find_false_candor(text: str) -> list[str]:
    """Claims of bluntness used as throat-clearing: "Let's be honest"."""
    return _distinct(FALSE_CANDOR, text)


def find_overstatement_formula(text: str) -> list[str]:
    """Asserted importance instead of demonstrated: "cannot be overstated"."""
    return _distinct(OVERSTATEMENT_FORMULA, text)


def find_product_pivot(text: str) -> list[str]:
    """The marketing-page pivot: "That's where <product> comes in"."""
    return _distinct(PRODUCT_PIVOT, text)


def find_correlative_hedge(text: str) -> list[str]:
    """"Not only X but also Y" and "Whether you're X or Y". SOFT by default."""
    return _distinct(CORRELATIVE_HEDGE, text)


def find_era_frame(text: str) -> list[str]:
    """Manufactured momentum: "Gone are the days", "in the age of"."""
    return _distinct(ERA_FRAME, text)


def find_metaphorical_navigate(text: str) -> list[str]:
    """"Navigating the complexities" — filler for "dealing with"."""
    return _distinct(METAPHORICAL_NAVIGATE, text)


def find_filler_intensifiers(text: str) -> list[str]:
    return _distinct(FILLER_INTENSIFIER, text)


def find_false_agency(text: str) -> list[str]:
    return _distinct(FALSE_AGENCY, text)


def find_copula_avoidance(text: str) -> list[str]:
    return _distinct(COPULA_AVOIDANCE, text)


def find_meta_commentary(text: str) -> list[str]:
    return _distinct(META_COMMENTARY, text)


def find_spelled_percent(text: str) -> list[str]:
    return _distinct(SPELLED_PERCENT, text)


def find_placeholder_tokens(text: str) -> list[str]:
    return _distinct(PLACEHOLDER_TOKEN, text)


_SENTENCE_END = re.compile(r"[.!?:\n\-•|>\"'(\[]$")


def find_banned_words(
    text: str, extra: tuple[str, ...] = (), proper_nouns: tuple[str, ...] = ()
) -> list[str]:
    """Banned vocabulary, with proper-noun protection.

    Scans prose only: link targets and bare URLs are stripped first, so a banned
    word inside a cited source's URL slug never fails the draft.

    Proper-noun heuristic. Several banned words are also company names — the
    "Profound" of "Profound raised a $96M Series C" is not the "profound" of
    "a profound shift". A word is treated as a proper noun if it appears
    Capitalized *mid-sentence* somewhere in the text ("Before Profound, Lafferty
    led growth at Loom"). Capitalization at a sentence start proves nothing,
    since "Optimize for conversations." is the banned verb.

    When a word is judged a proper noun, only its lowercase occurrences are
    flagged, so a text can legitimately contain both the company and the tell.

    (The pre-2026-07 checker claimed in a comment to allow "capitalized proper
    nouns" but lowercased the text before matching, so it never did. This is
    that comment made true.)
    """
    prose = normalize(strip_links(text))
    allow = {p.lower() for p in proper_nouns}
    hits: list[str] = []

    for w in tuple(BANNED_WORDS) + tuple(extra):
        if w.lower() in allow:
            continue
        pat = re.compile(r"(?<![\w-])" + re.escape(w) + r"(?![\w-])", re.IGNORECASE)
        matches = list(pat.finditer(prose))
        if not matches:
            continue

        is_proper = False
        for m in matches:
            if not m.group(0)[0].isupper():
                continue
            before = prose[: m.start()].rstrip()
            if before and not _SENTENCE_END.search(before):
                is_proper = True
                break

        real = [m for m in matches if not m.group(0)[0].isupper()] if is_proper else matches
        if real:
            hits.append(w)
    return hits


def find_banned_phrases(text: str) -> list[str]:
    low = normalize(text).lower()
    return [p for p in BANNED_PHRASES if p in low]


def find_inflation(text: str) -> list[str]:
    low = normalize(text).lower()
    return [p for p in INFLATION_PHRASES if p in low]


def find_chatbot_artifacts(text: str) -> list[str]:
    low = normalize(text).lower()
    return [p for p in CHATBOT_ARTIFACTS if p in low]


def rhythm_variance(text: str) -> float | None:
    """Coefficient of variation of sentence length.

    The monotony detector, and the best single proxy for "sounds like a machine".
    Humans vary sentence length a lot; models regress to a uniform middle. Below
    0.30 the prose reads flat even when every word passes. Needs >5 sentences to
    mean anything.
    """
    sents = [s.strip() for s in re.split(r"[.!?]+", text) if len(s.strip()) > 5]
    if len(sents) <= 5:
        return None
    lengths = [len(s.split()) for s in sents]
    mean = sum(lengths) / len(lengths)
    if mean <= 0:
        return None
    var = sum((l - mean) ** 2 for l in lengths) / len(lengths)
    return (var**0.5) / mean


def citation_domains(text: str, own_host: str, non_citation_hosts: tuple[str, ...]) -> set[str]:
    """Distinct external domains cited. Three links to one site is one source."""
    domains = set()
    for url in MD_LINK.findall(body_of(text)):
        host = re.sub(r"^https?://", "", url).split("/")[0].lower()
        host = host[4:] if host.startswith("www.") else host
        if own_host and own_host in host:
            continue
        if any(h in host for h in non_citation_hosts):
            continue
        domains.add(host)
    return domains


def duplicate_sentences(text: str, sibling_texts: dict[str, str], min_words: int = 12) -> list[tuple[str, str]]:
    """12+ word sentences reused verbatim from a sibling. The scaled-content fingerprint."""
    body = body_of(text)
    mine = {
        s.strip()
        for s in re.split(r"(?<=[.!?])\s+", body)
        if len(s.split()) >= min_words and not s.strip().startswith(("#", "-", "*", "|", ">"))
    }
    out = []
    for name, sib in sibling_texts.items():
        for s in mine:
            if s and s in sib:
                out.append((s[:55], name))
                break
    return out


# ---------------------------------------------------------------------------
# Profile + the one entry point
# ---------------------------------------------------------------------------

@dataclass
class Profile:
    """Brand knobs. Everything brand-specific lives here, nothing in the module."""

    name: str = "generic"
    banned_extra: tuple[str, ...] = ()
    # Explicit escape hatch for banned words that are also entity names in this
    # brand's world. The mid-sentence-capitalization heuristic handles most
    # cases; this is for the ones it can't (a company only ever named at the
    # start of a sentence, say).
    proper_nouns: tuple[str, ...] = ()
    own_host: str = ""
    non_citation_hosts: tuple[str, ...] = ()
    min_citation_domains: int = 3
    citation_exempt_below_words: int = 400
    rhythm_floor: float = 0.30
    max_bold_spans: int = 8
    max_sentence_words: int = 30
    max_allcaps: int = 3
    # Detectors that WARN instead of FAIL for this brand. Use sparingly; the
    # engine spec is a floor. Loosening is a conflict to resolve, not record.
    soft: frozenset[str] = frozenset()


@dataclass
class Result:
    passed: bool = True
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    stats: dict = field(default_factory=dict)


def check_text(text: str, profile: Profile | None = None) -> Result:
    """Run every universal detector. Structural/link checks are caller-owned."""
    p = profile or Profile()
    r = Result()

    def emit(key: str, msg: str) -> None:
        (r.warnings if key in p.soft else r.issues).append(
            ("WARN: " if key in p.soft else "FAIL: ") + msg
        )

    n = normalize(text)

    def occurrences(hit: str) -> str:
        """Suffix showing how many times this exact hit appears.

        The detectors dedupe (via _distinct), which is right for readability but
        hides scale: a draft with 9 "actually"s reported identically to one with a
        single instance, so the cleanup looked far smaller than it was. Found while
        scanning real published articles.
        """
        c = n.lower().count(hit.lower())
        return f" (x{c})" if c > 1 else ""

    r.stats["word_count"] = len(text.split())
    r.stats["char_count"] = len(text)

    if (c := len(EM_DASH.findall(text))):
        emit("em_dash", f"{c} em dash(es). Replace with periods, commas, or a rewrite.")

    for w in find_banned_words(text, p.banned_extra, p.proper_nouns):
        emit("banned_words",
             f"Banned AI word '{w}'{occurrences(w)}. Replace with a natural alternative.")

    # Report up to 3, not just the first. Reporting only hits[0] turns cleanup
    # into whack-a-mole: you fix one, re-run, and the next one you never saw
    # appears. Every other detector below already reports [:3]; this one lagged.
    for h in find_reversal_patterns(text)[:3]:
        emit("reversal", f'Contrast/reversal pattern: "{h[:70]}". Write the direct claim.')

    for key, fn, label in (
        ("contrast_formula", find_contrast_formula, "Contrast formula"),
        ("hollow_opener", find_hollow_openers, "Hollow opener"),
        ("scaffold", find_scaffold_transitions, "Essay-scaffold transition"),
        ("vague_quantifier", find_vague_quantifiers, "Vague quantifier"),
        ("ai_tell_verb", find_ai_tell_verbs, "AI-tell verb"),
        ("false_agency", find_false_agency, "False agency (inanimate subject acting)"),
        ("copula", find_copula_avoidance, "Copula avoidance"),
        ("meta_commentary", find_meta_commentary, "Meta-commentary"),
        ("filler_intensifier", find_filler_intensifiers, "Empty intensifier"),
        ("spelled_percent", find_spelled_percent, "Spelled-out percent (use %)"),
        ("placeholder", find_placeholder_tokens, "Placeholder token left in draft"),
        ("banned_phrase", find_banned_phrases, "Bland filler phrase"),
        ("inflation", find_inflation, "Significance inflation"),
        ("chatbot", find_chatbot_artifacts, "Chatbot artifact"),
        # 2026-07-29 refresh. Shape-level tells: a draft can pass every
        # word-level check above and still read as generated if it keeps
        # doing these.
        ("reassurance", find_reassurance_opener, "Manufactured rapport"),
        ("interrogative_fragment", find_interrogative_fragment,
         "Fake-punchy question fragment"),
        ("false_candor", find_false_candor, "Claimed candor (throat-clearing)"),
        ("overstatement", find_overstatement_formula, "Asserted, not demonstrated"),
        ("product_pivot", find_product_pivot, "Pivot-to-product cliché"),
        ("era_frame", find_era_frame, "Manufactured historical momentum"),
        ("metaphorical_navigate", find_metaphorical_navigate,
         "Metaphorical 'navigate' (use 'dealing with')"),
    ):
        for h in fn(text)[:3]:
            emit(key, f"{label}: \"{h}\"{occurrences(h)}.")

    # SOFT by default: both constructions are legitimate English, so the tell is
    # frequency rather than any single use. Warn, never fail.
    for h in find_correlative_hedge(text)[:3]:
        r.warnings.append(
            f'WARN: Correlative scaffolding: "{h[:60]}". Split into two claims, '
            f"or name the audience directly."
        )

    if (hits := find_closing_reflex(text)):
        r.warnings.append(
            f"WARN: Engagement-bait closer '{hits[0]}'. Close on a specific "
            f"observation or the concrete stakes."
        )

    for longform, short in LONGFORM_TERMS:
        if longform in n.lower():
            emit("longform_term", f"Written-out term '{longform}' should be '{short}'.")

    for longform, repl in FILLER_CONSTRUCTIONS:
        if longform in n.lower():
            r.warnings.append(f"WARN: Filler construction '{longform}'. Consider '{repl}'.")

    if BARE_URL_LINE.search(text):
        emit("bare_url", "Bare URL without anchor text. Add action text around the link.")

    if CURLY_QUOTE.search(text):
        r.warnings.append("WARN: Curly quotes. Replace with straight quotes.")

    if (b := len(BOLD_SPAN.findall(text))) > p.max_bold_spans:
        r.warnings.append(f"WARN: {b} bold spans (max {p.max_bold_spans}). Reads as AI formatting.")

    sents = [s.strip() for s in re.split(r"[.!?]+", text) if len(s.strip()) > 5]
    if sents:
        lengths = [len(s.split()) for s in sents]
        r.stats["sentence_count"] = len(sents)
        r.stats["avg_sentence_length"] = round(sum(lengths) / len(lengths), 1)
        if (long_ := [s for s in sents if len(s.split()) > p.max_sentence_words]):
            r.warnings.append(f"WARN: {len(long_)} sentence(s) over {p.max_sentence_words} words. Split them.")

    if (cv := rhythm_variance(text)) is not None:
        r.stats["rhythm_variance"] = round(cv, 2)
        if cv < p.rhythm_floor:
            r.warnings.append(
                f"WARN: Low sentence-length variance ({cv:.2f}, target >{p.rhythm_floor}). "
                f"Monotone rhythm is the strongest 'machine wrote this' signal that "
                f"survives a clean word-level pass. Vary it deliberately."
            )

    lines = [l.strip() for l in text.split("\n") if l.strip() and not l.strip().startswith("#")]
    for i in range(len(lines) - 2):
        fw = [l.split()[0].lower() if l.split() else "" for l in lines[i : i + 3]]
        if fw[0] and fw[0] == fw[1] == fw[2]:
            r.warnings.append(f"WARN: 3+ consecutive lines starting with '{fw[0]}'. Break the parallel structure.")
            break

    caps = [w for w in ALLCAPS.findall(text) if w not in COMMON_ACRONYMS]
    if len(caps) > p.max_allcaps:
        r.warnings.append(f"WARN: {len(caps)} ALL-CAPS emphasis words ({', '.join(caps[:5])}). Limit to 1 per section.")

    r.passed = not r.issues
    return r


def check_citations(text: str, profile: Profile) -> list[str]:
    """>=N distinct external domains. Caller decides if the file is long-form."""
    body = body_of(text)
    if len(body.split()) < profile.citation_exempt_below_words:
        return []
    d = citation_domains(text, profile.own_host, profile.non_citation_hosts)
    if len(d) < profile.min_citation_domains:
        return [
            f"FAIL: Long-form needs >={profile.min_citation_domains} credible external "
            f"citations from distinct sources (found {len(d)}). Add inline links and "
            f"distribute them across the body."
        ]
    return []


def read_siblings(path: Path) -> dict[str, str]:
    """Sibling .md files in the same directory, for the duplication check."""
    out = {}
    for p in path.parent.glob("*.md"):
        if p == path:
            continue
        try:
            out[p.stem] = p.read_text()
        except OSError:
            continue
    return out
