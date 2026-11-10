"""The ambient dw observer's core (HS-88-03).

The pure half — event diffing, batch summary, journal body — against a
fake model. The invariants: off by default (config), a batch summarizes
only NEW events, the model-unreachable degrade is a typed absence (never
a fabricated summary), and the observer is READ-ONLY (a census: the
module has no rails-write path).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from holdspeak import rails_observer
from holdspeak.config import Config, RailsObserverConfig
from holdspeak.db.core import Database, reset_database
from holdspeak.principals import Principal, PrincipalKind


def _event(ts: str, event: str, story: str = "", **detail):
    e = {"ts": ts, "event": event, "story": story, "repo": "code"}
    if detail:
        e["detail"] = detail
    return e


def _rails_principal() -> Principal:
    return Principal(
        PrincipalKind.SERVICE,
        "rails-observer",
        frozenset(
            {
                ("rails.observer-batch", 1),
                ("inference.invoke", 1),
                ("inference.cancel", 1),
            }
        ),
        "rails-observer:journal-only",
    )


# --- config: off by default ------------------------------------------------


# --- event diffing ---------------------------------------------------------


def test_new_events_reports_only_the_unseen() -> None:
    events = [_event("t1", "gate_pass"), _event("t2", "story_status", "HS-1")]
    fresh, seen = rails_observer.new_events(events, set())
    assert len(fresh) == 2
    # A second pass with the same events yields nothing new.
    again, seen2 = rails_observer.new_events(events, seen)
    assert again == []
    assert seen2 == seen


def test_event_signature_distinguishes_detail() -> None:
    a = rails_observer.event_signature(_event("t1", "gate_refusal", "HS-1", rule="evidence"))
    b = rails_observer.event_signature(_event("t1", "gate_refusal", "HS-1", rule="tests"))
    assert a != b


# --- batch summary + degrade ----------------------------------------------


def test_summarize_batch_calls_the_model_and_carries_events() -> None:
    seen_prompts = {}

    def fake_model(system, user):
        seen_prompts["system"] = system
        seen_prompts["user"] = user
        return "HS-1 flipped to done; a gate refusal on evidence."

    batch = rails_observer.summarize_batch(
        [_event("t1", "story_status", "HS-1", to="done")], summarize_fn=fake_model
    )
    assert batch["degraded"] is False
    assert "flipped to done" in batch["summary"]
    # The model sees the raw events, faithfully rendered.
    assert "HS-1" in seen_prompts["user"] and "story_status" in seen_prompts["user"]


def test_model_unavailable_degrades_to_events_only() -> None:
    batch = rails_observer.summarize_batch(
        [_event("t1", "gate_pass")], summarize_fn=None
    )
    assert batch["degraded"] is True
    assert batch["summary"] == ""
    # A raising model degrades the same way — never a fabricated summary.
    def boom(system, user):
        raise RuntimeError("model down")

    batch2 = rails_observer.summarize_batch([_event("t1", "gate_pass")], summarize_fn=boom)
    assert batch2["degraded"] is True


def test_journal_body_names_the_events_and_the_summary() -> None:
    batch = {
        "events": [_event("t1", "story_status", "HS-1", to="done")],
        "summary": "HS-1 shipped.",
        "degraded": False,
    }
    body = rails_observer.journal_body(batch)
    assert "1 rail event observed" in body
    assert "HS-1" in body
    assert "HS-1 shipped." in body


def test_degraded_journal_body_is_honest() -> None:
    body = rails_observer.journal_body(
        {"events": [_event("t1", "gate_pass")], "summary": "", "degraded": True}
    )
    assert "summary unavailable" in body
    assert "gate_pass" in body  # events recorded verbatim


def test_admitted_summary_stamps_journal_observer_provenance_and_degrades_honestly(db) -> None:
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from tests.unit.test_phase143_inference_assignments import OWNER, _profile

    profile = _profile(db, "rails")
    InferenceAssignmentService(db).set_assignment(
        OWNER,
        {
            "command_id": "rails-assignment",
            "expected_revision": 0,
            "scope": {"kind": "capability", "capability_id": "background.rails_summary"},
            "entries": [{"profile_id": "rails", "profile_revision": 1}],
        },
    )
    principal = Principal(
        PrincipalKind.SERVICE, "rails-observer",
        frozenset(
            {
                ("rails.observer-batch", 1),
                ("inference.invoke", 1),
                ("inference.cancel", 1),
            }
        ),
        "rails-observer:journal-only",
    )
    from holdspeak.kernel.runtime import _configure
    broker = _configure(db)

    class FakeIntel:
        def run_prompt(self, **_):
            return "Only the observed facts."

    broker.inference_runner._engine_factory = lambda _revision, **_kw: FakeIntel()
    summarizer = rails_observer.build_profile_summarizer(
        db=db, broker=broker, principal=principal,
    )
    batch = rails_observer.summarize_batch([_event("t1", "gate_pass")], summarize_fn=summarizer)
    assert not batch["degraded"], batch
    note = rails_observer.record_journal_entry(db, batch, title="Rails journal")
    # The journal's route receipt is the runner's kernel operation.
    receipt = broker.store.receipt(batch["route_receipt_id"])
    assert batch["events"] == [_event("t1", "gate_pass")]
    assert batch["summary"] == "Only the observed facts."
    assert batch["degraded"] is False and batch["route_receipt_id"]
    assert "Only the observed facts." in note.body_markdown
    assert (receipt["actor_kind"], receipt["actor_identity"], receipt["authority_basis"]) == (
        "service", "rails-observer", "rails-observer:journal-only",
    )

    broker.inference_runner._engine_factory = lambda _revision, **_kw: (_ for _ in ()).throw(RuntimeError("model down"))
    degraded = rails_observer.summarize_batch([_event("t2", "gate_refusal")], summarize_fn=summarizer)
    degraded_note = rails_observer.record_journal_entry(db, degraded, title="Rails journal")
    assert degraded["events"] == [_event("t2", "gate_refusal")]
    assert degraded["summary"] == "" and degraded["degraded"] is True
    assert degraded["route_receipt_id"]
    assert "Only the observed facts." not in degraded_note.body_markdown
    assert "summary unavailable" in degraded_note.body_markdown


def test_rails_batch_keeps_its_engine_when_the_assignment_changes_mid_run(db) -> None:
    """The engine is read once per batch: an edit during the run takes the next batch."""
    from holdspeak.kernel.runtime import _configure
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from tests.unit.test_phase143_inference_assignments import OWNER, _profile

    _profile(db, "rails-one")
    _profile(db, "rails-two")
    assignments = InferenceAssignmentService(db)
    assignments.set_assignment(
        OWNER,
        {
            "command_id": "rails-one",
            "expected_revision": 0,
            "scope": {"kind": "capability", "capability_id": "background.rails_summary"},
            "entries": [{"profile_id": "rails-one", "profile_revision": 1}],
        },
    )
    broker = _configure(db)
    revisions: list[str] = []

    class Engine:
        def run_prompt(self, **_):
            if len(revisions) == 1:
                assignments.set_assignment(
                    OWNER,
                    {
                        "command_id": "rails-retarget",
                        "expected_revision": 1,
                        "scope": {"kind": "capability", "capability_id": "background.rails_summary"},
                        "entries": [{"profile_id": "rails-two", "profile_revision": 1}],
                    },
                )
            return "Route answer."

    def factory(revision, **_kw):
        revisions.append(revision.id)
        return Engine()

    broker.inference_runner._engine_factory = factory
    summarizer = rails_observer.build_profile_summarizer(
        db=db, broker=broker, principal=_rails_principal()
    )
    first = rails_observer.summarize_batch([_event("t3", "story_status", "HS-143", to="done")], summarize_fn=summarizer)
    first_note = rails_observer.record_journal_entry(db, first, title="Rails journal")
    replay_note = rails_observer.record_journal_entry(db, first, title="Rails journal")
    second = rails_observer.summarize_batch([_event("t4", "gate_pass", "HS-143")], summarize_fn=summarizer)
    assert first["summary"] == second["summary"] == "Route answer."
    assert first["egress"] == "local"
    assert replay_note.id == first_note.id
    assert len(revisions) == 2 and revisions[0] != revisions[1]


def test_routed_rails_persists_one_frozen_egress_badge_for_local_and_cloud(tmp_path) -> None:
    """E-F3: journal materialization preserves the route's widest boundary."""
    from holdspeak.kernel.runtime import _configure
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from tests.unit.test_phase143_inference_assignments import OWNER, _profile

    for name, expected_badge in (("local", "local"), ("cloud", "cloud")):
        db = Database(tmp_path / f"rails-egress-{name}.db")
        profile_id = f"rails-{name}"
        if name == "local":
            _profile(db, profile_id)
        else:
            # The real v1 profile adapter is the product's cloud-shaped
            # deployment source; only its physical engine leaf is substituted.
            db.profiles.upsert(
                profile_id=profile_id,
                name="Rails cloud",
                kind="openAICompatible",
                base_url="https://example.invalid/v1",
                model="rails-cloud",
                context_limit=16384,
            )
            profile_id = "legacy-" + profile_id
        InferenceAssignmentService(db).set_assignment(
            OWNER,
            {
                "command_id": f"assign-rails-{name}",
                "expected_revision": 0,
                "scope": {"kind": "capability", "capability_id": "background.rails_summary"},
                "entries": [{"profile_id": profile_id, "profile_revision": 1}],
            },
        )
        broker = _configure(db)
        calls: list[str] = []

        class Engine:
            def run_prompt(self, **_):
                calls.append("physical")
                return f"{name} route answered."

        broker.inference_runner._engine_factory = lambda _revision, **_kw: Engine()
        summarizer = rails_observer.build_profile_summarizer(
            db=db, broker=broker, principal=_rails_principal()
        )
        events = [_event(f"egress-{name}", "gate_pass", "HS-143")]
        first = rails_observer.summarize_batch(events, summarize_fn=summarizer)
        first_note = rails_observer.record_journal_entry(db, first, title="Rails journal")
        replay_note = rails_observer.record_journal_entry(db, first, title="Rails journal")
        badge = f"[egress: {expected_badge}]"
        assert calls == ["physical"]
        assert first["egress"] == expected_badge
        assert first_note.id == replay_note.id
        assert first_note.body_markdown.count(badge) == 1
        with db._connection() as conn:
            assert conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0] == 1
        assert broker.store.receipt(first["route_receipt_id"])["outcome"] == "succeeded"


