"""Profile presets and JSON (de)serialization.

`Profile` is where every brand-specific value lives, so the detector engine
itself can stay free of house style. This module exists so you can keep that
configuration in a file next to your content instead of in code.

Presets are starting points, not recommendations. The numbers in them came from
tuning against one publishing operation; yours will differ, and the honest move
is to run the scanner over work you already consider good and loosen whatever
fires on it.
"""

from __future__ import annotations

import json
from pathlib import Path

from .content_quality import Profile

# Fields that are tuples on Profile but arrive from JSON as lists.
_TUPLE_FIELDS = ("banned_extra", "proper_nouns", "non_citation_hosts")


PRESETS: dict[str, Profile] = {
    # Nothing assumed. Citation checks effectively off, since a general document
    # has no reason to cite anything.
    "generic": Profile(
        name="generic",
        min_citation_domains=0,
        citation_exempt_below_words=10_000,
    ),
    # Long-form article or blog post meant to be found and cited. The citation
    # floor is the one rule here with real evidence behind it: pages that name
    # concrete sources get cited by AI search far more often than pages that
    # gesture at authority. Length is NOT a ranking factor. Do not read the
    # 400-word exemption as a target.
    "blog": Profile(
        name="blog",
        min_citation_domains=3,
        citation_exempt_below_words=400,
        rhythm_floor=0.30,
        max_sentence_words=30,
    ),
    # Short social copy. No citations expected, tighter sentences, and less
    # tolerance for bold-spam formatting.
    "social": Profile(
        name="social",
        min_citation_domains=0,
        citation_exempt_below_words=10_000,
        max_sentence_words=25,
        max_bold_spans=2,
        max_allcaps=1,
    ),
}


def to_dict(p: Profile) -> dict:
    """Serialize a Profile to plain JSON-safe types."""
    return {
        "name": p.name,
        "banned_extra": list(p.banned_extra),
        "proper_nouns": list(p.proper_nouns),
        "own_host": p.own_host,
        "non_citation_hosts": list(p.non_citation_hosts),
        "min_citation_domains": p.min_citation_domains,
        "citation_exempt_below_words": p.citation_exempt_below_words,
        "rhythm_floor": p.rhythm_floor,
        "max_bold_spans": p.max_bold_spans,
        "max_sentence_words": p.max_sentence_words,
        "max_allcaps": p.max_allcaps,
        "soft": sorted(p.soft),
    }


def from_dict(data: dict, base: str = "generic") -> Profile:
    """Build a Profile from a dict, filling gaps from a preset.

    Unknown keys raise rather than being ignored. A typo in a config file that
    silently disables a detector is the failure mode worth being loud about.
    You would never see it, and you would believe you were covered.
    """
    start = PRESETS.get(data.get("preset", base), PRESETS["generic"])
    fields = set(to_dict(start))
    unknown = set(data) - fields - {"preset"}
    if unknown:
        raise ValueError(
            f"unknown profile key(s): {', '.join(sorted(unknown))}. "
            f"Valid keys: {', '.join(sorted(fields))}"
        )

    merged = to_dict(start)
    merged.update({k: v for k, v in data.items() if k != "preset"})
    for f in _TUPLE_FIELDS:
        merged[f] = tuple(merged[f])
    merged["soft"] = frozenset(merged["soft"])
    return Profile(**merged)


def load(path: str | Path, base: str = "generic") -> Profile:
    """Read a Profile from a JSON file."""
    return from_dict(json.loads(Path(path).read_text()), base=base)


def dump(p: Profile, path: str | Path) -> None:
    """Write a Profile to a JSON file, for use as a starting template."""
    Path(path).write_text(json.dumps(to_dict(p), indent=2) + "\n")
