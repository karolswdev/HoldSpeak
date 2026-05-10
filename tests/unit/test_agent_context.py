from __future__ import annotations

import io
import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from holdspeak.agent_context import (
    claude_hook_template,
    clear_agent_session_response,
    codex_hook_template,
    detect_repo_root,
    extract_last_assistant_text,
    get_recent_awaiting_agent_session,
    get_recent_agent_session,
    ingest_agent_hook_event,
    load_hs_project_context,
    looks_like_agent_question,
    render_hs_context_for_prompt,
    set_agent_session_summary,
)
from holdspeak.commands.agent_hook import run_agent_hook_command
from holdspeak.plugins.dictation.project_root import detect_project_for_cwd


def test_ingest_agent_hook_event_records_repo_context(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / "pyproject.toml").write_text('[project]\nname = "demo-app"\n', encoding="utf-8")
    state = tmp_path / "state.json"

    session = ingest_agent_hook_event(
        agent="claude",
        payload={
            "session_id": "abc",
            "hook_event_name": "SessionStart",
            "cwd": str(repo),
            "transcript_path": "/tmp/transcript.jsonl",
            "model": "claude-sonnet",
        },
        state_path=state,
        now=datetime(2026, 5, 10, tzinfo=timezone.utc),
    )

    assert session.agent == "claude"
    assert session.cwd == str(repo)
    assert session.repo_root == str(repo)
    assert session.repo_anchor == "git"
    assert session.project_name == "demo-app"

    latest = get_recent_agent_session(state_path=state, max_age_seconds=10**9)
    assert latest is not None
    assert latest.session_id == "abc"


