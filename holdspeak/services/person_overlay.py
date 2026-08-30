"""Read-time chief-of-staff overlay for the Monday Brief.

HS-150-03: compose_person_overlay builds per-relationship sections AFTER
the persisted brief service returns.  The MondayBrief dataclass NEVER
carries person_sections; this module is the sole manufacturer, called at
the adapter layer (routes + MCP tools).  Nothing here writes to any store.
"""
from __future__ import annotations

import datetime
from typing import Any


def compose_person_overlay(
    brief_window: tuple[str, str],
    people_service: Any,
    follow_through_service: Any,
    db: Any,
    principal: Any,
) -> dict[str, Any]:
    """Build person_sections from encrypted + plaintext sources.

    Returns ``{"state": "unavailable"}`` when the encrypted sidecar is
    closed -- the L2 honesty line.  Otherwise returns
    ``{"state": "ready", "sections": [...]}``.

    Read-time, in-memory, NEVER persisted.
    """
    # -- readiness gate -------------------------------------------------------
    try:
        readiness = people_service.readiness(principal)
    except Exception:
        return {"state": "unavailable"}

    state = str(readiness.get("state") or "")
    if state != "ready":
        return {"state": "unavailable"}

    # -- gather relationships with signal -------------------------------------
    try:
        relationships = people_service.list_relationships(principal)
    except Exception:
        return {"state": "unavailable"}

    if not relationships:
        return {"state": "ready", "sections": []}

    # The board, fetched once for all relationships.
    try:
        board = follow_through_service.board(principal)
    except Exception:
        board = None

    # All board cards flat.
    all_cards: list[Any] = []
    if board is not None:
        for lane_name in ("now", "waiting", "unassigned", "overdue"):
            all_cards.extend(getattr(board, lane_name, []))

    window_start, _window_end = brief_window

    sections: list[dict[str, Any]] = []
    for rel in relationships:
        rel_id = str(rel.get("id") or "")
        display_name = str(rel.get("display_name") or "")
        aliases = [
            str(a).casefold() for a in (rel.get("owner_aliases") or []) if isinstance(a, str)
        ]
        if not rel_id:
            continue

        # THEY-OWE: board cards whose owner matches any alias.
        they_owe_cards = _cards_by_aliases(all_cards, aliases)
        they_owe_count = len(they_owe_cards)
        stalest_age = _stalest_age(they_owe_cards) if they_owe_cards else None

        # YOU-OWE: open encrypted commitments.
        you_owe_count = 0
        try:
            brief_data = people_service.one_on_one_brief(principal, rel_id, db=db)
            you_owe_count = len(brief_data.get("open_commitments") or [])
            agenda_backlog = len(brief_data.get("agenda_items") or [])
        except Exception:
            agenda_backlog = 0

        # Next linked 1:1 in the window (upcoming calendar events by series).
        next_one_on_one = _next_linked_one_on_one(rel, db, window_start)

        # Only include relationships that have at least one signal.
        if not any([they_owe_count, you_owe_count, agenda_backlog, next_one_on_one]):
            continue

        section: dict[str, Any] = {
            "relationship_id": rel_id,
            "display_name": display_name,
            "they_owe_count": they_owe_count,
            "stalest_age_days": stalest_age,
            "you_owe_count": you_owe_count,
            "agenda_backlog": agenda_backlog,
            "next_one_on_one": next_one_on_one,
        }
        sections.append(section)

    return {"state": "ready", "sections": sections}


def _cards_by_aliases(
    cards: list[Any], aliases: list[str],
) -> list[Any]:
    """Filter board cards whose owner string matches any alias (case-insensitive)."""
    if not aliases:
        return []
    result = []
    for card in cards:
        owner = getattr(card, "owner", None)
        if owner is not None and str(owner).casefold() in aliases:
            result.append(card)
    return result


def _stalest_age(cards: list[Any]) -> int | None:
    """Return the age in days of the stalest card (delegated_at ?? created_at).

    The ruled law: delegated_at wins when present (it records WHEN ownership
    last changed); created_at is the fallback (the row's birth).  Honest
    absence when neither exists (non-action sources like People commitments).
    """
    today = datetime.date.today()
    oldest: datetime.date | None = None
    for card in cards:
        # HS-150-02: delegated_at ?? created_at (the ruled law).
        raw = getattr(card, "delegated_at", None)
        if raw is None:
            raw = getattr(card, "created_at", None)
        if raw is None:
            continue
        try:
            ts = datetime.datetime.fromisoformat(
                str(raw).replace("Z", "+00:00")
            ).date()
        except (ValueError, TypeError):
            continue
        if oldest is None or ts < oldest:
            oldest = ts
    if oldest is None:
        return None
    return max(0, (today - oldest).days)


def _next_linked_one_on_one(
    relationship: dict[str, Any],
    db: Any,
    window_start: str,
) -> dict[str, str] | None:
    """Find the next upcoming calendar event linked to this relationship's series."""
    calendar_links = relationship.get("calendar_links") or []
    if not calendar_links or db is None:
        return None

    uid_source_pairs = [
        (str(link.get("uid") or ""), str(link.get("source_id") or ""))
        for link in calendar_links
        if isinstance(link, dict) and link.get("uid")
    ]
    if not uid_source_pairs:
        return None

    now_iso = datetime.datetime.now().isoformat()

    try:
        with db._connection() as conn:
            # Find the next upcoming event from linked series.
            conditions = " OR ".join(
                "(uid = ? AND source_id = ?)" for _ in uid_source_pairs
            )
            params: list[str] = []
            for uid, sid in uid_source_pairs:
                params.extend([uid, sid])
            params.append(now_iso)

            row = conn.execute(
                f"""SELECT id, uid, title, starts_at
                    FROM calendar_events
                    WHERE ({conditions})
                      AND starts_at > ?
                    ORDER BY starts_at ASC
                    LIMIT 1""",
                params,
            ).fetchone()

            if row is not None:
                return {
                    "event_id": str(row["id"]),
                    "title": str(row["title"] or ""),
                    "starts_at": str(row["starts_at"]),
                }
    except Exception:
        pass

    return None