def test_rails_with_no_engine_journals_the_events_only(db) -> None:
    """No engine assigned: event-only, no model call, no receipt."""
    from holdspeak.kernel.runtime import _configure
    broker = _configure(db)
    # The default observer is disabled, so startup creates no inferred Rails
    # assignment.  This is the genuine no-authority refusal path.
    summarizer = rails_observer.build_profile_summarizer(
        db=db, broker=broker, principal=_rails_principal()
    )
    batch = rails_observer.summarize_batch([_event("t4", "gate_refusal")], summarize_fn=summarizer)
    note = rails_observer.record_journal_entry(db, batch, title="Rails journal")
    assert batch["degraded"] is True and not batch.get("route_receipt_id")
    assert "summary unavailable" in note.body_markdown
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM kernel_operations WHERE name='inference.invoke'").fetchone()[0] == 0


def test_routed_rails_known_preflight_failure_stays_failed_at_parent(db) -> None:
    """E-F4: known unavailable is durable failure, not indeterminate."""
    from holdspeak.kernel.runtime import _configure
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from tests.unit.test_phase143_inference_assignments import OWNER, _profile

    _profile(db, "rails-unavailable", ready=False)
    InferenceAssignmentService(db).set_assignment(
        OWNER,
        {
            "command_id": "assign-rails-unavailable", "expected_revision": 0,
            "scope": {"kind": "capability", "capability_id": "background.rails_summary"},
            "entries": [{"profile_id": "rails-unavailable", "profile_revision": 1}],
        },
    )
    broker = _configure(db)
    batch = rails_observer.summarize_batch(
        [_event("unavailable", "gate_pass", "HS-143")],
        summarize_fn=rails_observer.build_profile_summarizer(
            db=db, broker=broker, principal=_rails_principal()
        ),
    )
    # An engine that is not ready never answers: the events are journaled alone.
    assert batch["degraded"] is True
    assert batch["summary"] == ""


