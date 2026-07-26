"""`holdspeak gate` CLI (HS-104-02): the tool-call gate's owner verbs.

- ``gate hook`` — the PreToolUse forwarder Claude Code invokes: stdin
  JSON in, decision out. Inert when the gate is not armed for the
  (cwd, tool); fail-closed once it is.
- ``gate install`` — PRINTS the hook block for the user to add to
  ``~/.claude/settings.json``. Never edits another app's config.
- ``gate arm`` / ``gate disarm`` — the master switch.
- ``gate allow --repo PATH [--tool NAME]`` / ``gate revoke --repo
  PATH`` — the per-repo matcher, the second opt-in.
- ``gate status`` — both opt-ins, plainly.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TextIO

from ..coder_gate import (
    DEFAULT_TOOLS,
    GateConfig,
    install_block,
    load_gate_config,
    run_hook,
    save_gate_config,
)

_EXIT_OK = 0
_EXIT_USAGE = 2


def build_gate_subparsers(parser) -> None:
    sub = parser.add_subparsers(dest="gate_action")
    sub.add_parser("hook", help="PreToolUse forwarder (stdin JSON in, decision out)")
    sub.add_parser("install", help="Print the hook block to add to ~/.claude/settings.json")
    sub.add_parser("arm", help="Flip the master switch on (repos still gate individually)")
    sub.add_parser("disarm", help="Flip the master switch off")
    allow = sub.add_parser("allow", help="Hold a tool for a repo (the second opt-in)")
    allow.add_argument("--repo", required=True, help="Repo path whose agent calls are held")
    allow.add_argument(
        "--tool",
        action="append",
        default=None,
        help=f"Tool to hold (repeatable; default: {', '.join(DEFAULT_TOOLS)})",
    )
    revoke = sub.add_parser("revoke", help="Stop holding a repo's calls")
    revoke.add_argument("--repo", required=True)
    status = sub.add_parser("status", help="Show both opt-ins")
    status.add_argument("--json", action="store_true")


def run_gate_command(args, *, stdin: TextIO | None = None, stream: TextIO | None = None) -> int:
    out = stream if stream is not None else sys.stdout
    action = getattr(args, "gate_action", None)

    if action == "hook":
        return _cmd_hook(stdin=stdin or sys.stdin, out=out)
    if action == "install":
        print(
            "Add this to ~/.claude/settings.json yourself (merging with any\n"
            "existing hooks). HoldSpeak never edits another app's config:\n",
            file=out,
        )
        print(install_block(), file=out)
        return _EXIT_OK
    if action == "arm":
        config = load_gate_config()
        config.armed = True
        path = save_gate_config(config)
        print(f"Gate armed ({path}).", file=out)
        if not config.repos:
            print(
                "No repos are held yet; the gate stays inert until "
                "`holdspeak gate allow --repo <path>`.",
                file=out,
            )
        return _EXIT_OK
    if action == "disarm":
        config = load_gate_config()
        config.armed = False
        save_gate_config(config)
        print("Gate disarmed. Every hook arrival is inert.", file=out)
        return _EXIT_OK
    if action == "allow":
        config = load_gate_config()
        repo = str(Path(args.repo).expanduser().resolve())
        tools = [t for t in (args.tool or list(DEFAULT_TOOLS)) if str(t).strip()]
        config.repos[repo] = tools
        save_gate_config(config)
        held = ", ".join(tools)
        print(f"Holding {held} for {repo}.", file=out)
        if not config.armed:
            print("The master switch is off; `holdspeak gate arm` completes the opt-in.", file=out)
        return _EXIT_OK
    if action == "revoke":
        config = load_gate_config()
        repo = str(Path(args.repo).expanduser().resolve())
        if config.repos.pop(repo, None) is None:
            print(f"{repo} was not held.", file=out)
        else:
            save_gate_config(config)
            print(f"No longer holding {repo}.", file=out)
        return _EXIT_OK
    if action == "status":
        config = load_gate_config()
        if getattr(args, "json", False):
            print(json.dumps(config.to_dict(), indent=2, sort_keys=True), file=out)
        else:
            print(f"Master switch: {'armed' if config.armed else 'off'}", file=out)
            if config.repos:
                for repo, tools in sorted(config.repos.items()):
                    print(f"  holds {', '.join(tools)} in {repo}", file=out)
            else:
                print("  no repos held", file=out)
        return _EXIT_OK

    print("usage: holdspeak gate <hook|install|arm|disarm|allow|revoke|status> ...", file=out)
    return _EXIT_USAGE


def _cmd_hook(*, stdin: TextIO, out: TextIO) -> int:
    """Claude Code's PreToolUse entry. Every failure inside an ARMED
    match is a deny (fail-closed); a payload we cannot even parse
    cannot be matched, so it is inert — the unarmed posture must
    never break the agent."""
    try:
        payload = json.loads(stdin.read() or "{}")
    except json.JSONDecodeError:
        return _EXIT_OK
    if not isinstance(payload, dict):
        return _EXIT_OK
    decision = run_hook(payload)
    output = decision.to_hook_output()
    if output is not None:
        print(json.dumps(output), file=out)
    return _EXIT_OK
