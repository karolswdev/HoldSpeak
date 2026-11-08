"""Meaning search with the REAL embedding model: INDEXING n of m -> ON -> OFF.

The test diet (2026-10-11): the browser test drove these states through the
Runs on row. The states are the service's own answer (MeaningSearchService
.status), so this asks the service directly, with the same real GGUF, the
same 700 notes and the real memory conductor. It skips without the model,
as the browser test did. The row's words for each state are fenced in
web/src/features/concierge/__tests__/meaningSearchRow.test.tsx.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

MODEL_PATH = os.environ.get("HOLDSPEAK_MEMORY_EMBED_MODEL", "")

pytestmark = [pytest.mark.slow, pytest.mark.requires_llama_cpp, pytest.mark.timeout(600, method="thread")]


def test_indexing_on_and_off_with_the_real_model(tmp_path: Path) -> None:
    """replaces: tests/e2e/test_meaning_search_row_glass.py::test_indexing_on_and_off_with_the_real_model"""
    if not MODEL_PATH or not Path(MODEL_PATH).is_file():
        pytest.skip("set HOLDSPEAK_MEMORY_EMBED_MODEL to nomic-embed-text-v1.5.Q8_0.gguf")
    pytest.importorskip("llama_cpp")
    from holdspeak import memory_conductor
    from holdspeak.db import Database
    from holdspeak.kernel.runtime import _configure
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from holdspeak.services.meaning_search_service import MeaningSearchService
    from tests.unit.test_phase143_inference_assignments import OWNER

    db = Database(tmp_path / "meaning.db")
    for index in range(700):
        db.notes.upsert(
            note_id=f"seed-{index}", title=f"Site visit {index}",
            body_markdown=f"Visit {index}: the crew checked pump {index % 17} and logged valve {index % 29}.",
        )
    broker = _configure(db)
    home = tmp_path / "home"
    home.mkdir()
    service = MeaningSearchService(
        db, assignment_service=InferenceAssignmentService(db),
        broker_provider=lambda: broker, home_provider=lambda: home, wake=lambda: None,
    )
    try:
        # OFF with the file on this device: the press sends nothing out.
        off = service.status(OWNER)
        assert off["state"] == "off" and off["model"]["on_device"] is True and off["egress"] is None, off

        on = service.turn_on(OWNER)
        assert on["state"] == "indexing", on
        memory_conductor.tick(db, broker)
        status = service.status(OWNER)
        assert status["total"] > 0 and status["indexed"] >= 1, status
        for _ in range(20):
            if status["state"] == "on":
                break
            memory_conductor.tick(db, broker)
            status = service.status(OWNER)
        assert status["state"] == "on" and status["indexed"] == status["total"], status
        assert status["egress"] is None

        assert service.turn_off(OWNER)["state"] == "off"
    finally:
        service.wait(10)
