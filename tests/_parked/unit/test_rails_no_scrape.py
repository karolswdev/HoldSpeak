"""The receipt rule (HS-88-01), mechanical: rails grounding is a
receipt, not a scrape.

`grounding_rails.py` reads files that `dw context` NAMES, as opaque
text. It must never re-derive rail STATE — a story's status, a
session's correlation — by parsing the markdown body. This census
fails if the rails path grows a status-parsing pattern; status, when a
run needs it, comes from `dw state`/`dw sessions`, the three-document
client contract.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RAILS = REPO / "holdspeak" / "grounding_rails.py"

# Patterns that would mean "I parsed state out of the markdown."
_SCRAPE_PATTERNS = [
    re.compile(r"""["']\s*Status\s*:""", re.IGNORECASE),
    re.compile(r"\bStatus\s*:\s*\{"),
    re.compile(r"re\.(search|match|findall|compile)\s*\(\s*['\"][^'\"]*[Ss]tatus"),
    re.compile(r"\.split\(\s*['\"]\s*Status"),
    re.compile(r"\bcorrelation\b\s*="),
]


def test_rails_hydration_reads_files_it_never_status_scrapes() -> None:
    src = RAILS.read_text(encoding="utf-8")
    hits = [p.pattern for p in _SCRAPE_PATTERNS if p.search(src)]
    assert not hits, (
        "grounding_rails.py appears to parse rail STATE from markdown "
        f"({hits}) — the receipt rule: read the dw-named file as opaque "
        "text; status comes from dw state/sessions, never a .md scrape."
    )


def test_rails_hydration_resolves_paths_only_via_dw_context() -> None:
    # The file it reads must be a path the context document NAMED
    # (trace/status_file/readme), never composed from a slug. Proxy:
    # the module reads `_fetch_document(..., ["context", ...])` and
    # pulls paths from the doc, and does not build phase/story paths by
    # f-string slug interpolation.
    src = RAILS.read_text(encoding="utf-8")
    assert '"context"' in src, "rails hydration must read dw context"
    # No hand-built roadmap paths (the smell of a scrape/guess).
    assert 'phase-{' not in src and 'story-{' not in src, (
        "rails hydration builds a path by slug interpolation — resolve "
        "via the context document's named trace instead"
    )
