"""HS-39: real spoken→enriched dictation e2e against a live LLM endpoint.

Opt-in / auto-skip, mirroring the spoken-meeting e2e tests: it runs only when
`HOLDSPEAK_DICTATION_E2E_BASE_URL` + `HOLDSPEAK_DICTATION_E2E_MODEL` point at a
reachable OpenAI-compatible endpoint (e.g. the `.43` homelab llama.cpp). In
hosted CI (no endpoint) it skips. Where it runs, it drives the **real**
multi-pass project-rewriter (HS-39-01) over the `dictation_demo_project`
fixture (`.hs/` context + code) and asserts rough dictation became a precise,
project-grounded coding-agent task.

Run it:

    HOLDSPEAK_DICTATION_E2E_BASE_URL=http://192.168.1.43:8080/v1 \
    HOLDSPEAK_DICTATION_E2E_MODEL=Qwen3.5-9B-UD-Q6_K_XL.gguf \
    uv run pytest -s tests/e2e/test_dictation_enrichment_e2e.py
"""

from __future__ import annotations

import os
import socket
import sys
from pathlib import Path
from urllib.parse import urlparse

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from dictation_enrichment_demo import run_enrichment, render  # noqa: E402

_BASE_URL = os.environ.get("HOLDSPEAK_DICTATION_E2E_BASE_URL")
_MODEL = os.environ.get("HOLDSPEAK_DICTATION_E2E_MODEL")


def _reachable(base_url: str | None) -> bool:
    if not base_url:
        return False
    parsed = urlparse(base_url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        with socket.create_connection((host, port), timeout=2.0):
            return True
    except OSError:
        return False


pytestmark = pytest.mark.skipif(
    not (_BASE_URL and _MODEL and _reachable(_BASE_URL)),
    reason=(
        "set HOLDSPEAK_DICTATION_E2E_BASE_URL + HOLDSPEAK_DICTATION_E2E_MODEL to a "
        "reachable OpenAI-compatible endpoint to run the real dictation enrichment e2e"
    ),
)


def test_spoken_dictation_enriches_against_real_endpoint() -> None:
    result = run_enrichment(base_url=_BASE_URL, model=_MODEL, rewrite_passes=2)

    # Show the gorgeous before/after + feature panel under `pytest -s`.
    print(render(result, color=sys.stdout.isatty()))

    assert result.runtime_status == "loaded"
    # The fixture's `.hs/` context actually loaded (grounding is wired).
    assert result.hs_files, "no .hs context loaded from the demo fixture"
    assert "memory" in result.hs_files and "instructions" in result.hs_files

    # --- every Phase-39 feature fired, end-to-end, against the real endpoint ---
    # HS-39-01 multi-pass rewriting.
    assert result.passes_run == 2, f"expected 2 rewrite passes, got {result.passes_run}"
    assert len(result.pass_ms) == 2
    # HS-39-02 correction memory nudged routing to the seeded block.
    assert result.correction_nudge == result.seeded_correction_block
    assert result.intent_block == result.seeded_correction_block
    assert result.intent_corrected
    # the kb-enricher injected for that nudged block.
    assert result.kb_applied_block == result.seeded_correction_block
    # HS-39-03 model-assisted target detection inferred a target from the words.
    assert result.target_heuristic_conf < 0.8
    assert result.model_assisted_fired, "model-assisted target detection did not fire"
    assert result.target_final_source == "llm"

    # Enrichment happened and is substantially richer than the raw dictation.
    assert result.changed, "enriched text is identical to the spoken input"
    assert len(result.task) > len(result.spoken) * 1.5

    low = result.task.lower()
    assert "idempotency" in low  # on-topic …
    # … and grounded in project specifics drawn from `.hs/`/KB (not generic prose).
    grounding = ("ledger_entries", "idempotency", "double-entry", "double entry",
                 "src/ledgerline", "minor units", "append-only", "acceptance criteria")
    hits = [g for g in grounding if g in low]
    assert len(hits) >= 2, f"enriched task not grounded in project specifics; hits={hits}"
