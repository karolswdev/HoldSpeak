"""HS-173-02: The model drafter wire -- provenance, prompt, and fallback.

Acceptance tested:
- UNGROUNDED: model output with an ungrounded sentence produces
  verified=False and UNVERIFIED_MARKER present in body_md.
- REF-PRESERVATION: every inventory ref is preserved verbatim in the
  model output.
- FALLBACK: _ModelDraftFailed falls back to deterministic; host and
  model are null.
- PROVENANCE-COLUMNS: generator_host and generator_model are recorded
  in the persisted draft row.
- ROUTE-KEYS: the route exposes generatorHost and generatorModel.
- STEWARD-RECEIPT: the steward's draft_update receipt carries
  generator, generator_host, generator_model.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import pytest

from holdspeak.db import Database, reset_database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.project_contracts import generate_pupd_id
from holdspeak.services.project_service import ProjectService
from holdspeak.services.project_evidence_collector import (
    ProjectEvidenceCollector,
)
from holdspeak.services.project_delta_service import ProjectDeltaService
from holdspeak.services.project_update_service import (
    PROJECT_UPDATE_CAPABILITY,
    SECTION_KEYS,
    UNVERIFIED_MARKER,
    Claim,
    ProjectUpdateService,
    _HONEST_MINIMAL,
    _build_model_prompt,
    _parse_model_output,
    _resolve_generator_provenance,
)


OWNER = Principal(PrincipalKind.OWNER, "drafter-wire-test")
NOW_ISO = "2026-06-15T10:00:00"

# ---- DB rig ----------------------------------------------------------------

@pytest.fixture()
def rig(tmp_path):
    reset_database()
    db = Database(tmp_path / "drafter_wire.db")
    yield db
    reset_database()


# ---- Helpers ----------------------------------------------------------------

def _seed_project(
    db: Database,
    project_id: str = "proj-wire01",
    name: str = "Wire Project",
    revision: int = 5,
) -> str:
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO projects
               (id, name, description, keywords_json, team_members_json,
                context_json, detection_threshold, revision,
                created_at, updated_at)
               VALUES (?, ?, '', '[]', '[]', '{}', 0.4, ?,
                       ?, ?)""",
            (project_id, name, revision, NOW_ISO, NOW_ISO),
        )
    return project_id


def _seed_items(db: Database, project_id: str) -> None:
    """Seed two focus items so the deterministic drafter has claims."""
    with db._connection() as conn:
        for i, (title, lifecycle) in enumerate([
            ("Widget build", "active"),
            ("API migration", "planned"),
        ]):
            conn.execute(
                """INSERT INTO project_items
                   (id, project_id, item_type, title, lifecycle,
                    severity, sort_key, created_at, updated_at)
                   VALUES (?, ?, 'milestone', ?, ?, NULL, ?, ?, ?)""",
                (
                    f"item_{i}",
                    project_id,
                    title,
                    lifecycle,
                    float(i),
                    NOW_ISO,
                    NOW_ISO,
                ),
            )


