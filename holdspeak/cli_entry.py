"""The ``holdspeak`` console entry: a fast path for the agent hooks.

``holdspeak.main`` imports the whole product at module level (the
transcriber, the meeting session, the model clients): about 2.3 s cold. The
agents run two of its verbs on every hook event, under a hook timeout:
``holdspeak agent-hook ingest`` (the rider) and ``holdspeak gate hook`` (the
tool gate). Those two are dispatched here with only their own modules; every
other command goes to ``holdspeak.main.main`` unchanged (Conductor R3).
"""
from __future__ import annotations

import argparse
import sys
from typing import Optional, Sequence

#: The hook verbs that start without ``holdspeak.main``.
FAST_VERBS = (("agent-hook", "ingest"), ("gate", "hook"))


def _fast(argv: Sequence[str]) -> Optional[int]:
    if len(argv) < 2 or (argv[0], argv[1]) not in FAST_VERBS:
        return None
    parser = argparse.ArgumentParser(prog="holdspeak")
    sub = parser.add_subparsers(dest="command")
    if argv[0] == "agent-hook":
        from .commands.agent_hook import build_argparse_subparsers, run_agent_hook_command

        build_argparse_subparsers(sub.add_parser("agent-hook"))
        return run_agent_hook_command(parser.parse_args(list(argv)))
    from .commands.gate import build_gate_subparsers, run_gate_command

    build_gate_subparsers(sub.add_parser("gate"))
    return run_gate_command(parser.parse_args(list(argv)))


def main() -> None:
    code = _fast(sys.argv[1:])
    if code is not None:
        raise SystemExit(code)
    from .main import main as full_main

    full_main()


if __name__ == "__main__":
    main()
