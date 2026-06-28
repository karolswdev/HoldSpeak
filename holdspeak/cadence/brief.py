"""The daily push brief (CAD-5).

Deterministic by default: rank the open loops, take the top few, attach each one's
prepared next move, and lead with the single highest-leverage move. An LLM may
*polish the wording* of the headline (behind a capability gate, fail-closed) — it
never changes WHICH loops are chosen or any policy. Pure given `now` + the loops.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Optional

from .models import NextBestAction, OpenLoop
from .next_action import generate_next_action


@dataclass
class BriefItem:
    loop: OpenLoop
    next_action: NextBestAction


@dataclass
class Brief:
    date: str                      # YYYY-MM-DD
    headline: str                  # the single highest-leverage move, in prose
    items: list[BriefItem] = field(default_factory=list)
    open_count: int = 0
    generated_by: str = "deterministic"

    @property
    def is_empty(self) -> bool:
        return not self.items


def build_brief(db, *, now: Optional[datetime] = None, limit: int = 5) -> Brief:
    """Rank open loops, take the top `limit` pushable ones, attach next actions."""
    now = now or datetime.now()
    loops = db.cadence.list_loops()  # excludes terminal, ordered by stale_score desc
    pushable = [l for l in loops if not l.needs_review]
    top = pushable[:limit]
    items = [BriefItem(loop=l, next_action=generate_next_action(l)) for l in top]
    headline = _deterministic_headline(items)
    return Brief(date=now.strftime("%Y-%m-%d"), headline=headline, items=items,
                 open_count=len(loops))


def _deterministic_headline(items: list[BriefItem]) -> str:
    if not items:
        return "Nothing pressing today — your loops are clear."
    top = items[0]
    return f"{top.next_action.title}."


def polish_headline(brief: Brief, *, llm: Optional[Callable[[str], str]] = None) -> Brief:
    """Optionally rewrite the headline's WORDING via an LLM. Fail-closed: any error,
    or no llm, leaves the deterministic headline untouched. Never changes the items."""
    if llm is None or brief.is_empty:
        return brief
    try:
        prompt = (
            "Rewrite this as one crisp, encouraging sentence naming the single most "
            f"important next move. No preamble.\n\n{brief.headline}"
        )
        out = (llm(prompt) or "").strip().splitlines()
        polished = out[0].strip() if out else ""
        if polished:
            brief.headline = polished
            brief.generated_by = "llm"
    except Exception:
        pass  # fail-closed — keep the deterministic headline
    return brief


def render_brief_markdown(brief: Brief) -> str:
    """Telegram/web markdown."""
    lines = [f"🧷 *Morning Push — {brief.date}*", "", f"*{brief.headline}*"]
    if brief.items:
        lines.append("")
        for i, item in enumerate(brief.items, 1):
            lines.append(f"{i}. *{item.loop.title}*  —  {item.next_action.title}")
    lines.append("")
    lines.append(f"_{brief.open_count} open loop(s)._")
    return "\n".join(lines)


def render_brief_text(brief: Brief) -> str:
    """Plain text for the CLI."""
    lines = [f"Morning Push — {brief.date}", "", brief.headline]
    for i, item in enumerate(brief.items, 1):
        lines.append(f"  {i}. {item.loop.title}  ->  {item.next_action.title}")
    lines.append("")
    lines.append(f"{brief.open_count} open loop(s).")
    return "\n".join(lines)


def should_send_daily_brief(
    now: datetime, *, last_sent_date: Optional[str], earliest_hour: int = 7
) -> bool:
    """First-activity trigger (pure): fire once per local day, only after the earliest
    hour, and never twice the same day. `last_sent_date` is the YYYY-MM-DD last pushed."""
    if now.hour < earliest_hour:
        return False
    return now.strftime("%Y-%m-%d") != (last_sent_date or "")
