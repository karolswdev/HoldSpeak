"""End-to-end integration test for `MermaidArchitecturePlugin` (HS-16-01).

Verifies that, given a meeting with architecture-flavoured transcript:
  1. `host.execute("mermaid_architecture", ...)` queues the run because
     the plugin is `execution_mode="deferred"`,
  2. `host.process_next_deferred_run()` actually invokes the plugin's
     `run()` (with our stub intel call) and produces the success-shape
     output,
  3. `synthesize_and_persist` lifts that run into a `diagram` artifact
     persisted into the `MeetingDatabase`.

The synthesis body shape itself is HS-16-03's concern; here we just
assert the artifact exists with the right `artifact_type` and
`plugin_id`.
"""

from __future__ import annotations

import shutil
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from holdspeak.db import MeetingDatabase, reset_database
from holdspeak.meeting_session import MeetingState, TranscriptSegment
from holdspeak.plugins.builtin import MermaidArchitecturePlugin
from holdspeak.plugins.host import PluginHost
from holdspeak.plugins.synthesis import synthesize_and_persist


_STUB_RESPONSE = (
    "API fans out to Auth, Inventory, and Postgres while the frontend "
    "talks only to the API.\n"
    "```mermaid\n"
    "flowchart TD\n"
    "  Frontend --> API\n"
    "  API --> Auth\n"
    "  API --> Inventory\n"
    "  API --> DB[(Postgres)]\n"
    "```\n"
)


@pytest.fixture
def temp_db():
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "mermaid_arch.db"
    try:
        yield MeetingDatabase(db_path)
    finally:
        reset_database()
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.integration
def test_mermaid_architecture_plugin_lands_diagram_artifact(temp_db) -> None:
    host = PluginHost(default_timeout_seconds=5.0, enabled_capabilities={"llm"})
    host.register(
        MermaidArchitecturePlugin(intel_call=lambda _messages: _STUB_RESPONSE)
    )

    state = MeetingState(
        id="m-mermaid-it",
        started_at=datetime(2026, 5, 8, 9, 0, 0),
        title="Architecture review",
        segments=[
            TranscriptSegment(
                text=(
                    "Let's lay out the API service: the frontend talks to the API, "
                    "which fans out to Auth, Inventory, and Postgres."
                ),
                speaker="Me",
                start_time=0.0,
                end_time=20.0,
            ),
        ],
    )
    temp_db.save_meeting(state)

    transcript = state.segments[0].text

    # Step 1 — execute() queues the deferred plugin without running it.
    queued = host.execute(
        "mermaid_architecture",
        context={"transcript": transcript, "active_intents": ["architecture"]},
        meeting_id="m-mermaid-it",
        window_id="w-1",
        transcript_hash="h-1",
    )
    assert queued.status == "queued"

    # Step 2 — drain the deferred queue: this is where run() actually
    # fires (host's worker uses our stubbed intel_call).
    executed = host.process_next_deferred_run(timeout_seconds=5.0)
    assert executed is not None, "deferred queue was unexpectedly empty"
    assert executed.status == "success", f"plugin failed: {executed.error}"
    assert executed.output is not None
    assert "mermaid" in executed.output, (
        f"expected success shape with 'mermaid' key, got keys "
        f"{sorted(executed.output.keys())}"
    )
    assert executed.output["diagram_kind"] == "flowchart"
    assert executed.output["confidence_hint"] == 1.0

    # Step 3 — persist the run, then synthesize + persist the artifact.
    temp_db.record_plugin_run(
        meeting_id="m-mermaid-it",
        window_id="w-1",
        plugin_id="mermaid_architecture",
        plugin_version=executed.plugin_version,
        status=executed.status,
        idempotency_key=executed.idempotency_key,
        duration_ms=executed.duration_ms,
        output=executed.output,
    )

    drafts, lineages = synthesize_and_persist(temp_db, "m-mermaid-it")

    assert len(drafts) == 1, f"expected exactly one draft, got {len(drafts)}"
    diagram = drafts[0]
    assert diagram.artifact_type == "diagram"
    assert diagram.plugin_id == "mermaid_architecture"
    assert diagram.confidence > 0.5
    assert diagram.structured_json["plugin_id"] == "mermaid_architecture"

    # Lineage matches the artifact we just landed.
    assert len(lineages) == 1
    assert lineages[0].artifact_id == diagram.artifact_id

    # Persisted in the DB.
    persisted = temp_db.list_artifacts("m-mermaid-it")
    assert {a.id for a in persisted} == {diagram.artifact_id}
    assert {a.artifact_type for a in persisted} == {"diagram"}
