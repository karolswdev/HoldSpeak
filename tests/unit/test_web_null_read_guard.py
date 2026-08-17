"""Static guard against selector-owned or HTML-string React regressions."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2] / "web/src"


def test_product_components_do_not_mutate_global_dom_or_inject_html() -> None:
    offenders = []
    for path in sorted(ROOT.rglob("*")):
        if path.suffix not in {".ts", ".tsx"}:
            continue
        text = path.read_text()
        for pattern in (r"document\.(?:querySelector|querySelectorAll)\s*\(", r"\.innerHTML\s*=", r"insertAdjacentHTML\s*\("):
            if re.search(pattern, text):
                offenders.append(str(path.relative_to(ROOT)))
    assert not offenders, f"Selector/HTML-owned product state: {sorted(set(offenders))}"


def test_only_typed_api_client_calls_fetch() -> None:
    # lib/sfx.ts fetches STATIC AUDIO ASSETS (HS-135-12), not API data —
    # the typed-client law governs API reads, so the asset loader is the
    # one sanctioned non-api fetch site.
    allowed = ["lib/api.ts", "lib/sfx.ts"]
    callers = []
    for path in sorted(ROOT.rglob("*.ts*")):
        if re.search(r"\bfetch\s*\(", path.read_text()):
            callers.append(str(path.relative_to(ROOT)))
    assert callers == allowed
