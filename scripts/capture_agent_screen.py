#!/usr/bin/env python3
"""Record one agent screen for the screen-rule tests (Betterment AG7).

    uv run python scripts/capture_agent_screen.py <tmux target> <agent> <name> [--state STATE]

It reads the pane's visible screen and its title exactly as the hub's screen
watcher reads them (``agent_context.screen_watch.capture``), and writes
``tests/fixtures/agent_screens/<name>.txt`` (the screen) and ``<name>.json``
(the agent, the title, the state the person saw, and what the rules say now).
``tests/unit/test_screen_rules.py`` replays every recorded screen.

Record a REAL Claude Code or Codex screen only with the owner's consent: a
screen can hold his code and his words. Read the file before committing it.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from holdspeak.agent_context.screen_rules import read_screen  # noqa: E402
from holdspeak.agent_context.screen_watch import capture  # noqa: E402

OUT = REPO / "tests" / "fixtures" / "agent_screens"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("target", help="tmux target: a session name or a pane id (%%3)")
    parser.add_argument("agent", help="claude, codex, pi, gemini or opencode")
    parser.add_argument("name", help="the fixture's file name, without an extension")
    parser.add_argument("--state", help="the state the person saw (working, blocked, idle, unknown)")
    parser.add_argument("--source", default="", help="where the screen came from (one line)")
    args = parser.parse_args()
    seen = capture(args.target)
    if seen is None:
        print(f"tmux could not read {args.target!r}", file=sys.stderr)
        return 1
    screen, title = seen
    verdict = read_screen(args.agent, screen, title=title)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{args.name}.txt").write_text(screen + "\n", encoding="utf-8")
    meta = {
        "agent": args.agent,
        "title": title,
        "expected_state": args.state or (verdict.state if verdict else None),
        "rule_at_capture": verdict.rule if verdict else None,
        "source": args.source,
        "captured_at": datetime.now(timezone.utc).isoformat(),
    }
    (OUT / f"{args.name}.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{args.name}: {verdict.state if verdict else '-'} ({verdict.rule if verdict else 'no rules'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
