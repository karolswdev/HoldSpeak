"""Betterment AG7: screen rules, the herdr port.

- The engine reads herdr's own rule files the way herdr does: the semantics
  tests below are herdr's (``src/detect/manifest/tests.rs``, v0.9.5,
  Apache-2.0), ported with their manifests and inputs unchanged.
- Every vendored rule file compiles here and carries its license header.
- The recorded screens (``tests/fixtures/agent_screens``) are read through
  tmux by ``scripts/capture_agent_screen.py``, exactly as the hub's watcher
  reads a pane. Today they come from the rig's fake Claude Code
  (``docs/internal/betterment/agents/rig/fake_claude.py``); no real Claude
  Code or Codex screen is recorded yet (that needs the owner's consent).
- The watcher's record (herdr's completion sequence, No signal) and the
  flight merge (the hook first, then the rule).
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from holdspeak.agent_context import screen_rules as rules
from holdspeak.agent_context import screen_watch as watch
from holdspeak.agent_context.screen_rules import classify, parse_manifest

SCREENS = Path(__file__).resolve().parents[1] / "fixtures" / "agent_screens"
T0 = datetime(2026, 10, 18, 12, 0, tzinfo=timezone.utc)


def _explain(manifest_text: str, screen: str) -> rules.Verdict:
    return classify("codex", screen, manifest=parse_manifest(manifest_text, source="local override"))


# ── the vendored files ────────────────────────────────────────────────


@pytest.mark.parametrize("agent", rules.BUNDLED_AGENTS)
def test_every_vendored_rule_file_compiles_and_names_its_license(agent: str) -> None:
    path = rules.RULES_DIR / f"{agent}.toml"
    head = path.read_text(encoding="utf-8").splitlines()[:4]
    assert head[0].startswith("# Vendored from herdr") and "Apache License, Version 2.0" in head[2]
    manifest = rules.load_manifest(agent)
    assert manifest is not None and manifest.agent == agent and manifest.rules
    assert manifest.source == "bundled"


def test_rust_regex_reads_code_points_and_the_end_of_text() -> None:
    assert rules.rust_regex(r"^[\x{2800}-\x{28FF}] ") == "^[\\U00002800-\\U000028ff] "
    assert rules.rust_regex(r"cancel\s*\z") == r"cancel\s*\Z"
    assert rules.rust_regex(r"a\\z") == r"a\\z"   # an escaped backslash, then z


# ── herdr's engine semantics (manifest/tests.rs, ported) ──────────────


def test_known_agent_no_match_defaults_to_idle_fallback() -> None:
    verdict = _explain('id = "codex"\n[[rules]]\nid = "test"\nstate = "working"\ncontains = ["active-marker"]\n',
                       "unmatched-marker")
    assert verdict.state == "idle" and verdict.fallback == rules.IDLE_FALLBACK and verdict.rule is None


RULE_SEMANTICS = '''
id = "codex"

[[rules]]
id = "low_contains"
state = "idle"
priority = 1
contains = ["match"]

[[rules]]
id = "high_nested_gates"
state = "working"
priority = 10
contains = ["match"]
all = [
  { any = [{ regex = ["w[io]n"] }, { contains = ["fallback"] }] },
]
not = [
  { contains = ["blocked"] },
]

[[rules]]
id = "line_regex"
state = "blocked"
priority = 20
line_regex = ["^exact line$"]
'''


def test_rule_semantics_apply_gates_priority_and_line_regex() -> None:
    high = _explain(RULE_SEMANTICS, "match win")
    assert (high.state, high.rule) == ("working", "high_nested_gates")
    not_gate = _explain(RULE_SEMANTICS, "match win blocked")
    assert (not_gate.state, not_gate.rule) == ("idle", "low_contains")
    line = _explain(RULE_SEMANTICS, "before\nexact line\nafter")
    assert (line.state, line.rule) == ("blocked", "line_regex")


FOOTER = '''
id = "codex"

[[rules]]
id = "live_controls"
state = "blocked"
region = "whole_recent"
regex = ['(?i)(?:^|\\n)controls:\\s+(?:confirm-marker|select-marker\\s+navigate-marker)\\s+cancel-marker[ \\t]*\\n---[^\\n]*(?:\\npanel: \\d+(?:\\nrow: [^\\n]+)+(?:\\n… \\+\\d+ pending)?)?(?:\\n[ \\t]*)*\\z']
'''


def test_end_anchored_footer_gates_allow_only_auxiliary_tail() -> None:
    footer = "controls: select-marker navigate-marker cancel-marker"
    for tail in (
        "--- name",
        "--- name\npanel: 5\nrow: active\nrow: pending\nrow: pending\nrow: pending\nrow: done\n",
        "--- name\npanel: 5\nrow: active\nrow: done\n… +3 pending",
    ):
        live = f"old output\n{footer}\n{tail}"
        assert _explain(FOOTER, live).state == "blocked", tail
        for later in ("new output", "prompt:", "--- next\nprompt:", "prompt: continue…", "working: processing…",
                      "…ordinary output", "finished…", "… +2 arbitrary words"):
            assert _explain(FOOTER, f"{live}\n{later}").state == "idle", (tail, later)
    for tail in ("--- name\n… +2 pending", "--- name\nrow: active", "--- name\npanel: 5",
                 "--- name\npanel: 5\nrow: active\n  working: processing…",
                 "--- name\npanel: 5\nrow: active\n  prompt: continue…"):
        assert _explain(FOOTER, f"{footer}\n{tail}").state == "idle", tail
    for controls in ("controls: confirm-marker cancel-marker",
                     "controls: select-marker\nnavigate-marker cancel-marker",
                     "controls:\nselect-marker\nnavigate-marker\ncancel-marker"):
        assert _explain(FOOTER, f"{controls}\n--- name").state == "blocked", controls
    for controls in ("controls: select-marker cancel-marker", "controls: navigate-marker cancel-marker",
                     "controls: confirm-marker", "controls: select-marker unrelated navigate-marker cancel-marker",
                     "controls: select-marker\nprompt: navigate-marker cancel-marker"):
        assert _explain(FOOTER, f"confirm-marker navigate-marker\n{controls}\n--- name").state == "idle", controls


PAIRED = '''
id = "codex"

[[rules]]
id = "paired"
state = "blocked"
region = "bottom_non_empty_lines(3)"
visible_blocker = true
any = [
  { all = [
    { contains = ["alpha heading"] },
    { regex = ['alpha\\s+control\\s*\\z'] },
  ] },
  { all = [
    { contains = ["beta heading"] },
    { regex = ['beta\\s+control\\s*\\z'] },
  ] },
]
'''


def test_paired_alternatives_require_complete_gates_at_bottom_buffer() -> None:
    for text in ("alpha heading\nalpha control", "beta heading\nbeta\ncontrol"):
        assert _explain(PAIRED, text).state == "blocked", text
    for text in ("alpha heading\nbeta control", "beta heading\nalpha control", "beta control", "beta heading",
                 "beta heading\nbeta control\nnewer content", "beta heading\nfiller one\nfiller two\nbeta control"):
        assert _explain(PAIRED, text).rule is None, text


def test_a_local_override_wins_over_the_bundled_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rules, "override_dir", lambda: tmp_path)
    (tmp_path / "codex.toml").write_text(
        'id = "codex"\nversion = "9999.1"\n[[rules]]\nid = "mine"\nstate = "blocked"\ncontains = ["my-marker"]\n')
    verdict = classify("codex", "my-marker")
    assert (verdict.state, verdict.rule, verdict.source, verdict.version) == ("blocked", "mine", "local override", "9999.1")
    # An override that does not parse falls back to the bundled file.
    (tmp_path / "codex.toml").write_text('id = "codex"\n[[rules]]\nid = "bad"\nstate = "blocked"\nregex = ["("]\n')
    assert rules.load_manifest("codex").source == "bundled"


# ── the recorded screens ──────────────────────────────────────────────


def _recorded() -> list[str]:
    return sorted(p.stem for p in SCREENS.glob("*.txt"))


def test_screens_are_recorded() -> None:
    assert _recorded(), "no recorded screen: scripts/capture_agent_screen.py writes them"


@pytest.mark.parametrize("name", _recorded())
def test_each_recorded_screen_reads_as_the_state_it_showed(name: str) -> None:
    meta = json.loads((SCREENS / f"{name}.json").read_text(encoding="utf-8"))
    screen = (SCREENS / f"{name}.txt").read_text(encoding="utf-8").rstrip("\n")
    verdict = classify(meta["agent"], screen, title=meta["title"])
    assert verdict is not None and verdict.state == meta["expected_state"], (name, verdict)
    assert verdict.rule is not None, f"{name}: no rule matched (the idle fallback is not a reading)"


def _screen(name: str) -> tuple[str, str]:
    meta = json.loads((SCREENS / f"{name}.json").read_text(encoding="utf-8"))
    return (SCREENS / f"{name}.txt").read_text(encoding="utf-8").rstrip("\n"), meta["title"]


def test_an_approval_prompt_names_its_command_and_choices() -> None:
    screen, _title = _screen("claude-rig-permission")
    reading = rules.prompt_reading(screen)
    assert reading["wait"] == "approve"
    assert reading["command"].splitlines()[0] == "rm -rf build/ && make release"
    assert [c["n"] for c in reading["choices"]] == ["1", "2"]
    assert reading["choices"][0]["label"] == "Yes"
    assert reading["choices"][1]["label"] == "No, and tell Claude what to do differently"


def test_the_last_message_above_the_prompt_box() -> None:
    screen, _title = _screen("claude-rig-asks")
    said = rules.last_message(screen)
    assert said.startswith("I found two places for the rollback flag.") and said.endswith("2 for env.")


# ── the watcher's record: herdr's completion sequence, No signal ──────


def _observe(store: watch.ScreenStore, name: str, at: datetime, key: str = "launch:l1") -> bool:
    screen, title = _screen(name)
    verdict = classify("claude", screen, title=title)
    return store.observe(key, agent="claude", target="hs-l1", verdict=verdict, screen=screen, title=title, now=at)


def test_a_turn_is_done_only_after_the_screen_saw_work() -> None:
    store = watch.ScreenStore()
    _observe(store, "claude-rig-start", T0)
    assert watch.merged_state(store.get("launch:l1"), T0) == "idle"   # a start-up idle is Quiet, never Done
    _observe(store, "claude-rig-working", T0 + timedelta(seconds=2))
    assert watch.merged_state(store.get("launch:l1"), T0 + timedelta(seconds=2)) == "working"
    _observe(store, "claude-rig-asks", T0 + timedelta(seconds=10))
    row = store.get("launch:l1")
    assert row.turn_id == "screen:2026-10-18T12:00:10Z"
    assert watch.merged_state(row, T0 + timedelta(seconds=10)) == "asks"   # its last words ask
    _observe(store, "claude-rig-working", T0 + timedelta(seconds=12))
    assert store.get("launch:l1").turn_id is None
    assert _observe(store, "claude-rig-permission", T0 + timedelta(seconds=20))
    row = store.get("launch:l1")
    assert watch.merged_state(row, T0 + timedelta(seconds=20)) == "approve"
    assert row.command.startswith("rm -rf build/") and len(row.choices) == 2
    _observe(store, "claude-rig-working", T0 + timedelta(seconds=22))
    _observe(store, "claude-rig-done", T0 + timedelta(seconds=30))
    assert watch.merged_state(store.get("launch:l1"), T0 + timedelta(seconds=30)) == "done"
    # The same screen again changes nothing a face shows.
    assert not _observe(store, "claude-rig-done", T0 + timedelta(seconds=32))


def test_no_signal_after_ten_minutes_with_no_rule() -> None:
    store = watch.ScreenStore()
    verdict = classify("claude", "a plain shell prompt $")
    assert verdict.fallback == rules.IDLE_FALLBACK
    store.observe("launch:l1", agent="claude", target="t", verdict=verdict, screen="$", title="", now=T0)
    assert watch.merged_state(store.get("launch:l1"), T0 + timedelta(minutes=9)) == "idle"
    assert watch.merged_state(store.get("launch:l1"), T0 + timedelta(minutes=11)) == "no_signal"


def test_the_watcher_reads_each_running_launch_and_hooked_pane(monkeypatch: pytest.MonkeyPatch) -> None:
    from types import SimpleNamespace

    screens = {"hs-l1": _screen("claude-rig-permission"), "%7": _screen("claude-rig-working")}
    calls: list[list[str]] = []

    def runner(argv: list[str]) -> SimpleNamespace:
        calls.append(argv)
        target = argv[argv.index("-t") + 1]
        if target not in screens:
            return SimpleNamespace(returncode=1, stdout="", stderr="can't find pane")
        screen, title = screens[target]
        return SimpleNamespace(returncode=0, stdout=(title if argv[1] == "display-message" else screen) + "\n", stderr="")

    records = [
        {"launch_id": "l1", "state": "launched", "session": "hs-l1", "profile_id": "claude-default"},
        {"launch_id": "l2", "state": "complete", "session": "hs-l2", "profile_id": "claude-default"},
    ]
    sessions = [SimpleNamespace(agent="claude", session_id="own", tmux_pane="%7", lifecycle="working")]
    store = watch.ScreenStore()
    changed = watch.tick(store, records=records, sessions=sessions, db=None, runner=runner, now=T0)
    assert changed == ["launch:l1", "claude:own"]
    assert watch.merged_state(store.get("launch:l1"), T0) == "approve"
    assert watch.merged_state(store.get("claude:own"), T0) == "working"
    assert not any("hs-l2" in argv for argv in calls)   # a finished launch is never read
    monkeypatch.setenv(watch.SCREEN_RULES_ENV, "off")
    calls.clear()
    assert watch.tick(store, records=records, sessions=sessions, db=None, runner=runner, now=T0) == []
    assert calls == []


# ── the merge: the hook first, then the rule, then No signal ──────────


class _Ledger:
    def __init__(self, *records):
        self.rows = {r["launch_id"]: dict(r) for r in records}

    def list(self):
        return list(self.rows.values())

    def get(self, launch_id):
        return self.rows.get(launch_id)


class _DB:
    class work_attempts:  # noqa: N801
        @staticmethod
        def get(_attempt_id):
            from types import SimpleNamespace

            return SimpleNamespace(session_id="claude:s1")


def _flight(monkeypatch, *, record, sessions, rows, now):
    from holdspeak.services import agent_flights

    monkeypatch.setattr(agent_flights, "_title_of", lambda db, ref: "Fix the rollback flag")
    monkeypatch.setattr(agent_flights, "_project_of", lambda db, kind, item_id: ("p1", "Platform"))
    monkeypatch.setattr(watch, "STORE", rows)
    [flight] = agent_flights.agent_flights(_DB(), sessions, ledger=_Ledger(record), now=now)
    return flight


RECORD = {"launch_id": "l1", "state": "launched", "session": "hs-l1", "profile_id": "claude-default",
          "origin_ref": {"kind": "action", "id": "a1"}, "launched_at": "2026-10-18T11:59:00Z"}


def test_with_no_hook_the_screen_decides_the_flight(monkeypatch: pytest.MonkeyPatch) -> None:
    store = watch.ScreenStore()
    _observe(store, "claude-rig-working", T0)
    flight = _flight(monkeypatch, record=RECORD, sessions=[], rows=store, now=T0)
    assert (flight["state"], flight["state_source"]) == ("working", "screen")
    _observe(store, "claude-rig-permission", T0 + timedelta(seconds=5))
    flight = _flight(monkeypatch, record=RECORD, sessions=[], rows=store, now=T0 + timedelta(seconds=5))
    assert (flight["state"], flight["turn_end"]) == ("waiting", "asks")
    assert flight["screen"]["wait"] == "approve" and flight["screen"]["command"].startswith("rm -rf build/")
    _observe(store, "claude-rig-working", T0 + timedelta(seconds=8))
    _observe(store, "claude-rig-done", T0 + timedelta(seconds=15))
    flight = _flight(monkeypatch, record=RECORD, sessions=[], rows=store, now=T0 + timedelta(seconds=15))
    assert (flight["state"], flight["turn_id"], flight["new"]) == ("done", "screen:2026-10-18T12:00:15Z", True)
    seen = {**RECORD, "seen_wait_id": "screen:2026-10-18T12:00:15Z"}
    assert _flight(monkeypatch, record=seen, sessions=[], rows=store, now=T0 + timedelta(seconds=16))["new"] is False


def test_a_fresh_hook_outranks_the_screen(monkeypatch: pytest.MonkeyPatch) -> None:
    store = watch.ScreenStore()
    _observe(store, "claude-rig-done", T0)
    hooked = {**RECORD, "state": "registered", "attempt_id": "at1"}
    session = {"agent": "claude", "session_id": "s1", "cwd": "/repo", "hook_event_name": "PostToolUse",
               "lifecycle": "working", "updated_at": "2026-10-18T11:58:00Z"}
    flight = _flight(monkeypatch, record=hooked, sessions=[session], rows=store, now=T0)
    assert (flight["state"], flight["state_source"]) == ("working", "hook")
    # The hook went quiet while it said working: the screen's reading stands.
    later = T0 + timedelta(minutes=watch.HOOK_FRESH_SECONDS // 60 + 3)
    flight = _flight(monkeypatch, record=hooked, sessions=[session], rows=store, now=later)
    assert (flight["state"], flight["state_source"]) == ("waiting", "screen")


def test_explain_names_the_source_the_rule_and_the_evidence(monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak.services import agent_flights

    store = watch.ScreenStore()
    _observe(store, "claude-rig-permission", T0)
    monkeypatch.setattr(agent_flights, "_title_of", lambda db, ref: "")
    monkeypatch.setattr(agent_flights, "_project_of", lambda db, kind, item_id: ("", ""))
    monkeypatch.setattr(watch, "STORE", store)
    answer = agent_flights.explain_agent(_DB(), "launch:l1", ledger=_Ledger(RECORD), sessions=[],
                                         now=T0 + timedelta(seconds=4))
    assert (answer["source"], answer["state"], answer["hook"]) == ("screen", "waiting", None)
    screen = answer["screen"]
    assert (screen["rule"], screen["state"], screen["age_seconds"]) == ("bash_permission_prompt", "approve", 4)
    assert screen["rules_source"] == "bundled" and screen["rules_version"] == "2026.10.11.1"
    assert any("Do you want to proceed?" in line for line in screen["evidence"])
    assert agent_flights.explain_agent(_DB(), "launch:nope", ledger=_Ledger(RECORD), sessions=[]) is None
