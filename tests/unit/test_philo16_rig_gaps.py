"""PHILO-16 lane 16-RIG (rig gaps G1, G2): two rig isolation gaps closed at their cause.

G1. The Agents detector on a fresh isolated HOME read the owner's machine: the
    hub inherits the owner's environment (``CLAUDE_CONFIG_DIR``, ``CODEX_HOME``,
    ``ANTHROPIC_API_KEY`` point at his real sign-in and hook files) and pi's row
    claimed SIGNED IN and HOOKS on every machine. ``HOLDSPEAK_AGENT_STATE=off``
    makes those reads answer ``not_read`` (never ``no``); both rig envs set it;
    the default (the owner's desk, ``holdspeak doctor``) stays on.

G2. An ``engine_reply`` or ``cli_runner`` boundary without ``reply`` booted the
    hub without its double; only the boundary step refused, after a work step
    ordered before it could reach the real seam. The rig now refuses the case
    before the build and the hub (R2's import_transcriber guard, extended), and
    the schema requires ``reply`` on both.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from holdspeak.services import onboarding_service
from holdspeak.services.onboarding_service import (
    AGENT_STATE_ENV,
    NOT_READ,
    OnboardingService,
    agent_state_read,
    detect_agents,
)
from scripts import graph_walk

REPO = Path(__file__).resolve().parents[2]
GRAPH = REPO / "docs/internal/philo/graph"
SCHEMA = GRAPH / "atlas.schema.json"


# ── G1: the agent state switch ──────────────────────────────────────────


def _which(name: str) -> str | None:
    return f"/opt/bin/{name}" if name in {"claude", "codex", "pi", "tmux", "holdspeak"} else None


def _owner_state(root: Path) -> dict[str, str]:
    """A stand-in for the owner's real agent state OUTSIDE the rig's HOME."""
    claude = root / "owner-claude"
    codex = root / "owner-codex"
    claude.mkdir(parents=True)
    codex.mkdir(parents=True)
    (claude / ".credentials.json").write_text(json.dumps({"claudeAiOauth": {"accessToken": "t"}}))
    (codex / "auth.json").write_text(json.dumps({"tokens": {"access_token": "t"}}))
    hooks = {"hooks": {"SessionStart": [{"hooks": [{"command": "holdspeak agent-hook ingest"}]}]}}
    (claude / "settings.json").write_text(json.dumps(hooks))
    (codex / "hooks.json").write_text(json.dumps(hooks))
    return {"CLAUDE_CONFIG_DIR": str(claude), "CODEX_HOME": str(codex), "ANTHROPIC_API_KEY": "sk-owner"}


@pytest.mark.parametrize("value,expected", [
    (None, True), ("", True), ("on", True), ("1", True),
    ("off", False), ("OFF", False), ("0", False), ("false", False), ("no", False),
])
def test_the_switch_is_on_by_default_and_off_only_when_named(value: str | None, expected: bool) -> None:
    env = {} if value is None else {AGENT_STATE_ENV: value}
    assert agent_state_read(env) is expected


def test_with_the_switch_off_a_fresh_home_reports_no_sign_in_and_no_hooks(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    env = {**_owner_state(tmp_path), AGENT_STATE_ENV: "off"}

    rows = {row["id"]: row for row in detect_agents(which=_which, home=home, environ=env)["agents"]}

    assert set(rows) == {"claude", "codex", "pi"}
    for row in rows.values():
        # Installed is lawful to detect (the binary on PATH).
        assert row["installed"] is True
        # Never "yes", and never a "no" a face could act on.
        assert row["signed_in"] == NOT_READ, row
        assert row["signed_in_from"] is None
        assert row["hooks"] != "installed", row
        assert row["ready"] is False
    assert rows["pi"]["hooks"] == NOT_READ
    # The owner's config dirs are not where the rig looked.
    for agent in ("claude", "codex"):
        assert Path(rows[agent]["hooks_path"]).is_relative_to(home), rows[agent]["hooks_path"]


def test_the_default_still_reads_the_real_state_for_the_owner_and_doctor(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    env = _owner_state(tmp_path)  # no switch: the owner's desk

    rows = {row["id"]: row for row in detect_agents(which=_which, home=home, environ=env)["agents"]}

    assert rows["claude"]["signed_in"] == "yes"
    assert rows["claude"]["signed_in_from"] == "ANTHROPIC_API_KEY"
    assert rows["codex"]["signed_in"] == "yes"
    assert rows["claude"]["hooks_path"].startswith(env["CLAUDE_CONFIG_DIR"])
    assert rows["pi"]["signed_in"] == "yes"
    assert rows["pi"]["hooks"] in {"installed", "missing"}


def test_doctor_reads_with_the_process_environment_default_on(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``holdspeak doctor`` calls ``detect_agents()`` with no env: the process's, switch unset."""
    from holdspeak.commands import doctor

    monkeypatch.delenv(AGENT_STATE_ENV, raising=False)
    for key, value in _owner_state(tmp_path).items():
        monkeypatch.setenv(key, value)
    seen: dict[str, Any] = {}
    real = onboarding_service.detect_agents

    def spy(**kwargs: Any) -> dict[str, Any]:
        result = real(which=_which, home=tmp_path / "home", **kwargs)
        seen.update({row["id"]: row for row in result["agents"]})
        return result

    monkeypatch.setattr(onboarding_service, "detect_agents", spy)
    check = doctor._check_coding_agents()
    assert check.name == "Coding agents"
    assert seen["claude"]["signed_in"] == "yes" and seen["pi"]["signed_in"] == "yes"


