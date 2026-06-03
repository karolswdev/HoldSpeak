"""HS-34-03: lock the agent_context public surface after the package split.

The 1,381-line `agent_context.py` module became an `agent_context/` package
(_common / models / hs_context / hooks / sessions) with a full re-export
`__init__`. This guards that every name callers/tests rely on is still importable
from `holdspeak.agent_context`, that the two dataclasses kept `frozen=True`, and
that `shutil` is re-exposed for the tmux monkeypatch.
"""

from __future__ import annotations

import dataclasses

import holdspeak.agent_context as agent_context

# The names external callers + the test suite import from the package today.
_PUBLIC = {
    # models
    "AgentSession",
    "AGENT_CONTEXT_FILE",
    "HS_CONTEXT_FILES",
    "DEFAULT_CONTEXT_HARD_FILE_MAX_BYTES",
    # sessions
    "ingest_agent_hook_event",
    "get_recent_agent_session",
    "get_recent_awaiting_agent_session",
    "get_selected_awaiting_agent_session",
    "select_awaiting_agent_session",
    "select_next_awaiting_agent_session",
    "clear_agent_session_response",
    "pin_agent_session",
    "clear_stale_agent_sessions",
    "set_agent_session_summary",
    "list_agent_sessions",
    "extract_last_assistant_text",
    "looks_like_agent_question",
    # hs_context
    "RepoRoot",
    "detect_repo_root",
    "load_hs_project_context",
    "compact_hs_project_context",
    "render_hs_context_for_prompt",
    # hooks
    "claude_hook_template",
    "codex_hook_template",
    "detect_tmux_context",
}


def test_public_surface_is_importable() -> None:
    missing = sorted(n for n in _PUBLIC if not hasattr(agent_context, n))
    assert not missing, f"agent_context no longer exports: {missing}"


def test_public_names_are_in_dunder_all() -> None:
    not_exported = sorted(n for n in _PUBLIC if n not in agent_context.__all__)
    assert not not_exported, f"missing from __all__: {not_exported}"


def test_dataclasses_stay_frozen() -> None:
    assert dataclasses.is_dataclass(agent_context.AgentSession)
    assert agent_context.AgentSession.__dataclass_params__.frozen
    assert dataclasses.is_dataclass(agent_context.RepoRoot)
    assert agent_context.RepoRoot.__dataclass_params__.frozen


def test_shutil_reexposed_for_monkeypatch() -> None:
    # The tmux tests patch holdspeak.agent_context.shutil.which.
    assert hasattr(agent_context, "shutil")
    assert hasattr(agent_context.shutil, "which")