def _seed_assignment(
    db: Database,
    capability_id: str = PROJECT_UPDATE_CAPABILITY,
    *,
    endpoint: str = "http://192.168.1.43:8080",
    profile_name: str = "Qwen3-32B-Q6_K",
    profile_model: str = "qwen3-32b",
    boundary: str = "private_network",
    node: str = "",
) -> str:
    """Seed the minimal assignment chain WITH provenance-carrying fields."""
    assignment_id = "assign_wire_001"
    profile_id = "profile_wire_draft"
    with db._connection() as conn:
        conn.execute("PRAGMA foreign_keys = OFF")

        # Profile with a name and model the concierge can display.
        conn.execute(
            """INSERT OR IGNORE INTO profiles
               (id, name, kind, model_file, base_url, model, node,
                context_limit, requires_key, created_at, last_modified, deleted)
               VALUES (?, ?, 'onDevice', '', ?, ?, ?, 16384, 0, ?, ?, 0)""",
            (
                profile_id,
                profile_name,
                endpoint,
                profile_model,
                node,
                NOW_ISO,
                NOW_ISO,
            ),
        )

        # Deployment revision with endpoint and boundary.
        conn.execute(
            """INSERT OR IGNORE INTO deployment_revisions
               (id, model, kind, boundary, engine, destination_id,
                endpoint, node)
               VALUES (?, ?, 'local', ?, 'test', 'local', ?, ?)""",
            (
                f"deprev_{profile_id}",
                profile_id,
                boundary,
                endpoint,
                node,
            ),
        )

        # Inference assignment chain.
        conn.execute(
            """INSERT OR IGNORE INTO inference_assignment_revisions
               (assignment_id, revision, assignment_key,
                scope_kind, selector_kind, capability_id,
                payload_json, sha256, created_at)
               VALUES (?, 1, ?, 'invocation', 'capability', ?,
                       '{}', '', ?)""",
            (
                assignment_id,
                f"capability:{capability_id}",
                capability_id,
                NOW_ISO,
            ),
        )
        conn.execute(
            """INSERT OR IGNORE INTO inference_assignment_heads
               (assignment_key, assignment_id, revision, cleared,
                updated_at)
               VALUES (?, ?, 1, 0, ?)""",
            (f"capability:{capability_id}", assignment_id, NOW_ISO),
        )
        conn.execute(
            """INSERT OR IGNORE INTO inference_assignments
               (id, assignment_id, assignment_revision, ordinal,
                profile_id, profile_revision)
               VALUES (?, ?, 1, 1, ?, 1)""",
            (f"ia_{assignment_id}", assignment_id, profile_id),
        )

        conn.execute("PRAGMA foreign_keys = ON")
    return assignment_id


# ---- Mock runner/broker ----------------------------------------------------

class _MockRunner:
    def __init__(self, *, output=None, error=None):
        self._output = output
        self._error = error
        self.invoke_calls: list[Any] = []

    def invoke(self, request, adapter, publish=None):
        self.invoke_calls.append(request)
        if self._error is not None:
            raise self._error
        if publish is not None and self._output is not None:
            publish({"output": self._output})
        class _Outcome:
            result = None
        return _Outcome()


class _MockBroker:
    def __init__(self, db, runner):
        self.database = db
        self.inference_runner = runner


def _make_service(db):
    collector = ProjectEvidenceCollector(db)
    delta_svc = ProjectDeltaService(db, collector)
    project_svc = ProjectService(db, delta_service=delta_svc)
    return ProjectUpdateService(
        db, project_service=project_svc, delta_service=delta_svc,
    )


def _make_model_service(db, *, runner_output=None, runner_error=None):
    collector = ProjectEvidenceCollector(db)
    delta_svc = ProjectDeltaService(db, collector)
    project_svc = ProjectService(db, delta_service=delta_svc)
    runner = _MockRunner(output=runner_output, error=runner_error)
    broker = _MockBroker(db, runner)
    _seed_assignment(db)
    svc = ProjectUpdateService(
        db, project_service=project_svc, delta_service=delta_svc,
        broker=broker,
    )
    return svc, runner


def _model_json_output(sections):
    return json.dumps({"sections": sections})


def _good_model_output(inventory_claims):
    sections = []
    by_section = {}
    for claim in inventory_claims:
        by_section.setdefault(claim.section, []).append(claim)
    for key in SECTION_KEYS:
        claims = by_section.get(key, [])
        sentences = [
            {"text": f"Rewritten: {c.text}", "cited_refs": list(c.refs)}
            for c in claims
        ]
        sections.append({"key": key, "sentences": sentences})
    return _model_json_output(sections)


# ╔═══════════════════════════════════════════════════════════════════╗
# ║  UNGROUNDED SENTENCE -> verified=False + MARKER                  ║
# ╚═══════════════════════════════════════════════════════════════════╝