def test_routed_rails_genuine_dispatch_uncertainty_stays_indeterminate(db) -> None:
    """E-F4's converse: a real unknown dispatch is still indeterminate."""
    from holdspeak.kernel.provider_signals import ProviderIndeterminate
    from holdspeak.kernel.runtime import _configure
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from tests.unit.test_phase143_inference_assignments import OWNER, _profile

    _profile(db, "rails-indeterminate")
    InferenceAssignmentService(db).set_assignment(
        OWNER,
        {
            "command_id": "assign-rails-indeterminate", "expected_revision": 0,
            "scope": {"kind": "capability", "capability_id": "background.rails_summary"},
            "entries": [{"profile_id": "rails-indeterminate", "profile_revision": 1}],
        },
    )
    broker = _configure(db)

    class UnknownEngine:
        def run_prompt(self, **_):
            raise ProviderIndeterminate()

    broker.inference_runner._engine_factory = lambda _revision, **_kw: UnknownEngine()
    batch = rails_observer.summarize_batch(
        [_event("unknown", "gate_pass", "HS-143")],
        summarize_fn=rails_observer.build_profile_summarizer(
            db=db, broker=broker, principal=_rails_principal()
        ),
    )
    assert batch["degraded"] is True and batch["route_receipt_id"]
    assert broker.store.receipt(batch["route_receipt_id"])["outcome"] == "indeterminate"


