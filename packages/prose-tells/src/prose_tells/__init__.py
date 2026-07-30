"""prose-tells — find the lines that make copy read as machine-written.

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

    from prose_tells import check_text, Profile
    result = check_text(draft, Profile())

Everything is a pure function over strings. No network, no API key, no config
file, no state. `Profile` carries anything brand-specific, so nothing in this
package hardcodes a house style.
"""

from .content_quality import Profile, Result, check_text, normalize, strip_links
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
