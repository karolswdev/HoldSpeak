"""`holdspeak cadence …` (CAD-1-05).

The first human surface for the Cadence Engine: inspect what it would push, before
any web/Telegram UI exists. `run-now` runs one synchronous tick (works even when
cadence is disabled, so it's testable/dogfoodable) and prints the projected, scored,
and due loops. No external side effects.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from typing import Optional, TextIO

from ..config import Config
from ..db import get_database


def _out(stream: Optional[TextIO]) -> TextIO:
    return stream or sys.stdout


def run_cadence_command(args, *, stream: Optional[TextIO] = None, db=None, config=None) -> int:
    out = _out(stream)
    db = db if db is not None else get_database()
    config = config if config is not None else Config.load()
    action = getattr(args, "cadence_action", None) or "status"

    if action == "status":
        return _cmd_status(out, db, config)
    if action == "loops":
        return _cmd_loops(out, db, as_json=getattr(args, "json", False),
                          include_all=getattr(args, "all", False))
    if action == "run-now":
        return _cmd_run_now(out, db, config, as_json=getattr(args, "json", False))
    if action == "brief":
        return _cmd_brief(out, db, as_json=getattr(args, "json", False))
    if action == "closeout":
        return _cmd_closeout(out, db, as_json=getattr(args, "json", False))
    if action == "audit":
        return _cmd_audit(out, db, path=getattr(args, "out", None))
    print(f"Unknown cadence action: {action}", file=sys.stderr)
    return 2


def _cmd_audit(out: TextIO, db, *, path: Optional[str]) -> int:
    from ..cadence.audit import export_audit

    snapshot = export_audit(db)
    text = json.dumps(snapshot, indent=2)
    if path:
        from pathlib import Path

        Path(path).write_text(text, encoding="utf-8")
        print(f"Local cadence audit written to {path} "
              f"({snapshot['totals']['loops']} loops, {len(snapshot['nudges'])} nudges).", file=out)
    else:
        print(text, file=out)
    return 0


def _cmd_closeout(out: TextIO, db, *, as_json: bool) -> int:
    from ..cadence.closeout import build_closeout, render_closeout_text

    co = build_closeout(db)
    if as_json:
        print(json.dumps({
            "date": co.date, "open_count": co.open_count, "summary": co.summary,
            "recs": [{"title": r.loop.title, "action": r.action, "severity": r.severity,
                      "reason": r.reason} for r in co.recs],
        }, indent=2), file=out)
        return 0
    print(render_closeout_text(co), file=out)
    return 0


def _cmd_brief(out: TextIO, db, *, as_json: bool) -> int:
    from ..cadence.brief import build_brief, render_brief_text

    brief = build_brief(db)
    if as_json:
        print(json.dumps({
            "date": brief.date, "headline": brief.headline, "open_count": brief.open_count,
            "items": [{"title": it.loop.title, "next_action": it.next_action.title}
                      for it in brief.items],
        }, indent=2), file=out)
        return 0
    print(render_brief_text(brief), file=out)
    return 0


def _cmd_status(out: TextIO, db, config) -> int:
    c = config.cadence
    loops = db.cadence.list_loops(include_terminal=True)
    by_status: dict[str, int] = {}
    for loop in loops:
        by_status[loop.status] = by_status.get(loop.status, 0) + 1
    print("Cadence Engine", file=out)
    print(f"  enabled:        {c.enabled}", file=out)
    print(f"  pressure:       {c.pressure}", file=out)
    print(f"  tick interval:  {c.tick_interval_seconds}s", file=out)
    print(f"  quiet hours:    {c.quiet_hours_start:02d}:00–{c.quiet_hours_end:02d}:00", file=out)
    print(f"  max nudges/day: {c.max_nudges_per_day}", file=out)
    print(f"  policies:       {len(db.cadence.list_policies())}", file=out)
    if by_status:
        summary = ", ".join(f"{k}={v}" for k, v in sorted(by_status.items()))
        print(f"  loops:          {summary}", file=out)
    else:
        print("  loops:          none yet (run `holdspeak cadence run-now`)", file=out)
    return 0


def _loop_dict(loop) -> dict:
    return {
        "id": loop.id,
        "title": loop.title,
        "project": loop.project,
        "source_type": loop.source_type,
        "status": loop.status,
        "priority": loop.priority,
        "needs_review": loop.needs_review,
        "owner": loop.owner,
        "stale_score": loop.stale_score,
    }


def _cmd_loops(out: TextIO, db, *, as_json: bool, include_all: bool) -> int:
    loops = db.cadence.list_loops(include_terminal=include_all)
    if as_json:
        print(json.dumps([_loop_dict(loop) for loop in loops], indent=2), file=out)
        return 0
    if not loops:
        print("No open loops. Run `holdspeak cadence run-now` to project from your meetings.", file=out)
        return 0
    for loop in loops:
        review = " [review]" if loop.needs_review else ""
        owner = loop.owner or "unowned"
        print(f"  {loop.stale_score:6.1f}  {loop.source_type:14s}  {owner:12s}  {loop.title}{review}", file=out)
    return 0


def _cmd_run_now(out: TextIO, db, config, *, as_json: bool) -> int:
    from ..cadence.service import CadenceService

    result = CadenceService(db, config.cadence).tick(datetime.now())
    if as_json:
        print(json.dumps({
            "at": result.at,
            "projected": result.projected,
            "open_loops": result.open_loops,
            "due": [_loop_dict(loop) for loop in result.due],
        }, indent=2), file=out)
        return 0
    print(f"Tick @ {result.at}", file=out)
    print(f"  projected: {result.projected}   open: {result.open_loops}   due now: {result.due_count}", file=out)
    if result.due:
        print("  Due to nudge (highest staleness first):", file=out)
        for loop in result.due:
            print(f"    {loop.stale_score:6.1f}  {loop.title}  ({loop.source_type})", file=out)
    return 0
