"""AG12: the explicit, bounded builder/reviewer hand-off loop."""
from __future__ import annotations

from holdspeak.services.agent_review import (
    AgentReviewLoop,
    initial_review,
    parse_findings,
    review_row_words,
)


def test_native_reviewer_profiles_keep_read_only_posture_when_yolo_is_global(tmp_path):
    from holdspeak.delivery import agent_mcp, pi_launch
    from holdspeak.delivery.pi_launch import PiEngine

    assert agent_mcp.claude_permission_args("yolo", ["claude"], read_only=True) == [
        "--permission-mode", "plan"
    ]
    assert "mcp__holdspeak" not in agent_mcp.claude_args(
        tmp_path / "mcp.json", "yolo", read_only=True
    )
    codex = agent_mcp.codex_args("http://127.0.0.1:8765", "yolo", read_only=True)
    assert "default_tools_approval_mode" not in " ".join(codex)
    assert pi_launch.launch_args(
        PiEngine(endpoint="http://127.0.0.1:1", host="http://127.0.0.1:1", model="test",
                 context_window=1, key_slot="", boundary="local"),
        tmp_path,
        read_only=True,
    )[-2:] == ["--tools", "read,grep,find,ls"]


def test_hostile_reviewer_profile_options_cannot_widen_native_posture():
    from holdspeak.delivery.factory_launch import (
        _claude_read_only_argv,
        _codex_read_only_argv,
    )

    claude = _claude_read_only_argv([
        "claude", "--permission-mode", "acceptEdits",
        "--tools", "Write,Edit,Bash", "--tools=Write",
        "--allowedTools", "Bash", "--dangerously-skip-permissions",
    ])
    assert claude[claude.index("--permission-mode") + 1] == "plan"
    assert claude[-2:] == ["--tools", "Read,Grep,Glob"]
    assert all(
        "Write" not in token and "Edit" not in token and "Bash" not in token
        for token in claude
    )
    assert "--allowedTools" not in claude
    assert "--dangerously-skip-permissions" not in claude

    codex = _codex_read_only_argv([
        "codex", "exec", "--yolo", "--full-auto",
        "--dangerously-bypass-approvals-and-sandbox", "--sandbox=workspace-write",
        "--ask-for-approval", "never", "--config", "sandbox_mode=workspace-write",
        "--add-dir", "/tmp/write",
    ])
    assert "--sandbox" in codex
    assert codex[codex.index("--sandbox") + 1] == "read-only"
    assert all(token not in codex for token in (
        "--yolo", "--full-auto", "--dangerously-bypass-approvals-and-sandbox",
        "--ask-for-approval", "never", "--add-dir", "workspace-write",
        "sandbox_mode=workspace-write", "/tmp/write",
    ))


def test_reviewer_credential_is_read_only_at_dispatch_even_in_yolo(monkeypatch):
    from holdspeak.mcp import palettes
    from holdspeak.principals import AgentCredentialStore
    from holdspeak.services import conductor_launch
    from holdspeak.services.errors import ServiceError

    store = AgentCredentialStore()
    credential = store.issue(
        "agent:launch:reviewer-test",
        palette=palettes.resolve_palette("CONDUCTOR"),
        palette_name="CONDUCTOR",
        launch_id="reviewer-test",
        role="reviewer",
        read_only=True,
    )
    monkeypatch.setattr("holdspeak.principals.agent_credentials", store)
    principal = credential.principal

    assert conductor_launch.gate_call("desk.get", {"id": "note-1"}, principal) == {"id": "note-1"}
    for tool in ("desk.create", "settings.update", "channel.prepare", "channel.send", "agent.start_helper"):
        try:
            conductor_launch.gate_call(tool, {}, principal)
        except ServiceError as exc:
            assert exc.code == "reviewer_read_only"
        else:
            raise AssertionError(f"reviewer call was not refused: {tool}")


def test_durable_reviewer_role_cannot_be_downgraded_at_credential_issue(tmp_path, monkeypatch):
    from holdspeak.delivery import factory_launch
    from holdspeak.mcp import palettes
    from holdspeak.principals import AgentCredentialStore

    monkeypatch.setattr(factory_launch, "DEFAULT_LAUNCHES_PATH", tmp_path / "launches.json")
    factory_launch.LaunchLedger().record({
        "launch_id": "reviewer-durable",
        "role": "reviewer",
        "read_only": True,
        "review": {"role": "reviewer", "read_only": True},
    })
    credential = AgentCredentialStore().issue(
        "agent:launch:reviewer-durable",
        palette=palettes.resolve_palette("CONDUCTOR"),
        palette_name="CONDUCTOR",
        launch_id="reviewer-durable",
        role="builder",
        read_only=False,
    )
    assert credential.role == "reviewer"
    assert credential.read_only is True