def test_rails_blank_sentinel_migrates_one_visible_local_assignment(db) -> None:
    """E1 converts documented this_machine exactly once in one transaction."""
    from holdspeak.services.assignment_migration import (
        RAILS_OBSERVER_MIGRATION_FAMILY,
        AssignmentMigration,
    )
    from holdspeak.services.inference_setup_service import InferenceSetupApplicationService
    from tests.unit.test_phase143_inference_assignments import OWNER

    config = Config()
    config.rails_observer.enabled = True
    config.rails_observer.profile_id = None
    config.meeting.intel_realtime_model = "/exactly/saved/rails-observer.gguf"
    # The setup projection is the product's generic Thought resolver.  Rails'
    # capability-owned deployment must not appear there before or after E1.
    setup = InferenceSetupApplicationService(db, config_provider=lambda: config)
    thought_before = setup.get_inference_setup(OWNER)["current_thought_deployment"]["execution_revision"]
    result = AssignmentMigration(db).migrate_rails_observer_route_assignments(OWNER, config)
    assert result["family"] == RAILS_OBSERVER_MIGRATION_FAMILY
    assert result["status"] == "migrated"
    assert len(result["assignments"]) == 1
    setup_after = setup.get_inference_setup(OWNER)
    thought_after = setup_after["current_thought_deployment"]["execution_revision"]
    assert thought_after == thought_before
    assert not any(
        row["id"].startswith("artifact-rails-observer-local-")
        for row in setup_after["installed_model_artifacts"]
    )
    with db._connection() as conn:
        assignment = conn.execute(
            "SELECT profile_id FROM inference_assignments"
        ).fetchone()
        assert assignment is not None and str(assignment["profile_id"]).startswith("rails-observer-local-")
        artifact = conn.execute(
            "SELECT state,local_locator FROM inference_model_artifacts"
        ).fetchone()
        assert tuple(artifact) == ("verified", "/exactly/saved/rails-observer.gguf")
        deployment = conn.execute("SELECT active FROM inference_deployments").fetchone()
        assert deployment["active"] == 0
        assert conn.execute("SELECT COUNT(*) FROM model_profile_binding_heads").fetchone()[0] == 1
        assert conn.execute(
            "SELECT COUNT(*) FROM inference_assignment_migrations WHERE family=?",
            (RAILS_OBSERVER_MIGRATION_FAMILY,),
        ).fetchone()[0] == 1
        # Simulate the one release-local bad footprint. A marker replay repairs
        # it without re-reading selector Config or changing route authority.
        conn.execute("UPDATE inference_deployments SET active=1")
        conn.commit()
    replay = AssignmentMigration(db).migrate_rails_observer_route_assignments(
        OWNER, config
    )
    assert replay["legacy_config_read"] is False
    with db._connection() as conn:
        assert conn.execute("SELECT active FROM inference_deployments").fetchone()["active"] == 0

    # E-F1: the migration does not probe/load, but its first frozen route is
    # executable with the exact saved locator and records readiness only after
    # the physical leaf returns.
    from holdspeak.kernel.runtime import _configure
    broker = _configure(db)
    calls: list[str] = []

    class Engine:
        def run_prompt(self, **_):
            calls.append("physical")
            return "Migrated local route answered."

    broker.inference_runner._engine_factory = lambda _revision, **_kw: Engine()
    batch = rails_observer.summarize_batch(
        [_event("migrated", "gate_pass", "HS-143")],
        summarize_fn=rails_observer.build_profile_summarizer(
            db=db, broker=broker, principal=_rails_principal()
        ),
    )
    note = rails_observer.record_journal_entry(db, batch, title="Rails journal")
    assert calls == ["physical"]
    assert batch["summary"] == "Migrated local route answered."
    assert "Migrated local route answered." in note.body_markdown
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM kernel_operations WHERE name='inference.invoke'").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM notes WHERE id=?", (note.id,)).fetchone()[0] == 1
        readiness = conn.execute(
            "SELECT state,reason_code FROM model_profile_readiness_observations ORDER BY observed_at DESC"
        ).fetchone()
    assert tuple(readiness) == ("ready", "loaded_under_rails_observer")


