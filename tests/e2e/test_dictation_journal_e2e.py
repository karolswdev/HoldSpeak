"""HS-45-01: real spoken→enriched→**journaled** dictation e2e against a live LLM.

Opt-in / auto-skip, mirroring the HS-39 enrichment e2e: it runs only when
`HOLDSPEAK_DICTATION_E2E_BASE_URL` + `HOLDSPEAK_DICTATION_E2E_MODEL` point at a
reachable OpenAI-compatible endpoint (e.g. the `.43` homelab llama.cpp). In
hosted CI (no endpoint) it skips. Where it runs, it drives the **real**
all-features dictation pipeline and then journals the resulting run through the
**real** `DictationJournalRepository` into a real SQLite DB — the same path the
live runtime + dry-run use — and asserts the persisted row faithfully captures
the run.

Run it:

    HOLDSPEAK_DICTATION_E2E_BASE_URL=http://192.168.1.43:8080/v1 \
    HOLDSPEAK_DICTATION_E2E_MODEL=Qwen3.5-9B-UD-Q6_K_XL.gguf \
    uv run pytest -s tests/e2e/test_dictation_journal_e2e.py
"""
from __future__ import annotations

import os
import socket
import sys
from pathlib import Path
from urllib.parse import urlparse

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from journal_e2e_demo import run_journal_e2e, render  # noqa: E402

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
        "reachable OpenAI-compatible endpoint to run the real dictation journal e2e"
    ),
)


def test_real_dictation_run_is_durably_journaled(tmp_path) -> None:
    result = run_journal_e2e(
        base_url=_BASE_URL,
        model=_MODEL,
        rewrite_passes=2,
        db_path=tmp_path / "journal.db",
    )

    # Show the persisted afterlife under `pytest -s`.
    print(render(result, color=sys.stdout.isatty()))

    assert result.runtime_status == "loaded"

    # --- a row was persisted, tagged as a real dictation run ---
    assert result.row_id > 0
    assert result.row_source == "dictation"

    # --- the row faithfully captures what the real pipeline did ---
    # transcript stored verbatim (no secret in this fixture, so not redacted)
    assert result.row_transcript == result.spoken
    # the typed result == the enriched output, and is substantially richer
    assert result.row_final_text == result.enriched
    assert result.changed, "journaled final text is identical to the raw dictation"
    assert len(result.row_final_text) > len(result.spoken) * 1.5

    # routing + target + confidence captured
    assert result.row_block_id == result.intent_block
    assert result.row_target == result.target_profile
    assert result.row_confidence is not None

    # per-stage latency captured for every stage that ran (all 3 against a real
    # endpoint), with the multi-pass rewrite timings preserved
    assert "intent-router" in result.row_stage_ms
    assert "kb-enricher" in result.row_stage_ms
    assert "project-rewriter" in result.row_stage_ms
    assert result.row_total_ms > 0
    assert len(result.row_rewrite_pass_ms) == 2

    # set by HS-45-03, not here
    assert result.row_corrected is False
