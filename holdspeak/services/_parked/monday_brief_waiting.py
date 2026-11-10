"""Parked: the brief now uses one Needs you answer for waiting and coverage."""
from __future__ import annotations

import uuid
from typing import Any
from holdspeak.services.follow_through_service import FollowThroughService
from holdspeak.services.monday_brief_service import BriefItem, _local_moment, _not_read_item, _when_words, log


class PrivateBriefGather:
    def _collect_coverage_gaps(self, principal: Any) -> list[BriefItem]:
        """HS-200-07 (C4): one WAITING row per source that was not observed.

        Reads the SAME coverage projection the arrival and the shade read
        (``needs_you_aggregate.build_aggregate``) -- no second attention
        store, no second vocabulary.  A source the aggregate reports as
        available produces nothing.
        """
        from holdspeak.services.needs_you_aggregate import (
            LastKnownStore, build_aggregate,
        )
        from holdspeak.services.project_service import ProjectService

        try:
            service = ProjectService(self._db)
            # Its OWN memory: the brief reports coverage, it does not
            # replay another reader's remembered items (and it never
            # writes into the arrival's memory).
            aggregate = build_aggregate(
                list_projects=service.list_projects,
                room=service.room,
                principal=principal,
                last_known=LastKnownStore(),
            )
            coverage = aggregate.get("coverage") or []
        except Exception as exc:  # pragma: no cover - defensive
            return [
                BriefItem(
                    id=f"brief-item-{uuid.uuid4().hex}",
                    section="waiting",
                    text="NOT READ · attention coverage",
                    detail=str(exc).split("\n")[0][:120] or "Coverage unavailable",
                    source_ref="coverage:aggregate",
                    priority=320,
                )
            ]

        items: list[BriefItem] = []
        today = _local_moment(self._clock())
        for row in coverage:
            # PHILO-15 B60: a source held by HoldSpeak's own quiet hours was
            # not missed; it waits for the quiet end and is not a gap.
            if row.get("state") in ("available", "quiet"):
                continue
            repair = row.get("repair") or {}
            label = str(row.get("label") or row.get("source_id") or "source")
            detail_parts = [str(repair.get("token") or row.get("state") or "").strip()]
            if row.get("reason"):
                detail_parts.append(str(row["reason"]))
            # PHILO-15 B73: the last read in local time, never a UTC stamp.
            seen = _when_words(row.get("observed_at"), today.date() if today else None)
            if seen:
                detail_parts.append(f"last read {seen}")
            items.append(
                BriefItem(
                    id=f"brief-item-{uuid.uuid4().hex}",
                    section="waiting",
                    # PHILO-15 ruling: a thing not read says NOT READ, with
                    # the reason in the detail.
                    text=f"NOT READ · {label}",
                    detail=" · ".join(part for part in detail_parts if part),
                    source_ref=f"coverage:{row.get('source_id')}",
                    # Above every other WAITING row: an unobserved source
                    # changes what the rest of the brief can claim.
                    priority=320,
                )
            )
        return items

    def _collect_waiting_or_unread(self, principal: Any) -> list[BriefItem]:
        """The brief's own follow-through collector; a NOT READ row when it
        cannot be read (PHILO-15 05 r2: never a silent zero)."""
        try:
            return self._collect_waiting(principal)
        except Exception as exc:  # noqa: BLE001 - said as a NOT READ row
            log.warning("brief: the follow-through board is unavailable: %s", exc)
            return [_not_read_item("follow_through", exc)]

    def _collect_waiting(self, principal: Any) -> list[BriefItem]:
        """Gather pending work: overdue follow-through, high-priority loops, pending proposals."""
        board = FollowThroughService(self._db).board(principal)
        items: list[BriefItem] = []
        seen_loop_ids: set[str] = set()
        seen_action_ids: set[str] = set()

        for lane, priority, label in (
            (board.overdue, 300, "Overdue"),
            (board.unassigned, 200, "Unassigned"),
        ):
            for card in lane:
                if card.source == "cadence_loop":
                    seen_loop_ids.add(card.id)
                elif card.source == "action_item":
                    seen_action_ids.add(card.id)
                # Inventory gap 11 (2026-10-03): the `unassigned` lane also
                # holds an item that HAS an owner and is not reviewed yet.
                # The line names the item's own state, never "Unassigned"
                # for an item with an owner.
                has_owner = bool(str(card.owner or "").strip())
                if label == "Unassigned" and has_owner:
                    label_text, no_due = "To review", "Not reviewed"
                else:
                    label_text, no_due = label, "Needs an owner"
                detail = f"Due {card.due}" if card.due else no_due
                items.append(
                    BriefItem(
                        id=f"brief-item-{uuid.uuid4().hex}",
                        section="waiting",
                        text=f"{label_text}: {card.text}",
                        detail=detail,
                        source_ref=f"{card.source}:{card.id}",
                        priority=priority,
                    )
                )

        with self._db._connection() as conn:
            loop_rows = conn.execute(
                """SELECT id, source_type, source_id, title, priority, due_at
                   FROM cadence_loops
                   WHERE status = 'open' AND priority IN ('high', 'urgent')
                   ORDER BY CASE priority WHEN 'urgent' THEN 1 ELSE 0 END DESC,
                            due_at ASC, id ASC"""
            ).fetchall()
            proposal_rows = []
            proposal_table = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'actuator_proposals'"
            ).fetchone()
            if proposal_table is not None:
                proposal_rows = conn.execute(
                    """SELECT id, preview, target, action
                       FROM actuator_proposals
                       WHERE status = 'proposed' AND review_decision = 'unreviewed'
                       ORDER BY created_at ASC, id ASC"""
                ).fetchall()

        for loop in loop_rows:
            loop_id = str(loop["id"])
            if loop_id in seen_loop_ids or (
                loop["source_type"] == "meeting_action"
                and str(loop["source_id"]) in seen_action_ids
            ):
                continue
            urgency = 120 if str(loop["priority"]) == "urgent" else 100
            due_at = str(loop["due_at"]) if loop["due_at"] else None
            items.append(
                BriefItem(
                    id=f"brief-item-{uuid.uuid4().hex}",
                    section="waiting",
                    text=f"Open loop: {loop['title']}",
                    detail=f"Due {due_at[:10]}" if due_at else "High priority",
                    source_ref=f"cadence_loop:{loop_id}",
                    priority=urgency,
                )
            )

        for proposal in proposal_rows:
            preview = str(proposal["preview"]).strip()
            description = preview or f"{proposal['action']} on {proposal['target']}"
            items.append(
                BriefItem(
                    id=f"brief-item-{uuid.uuid4().hex}",
                    section="waiting",
                    text=f"Approval needed: {description}",
                    detail="Awaiting review",
                    source_ref=f"actuator_proposal:{proposal['id']}",
                    priority=150,
                )
            )

        return sorted(items, key=lambda item: (-item.priority, item.source_ref or ""))