class Ledger:
    def __init__(self, *rows):
        self.rows = {str(row["launch_id"]): dict(row) for row in rows}

    def list(self):
        return [dict(row) for row in self.rows.values()]

    def get(self, launch_id):
        row = self.rows.get(str(launch_id))
        return dict(row) if row else None

    def update(self, launch_id, **fields):
        row = self.rows[str(launch_id)]
        row.update(fields)
        return dict(row)

    def record(self, row):
        self.rows[str(row["launch_id"])] = dict(row)


def builder(*, review=None):
    return {
        "launch_id": "B1",
        "state": "registered",
        "agent": "claude",
        "profile_id": "claude-default",
        "branch": "hs/item",
        "origin_ref": {"kind": "action", "id": "a1"},
        "review": review,
    }


class HubProducer:
    """A tiny real hub-shaped producer: each reviewer is a launch record."""

    def __init__(self, ledger, states):
        self.ledger = ledger
        self.states = states
        self.calls = []

    def hand(self, principal, kind, item_id, **kwargs):
        number = len(self.calls) + 1
        launch_id = f"R{number}"
        self.calls.append((kind, item_id, kwargs))
        self.ledger.record({
            "launch_id": launch_id,
            "state": "registered",
            "helper_of": "B1",
            "origin_ref": {"kind": kind, "id": item_id},
            "profile_id": kwargs["profile"],
        })
        self.states[launch_id] = "registered"
        return {"launch_id": launch_id, "worktree": {"name": f"hs-action-a1-{number}-helper"}}


def test_findings_are_explicit_and_must_none_closes_the_pair():
    assert parse_findings("MUST: fix a.py:1\nSHOULD: add a check") == [
        {"level": "MUST", "text": "fix a.py:1"},
        {"level": "SHOULD", "text": "add a check"},
    ]
    assert parse_findings("MUST: none") == []
    assert parse_findings("MUST: fix it\nMUST: none") == [{"level": "MUST", "text": "fix it"}]


def test_unknown_done_words_cannot_silently_clear_a_pair():
    pair = initial_review("codex")
    pair.update({
        "round": 1,
        "reviewer_launch_id": "R1",
        "last_builder_commit": "c1",
        "rounds": [{"round": 1, "builder_commit": "c1", "reviewer_launch_id": "R1"}],
    })
    ledger = Ledger(builder(review=pair), {"launch_id": "R1", "state": "registered", "helper_of": "B1"})
    states = {"B1": "done", "R1": "done"}
    loop = AgentReviewLoop(
        None,
        object(),
        ledger=ledger,
        state_reader=lambda launch_id: states.get(launch_id, ""),
        commit_reader=lambda record: "c1",
        result_reader=lambda launch_id: "review complete, no details",
    )
    event = loop.tick()[0]
    assert event["status"] == "needs_you"
    assert ledger.get("B1")["review"]["result"]["reason"] == "review_result_unclear"


def test_real_hub_producer_runs_two_bounded_rounds_and_retains_history():
    pair = initial_review("codex")
    pair["item"] = {"kind": "action", "id": "a1", "title": "Fix the item"}
    pair["acceptance"] = ["the focused test is green"]
    ledger = Ledger(builder(review=pair))
    states = {"B1": "done"}
    commits = {"B1": "c1"}
    words = {"R1": "MUST: fix the failing check (test_a.py:4)"}
    prompted = []
    producer = HubProducer(ledger, states)
    loop = AgentReviewLoop(
        None,
        producer,
        ledger=ledger,
        state_reader=lambda launch_id: states.get(launch_id, ""),
        commit_reader=lambda record: commits.get(record["launch_id"]),
        result_reader=lambda launch_id: words.get(launch_id, ""),
        prompt=lambda launch_id, text: prompted.append((launch_id, text)),
        clock=lambda: "2026-10-19T12:00:00+00:00",
    )

    assert loop.tick()[0]["status"] == "reviewing"
    review_call = producer.calls[0][2]
    assert "helper_round" not in review_call
    assert review_call["start_point"] == "c1"
    assert review_call["review"]["read_only"] is True
    assert ledger.get("R1")["review"]["read_only"] is True
    assert "MUST" in review_call["instruction"] and "Acceptance checks" in review_call["instruction"]

    states["R1"] = "done"
    assert loop.tick()[0]["status"] == "awaiting_builder_commit"
    assert prompted and "Fix the MUST findings" in prompted[0][1]
    assert ledger.get("B1")["review"]["rounds"][0]["findings_left"]

    commits["B1"] = "c2"
    assert loop.tick()[0]["round"] == 2
    assert producer.calls[1][2]["helper_round"] == 2
    words["R2"] = "MUST: none"
    states["R2"] = "done"
    assert loop.tick()[0]["status"] == "done"
    final = ledger.get("B1")["review"]
    assert final["result"] == {"rounds": 2, "findings_left": [], "wording": "round 2, nothing left"}
    assert [row["status"] for row in final["rounds"]] == ["done", "done"]


