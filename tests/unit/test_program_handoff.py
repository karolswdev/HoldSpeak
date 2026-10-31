"""Programs PG19: Runs on as a list, the usage-limit state, the handoff brief.

Design: docs/internal/betterment/programs/PROGRAMS-DESIGN-2026-10-28.md
("PG19 Handoff"). The notice wordings below are NOT real captures. They are
the harnesses' documented and widely reported wordings (2025-2026), pinned
here so a change to the reader is seen. The one real capture (Claude Code on
this Mac, PG21) is tests/fixtures/usage_limit_captures.json, read by
tests/unit/test_usage_limit_matrix.py.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from holdspeak.agent_context.usage_limit import read_limit, reset_moment
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.program_handoff import HandoffInputs, brief_of, gather, redact_counted, redacted_words
from holdspeak.services.program_rules import CoreQuestion, Decision, decide
from holdspeak.services.program_service import ProgramRefused
from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig, git

GOLDEN = Path(__file__).resolve().parents[1] / "fixtures" / "program_handoff_brief.txt"
NOW = datetime(2026, 10, 28, 12, 30, tzinfo=timezone.utc)


# ── the notice (documented wordings, not captures) ────────────────────

@pytest.mark.parametrize("line", [
    "Claude AI usage limit reached|1793196000",
    "5-hour limit reached ∙ resets 2pm",
    "You've hit your limit · resets 2pm (Europe/Warsaw)",
    "Claude usage limit reached. Your limit will reset at 2pm (America/New_York).",
])
def test_claude_code_notice_is_read(line: str) -> None:
    reading = read_limit("claude", f"> fix the routes\n● Working on it\n{line}\n╭──╮\n│ > │\n╰──╯", NOW)
    assert reading is not None and reading.rule == "claude.usage_limit" and reading.stopped
    assert reading.until is not None and reading.until > NOW


@pytest.mark.parametrize("line,delta", [
    ("■ You've hit your usage limit. Upgrade to Pro (https://openai.com/chatgpt/pricing) or try again in 2 hours 13 minutes.",
     timedelta(hours=2, minutes=13)),
    ("You've hit your usage limit. Try again in 45 minutes.", timedelta(minutes=45)),
])
def test_codex_notice_is_read_with_its_wait(line: str, delta: timedelta) -> None:
    reading = read_limit("codex", f"› write the tests\n{line}\n", NOW)
    assert reading is not None and reading.rule == "codex.usage_limit"
    assert reading.until == NOW + delta


def test_codex_try_again_at_a_clock_time() -> None:
    reading = read_limit("codex", "You've hit your usage limit. Try again at 2:05 PM.", NOW)
    assert reading is not None and reading.until is not None
    local = reading.until.astimezone()
    assert (local.hour, local.minute) == (14, 5)


def test_a_share_of_the_window_is_a_warning_not_a_stop() -> None:
    reading = read_limit("claude", "Approaching usage limit · 90% of your 5-hour limit used", NOW)
    assert reading is not None and not reading.stopped and reading.share == 0.9


def test_plain_work_is_no_notice() -> None:
    screen = "● Read the rate limiter in web/limits.py\n● The limit is 30 per minute; tests pass\n> "
    assert read_limit("claude", screen, NOW) is None
    assert read_limit("codex", "› all 12 tests passed", NOW) is None


def test_reset_moment_reads_an_epoch_and_rolls_a_past_clock_to_tomorrow() -> None:
    assert reset_moment("usage limit reached|1793196000", NOW) == datetime.fromtimestamp(1793196000, tz=timezone.utc)
    early = reset_moment("resets 1am (UTC/UTC)", NOW)  # an unknown zone falls back to local; rolls to the next 1am
    assert early is not None and early > NOW


def test_the_screen_record_carries_the_notice_and_the_flight_says_limited() -> None:
    from holdspeak.agent_context.screen_rules import read_screen
    from holdspeak.agent_context.screen_watch import ScreenStore
    from holdspeak.services.agent_flights import _limit_wire

    screen = "● Done with 20 of 31\nYou've hit your limit · resets 2pm\n╭──╮\n│ > │\n╰──╯"
    store = ScreenStore()
    verdict = read_screen("claude", screen)
    store.observe("launch:L1", agent="claude", target="%1", verdict=verdict, screen=screen, title="", now=NOW)
    row = store.get("launch:L1")
    assert row is not None and row.limit is not None
    wire = _limit_wire({"state": "launched"}, row, "done", NOW)
    assert wire and wire["rule"] == "claude.usage_limit" and wire["until"]
    assert _limit_wire({"state": "launched"}, row, "done", NOW + timedelta(days=2)) is None  # the window reset
    assert _limit_wire({"state": "handed_off"}, row, "done", NOW) is None


# ── the rules, per level ──────────────────────────────────────────────

def test_the_rules_rows_per_level() -> None:
    free = {"next": True, "minutes": 1}
    assert isinstance(decide("secure", "limited", free), CoreQuestion)
    assert isinstance(decide("normal", "limited", free), CoreQuestion)
    assert isinstance(decide("normal", "limited", {**free, "may_handoff": True}), CoreQuestion)  # before 10 min
    later = decide("normal", "limited", {**free, "may_handoff": True, "minutes": 10})
    assert isinstance(later, Decision) and later.choice == "handoff"
    assert decide("yolo", "limited", free).choice == "handoff"
    for level in ("secure", "normal", "yolo"):
        assert decide(level, "limited", {"next": False}).choice == "wait"
        assert decide(level, "limited", {**free, "handed": True}).choice == "none"
        assert decide(level, "limited", {**free, "waiting": True}).choice == "wait"


# ── the brief: golden, redaction ──────────────────────────────────────

def _inputs() -> HandoffInputs:
    return HandoffInputs(
        program_title="The hub stops stalling", step_ordinal=4, step_total=6, step_title="People routes",
        from_label="Claude Code", to_label="Codex", reason="usage_limit",
        goal="Make the hub stop stalling.", step_brief="31 handlers through run_in_threadpool.",
        plan=((1, "Indexes", "[x]", "Merged"), (2, "Retention", "[~]", "PR open"), (4, "People routes", "[~]", "this step"),
              (5, "Projects routes", "[ ]", "Ready")),
        checkpoints=("Handed to Claude Code in hs-program-step-4", "31 handlers, 20 done"),
        said=("Keep the 14-day rule", "Our deploy key is api_key=sk-live-abcdefghijklmnopqrstuv"),
        files=("M holdspeak/web/routes/people.py", "A tests/unit/test_people_routes.py"),
        git_status=" M holdspeak/web/routes/people.py\n?? notes.txt",
        diff_stat=" holdspeak/web/routes/people.py | 40 ++++++++++++++++++++--------------\n 1 file changed, 22 insertions(+), 18 deletions(-)",
        failing_check=("scripts/quick_check.sh", "== pytest affected (2 files)\n   FAILED tests/unit/test_people_routes.py::test_list\n   1 failed, 11 passed"),
        open_asks=("Answer step 4 “People routes”",),
        limit_line="You've hit your limit · resets 2pm", instructions=("CLAUDE.md", "Run one test at a time.\ntoken=ghp_abcdefghijklmnopqrstuvwx1234\n"),
        branch="program/the-hub-stops-stalling/4-people-routes", base_branch="main", worktree="hs-program-step-4",
        earlier_turns=12, gate="scripts/quick_check.sh",
    )


def test_the_golden_brief_byte_for_byte() -> None:
    brief = brief_of(_inputs())
    assert brief.text == GOLDEN.read_text(encoding="utf-8")
    assert brief_of(_inputs()).text == brief.text      # the same inputs, the same bytes
    assert brief.redacted == {"key": 1, "token": 1}
    assert brief.redacted_words == "1 key, 1 token"
    assert "sk-live" not in brief.text and "ghp_" not in brief.text
    assert brief.earlier_turns == 12


def test_redaction_counts_by_kind() -> None:
    text = ("api_key=sk-abcdefghijklmnopqrstuvwx\nAKIAABCDEFGHIJKLMNOP\nAuthorization: Bearer abcdef1234567890xyz\n"
            "password: hunter2x9\n-----BEGIN RSA PRIVATE KEY-----\nMIIabc\n-----END RSA PRIVATE KEY-----\n")
    clean, counts = redact_counted(text)
    assert counts == {"key": 2, "token": 1, "password": 1, "private_key": 1}
    assert "hunter2x9" not in clean and "MIIabc" not in clean
    assert redacted_words(counts) == "2 keys, 1 token, 1 password, 1 private key"
    assert redact_counted("no secrets here") == ("no secrets here", {})


# ── the engine: the rig ───────────────────────────────────────────────

def _program(rig: Rig, control: str, runs_on, **kw) -> str:
    pid = rig.service.create(OWNER, title="The hub stops stalling", goal="Make the hub stop stalling.",
                             repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}", control=control,
                             runs_on=runs_on, **kw)["id"]
    rig.service.plan(OWNER, pid, steps=[{"title": "People routes", "brief": "31 handlers through run_in_threadpool."}])
    rig.service.start(OWNER, pid)
    return pid


def _limit(rig: Rig, launch_id: str, *, turn: str = "t-limit", minutes: int = 90) -> None:
    until = (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z")
    rig.states[launch_id] = {"state": "done", "turn_id": turn, "limit": {
        "rule": "claude.usage_limit", "line": "You've hit your limit · resets 2pm", "share": None,
        "until": until, "words": "14:00"}}


def test_runs_on_is_a_list_and_the_first_pair_stays_readable(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = rig.service.create(OWNER, title="P", repository=str(rig.repo), runs_on=["claude", {"profile": "codex"}])["id"]
    program = rig.service.store.get_program(pid)
    assert (program["default_profile"], program["default_engine"]) == ("claude-default", None)
    assert [row["profile"] for row in program["default_runs_on"]] == ["claude-default", "codex-default"]
    wire = rig.program(pid)
    assert [row["label"] for row in wire["default"]["runs_on"]] == ["Claude Code", "Codex"]
    rig.service.plan(OWNER, pid, steps=[{"title": "A", "runs_on": ["codex", "claude"]}, {"title": "B"}])
    one, two = rig.program(pid)["steps"]
    assert one["profile"] == "codex-default" and [row["agent"] for row in one["runs_on"]] == ["Codex", "Claude Code"]
    assert [row["agent"] for row in two["runs_on"]] == ["Claude Code", "Codex"]
    with pytest.raises(ProgramRefused) as refused:
        rig.service.update(OWNER, pid, runs_on=["nobody"])
    assert refused.value.code == "profile_unknown"


def test_yolo_continues_at_once_in_the_next_agent_same_worktree(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig, "yolo", ["claude", "codex"])
    step = rig.step(pid, 1)
    first = step["launch_id"]
    worktree = rig.ledger.get(first)["worktree_path"]
    (Path(worktree) / "people.py").write_text("x = 1\n", encoding="utf-8")
    _limit(rig, first)
    rig.tick()
    step = rig.step(pid, 1)
    assert step["state"] in ("briefed", "working") and step["launch_id"] != first
    assert step["profile"] == "codex-default"
    new = rig.ledger.get(step["launch_id"])
    assert new["worktree_path"] == worktree and new["branch"] == rig.ledger.get(first)["branch"]
    assert rig.ledger.get(first)["state"] == "handed_off"
    assert new["first_message"].startswith("# Handoff brief") and "people.py" in new["first_message"]
    [entry] = step["handoffs"]
    assert (entry["from"], entry["to"], entry["reason"], entry["by"]) == ("Claude Code", "Codex", "usage_limit", "engine")
    decided = [row for row in rig.program(pid)["decided_for_you"] if row["kind"] == "handoff"]
    assert decided and decided[0]["line"] == "Handed to Codex · usage limit"


def test_never_twice_for_the_same_stopped_turn(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig, "yolo", ["claude", "codex"])
    step = rig.step(pid, 1)
    _limit(rig, step["launch_id"])
    program = rig.service.store.get_program(pid)
    raw = rig.service.store.get_step(step["id"])
    raw["facts"] = {**raw["facts"], "handed_turns": [f"{step['launch_id']}:t-limit"]}
    rig.service.store.save_step(raw)
    calls = len(rig.hand.calls)
    rig.runner._limit_follow(program, rig.service.store.get_step(step["id"]), rig.states[step["launch_id"]])
    assert len(rig.hand.calls) == calls
    assert rig.service.store.get_step(step["id"])["state"] == "limited"


def test_the_skip_rules_and_none_left_waits_for_the_reset(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig, "yolo", ["claude", "codex", "pi"], allowed_profiles=["claude", "pi"])
    program = rig.service.store.get_program(pid)
    step = rig.service.store.list_steps(pid)[0]
    current = {"profile": "claude-default", "engine": None}
    assert rig.runner.next_agent(program, step, current)["profile"] == "pi-default"  # Codex is not allowed
    rig.service._profiles = lambda: {"claude-default", "codex-default"}              # the desk has no pi
    assert rig.runner.next_agent(program, step, current) is None
    _limit(rig, step["launch_id"])
    rig.tick()
    wire = rig.step(pid, 1)
    assert wire["state"] == "limited" and wire["state_word"] == "Limited until 14:00 · waits for the reset"
    assert not wire["handoffs"]


def test_dispatch_skips_an_agent_that_is_itself_limited(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig, "yolo", ["claude", "codex"])
    first = rig.step(pid, 1)
    _limit(rig, first["launch_id"])
    rig.tick()   # handed to Codex; Claude Code stays limited until its reset
    rig.service.plan(OWNER, pid, steps=[{"title": "Projects routes", "brief": "The next 20 handlers."}])
    rig.tick()
    second = rig.step(pid, 2)
    assert second["launch_id"] and second["profile"] == "codex-default"


def test_normal_asks_him_and_continue_hands_off_by_his_press(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig, "normal", ["claude", "codex"])
    step = rig.step(pid, 1)
    _limit(rig, step["launch_id"])
    rig.tick()
    wire = rig.program(pid)
    [item] = [row for row in wire["your_turn_items"] if row["kind"] == "limited"]
    assert item["title"] == "Claude Code is at its limit until 14:00: continue in Codex now, or wait?"
    assert item["choices"] == ["continue", "wait"]
    assert wire["steps"][0]["state_word"] == "Limited until 14:00 · continuing in Codex"
    answer = rig.service.decide(OWNER, pid, step["id"], kind="limited", choice="continue")
    after = answer["program"]["steps"][0]
    assert after["profile"] == "codex-default" and after["handoffs"][0]["by"] == "owner"
    line = next(row for row in answer["program"]["checkpoints"] if row["kind"] == "handoff")
    assert line["line"] == "Handed to Codex · usage limit" and line["by"] == "owner"


def test_wait_keeps_the_step_limited_until_the_reset_then_it_goes_on(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig, "secure", ["claude", "codex"])
    step = rig.step(pid, 1)
    _limit(rig, step["launch_id"])
    rig.tick()
    answer = rig.service.decide(OWNER, pid, step["id"], kind="limited", choice="wait")
    assert answer["program"]["steps"][0]["state_word"] == "Limited until 14:00 · waits for the reset"
    assert not [row for row in answer["program"]["your_turn_items"] if row["kind"] == "limited"]
    rig.states[step["launch_id"]] = {"state": "done", "turn_id": "t-limit"}   # the notice is gone
    rig.tick()
    assert rig.step(pid, 1)["state"] == "working"
    assert rig.prompts[-1] == (step["launch_id"], "HoldSpeak: your usage window reset. Continue the step where you stopped.")


def test_a_usage_warning_hands_off_at_a_turn_end_only_when_he_set_one(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig, "yolo", ["claude", "codex"])
    step = rig.step(pid, 1)
    share = {"rule": "claude.usage_share", "line": "90% of your 5-hour limit used", "share": 0.9, "until": None, "words": ""}
    rig.states[step["launch_id"]] = {"state": "done", "turn_id": "t1", "limit": share}
    rig.tick()
    assert not rig.step(pid, 1)["handoffs"]                       # no warning set: work on
    rig.service.update(OWNER, pid, usage_warning_share=0.85)
    rig.states[step["launch_id"]] = {"state": "done", "turn_id": "t2", "limit": share}
    rig.tick()
    assert rig.step(pid, 1)["handoffs"][0]["reason"] == "usage_warning"


def test_the_brief_from_a_fixed_worktree_is_the_same_twice(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig, "secure", ["claude", "codex"])
    step = rig.step(pid, 1)
    path = Path(rig.ledger.get(step["launch_id"])["worktree_path"])
    (path / "CLAUDE.md").write_text("Run one test at a time.\npassword: s3cret-pass\n", encoding="utf-8")
    (path / "people.py").write_text("x = 1\n", encoding="utf-8")
    git(path, "add", "-A")
    git(path, "commit", "-m", "half the handlers")
    (path / "notes.txt").write_text("left: 11 handlers\n", encoding="utf-8")
    rig.service.checkpoint(OWNER, pid, step["id"], "Keep the 14-day rule")
    program = rig.service.store.get_program(pid)
    raw = rig.service.store.get_step(step["id"])
    one = brief_of(gather(rig.service, program, raw, to_label="Codex", from_label="Claude Code", reason="usage_limit",
                          git=rig.runner._git_out, facts_reader=lambda _l, _p: {"files": [{"status": "A", "path": "people.py"}]}))
    two = brief_of(gather(rig.service, program, raw, to_label="Codex", from_label="Claude Code", reason="usage_limit",
                          git=rig.runner._git_out, facts_reader=lambda _l, _p: {"files": [{"status": "A", "path": "people.py"}]}))
    assert one.text == two.text
    assert "?? notes.txt" in one.text and "people.py | 1 +" in one.text and "- A people.py" in one.text
    assert "## Repository instructions (CLAUDE.md)" in one.text and "s3cret-pass" not in one.text
    assert one.redacted == {"password": 1}
    assert "- Keep the 14-day rule" in one.text


# ── by hand: the route and the MCP authority ──────────────────────────

def test_the_route_previews_then_sends_and_is_the_owners_alone(tmp_path, monkeypatch) -> None:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from holdspeak.services import program_service as module
    from holdspeak.web.routes.programs import build_programs_router

    rig = Rig(tmp_path)
    pid = _program(rig, "normal", ["claude", "codex"])
    step = rig.step(pid, 1)
    monkeypatch.setattr(module, "default_program_service", lambda db=None: rig.service)
    app = FastAPI()
    app.include_router(build_programs_router(None))  # type: ignore[arg-type]
    client = TestClient(app)
    url = f"/api/programs/{pid}/steps/{step['id']}/handoff"
    preview = client.post(url, json={"to": "codex", "preview": True})
    assert preview.status_code == 200, preview.text
    body = preview.json()
    assert body["preview"] is True and body["brief"].startswith("# Handoff brief") and body["to"]["label"] == "Codex"
    assert rig.step(pid, 1)["launch_id"] == step["launch_id"]       # nothing moved
    sent = client.post(url, json={"to": "codex"})
    assert sent.status_code == 200, sent.text
    assert sent.json()["program"]["steps"][0]["handoffs"][0]["reason"] == "by_hand"

    agents = FastAPI()

    @agents.middleware("http")
    async def as_agent(request, call_next):  # type: ignore[no-untyped-def]
        request.state.principal = Principal(PrincipalKind.AGENT, "agent:launch:L9")
        return await call_next(request)

    agents.include_router(build_programs_router(None))  # type: ignore[arg-type]
    refused = TestClient(agents).post(url, json={"to": "claude", "preview": True})
    assert refused.status_code == 403 and refused.json()["code"] == "owner_required"


def test_program_handoff_over_mcp_is_authority_and_not_the_agents(tmp_path, monkeypatch) -> None:
    from holdspeak.mcp import palettes
    from holdspeak.mcp.families import program as family
    from holdspeak.mcp.tool_authority import AUTHORITY, TOOL_AUTHORITY

    assert TOOL_AUTHORITY["program.handoff"] == AUTHORITY
    assert "program.handoff" not in palettes.resolve_palette("CONDUCTOR")
    rig = Rig(tmp_path)
    monkeypatch.setattr("holdspeak.services.program_service.default_program_service", lambda db=None: rig.service)
    pid = _program(rig, "normal", ["claude", "codex"])
    step = rig.step(pid, 1)
    agent = Principal(PrincipalKind.AGENT, f"agent:launch:{step['launch_id']}")
    with pytest.raises(ProgramRefused) as refused:
        family.dispatch("program.handoff", {"program_id": pid, "step_id": step["id"], "to": "codex"}, agent)
    assert refused.value.code == "owner_required"
    answer = family.dispatch("program.handoff", {"program_id": pid, "step_id": step["id"], "to": "codex", "preview": True}, OWNER)
    assert answer["preview"] is True and answer["earlier_turns"] == 0
