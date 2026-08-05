"""robot-check: find the lines that make copy read as machine-written.

Two layers, deliberately separate:

    content_quality  per-text detectors. Lexical (banned phrases, reversal
                     patterns, hollow openers) plus statistical (paragraph
                     rhythm variance, distinct citation domains, duplicated
                     sentences across files).

    repetition       corpus-level detectors. Compares one new draft against a
                     body of earlier work. This layer exists because per-text
                     checks structurally cannot see convergence: every piece
                     passes on its own while the library slowly becomes one
                     voice telling one anecdote.

Start here:

    from robot_check import check_text, Profile
    result = check_text(draft, Profile())

Everything is a pure function over strings. No network, no API key, no config
file, no state. `Profile` carries anything brand-specific, so nothing in this
package hardcodes a house style.
"""

from .content_quality import Profile, Result, check_text, normalize, strip_links
from .post_validators import (
    apply_contractions,
    apply_percent_symbol,
    find_stale_event_reference,
    strip_em_dashes,
    strip_filler_intensifiers,
)
from .repetition import (
    find_verbatim_runs,
    opener_echo,
    opening_line,
    phrasing_overlap,
    shingles,
    stat_fingerprint,
)

__version__ = "0.1.0"

__all__ = [
    "Profile",
    # Deterministic transformers: the `fix` half of the toolkit. These EDIT text
    # rather than reporting on it, which is why they live apart from check_text.
    "apply_contractions",
    "apply_percent_symbol",
    "strip_em_dashes",
    "strip_filler_intensifiers",
    "find_stale_event_reference",
    "Result",
    "check_text",
    "normalize",
    "strip_links",
    "find_verbatim_runs",
    "opener_echo",
    "opening_line",
    "phrasing_overlap",
    "shingles",
    "stat_fingerprint",
    "__version__",
]