def test_disabled_default_rails_does_not_materialize_a_sentinel_route(db) -> None:
    """A fresh off-by-default install has no saved Rails selector to convert."""
    from holdspeak.services.assignment_migration import AssignmentMigration
    from tests.unit.test_phase143_inference_assignments import OWNER

    result = AssignmentMigration(db).migrate_rails_observer_route_assignments(
        OWNER, Config()
    )
    assert result == {
        "family": "rails-observer-route-assignments",
        "status": "not_applicable",
        "reason_code": "rails_observer_disabled",
        "legacy_config_read": True,
    }
    with db._connection() as conn:
        for table in (
            "model_profile_revisions",
            "inference_model_artifacts",
            "deployment_revisions",
            "inference_deployments",
            "model_profile_binding_heads",
            "inference_assignments",
            "inference_assignment_migrations",
        ):
            assert conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0


def test_rails_unmappable_sentinel_writes_no_partial_migration(db, monkeypatch) -> None:
    """E1 refuses an unnamed this_machine selector without orphan rows."""
    from holdspeak.services.assignment_migration import AssignmentMigration
    from tests.unit.test_phase143_inference_assignments import OWNER
    import holdspeak.intel.providers as providers

    monkeypatch.setattr(providers, "DEFAULT_INTEL_MODEL_PATH", "")
    config = Config()
    config.rails_observer.enabled = True
    config.rails_observer.profile_id = None
    config.meeting.intel_realtime_model = ""
    result = AssignmentMigration(db).migrate_rails_observer_route_assignments(OWNER, config)
    assert result["status"] == "needs_attention"
    assert result["reason_code"] == "same_device_deployment_unnamed"
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM model_profile_revisions").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM model_profile_binding_heads").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM inference_assignments").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM inference_assignment_migrations").fetchone()[0] == 0

    # Keep the production startup coordinator on this same saved unmappable
    # config; otherwise its independent default Config read would name a model.
    monkeypatch.setattr(Config, "load", classmethod(lambda cls, *_args, **_kwargs: config))
    # E-F1's refusal half still runs the production SERVICE route/adopter and
    # journal materializer: one durable refusal, no partial frozen execution.
    from holdspeak.kernel.runtime import _configure
    broker = _configure(db)
    batch = rails_observer.summarize_batch(
        [_event("unmappable", "gate_refusal", "HS-143")],
        summarize_fn=rails_observer.build_profile_summarizer(
            db=db, broker=broker, principal=_rails_principal()
        ),
    )
    note = rails_observer.record_journal_entry(db, batch, title="Rails journal")
    assert batch["degraded"] is True and not batch.get("route_receipt_id")
    assert "summary unavailable" in note.body_markdown
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM kernel_operations WHERE name='inference.invoke'").fetchone()[0] == 0


