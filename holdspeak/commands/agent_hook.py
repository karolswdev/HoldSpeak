"""`holdspeak agent-hook` CLI for Claude/Codex hook ingestion."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, TextIO

from ..agent_context import (
    claude_hook_template,
    codex_hook_template,
    get_recent_agent_session,
    ingest_agent_hook_event,
    list_agent_sessions,
    load_hs_project_context,
    render_hs_context_for_prompt,
)
from ..agent_context.hooks import (
    AGENT_HOOK_SETTINGS_PATHS,
    install_agent_hooks,
    uninstall_agent_hooks,
)

_EXIT_OK = 0
_EXIT_USAGE = 2


def run_agent_hook_command(args, *, stdin: TextIO | None = None, stream: TextIO | None = None) -> int:
    out = stream if stream is not None else sys.stdout
    err = sys.stderr
    action = getattr(args, "agent_hook_action", None)

    if action == "ingest":
        return _cmd_ingest(args, stdin=stdin or sys.stdin, out=out, err=err)
    if action == "latest":
        return _cmd_latest(args, out=out)
    if action == "templates":
        return _cmd_templates(args, out=out)
    if action == "context":
        return _cmd_context(args, out=out)
    if action == "install":
        return _cmd_install(args, out=out, err=err)
    if action == "uninstall":
        return _cmd_uninstall(args, out=out, err=err)

    print(
        "usage: holdspeak agent-hook <ingest|latest|templates|context|install|uninstall> ...",
        file=out,
    )
    return _EXIT_USAGE


def _cmd_ingest(args, *, stdin: TextIO, out: TextIO, err: TextIO) -> int:
    try:
        payload = json.loads(stdin.read() or "{}")
    except json.JSONDecodeError as exc:
        print(f"error: invalid hook JSON: {exc}", file=err)
        return _EXIT_USAGE
    if not isinstance(payload, dict):
        print("error: hook payload must be a JSON object", file=err)
        return _EXIT_USAGE

    try:
        session = ingest_agent_hook_event(
            agent=args.agent,
            payload=payload,
            state_path=Path(args.state_path).expanduser() if args.state_path else None,
            capture_messages=bool(getattr(args, "capture_messages", False)),
        )
    except ValueError as exc:
        if getattr(args, "print_summary", False):
            print(f"warning: dropped malformed hook payload: {exc}", file=err)
        return _EXIT_OK

    if getattr(args, "print_summary", False):
        print(json.dumps(session.to_dict(), indent=2, sort_keys=True), file=out)
    return _EXIT_OK


def _cmd_latest(args, *, out: TextIO) -> int:
    state_path = Path(args.state_path).expanduser() if args.state_path else None
    if getattr(args, "all", False):
        sessions = list_agent_sessions(state_path=state_path, agent=args.agent)
        print(json.dumps([session.to_dict() for session in sessions], indent=2, sort_keys=True), file=out)
        return _EXIT_OK

    session = get_recent_agent_session(
        agent=args.agent,
        state_path=state_path,
        max_age_seconds=int(args.max_age_seconds),
    )
    if session is None:
        print("no recent agent session", file=out)
        return _EXIT_OK
    print(json.dumps(session.to_dict(), indent=2, sort_keys=True), file=out)
    return _EXIT_OK


def _cmd_templates(args, *, out: TextIO) -> int:
    agent = args.agent
    capture_messages = bool(getattr(args, "capture_messages", False))
    payload: dict[str, Any]
    if agent == "claude":
        payload = claude_hook_template(capture_messages=capture_messages)
    elif agent == "codex":
        payload = codex_hook_template(capture_messages=capture_messages)
    else:
        payload = {
            "claude": claude_hook_template(capture_messages=capture_messages),
            "codex": codex_hook_template(capture_messages=capture_messages),
        }
    print(json.dumps(payload, indent=2, sort_keys=True), file=out)
    return _EXIT_OK


def _cmd_context(args, *, out: TextIO) -> int:
    project_root = Path(args.project).expanduser().resolve()
    context = load_hs_project_context(project_root)
    if args.format == "json":
        print(json.dumps(context, indent=2, sort_keys=True), file=out)
    else:
        rendered = render_hs_context_for_prompt(context)
        print(rendered or f"no .hs context found at {project_root / '.hs'}", file=out)
    return _EXIT_OK


def _install_targets(args) -> list[tuple[str, Path]]:
    """(agent, settings_path) pairs for install/uninstall. `--settings-path`
    overrides the destination and requires a single --agent."""
    agent = getattr(args, "agent", "all") or "all"
    override = getattr(args, "settings_path", None)
    if override:
        if agent == "all":
            raise ValueError("--settings-path requires --agent claude or --agent codex")
        return [(agent, Path(override).expanduser())]
    agents = ["claude", "codex"] if agent == "all" else [agent]
    return [(a, Path(AGENT_HOOK_SETTINGS_PATHS[a]).expanduser()) for a in agents]


def _cmd_install(args, *, out: TextIO, err: TextIO) -> int:
    """HSM-17-02: the one-command "inject ourselves" step — idempotent."""
    capture_messages = bool(getattr(args, "capture_messages", False))
    try:
        targets = _install_targets(args)
    except ValueError as exc:
        print(f"error: {exc}", file=err)
        return _EXIT_USAGE
    for agent, settings_path in targets:
        template = (
            claude_hook_template(capture_messages=capture_messages)
            if agent == "claude"
            else codex_hook_template(capture_messages=capture_messages)
        )
        try:
            result = install_agent_hooks(settings_path, template)
        except ValueError as exc:
            print(f"error: {exc}", file=err)
            return 1
        verb = "created" if result["created_file"] else "updated"
        events = ", ".join(result["installed_events"])
        print(f"{agent}: {verb} {result['path']} ({events})", file=out)
    print(
        "Hooks take effect for NEW coder sessions. Remove them any time with "
        "`holdspeak agent-hook uninstall`.",
        file=out,
    )
    return _EXIT_OK


def _cmd_uninstall(args, *, out: TextIO, err: TextIO) -> int:
    try:
        targets = _install_targets(args)
    except ValueError as exc:
        print(f"error: {exc}", file=err)
        return _EXIT_USAGE
    for agent, settings_path in targets:
        try:
            result = uninstall_agent_hooks(settings_path)
        except ValueError as exc:
            print(f"error: {exc}", file=err)
            return 1
        if result["file_missing"]:
            print(f"{agent}: nothing installed at {result['path']}", file=out)
        elif result["removed_events"]:
            events = ", ".join(result["removed_events"])
            print(f"{agent}: removed our hooks from {result['path']} ({events})", file=out)
        else:
            print(f"{agent}: no HoldSpeak hooks found in {result['path']}", file=out)
    return _EXIT_OK


def build_argparse_subparsers(agent_hook_parser) -> None:
    subparsers = agent_hook_parser.add_subparsers(dest="agent_hook_action")

    ingest = subparsers.add_parser(
        "ingest",
        help="Read one Claude/Codex hook JSON payload from stdin and record session context",
    )
    ingest.add_argument("--agent", choices=["claude", "codex"], required=True)
    ingest.add_argument("--state-path", help="Override session registry path (test/debug)")
    ingest.add_argument(
        "--capture-messages",
        action="store_true",
        help=(
            "Opt in to bounded assistant-message capture from transcript_path. "
            "Stores recent assistant text locally for contextual replies."
        ),
    )
    ingest.add_argument(
        "--print-summary",
        action="store_true",
        help="Print normalized session JSON. Do not use inside hooks unless you want hook output.",
    )

    latest = subparsers.add_parser(
        "latest",
        help="Show the latest recorded Claude/Codex session context",
    )
    latest.add_argument("--agent", choices=["claude", "codex"])
    latest.add_argument("--state-path", help="Override session registry path (test/debug)")
    latest.add_argument(
        "--max-age-seconds",
        type=int,
        default=1800,
        help="Only return sessions updated within this many seconds (default: 1800)",
    )
    latest.add_argument("--all", action="store_true", help="List all recorded sessions")

    templates = subparsers.add_parser(
        "templates",
        help="Print hook configuration templates for Claude Code or Codex",
    )
    templates.add_argument("--agent", choices=["claude", "codex", "all"], default="all")
    templates.add_argument(
        "--capture-messages",
        action="store_true",
        help=(
            "Include --capture-messages in generated hooks. This stores bounded "
            "assistant replies locally and should be enabled only after review."
        ),
    )

    context = subparsers.add_parser(
        "context",
        help="Render a repo's .hs project context",
    )
    context.add_argument("--project", default=".", help="Project root to inspect (default: cwd)")
    context.add_argument("--format", choices=["text", "json"], default="text")

    install = subparsers.add_parser(
        "install",
        help=(
            "Wire the HoldSpeak hooks into your Claude Code / Codex config "
            "(idempotent; foreign hooks preserved; reverse with uninstall)"
        ),
    )
    install.add_argument("--agent", choices=["claude", "codex", "all"], default="all")
    install.add_argument(
        "--capture-messages",
        action="store_true",
        help=(
            "Include --capture-messages in the installed hooks (stores bounded "
            "assistant replies locally; enable only after review)."
        ),
    )
    install.add_argument(
        "--settings-path",
        help="Override the destination settings file (requires a single --agent)",
    )

    uninstall = subparsers.add_parser(
        "uninstall",
        help="Remove the HoldSpeak hooks from your Claude Code / Codex config",
    )
    uninstall.add_argument("--agent", choices=["claude", "codex", "all"], default="all")
    uninstall.add_argument(
        "--settings-path",
        help="Override the destination settings file (requires a single --agent)",
    )