class TestUngroundedClaims:
    """Model output with ungrounded sentences marks them UNVERIFIED."""

    def test_ungrounded_sentence_verified_false_and_marker_present(self, rig):
        db = rig
        pid = _seed_project(db)
        _seed_items(db, pid)

        # Build deterministic draft to get the inventory.
        det_svc = _make_service(db)
        det_result = det_svc.draft_update(OWNER, pid)
        det_claims = [
            Claim(**c) for c in json.loads(det_result["claims_json"])
        ]
        inventory_refs = frozenset(
            ref for c in det_claims for ref in c.refs
        )

        # Model output with one grounded + one ungrounded sentence.
        sections = []
        for key in SECTION_KEYS:
            section_claims = [c for c in det_claims if c.section == key]
            sentences = []
            for c in section_claims:
                sentences.append({
                    "text": f"Rewritten: {c.text}",
                    "cited_refs": list(c.refs),
                })
            if key == "progress":
                # Add an ungrounded sentence (no valid refs).
                sentences.append({
                    "text": "The team morale is extremely high.",
                    "cited_refs": [],
                })
            sections.append({"key": key, "sentences": sentences})

        model_output = _model_json_output(sections)

        svc, runner = _make_model_service(db, runner_output=model_output)
        result = svc.draft_update(OWNER, pid, generator="model")

        # Parse claims from the result.
        claims = json.loads(result["claims_json"])
        ungrounded = [c for c in claims if c.get("verified") is False]
        assert len(ungrounded) >= 1, "Expected at least one unverified claim"

        # The ungrounded claim's text matches what the model added.
        ungrounded_texts = [c["text"] for c in ungrounded]
        assert "The team morale is extremely high." in ungrounded_texts

        # The UNVERIFIED_MARKER appears in body_md.
        assert UNVERIFIED_MARKER in result["body_md"]

    def test_sentence_with_invented_refs_is_unverified(self, rig):
        db = rig
        pid = _seed_project(db)
        _seed_items(db, pid)

        model_output = _model_json_output([{
            "key": "progress",
            "sentences": [{
                "text": "Great progress on phase 99.",
                "cited_refs": ["item:nonexistent_999"],
            }],
        }])

        svc, runner = _make_model_service(db, runner_output=model_output)
        result = svc.draft_update(OWNER, pid, generator="model")

        claims = json.loads(result["claims_json"])
        progress_claims = [c for c in claims if c["section"] == "progress"]
        invented = [
            c for c in progress_claims
            if c["text"] == "Great progress on phase 99."
        ]
        assert len(invented) == 1
        assert invented[0].get("verified") is False
        assert invented[0]["refs"] == []


# ╔═══════════════════════════════════════════════════════════════════╗
# ║  REF PRESERVATION                                                ║
# ╚═══════════════════════════════════════════════════════════════════╝

class TestRefPreservation:
    """Every inventory ref is preserved verbatim in the model output."""

    def test_all_inventory_refs_preserved(self, rig):
        db = rig
        pid = _seed_project(db)
        _seed_items(db, pid)

        # Build deterministic to get the inventory.
        det_svc = _make_service(db)
        det_result = det_svc.draft_update(OWNER, pid)
        det_claims = [
            Claim(**c) for c in json.loads(det_result["claims_json"])
        ]

        # A good model output that cites every ref.
        model_output = _good_model_output(det_claims)

        svc, runner = _make_model_service(db, runner_output=model_output)
        result = svc.draft_update(OWNER, pid, generator="model")

        claims = json.loads(result["claims_json"])

        # All model claims should be verified (refs match inventory).
        for c in claims:
            assert c.get("verified", True) is True, (
                f"Claim with text {c['text']!r} should be verified"
            )

        # No UNVERIFIED marker in body.
        assert UNVERIFIED_MARKER not in result["body_md"]


# ╔═══════════════════════════════════════════════════════════════════╗
# ║  FALLBACK -> deterministic, host/model null                      ║
# ╚═══════════════════════════════════════════════════════════════════╝

class TestFallbackProvenance:
    """_ModelDraftFailed fallback produces deterministic with null host/model."""

    def test_no_broker_fallback(self, rig):
        db = rig
        pid = _seed_project(db)
        _seed_items(db, pid)

        # Service with NO broker.
        svc = _make_service(db)
        result = svc.draft_update(OWNER, pid, generator="model")

        assert result["generator"] == "deterministic"
        assert result["generator_host"] is None
        assert result["generator_model"] is None

    def test_unparseable_output_fallback(self, rig):
        db = rig
        pid = _seed_project(db)
        _seed_items(db, pid)

        svc, runner = _make_model_service(
            db, runner_output="this is not valid json {{{",
        )
        result = svc.draft_update(OWNER, pid, generator="model")

        assert result["generator"] == "deterministic"
        assert result["generator_host"] is None
        assert result["generator_model"] is None
        assert UNVERIFIED_MARKER not in result["body_md"]

    def test_runner_error_fallback(self, rig):
        db = rig
        pid = _seed_project(db)
        _seed_items(db, pid)

        svc, runner = _make_model_service(
            db, runner_error=RuntimeError("provider_timeout"),
        )
        result = svc.draft_update(OWNER, pid, generator="model")

        assert result["generator"] == "deterministic"
        assert result["generator_host"] is None
        assert result["generator_model"] is None

    def test_deterministic_generator_no_marker(self, rig):
        """Deterministic fallback has no UNVERIFIED markers, host/model null."""
        db = rig
        pid = _seed_project(db)
        _seed_items(db, pid)

        svc = _make_service(db)
        result = svc.draft_update(OWNER, pid)  # default = deterministic

        assert result["generator"] == "deterministic"
        assert result["generator_host"] is None
        assert result["generator_model"] is None
        assert UNVERIFIED_MARKER not in result["body_md"]
        claims = json.loads(result["claims_json"])
        for c in claims:
            assert "verified" not in c


