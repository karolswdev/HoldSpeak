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


# --- config: off by default ------------------------------------------------


def test_observer_is_off_by_default() -> None:
    assert RailsObserverConfig().enabled is False
    assert Config().rails_observer.enabled is False


def test_observer_config_roundtrips(tmp_path) -> None:
    cfg_path = tmp_path / "config.json"
    c = Config()
    c.rails_observer.enabled = True
    c.rails_observer.profile_id = "p1"
    c.save(cfg_path)
    loaded = Config.load(cfg_path)
    assert loaded.rails_observer.enabled is True
    assert loaded.rails_observer.profile_id == "p1"


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
    profile = db.profiles.upsert(
        profile_id="rails", name="Rails", kind="openAICompatible",
        base_url="http://rails", model="rails-model",
    )
    principal = Principal(
        PrincipalKind.SERVICE, "rails-observer",
        frozenset({("inference.invoke", 1)}), "rails-observer:journal-only",
    )
    from holdspeak.kernel.runtime import _configure
    broker = _configure(db)

    class FakeIntel:
        def run_prompt(self, **_):
            return "Only the observed facts."

    broker.inference_runner._engine_factory = lambda _: FakeIntel()
    summarizer = rails_observer.build_profile_summarizer(
        profile.id, db=db, broker=broker, principal=principal,
    )
    batch = rails_observer.summarize_batch([_event("t1", "gate_pass")], summarize_fn=summarizer)
    note = rails_observer.record_journal_entry(db, batch, title="Rails journal")
    with db._connection() as conn:
        operation_id = conn.execute(
            "SELECT operation_id FROM kernel_operations WHERE native_id LIKE 'rails_%'"
        ).fetchone()[0]
    receipt = broker.store.receipt(operation_id)
    assert batch == {"events": [_event("t1", "gate_pass")], "summary": "Only the observed facts.", "degraded": False}
    assert "Only the observed facts." in note.body_markdown
    assert (receipt["actor_kind"], receipt["actor_identity"], receipt["authority_basis"]) == (
        "service", "rails-observer", "rails-observer:journal-only",
    )

    broker.inference_runner._engine_factory = lambda _: (_ for _ in ()).throw(RuntimeError("model down"))
    degraded = rails_observer.summarize_batch([_event("t2", "gate_refusal")], summarize_fn=summarizer)
    degraded_note = rails_observer.record_journal_entry(db, degraded, title="Rails journal")
    assert degraded == {"events": [_event("t2", "gate_refusal")], "summary": "", "degraded": True}
    assert "Only the observed facts." not in degraded_note.body_markdown
    assert "summary unavailable" in degraded_note.body_markdown


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


def test_observer_module_has_no_rails_write_path() -> None:
    """The observer READS and journals; it must never carry a path that
    writes to the rails. The rails write seams are the story connector
    and the gate — neither may appear in this module."""
    src = (Path(__file__).resolve().parents[2] / "holdspeak" / "rails_observer.py").read_text()
    # Code-level write markers (not prose): the gated story connector, the
    # tmux steer transport, the proposal executor, and the dw commit gate.
    for forbidden in (
        "build_dw_story_connector",
        "decide_proposal",
        "record_proposal",  # the observer journals; it does not itself propose
        "send_text_to_pane",
        '"story", "status"',  # a dw story-status argv
        "coder_steering.deliver",
    ):
        assert forbidden not in src, (
            f"rails_observer.py names a write path ({forbidden!r}) — the "
            "observer is read-only; a suggested action is a proposal made "
            "elsewhere, never a write from here."
        )


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
