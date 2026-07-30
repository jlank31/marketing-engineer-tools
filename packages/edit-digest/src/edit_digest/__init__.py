"""edit-digest — learn an editor's style from what they actually change.

    from edit_digest import compute, render_prompt_block

    digest = compute(edits)          # [{"original_text": ..., "edited_text": ...}]
    print(render_prompt_block(digest))

    Write "brands", not "vendors" (7x).
    Cut "very" (5x). The editor removes it every time.

No model, no API key, no network. It's difflib over word tokens, so it costs
nothing and returns the same answer every time.
"""

from .digest import (
    Digest,
    compute,
    render_prompt_block,
    render_report,
    to_dict,
)
from .loaders import load, load_csv, load_json, load_jsonl, normalize

__version__ = "0.1.0"

__all__ = [
    "Digest", "compute", "render_prompt_block", "render_report", "to_dict",
    "load", "load_jsonl", "load_json", "load_csv", "normalize",
    "__version__",
]