# ╔═══════════════════════════════════════════════════════════════════╗
# ║  PROVENANCE COLUMNS                                              ║
# ╚═══════════════════════════════════════════════════════════════════╝

class TestProvenanceColumns:
    """generator_host and generator_model are persisted in the draft row."""

    def test_model_draft_records_host_and_model(self, rig):
        db = rig
        pid = _seed_project(db)
        _seed_items(db, pid)

        det_svc = _make_service(db)
        det_result = det_svc.draft_update(OWNER, pid)
        det_claims = [
            Claim(**c) for c in json.loads(det_result["claims_json"])
        ]
        model_output = _good_model_output(det_claims)

        svc, runner = _make_model_service(db, runner_output=model_output)
        result = svc.draft_update(OWNER, pid, generator="model")

        assert result["generator"].startswith("model:")

        # Provenance columns are recorded.
        assert result["generator_host"] is not None
        assert result["generator_host"] == "192.168.1.43"
        assert result["generator_model"] is not None
        assert "Qwen" in result["generator_model"]

    def test_deterministic_draft_null_provenance(self, rig):
        db = rig
        pid = _seed_project(db)
        _seed_items(db, pid)

        svc = _make_service(db)
        result = svc.draft_update(OWNER, pid)

        assert result["generator"] == "deterministic"
        assert result["generator_host"] is None
        assert result["generator_model"] is None

    def test_provenance_persisted_in_db_row(self, rig):
        """The provenance survives a re-read from the DB."""
        db = rig
        pid = _seed_project(db)
        _seed_items(db, pid)

        det_svc = _make_service(db)
        det_result = det_svc.draft_update(OWNER, pid)
        det_claims = [
            Claim(**c) for c in json.loads(det_result["claims_json"])
        ]
        model_output = _good_model_output(det_claims)

        svc, runner = _make_model_service(db, runner_output=model_output)
        result = svc.draft_update(OWNER, pid, generator="model")

        # Re-read from DB.
        row = db.project_updates.get_update(result["id"])
        assert row["generator_host"] == "192.168.1.43"
        assert "Qwen" in row["generator_model"]


# ╔═══════════════════════════════════════════════════════════════════╗
# ║  ROUTE KEYS                                                      ║
# ╚═══════════════════════════════════════════════════════════════════╝

class TestRouteKeys:
    """The route exposes generatorHost and generatorModel."""

    def test_enrich_update_adds_camel_keys(self):
        from holdspeak.web.routes.project_updates import _enrich_update

        update = {
            "id": "upd_001",
            "generator": "model:assign_001",
            "generator_host": "192.168.1.43",
            "generator_model": "Qwen3 32B Q6",
        }
        enriched = _enrich_update(update)

        assert enriched["generatorHost"] == "192.168.1.43"
        assert enriched["generatorModel"] == "Qwen3 32B Q6"
        # The original keys are preserved.
        assert enriched["generator_host"] == "192.168.1.43"
        assert enriched["generator_model"] == "Qwen3 32B Q6"

    def test_enrich_update_null_when_deterministic(self):
        from holdspeak.web.routes.project_updates import _enrich_update

        update = {
            "id": "upd_002",
            "generator": "deterministic",
            "generator_host": None,
            "generator_model": None,
        }
        enriched = _enrich_update(update)

        assert enriched["generatorHost"] is None
        assert enriched["generatorModel"] is None


# ╔═══════════════════════════════════════════════════════════════════╗
# ║  STEWARD RECEIPT                                                  ║
# ╚═══════════════════════════════════════════════════════════════════╝