def test_cwd_changed_prefers_new_cwd(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    nested = repo / "src"
    nested.mkdir(parents=True)
    (repo / ".git").mkdir()
    state = tmp_path / "state.json"

    session = ingest_agent_hook_event(
        agent="claude",
        payload={
            "session_id": "abc",
            "hook_event_name": "CwdChanged",
            "cwd": str(tmp_path),
            "old_cwd": str(tmp_path),
            "new_cwd": str(nested),
        },
        state_path=state,
    )

    assert session.cwd == str(nested)
    assert session.repo_root == str(repo)


def test_extract_last_assistant_text_from_claude_fixture() -> None:
    path = Path("tests/fixtures/agent_transcripts/claude_question.jsonl")

    text = extract_last_assistant_text("claude", path)

    assert text == "I found an obsolete file. Should I delete `tmp/old.py`?"
    assert looks_like_agent_question(text or "") is True


def test_extract_last_assistant_text_from_mixed_content_fixture() -> None:
    path = Path("tests/fixtures/agent_transcripts/claude_mixed.jsonl")

    text = extract_last_assistant_text("claude", path)

    assert text == "I will inspect the repo. Do you want me to update the README next?"


def test_extract_last_assistant_text_from_codex_fixture() -> None:
    path = Path("tests/fixtures/agent_transcripts/codex_question.jsonl")

    text = extract_last_assistant_text("codex", path)

    assert text == "The tests pass. Should I run the full suite now?"


def test_ingest_capture_messages_is_explicit_and_bounded(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    transcript = tmp_path / "transcript.jsonl"
    transcript.write_text(
        json.dumps(
            {
                "type": "assistant",
                "message": {
                    "role": "assistant",
                    "content": [{"type": "text", "text": "Should I proceed?"}],
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    state = tmp_path / "state.json"

    without_capture = ingest_agent_hook_event(
        agent="claude",
        payload={
            "session_id": "abc",
            "hook_event_name": "Stop",
            "cwd": str(repo),
            "transcript_path": str(transcript),
        },
        state_path=state,
    )
    with_capture = ingest_agent_hook_event(
        agent="claude",
        payload={
            "session_id": "abc",
            "hook_event_name": "Stop",
            "cwd": str(repo),
            "transcript_path": str(transcript),
        },
        state_path=state,
        capture_messages=True,
        now=datetime(2026, 5, 10, tzinfo=timezone.utc),
    )

    assert without_capture.last_assistant_text is None
    assert with_capture.last_assistant_text == "Should I proceed?"
    assert with_capture.last_assistant_text_at == "2026-05-10T00:00:00Z"
    assert with_capture.awaiting_response is True
    assert with_capture.capture_messages is True


def test_user_prompt_submit_clears_captured_assistant_text(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    state = tmp_path / "state.json"
    ingest_agent_hook_event(
        agent="codex",
        payload={
            "session_id": "abc",
            "hook_event_name": "Stop",
            "cwd": str(repo),
            "last_assistant_text": "ignored",
        },
        state_path=state,
    )
    # Seed the previous state directly with captured message fields; this
    # verifies the clear-on-next-user-prompt behavior independent of capture.
    raw = json.loads(state.read_text(encoding="utf-8"))
    raw["sessions"]["codex:abc"]["last_assistant_text"] = "Should I run tests?"
    raw["sessions"]["codex:abc"]["last_assistant_text_at"] = "2026-05-10T00:00:00Z"
    raw["sessions"]["codex:abc"]["awaiting_response"] = True
    raw["sessions"]["codex:abc"]["summary"] = {"provider": "codex", "summary": "Agent is waiting."}
    state.write_text(json.dumps(raw), encoding="utf-8")

    session = ingest_agent_hook_event(
        agent="codex",
        payload={
            "session_id": "abc",
            "hook_event_name": "UserPromptSubmit",
            "cwd": str(repo),
            "prompt": "yes run tests",
        },
        state_path=state,
    )

    assert session.last_assistant_text is None
    assert session.last_assistant_text_at is None
    assert session.summary is None
    assert session.awaiting_response is False


def test_prompt_capture_is_bounded(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    state = tmp_path / "state.json"
    prompt = "x" * 5_000

    session = ingest_agent_hook_event(
        agent="codex",
        payload={
            "session_id": "abc",
            "hook_event_name": "UserPromptSubmit",
            "cwd": str(repo),
            "prompt": prompt,
        },
        state_path=state,
    )

    assert session.last_prompt is not None
    assert len(session.last_prompt) == 4_096
    assert session.last_prompt == prompt[-4_096:]


def test_recent_awaiting_session_is_project_scoped(tmp_path: Path) -> None:
    repo_a = tmp_path / "repo-a"
    repo_b = tmp_path / "repo-b"
    repo_a.mkdir()
    repo_b.mkdir()
    (repo_a / ".git").mkdir()
    (repo_b / ".git").mkdir()
    state = tmp_path / "state.json"
    for repo, session_id, text, minute in (
        (repo_a, "a", "Should I update A?", 1),
        (repo_b, "b", "Should I update B?", 2),
    ):
        transcript = tmp_path / f"{session_id}.jsonl"
        transcript.write_text(json.dumps({"role": "assistant", "content": text}) + "\n", encoding="utf-8")
        ingest_agent_hook_event(
            agent="codex",
            payload={
                "session_id": session_id,
                "hook_event_name": "Stop",
                "cwd": str(repo),
                "transcript_path": str(transcript),
            },
            state_path=state,
            now=datetime(2026, 5, 10, 0, minute, tzinfo=timezone.utc),
            capture_messages=True,
        )

    session = get_recent_awaiting_agent_session(
        project_root=repo_a,
        state_path=state,
        max_age_seconds=10**9,
    )

    assert session is not None
    assert session.session_id == "a"
    assert session.last_assistant_text == "Should I update A?"


def test_clear_agent_session_response_clears_specific_capture(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    transcript = tmp_path / "transcript.jsonl"
    transcript.write_text(json.dumps({"role": "assistant", "content": "Proceed?"}) + "\n", encoding="utf-8")
    state = tmp_path / "state.json"
    ingest_agent_hook_event(
        agent="claude",
        payload={
            "session_id": "abc",
            "hook_event_name": "Stop",
            "cwd": str(repo),
            "transcript_path": str(transcript),
        },
        state_path=state,
        capture_messages=True,
    )

    cleared = clear_agent_session_response(
        agent="claude",
        session_id="abc",
        state_path=state,
        now=datetime(2026, 5, 10, tzinfo=timezone.utc),
    )
    latest = get_recent_agent_session(state_path=state, max_age_seconds=10**9)

    assert cleared is not None
    assert cleared.last_assistant_text is None
    assert cleared.summary is None
    assert cleared.awaiting_response is False
    assert latest is not None
    assert latest.hook_event_name == "ManualClear"


def test_set_agent_session_summary_persists_derived_context(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    state = tmp_path / "state.json"
    ingest_agent_hook_event(
        agent="codex",
        payload={
            "session_id": "abc",
            "hook_event_name": "Stop",
            "cwd": str(repo),
        },
        state_path=state,
    )

    updated = set_agent_session_summary(
        agent="codex",
        session_id="abc",
        summary={
            "provider": "codex",
            "summary": "Codex is waiting for confirmation.",
            "generated_at": "2026-05-10T00:00:00Z",
        },
        state_path=state,
        now=datetime(2026, 5, 10, 0, 1, tzinfo=timezone.utc),
    )
    latest = get_recent_agent_session(state_path=state, max_age_seconds=10**9)

    assert updated is not None
    assert updated.hook_event_name == "SummaryGenerated"
    assert updated.summary is not None
    assert updated.summary["summary"] == "Codex is waiting for confirmation."
    assert latest is not None
    assert latest.summary == updated.summary


def test_load_hs_project_context(tmp_path: Path) -> None:
    hs_dir = tmp_path / ".hs"
    hs_dir.mkdir()
    (hs_dir / "instructions.md").write_text("Rewrite as a coding task.", encoding="utf-8")
    (hs_dir / "context.md").write_text("This is a Python repo.", encoding="utf-8")
    (hs_dir / "ignore").write_text("# comment\n.env\nsecrets/\n", encoding="utf-8")

    context = load_hs_project_context(tmp_path)
    rendered = render_hs_context_for_prompt(context)

    assert context["exists"] is True
    assert context["ignore"] == [".env", "secrets/"]
    assert "## .hs/instructions.md" in rendered
    assert "Rewrite as a coding task." in rendered
    assert "## .hs/ignore" in rendered


def test_load_hs_project_context_supports_flat_dotfiles(tmp_path: Path) -> None:
    (tmp_path / ".hs_context").write_text("Flat context works.", encoding="utf-8")
    (tmp_path / ".hs_issues").write_text("Fix the dictation cockpit.", encoding="utf-8")

    context = load_hs_project_context(tmp_path)
    compact = render_hs_context_for_prompt(context)

    assert context["exists"] is True
    assert context["files"]["context.md"]["source"] == "flat"
    assert context["files"]["context.md"]["read_only"] is True
    assert context["flat_files"][".hs_context"]["canonical_name"] == "context.md"
    assert "Flat context works." in compact
    assert "Fix the dictation cockpit." in compact


def test_hs_directory_takes_precedence_over_flat_dotfiles(tmp_path: Path) -> None:
    (tmp_path / ".hs_context").write_text("Flat context", encoding="utf-8")
    hs_dir = tmp_path / ".hs"
    hs_dir.mkdir()
    (hs_dir / "context.md").write_text("Directory context", encoding="utf-8")

    context = load_hs_project_context(tmp_path)

    assert context["files"]["context.md"]["content"] == "Directory context"
    assert context["files"]["context.md"]["source"] == "directory"
    assert context["flat_files"][".hs_context"]["content"] == "Flat context"


def test_hs_project_context_skips_binary_large_and_secret_files(tmp_path: Path) -> None:
    hs_dir = tmp_path / ".hs"
    hs_dir.mkdir()
    (hs_dir / "context.md").write_bytes(b"abc\x00def")
    (hs_dir / "issues.md").write_text("sk-secret-key-value-1234567890", encoding="utf-8")
    (hs_dir / "memory.md").write_text("x" * 130_000, encoding="utf-8")

    context = load_hs_project_context(tmp_path)
    reasons = {entry["reason"] for entry in context["skipped"]}

    assert context["files"] == {}
    assert {"binary", "possible_secret", "too_large"} <= reasons
    assert len(context["warnings"]) == 3


def test_detect_repo_root_supports_flat_hs_context_marker(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    nested = root / "a" / "b"
    nested.mkdir(parents=True)
    (root / ".hs_context").write_text("flat", encoding="utf-8")

    detected = detect_repo_root(nested)

    assert detected is not None
    assert detected.root == root
    assert detected.anchor == "holdspeak-flat"


def test_templates_use_silent_ingest_command() -> None:
    claude = json.dumps(claude_hook_template())
    codex = json.dumps(codex_hook_template())

    assert "holdspeak agent-hook ingest --agent claude" in claude
    assert "holdspeak agent-hook ingest --agent codex" in codex
    assert "--print-summary" not in claude
    assert "--print-summary" not in codex


def test_templates_prefer_absolute_holdspeak_path(monkeypatch) -> None:
    monkeypatch.setattr("holdspeak.agent_context.shutil.which", lambda _name: "/opt/bin/holdspeak")

    claude = json.dumps(claude_hook_template())

    assert "/opt/bin/holdspeak agent-hook ingest --agent claude" in claude


def test_templates_can_opt_into_message_capture() -> None:
    claude = json.dumps(claude_hook_template(capture_messages=True))

    assert "--capture-messages" in claude


def test_hs_context_uses_per_file_budget(tmp_path: Path) -> None:
    hs_dir = tmp_path / ".hs"
    hs_dir.mkdir()
    (hs_dir / "instructions.md").write_text("a" * 100, encoding="utf-8")
    (hs_dir / "context.md").write_text("context survives", encoding="utf-8")

    context = load_hs_project_context(tmp_path, max_bytes=80, per_file_max_bytes=32)

    assert context["truncated"] is True
    assert len(context["files"]["instructions.md"]["content"]) == 32
    assert context["files"]["context.md"]["content"] == "context survives"


def test_agent_hook_ingest_command_is_silent_by_default(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    state = tmp_path / "state.json"
    stdout = io.StringIO()
    stdin = io.StringIO(json.dumps({"session_id": "codex-1", "cwd": str(repo)}))
    args = SimpleNamespace(
        agent_hook_action="ingest",
        agent="codex",
        state_path=str(state),
        print_summary=False,
    )

    rc = run_agent_hook_command(args, stdin=stdin, stream=stdout)

    assert rc == 0
    assert stdout.getvalue() == ""
    assert get_recent_agent_session(agent="codex", state_path=state, max_age_seconds=10**9) is not None


def test_agent_hook_ingest_drops_malformed_payload_silently(tmp_path: Path) -> None:
    stdout = io.StringIO()
    stdin = io.StringIO(json.dumps({"hook_event_name": "SessionStart"}))
    args = SimpleNamespace(
        agent_hook_action="ingest",
        agent="codex",
        state_path=str(tmp_path / "state.json"),
        print_summary=False,
    )

    rc = run_agent_hook_command(args, stdin=stdin, stream=stdout)

    assert rc == 0
    assert stdout.getvalue() == ""


def test_agent_hook_templates_command_prints_json() -> None:
    stdout = io.StringIO()
    args = SimpleNamespace(agent_hook_action="templates", agent="claude")

    rc = run_agent_hook_command(args, stream=stdout)
    payload = json.loads(stdout.getvalue())

    assert rc == 0
    assert "SessionStart" in payload["hooks"]


def test_project_detection_prefers_recent_agent_session(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    nested = repo / "src"
    nested.mkdir(parents=True)
    (repo / ".hs").mkdir()

    monkeypatch.setattr(
        "holdspeak.agent_context.get_recent_agent_session",
        lambda: SimpleNamespace(cwd=str(nested)),
    )

    project = detect_project_for_cwd()

    assert project is not None
    assert project["root"] == str(repo)
    assert project["anchor"] == "holdspeak"