def test_done_without_new_commit_is_inert_and_round_two_must_stays_needs_you():
    pair = initial_review("pi")
    pair.update({
        "round": 2,
        "last_builder_commit": "c2",
        "reviewer_launch_id": "R2",
        "rounds": [{"round": 2, "builder_commit": "c2", "reviewer_launch_id": "R2"}],
    })
    reviewer = {"launch_id": "R2", "state": "registered", "helper_of": "B1"}
    ledger = Ledger(builder(review=pair), reviewer)
    states = {"B1": "done", "R2": "done"}
    loop = AgentReviewLoop(
        None,
        object(),
        ledger=ledger,
        state_reader=lambda launch_id: states.get(launch_id, ""),
        commit_reader=lambda record: "c2",
        result_reader=lambda launch_id: "MUST: still broken",
    )
    event = loop.tick()[0]
    assert event["status"] == "needs_you"
    assert ledger.get("B1")["review"]["result"]["rounds"] == 2

    pair = initial_review("codex")
    pair["last_builder_commit"] = "same"
    ledger = Ledger(builder(review=pair))
    states = {"B1": "done"}
    producer = HubProducer(ledger, states)
    loop = AgentReviewLoop(None, producer, ledger=ledger, state_reader=lambda launch_id: states.get(launch_id, ""), commit_reader=lambda record: "same")
    assert loop.tick() == []
    assert producer.calls == []


def test_row_words_keep_builder_reviewer_and_round_visible():
    assert review_row_words({"builder": "Claude Code", "requested": "codex", "round": 1}) == "Claude Code builds · Codex reviews · round 1"
    assert review_row_words({"role": "reviewer", "builder": "Claude Code", "requested": "codex", "round": 2}) == "Codex reviews · Claude Code builds · round 2"


# ── the first real night (2026-11-01): the reviewers' recorded words ──

def _night_words(name: str) -> str:
    from pathlib import Path

    return (Path(__file__).resolve().parents[1] / "fixtures" / f"review_words_night_{name}.txt").read_text(encoding="utf-8")


def test_the_nights_real_clear_review_has_no_finding():
    """Claude Code's real review of step 1 ("- MUST: none." with its end mark,
    then "MUST: none"): no finding, and the pair is clear."""
    from holdspeak.services.agent_review import _review_result

    findings, clear = _review_result(_night_words("clear"))
    assert [row for row in findings if row["level"] == "MUST"] == [] and clear is True


def test_the_nights_real_must_review_has_one_must_not_its_count_line():
    """Step 3's real review: one "- MUST · docs/faq.md:5 · …" finding and the
    closing "MUST: 1 remains (…)" count, which is not a second finding."""
    from holdspeak.services.agent_review import _review_result

    findings, _clear = _review_result(_night_words("must"))
    musts = [row for row in findings if row["level"] == "MUST"]
    assert len(musts) == 1 and "docs/faq.md:5" in musts[0]["text"]
    assert parse_findings("MUST: none.\nSHOULD: none!") == []
    assert parse_findings("MUST: 2 left") == []


def test_an_empty_read_of_a_finished_reviewer_waits_before_it_is_unclear():
    """The turn ended before its Stop words landed: an empty read is read
    again on the next ticks; the words that land then are the result."""
    from holdspeak.services.agent_review import EMPTY_READS_WAIT

    pair = initial_review("codex")
    pair.update({"round": 1, "reviewer_launch_id": "R1", "last_builder_commit": "c1", "status": "reviewing",
                 "rounds": [{"round": 1, "builder_commit": "c1", "reviewer_launch_id": "R1"}]})
    ledger = Ledger(builder(review=pair), {"launch_id": "R1", "state": "registered", "helper_of": "B1"})
    words = {"R1": ""}
    loop = AgentReviewLoop(None, object(), ledger=ledger, state_reader=lambda launch_id: "done",
                           commit_reader=lambda record: "c1", result_reader=lambda launch_id: words["R1"])
    for _ in range(EMPTY_READS_WAIT):
        loop.tick()
        assert ledger.get("B1")["review"]["status"] == "reviewing"
    words["R1"] = "Findings:\n- MUST: none.\n\nMUST: none"
    loop.tick()
    assert ledger.get("B1")["review"]["status"] == "done"


def test_an_empty_read_that_stays_empty_is_unclear_after_the_wait():
    from holdspeak.services.agent_review import EMPTY_READS_WAIT

    pair = initial_review("codex")
    pair.update({"round": 1, "reviewer_launch_id": "R1", "last_builder_commit": "c1",
                 "rounds": [{"round": 1, "builder_commit": "c1", "reviewer_launch_id": "R1"}]})
    ledger = Ledger(builder(review=pair), {"launch_id": "R1", "state": "registered", "helper_of": "B1"})
    loop = AgentReviewLoop(None, object(), ledger=ledger, state_reader=lambda launch_id: "done",
                           commit_reader=lambda record: "c1", result_reader=lambda launch_id: "")
    for _ in range(EMPTY_READS_WAIT + 1):
        loop.tick()
    assert ledger.get("B1")["review"]["result"]["reason"] == "review_result_unclear"