def test_a_credential_in_the_rigs_own_home_is_still_read(tmp_path: Path) -> None:
    """Files under the isolated HOME are the rig's own state (the lane 18 glass writes them)."""
    home = tmp_path / "home"
    (home / ".codex").mkdir(parents=True)
    (home / ".codex" / "auth.json").write_text(json.dumps({"OPENAI_API_KEY": "sk-placeholder"}))
    env = {**_owner_state(tmp_path), AGENT_STATE_ENV: "off"}

    rows = {row["id"]: row for row in detect_agents(which=_which, home=home, environ=env)["agents"]}

    assert rows["codex"]["signed_in"] == "yes"
    assert rows["codex"]["signed_in_from"] == str(home / ".codex" / "auth.json")
    assert rows["claude"]["signed_in"] == NOT_READ


def test_the_install_target_stays_in_the_rigs_home_with_the_switch_off(tmp_path: Path) -> None:
    """Install hooks in a rig writes the rig's HOME, never the owner's CLAUDE_CONFIG_DIR."""
    home = tmp_path / "home"
    home.mkdir()
    owner = _owner_state(tmp_path)

    def service(env: dict[str, str]) -> OnboardingService:
        svc = OnboardingService.__new__(OnboardingService)
        svc._home = lambda: home
        svc._environ = env
        return svc

    off = service({**owner, AGENT_STATE_ENV: "off"})
    assert Path(off.agent_settings_target("claude")).is_relative_to(home)
    assert Path(off.agent_settings_target("codex")).is_relative_to(home)
    on = service(owner)
    assert off.agent_settings_target("claude") != on.agent_settings_target("claude")
    assert on.agent_settings_target("claude").startswith(owner["CLAUDE_CONFIG_DIR"])


def test_the_graph_walk_hub_env_turns_agent_state_off_without_touching_this_process(tmp_path: Path) -> None:
    before = os.environ.get(AGENT_STATE_ENV)
    env = graph_walk._isolated_hub_env(tmp_path, inherited={"PATH": "/usr/bin"})
    assert env[AGENT_STATE_ENV] == "off"
    assert agent_state_read(env) is False
    # The rig env is the child's: the parent (and `holdspeak web`) keep theirs.
    assert os.environ.get(AGENT_STATE_ENV) == before