class TestStewardReceipt:
    """The steward's draft_update receipt carries provenance."""

    def test_steward_draft_update_receipt_has_provenance(self, rig):
        db = rig
        pid = _seed_project(db)
        _seed_items(db, pid)

        det_svc = _make_service(db)
        det_result = det_svc.draft_update(OWNER, pid)
        det_claims = [
            Claim(**c) for c in json.loads(det_result["claims_json"])
        ]
        model_output = _good_model_output(det_claims)

        # Build update service with broker.
        collector = ProjectEvidenceCollector(db)
        delta_svc = ProjectDeltaService(db, collector)
        project_svc = ProjectService(db, delta_service=delta_svc)
        runner = _MockRunner(output=model_output)
        broker = _MockBroker(db, runner)
        _seed_assignment(db)
        update_svc = ProjectUpdateService(
            db, project_service=project_svc, delta_service=delta_svc,
            broker=broker,
        )

        # Import the steward service.
        from holdspeak.services.project_steward_service import (
            ProjectStewardService,
        )
        steward = ProjectStewardService(
            db, collector, delta_svc,
            update_service=update_svc,
            project_service=project_svc,
        )

        # Call _effect_draft_update directly.
        receipt = steward._effect_draft_update(OWNER, pid)

        assert receipt["effect"] == "draft_update"
        assert receipt["generator"] is not None
        assert "generator_host" in receipt
        assert "generator_model" in receipt


# ╔═══════════════════════════════════════════════════════════════════╗
# ║  _resolve_generator_provenance unit                              ║
# ╚═══════════════════════════════════════════════════════════════════╝

class TestResolveGeneratorProvenance:
    """The provenance helper derives host and model from a deployment rev."""

    def test_host_from_endpoint(self, rig):
        db = rig
        _seed_assignment(db, endpoint="http://192.168.1.43:8080")

        host, model = _resolve_generator_provenance(
            db, "deprev_profile_wire_draft",
        )
        assert host == "192.168.1.43"
        assert model  # Non-empty model name.

    def test_host_from_node_when_set(self, rig):
        db = rig
        _seed_assignment(
            db, endpoint="", node="my-lan-box.local",
            boundary="private_network",
        )

        host, model = _resolve_generator_provenance(
            db, "deprev_profile_wire_draft",
        )
        assert host == "my-lan-box.local"

    def test_host_fallback_to_boundary(self, rig):
        db = rig
        _seed_assignment(
            db, endpoint="", node="", boundary="same_device",
        )

        host, model = _resolve_generator_provenance(
            db, "deprev_profile_wire_draft",
        )
        assert host == "same_device"

    def test_model_display_name_from_profile(self, rig):
        db = rig
        _seed_assignment(
            db, profile_name="Qwen3-32B-Q6_K",
            profile_model="qwen3-32b",
        )

        host, model = _resolve_generator_provenance(
            db, "deprev_profile_wire_draft",
        )
        assert "Qwen" in model

    def test_nonexistent_revision_returns_defaults(self, rig):
        db = rig

        host, model = _resolve_generator_provenance(db, "nonexistent_rev")
        assert host == "local"
        assert model == "Unknown engine"


# ╔═══════════════════════════════════════════════════════════════════╗
# ║  PROMPT CONTENT                                                   ║
# ╚═══════════════════════════════════════════════════════════════════╝

class TestPromptContent:
    """The model prompt instructs stakeholder readability and ref preservation."""

    def test_prompt_mentions_stakeholder(self):
        claims = [
            Claim(
                span_id="s_progress_0",
                text="Widget build active",
                refs=["item:item_0"],
                section="progress",
            ),
        ]
        payload = _build_model_prompt(claims)
        system = payload["system_prompt"]

        assert "stakeholder" in system.lower()
        assert "ref" in system.lower()
        assert "verbatim" in system.lower()

    def test_prompt_prohibits_adding_facts(self):
        claims = [
            Claim(
                span_id="s_progress_0",
                text="Widget build active",
                refs=["item:item_0"],
                section="progress",
            ),
        ]
        payload = _build_model_prompt(claims)
        system = payload["system_prompt"]

        # The prompt must instruct the model not to add facts.
        assert "do not add" in system.lower() or "not add facts" in system.lower()