def test_marker_gated_settings_retire_only_meeting_and_rails_selectors(
    db, monkeypatch: pytest.MonkeyPatch
) -> None:
    """D6/D7: saved selectors migrate once, then cannot re-enter routing."""
    from holdspeak.services.errors import ValidationError
    from holdspeak.services.assignment_migration import AssignmentMigration
    from holdspeak.services.settings_service import SettingsService
    from tests.unit.test_phase143_inference_assignments import OWNER, _profile, _result_claim

    _profile(
        db,
        "meeting-before",
        claims=(
            "language",
            *(
                _result_claim(capability)
                for capability in (
                    "meeting.live_analysis",
                    "meeting.bookmark_label",
                    "meeting.auto_title",
                )
            ),
        ),
    )
    _profile(db, "rails-before", claims=("language", _result_claim("background.rails_summary")))
    config = Config()
    config.meeting.intel_profile_id = "meeting-before"
    config.meeting.intel_provider = "cloud"
    config.rails_observer.enabled = True
    config.rails_observer.profile_id = "rails-before"
    monkeypatch.setattr(Config, "load", classmethod(lambda cls, *_args, **_kwargs: config))
    settings = SettingsService(db)

    # Before each family marker the exact saved value supplies its one migration
    # and still appears only for that unmarked family.
    before = settings.get_settings(OWNER)
    assert before["meeting"]["intel_profile_id"] == "meeting-before"
    assert before["meeting"]["intel_provider"] == "cloud"
    assert before["rails_observer"]["profile_id"] == "rails-before"
    coordinator = AssignmentMigration(db)
    assert coordinator.migrate_meeting_route_assignments(OWNER, config)["legacy_config_read"]
    assert coordinator.migrate_rails_observer_route_assignments(OWNER, config)["legacy_config_read"]

    after = settings.get_settings(OWNER)
    assert "_placement" not in after
    assert "intel_profile_id" not in after["meeting"]
    assert "intel_provider" not in after["meeting"]
    assert "profile_id" not in after["rails_observer"]
    with pytest.raises(ValidationError, match="Meeting routing") as meeting_refusal:
        settings.update_settings(OWNER, {"meeting": {"intel_profile_id": "mutated"}})
    assert meeting_refusal.value.code == "meeting_legacy_selector_retired"
    with pytest.raises(ValidationError, match="Rails observer") as rails_refusal:
        settings.update_settings(OWNER, {"rails_observer": {"profile_id": "mutated"}})
    assert rails_refusal.value.code == "rails_observer_legacy_selector_retired"

    # A process-style service reconstruction sees the same markers.  Mutating
    # retained migration evidence cannot retarget the already saved assignments.
    config.meeting.intel_profile_id = "mutated"
    config.rails_observer.profile_id = "mutated"
    restarted = SettingsService(db).get_settings(OWNER)
    assert "intel_profile_id" not in restarted["meeting"]
    assert "profile_id" not in restarted["rails_observer"]
    with db._connection() as conn:
        meeting_profiles = {
            row["profile_id"]
            for row in conn.execute(
                "SELECT a.profile_id FROM inference_assignments a "
                "JOIN inference_assignment_revisions r "
                "ON r.assignment_id=a.assignment_id "
                "AND r.revision=a.assignment_revision "
                "WHERE r.capability_id LIKE 'meeting.%'"
            ).fetchall()
        }
        rails_profile = conn.execute(
            "SELECT a.profile_id FROM inference_assignments a "
            "JOIN inference_assignment_revisions r "
            "ON r.assignment_id=a.assignment_id "
            "AND r.revision=a.assignment_revision "
            "WHERE r.capability_id='background.rails_summary'"
        ).fetchone()["profile_id"]
    assert meeting_profiles == {"meeting-before"}
    assert rails_profile == "rails-before"