def test_the_glass_boot_turns_agent_state_off(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import holdspeak.web_server as web_server

    from tests.e2e import glass_infra

    seen: dict[str, Any] = {}

    class _Server:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def start(self) -> str:
            seen["env"] = os.environ.get(AGENT_STATE_ENV)
            seen["home"] = os.environ.get("HOME")
            return "http://127.0.0.1:0"

    monkeypatch.setattr(web_server, "MeetingWebServer", _Server)
    glass_infra._boot(tmp_path, monkeypatch)
    assert seen["env"] == "off"
    assert seen["home"] == str(tmp_path / "home")


# ── G2: replyless boot boundaries refuse before the build and the hub ───

WORK = {
    "engine_reply": {"kind": "api", "method": "POST", "path": "/api/meetings/m1/intel/run", "body": {}},
    "cli_runner": {"kind": "api", "method": "POST", "path": "/api/channels/send", "body": {"id": "x"}},
}


def _atlas(tmp_path: Path, substitution: str, boundary: dict) -> Path:
    case = {
        "id": f"case.rig.{substitution}_after_work",
        "job": "j6",
        "edge_ids": [],
        "state_id": "state.rig",
        "applicability": "applicable",
        "preconditions": [],
        "setup": [WORK[substitution], boundary],
        "trigger": {"kind": "api", "method": "GET", "path": "/api/meetings", "body": None},
        "expected": {"predicate": {"kind": "protocol_field", "path": "/meetings", "value": []},
                     "observe_at": "protocol: GET /api/meetings"},
        "completion_bound_s": 5,
        "viewports": [1440],
    }
    path = tmp_path / "atlas.json"
    path.write_text(json.dumps({"schema_version": 1, "cases": [case], "states": []}))
    return path


@pytest.mark.parametrize("substitution", ["engine_reply", "cli_runner"])
@pytest.mark.parametrize("reply", [None, "", "  "])
@pytest.mark.parametrize("engine", ["none", "replayed"])
def test_a_work_step_before_a_replyless_boot_boundary_is_refused_with_no_hub_and_no_request(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, substitution: str, reply: str | None, engine: str,
) -> None:
    boundary = {"kind": "boundary", "substitute": substitution, "label": "a double that names no file",
                "adapter": "labelled-substitution"}
    if reply is not None:
        boundary["reply"] = reply
    hubs: list[Any] = []
    builds: list[Any] = []
    requests: list[Any] = []

    class _NoHub:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            hubs.append(kwargs)
            raise AssertionError("a hub was started for a refused case")

    monkeypatch.setattr(graph_walk, "Hub", _NoHub)
    monkeypatch.setattr(graph_walk, "_ensure_build", lambda: builds.append(1))
    monkeypatch.setattr(graph_walk.urllib.request, "urlopen", lambda *a, **k: requests.append(a))

    record = graph_walk.run_case(
        _atlas(tmp_path, substitution, boundary), f"case.rig.{substitution}_after_work",
        brain="muaddib", viewport=1440, out=tmp_path / "out",
        engine=engine, build=True, headless=False,
    )

    assert record["verdict"] == "blocked"
    assert any(f"a {substitution} boundary declares no `reply`" in n for n in record["notes"]), record["notes"]
    assert hubs == [] and builds == [] and requests == []


@pytest.mark.parametrize("substitution", ["engine_reply", "cli_runner"])
def test_the_schema_requires_a_reply_on_a_boot_boundary(substitution: str) -> None:
    schema = json.loads(SCHEMA.read_text())
    step = Draft202012Validator({"$defs": schema["$defs"], "$ref": "#/$defs/step"})
    replyless = {"kind": "boundary", "substitute": substitution, "label": "a double",
                 "adapter": "labelled-substitution"}
    assert list(step.iter_errors(replyless))
    assert list(step.iter_errors({**replyless, "reply": ""}))
    assert not list(step.iter_errors({**replyless, "reply": "tests/fixtures/philo5_summary_reply.json"}))


def test_every_declared_boot_boundary_in_the_active_atlases_names_its_file() -> None:
    def boundaries(node: Any):
        if isinstance(node, dict):
            if node.get("kind") == "boundary":
                yield node
            for value in node.values():
                yield from boundaries(value)
        elif isinstance(node, list):
            for value in node:
                yield from boundaries(value)

    for path in sorted(GRAPH.glob("atlas*.json")):
        if path.name == "atlas.schema.json":
            continue
        for case in json.loads(path.read_text()).get("cases", []):
            assert graph_walk.boot_boundary_problem(case) is None, (path.name, case["id"])
            for boundary in boundaries(case):
                if boundary.get("substitute") in {"engine_reply", "cli_runner", "import_transcriber"}:
                    assert str(boundary.get("reply") or "").strip(), (path.name, case["id"])


# ── G3 closes: one rig env, both rigs ────────────────────────────────────

RIG_VARS = ("GIT_CONFIG_NOSYSTEM", "HOLDSPEAK_TEST_NO_REAL_CLI", "GH_CONFIG_DIR", "XDG_CONFIG_HOME",
            "HOLDSPEAK_DESKTOP_NOTIFY", "HOLDSPEAK_CHANNEL_KEYSTORE_FILE", "HOLDSPEAK_PEOPLE_KEYSTORE_FILE",
            AGENT_STATE_ENV, "HOLDSPEAK_MACOS_CALENDAR", "TMUX_TMPDIR")
OWNER_ENV = {"GH_CONFIG_DIR": "/Users/owner/.config/gh", "XDG_CONFIG_HOME": "/Users/owner/.config",
             "PATH": "/usr/bin"}


def _assert_rig_env(env: dict[str, Any], home: Path) -> None:
    assert env["GIT_CONFIG_NOSYSTEM"] == "1"
    assert env["HOLDSPEAK_TEST_NO_REAL_CLI"] == "1"
    assert env["HOLDSPEAK_DESKTOP_NOTIFY"] == "0"
    assert env[AGENT_STATE_ENV] == "off"
    for name in ("GH_CONFIG_DIR", "XDG_CONFIG_HOME", "HOLDSPEAK_CHANNEL_KEYSTORE_FILE",
                 "HOLDSPEAK_PEOPLE_KEYSTORE_FILE"):
        assert Path(env[name]).is_relative_to(home), (name, env[name])


def test_the_graph_walk_hub_env_closes_every_g3_read(tmp_path: Path) -> None:
    env = graph_walk._isolated_hub_env(tmp_path, inherited=dict(OWNER_ENV))
    _assert_rig_env(env, graph_walk.guard_home(tmp_path))


def test_the_glass_boot_closes_every_g3_read(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import holdspeak.web_server as web_server

    from tests.e2e import glass_infra

    for key, value in OWNER_ENV.items():
        monkeypatch.setenv(key, value)
    seen: dict[str, Any] = {}

    class _Server:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def start(self) -> str:
            seen.update({name: os.environ.get(name) for name in RIG_VARS})
            return "http://127.0.0.1:0"

    monkeypatch.setattr(web_server, "MeetingWebServer", _Server)
    glass_infra._boot(tmp_path, monkeypatch)
    _assert_rig_env(seen, tmp_path / "home")


# ── desktop notifications: HOLDSPEAK_DESKTOP_NOTIFY ──────────────────────


def test_notify_posts_by_default_and_not_with_the_switch_off(monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak import desktop_notify

    posted: list[str] = []
    fake = lambda title, body, *, click_url=None: posted.append(body) or True  # noqa: E731
    monkeypatch.setattr(desktop_notify, "_notify_macos", fake)
    monkeypatch.setattr(desktop_notify, "_notify_linux", fake)
    monkeypatch.setattr(desktop_notify, "_PLATFORM", "Darwin")

    monkeypatch.delenv(desktop_notify.DESKTOP_NOTIFY_ENV, raising=False)
    assert desktop_notify.desktop_notify_enabled()
    assert desktop_notify.notify("HoldSpeak", "default on") is True
    monkeypatch.setenv(desktop_notify.DESKTOP_NOTIFY_ENV, "0")
    assert not desktop_notify.desktop_notify_enabled()
    assert desktop_notify.notify("HoldSpeak", "rig") is False
    assert posted == ["default on"]


def test_the_cocoa_paths_post_nothing_with_the_switch_off(monkeypatch: pytest.MonkeyPatch) -> None:
    import subprocess

    from holdspeak import desktop_notify, desktop_presence_cocoa

    monkeypatch.setenv(desktop_notify.DESKTOP_NOTIFY_ENV, "0")
    runs: list[Any] = []
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: runs.append(a))
    desktop_presence_cocoa._cocoa_notify({"title": "HoldSpeak", "body": "rig"})

    class _Renderer:
        class _commands:  # noqa: N801
            put = staticmethod(lambda item: runs.append(item))

    assert desktop_notify._notify_cocoa_child(_Renderer(), "HoldSpeak", "rig") is False
    assert runs == []


def test_the_mcp_notify_test_answers_not_posted_in_this_rig(monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak import desktop_notify
    from holdspeak.mcp.families import heartbeat

    monkeypatch.setenv(desktop_notify.DESKTOP_NOTIFY_ENV, "0")
    monkeypatch.setattr(heartbeat, "db_or", lambda _: None)
    monkeypatch.setattr(heartbeat, "observer_or", lambda _: None)
    monkeypatch.setattr(heartbeat, "HeartbeatService", lambda *a, **k: None)
    monkeypatch.setattr(desktop_notify, "_notify_macos", lambda *a, **k: pytest.fail("posted"))
    assert heartbeat.dispatch("heartbeat.notify_test", {}, None) == {
        "fired": False, "reason": "not posted in this rig"}


# ── channel keys: HOLDSPEAK_CHANNEL_KEYSTORE_FILE ────────────────────────


def test_with_the_file_named_the_channel_keys_never_reach_the_keychain(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    import keyring

    from holdspeak.services import channel_email, channel_slack
    from holdspeak.services.channel_key_file import CHANNEL_KEYSTORE_ENV

    path = tmp_path / "home" / "channel-keys.json"
    monkeypatch.setenv(CHANNEL_KEYSTORE_ENV, str(path))
    monkeypatch.setattr(keyring, "get_keyring", lambda: pytest.fail("the Keychain was reached"))

    channel_email.save_key("resend", "main", "re_key")
    assert channel_email.read_key("resend", "main") == "re_key"
    store = channel_slack.KEY_STORE()
    store.put("slot", "https://hooks.slack.com/services/x")
    assert store.get("slot") == "https://hooks.slack.com/services/x"
    assert oct(path.stat().st_mode & 0o777) == "0o600"
    with pytest.raises(channel_email.EmailKeyError) as missing:
        channel_email.read_key("resend", "other")
    assert missing.value.code == "email_key_missing"
    with pytest.raises(channel_slack.SlackKeyError) as slack_missing:
        store.get("other")
    assert slack_missing.value.code == "slack_webhook_missing"


def test_unset_the_channels_use_the_keychain(monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak.services import channel_email, channel_slack
    from holdspeak.services.channel_key_file import CHANNEL_KEYSTORE_ENV

    monkeypatch.delenv(CHANNEL_KEYSTORE_ENV, raising=False)
    monkeypatch.setattr(channel_email, "NativeEmailKeyStore", lambda: "email-keychain")
    monkeypatch.setattr(channel_slack, "NativeSlackKeyStore", lambda: "slack-keychain")
    assert channel_email.default_key_store() == "email-keychain"
    assert channel_slack.default_key_store() == "slack-keychain"


# ── nested `then` boundaries install their double before boot ────────────


def test_a_boundary_inside_a_then_installs_its_double_at_boot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    reply = "tests/fixtures/philo5_summary_reply.json"
    runner = "tests/fixtures/philo10_atlas/gh-posted.json"
    transcript = "tests/fixtures/philo16_import_transcript.json"
    trigger = {"kind": "api", "method": "GET", "path": "/api/meetings", "body": None, "then": [
        {"kind": "boundary", "substitute": "engine_reply", "label": "nested", "reply": reply},
        {"kind": "boundary", "substitute": "cli_runner", "label": "nested", "reply": runner},
        {"kind": "boundary", "substitute": "import_transcriber", "label": "nested", "reply": transcript},
    ]}
    case = {"id": "case.rig.nested", "job": "j6", "edge_ids": [], "state_id": "s", "applicability": "applicable",
            "preconditions": [], "setup": [], "trigger": trigger,
            "expected": {"predicate": {"kind": "protocol_field", "path": "/meetings", "value": []},
                         "observe_at": "protocol: GET /api/meetings"},
            "completion_bound_s": 5, "viewports": []}
    assert graph_walk.case_engine_replay(case) == reply
    assert graph_walk.case_cli_runner(case) == runner
    assert graph_walk.case_import_transcriber(case) == transcript

    booted: list[dict[str, Any]] = []

    class _Hub:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            booted.append(kwargs)
            raise RuntimeError("stop after the boot arguments")

    monkeypatch.setattr(graph_walk, "Hub", _Hub)
    atlas = tmp_path / "atlas.json"
    atlas.write_text(json.dumps({"schema_version": 1, "cases": [case], "states": []}))
    with pytest.raises(RuntimeError, match="stop after the boot arguments"):
        graph_walk.run_case(atlas, "case.rig.nested", brain="muaddib", viewport=1440,
                            out=tmp_path / "out", engine="replayed", build=False, headless=True)
    assert booted and booted[0]["engine_replay"] == REPO / reply
    assert booted[0]["cli_runner"] == REPO / runner
    assert booted[0]["import_transcriber"] == REPO / transcript