# --- the journal write (a real note) ---------------------------------------


@pytest.fixture
def db(tmp_path):
    reset_database()
    d = Database(tmp_path / "hs.db")
    yield d
    reset_database()


def test_record_and_list_journal(db) -> None:
    batch = rails_observer.summarize_batch(
        [_event("t1", "story_status", "HS-1", to="done")],
        summarize_fn=lambda s, u: "HS-1 shipped.",
    )
    note = rails_observer.record_journal_entry(db, batch, title="Rails journal")
    assert rails_observer.JOURNAL_TAG in note.tags
    listed = rails_observer.list_journal(db)
    assert [n.id for n in listed] == [note.id]
    assert "HS-1 shipped." in listed[0].body_markdown


# --- the read-only census --------------------------------------------------


# --- cross-machine reach (HS-88-04) ----------------------------------------


class _Clock:
    def __init__(self, start=1000.0):
        self.now = start

    def __call__(self):
        return self.now


@pytest.fixture(autouse=True)
def _fresh_remote():
    rails_observer.clear_remote_buffer()
    yield
    rails_observer.clear_remote_buffer()


def test_valid_envelope_events_only():
    ok, _ = rails_observer.validate_remote_envelope(
        {"node": "beta", "ts": "t1", "events": [{"ts": "t1", "event": "gate_pass"}]}
    )
    assert ok is True


def test_envelope_must_name_its_node():
    ok, reason = rails_observer.validate_remote_envelope({"events": []})
    assert ok is False and "node" in reason


def test_envelope_rejects_a_file_body_crossing():
    # The reach is events only — a body-carrying event is refused.
    for body_key in ("text", "body_markdown", "content", "file"):
        ok, reason = rails_observer.validate_remote_envelope(
            {"node": "beta", "events": [{"event": "x", body_key: "the story file"}]}
        )
        assert ok is False and "events only" in reason


def test_push_and_drain_stamps_the_origin_node():
    clk = _Clock()
    rails_observer.push_remote_envelope(
        {"node": "beta", "events": [{"ts": "t1", "event": "story_status", "story": "HS-1"}]},
        clock=clk,
    )
    drained = rails_observer.drain_remote_events(clock=clk)
    assert len(drained) == 1
    assert drained[0]["origin_node"] == "beta"
    # A second drain is empty (buffer cleared).
    assert rails_observer.drain_remote_events(clock=clk) == []


def test_stale_node_stream_is_dropped_never_fabricated():
    clk = _Clock()
    rails_observer.push_remote_envelope(
        {"node": "beta", "events": [{"ts": "t1", "event": "gate_pass"}]}, clock=clk
    )
    clk.now += rails_observer.REMOTE_LIVENESS_SECONDS + 1
    # The node went quiet: its stream drops, and liveness reads it gone.
    assert rails_observer.drain_remote_events(clock=clk) == []
    assert rails_observer.remote_node_liveness(clock=clk) == {}


def test_liveness_tracks_a_live_node():
    clk = _Clock()
    rails_observer.push_remote_envelope(
        {"node": "beta", "events": [{"ts": "t1", "event": "gate_pass"}]}, clock=clk
    )
    assert rails_observer.remote_node_liveness(clock=clk) == {"beta": True}


def test_remote_events_render_with_the_origin_named():
    events = [{"ts": "t1", "repo": "code", "event": "story_status", "story": "HS-1", "origin_node": "beta"}]
    rendered = rails_observer.format_events_for_model(events)
    assert "@beta" in rendered


def test_a_remote_and_local_flip_do_not_collide_in_the_diff():
    local = {"ts": "t1", "event": "story_status", "story": "HS-1", "repo": "code"}
    remote = {**local, "origin_node": "beta"}
    assert rails_observer.event_signature(local) != rails_observer.event_signature(remote)
