# Parked: calendar, Room and Program facts now come from their owning services.

class _ParkedBody:
    def _collect_programs(self, items: list[BriefItem], today: Any) -> None:
        """One row per Project with a running Program: how many run, how many
        wait on him (Programs §9b)."""
        from holdspeak.services.program_service import ProgramService

        service = ProgramService(self._db)
        projects: dict[str, dict[str, int]] = {}
        for row in service.list().get("programs") or []:
            if row["state"] not in ("running", "waiting") or not row.get("project_id"):
                continue
            counts = projects.setdefault(str(row["project_id"]), {"running": 0, "waiting": 0})
            counts["running"] += 1
            counts["waiting"] += 1 if row["state"] == "waiting" else 0
        if not projects:
            return
        with self._db._connection() as conn:
            names = {str(r["id"]): str(r["name"]) for r in conn.execute("SELECT id, name FROM projects")}
        for project_id, counts in sorted(projects.items()):
            detail = f"{counts['running']} running" + (f", {counts['waiting']} wait on you" if counts["waiting"] else "")
            items.append(BriefItem(
                id=f"brief-item-{uuid.uuid4().hex}", section="changed",
                text=f"Programs: {names.get(project_id, project_id)}", detail=detail,
                source_ref=f"project:{project_id}", priority=self._DAY_PRIORITY["Programs"],
            ))


    def _collect_decisions(
        self, principal: Any, exclude_commitment_ids: set[str] | None = None,
    ) -> list[BriefItem]:
        """Gather decisions requiring owner attention.

        C11 follow-up: a commitment is said once.  ``exclude_commitment_ids``
        are the commitment ids THIS WEEK already counts (``N commitments
        due this week``); their lookback ``Commitment due`` items are
        dropped -- dedup by commitment id, never by text.
        """
        del principal
        items: list[BriefItem] = []
        excluded_commitments = exclude_commitment_ids or set()

        # A proposed actuator cannot cross the egress boundary until its owner
        # grants authorization. It enters the decision queue with its own
        # durable creation timestamp.
        for proposal in self._db.actuators.list_pending_proposals():
            items.append(
                BriefItem(
                    id=f"brief-item-{uuid.uuid4().hex}",
                    section="decisions",
                    text=f"Authorize {proposal.target} {proposal.action}: {proposal.preview}",
                    source_ref=f"actuator_proposal:{proposal.id}",
                    priority=300,
                    created_at=proposal.created_at,
                )
            )

        # Desk decisions carry an explicit proposed state. Meeting-derived
        # decisions are recorded until the owner accepts or rejects them.
        for decision in self._db.desk_decisions.list():
            if decision.status != "proposed":
                continue
            title = decision.title or decision.decision_markdown or decision.id
            items.append(
                BriefItem(
                    id=f"brief-item-{uuid.uuid4().hex}",
                    section="decisions",
                    text=f"Review decision: {title}",
                    source_ref=f"decision:{decision.id}",
                    priority=200,
                    created_at=decision.created_at,
                )
            )
        # The same rule the one ``needs you`` rule uses: a recorded decision
        # whose proposal is in a Room, or is confirmed or dismissed, does not
        # ask for review a second time.
        from .needs_you_membership import meeting_decision_asks_elsewhere

        proposal_cache: dict[str, list[Any]] = {}
        for decision in self._db.decisions.list(lifecycle="recorded"):
            if meeting_decision_asks_elsewhere(
                self._db, meeting_id=decision.source_meeting_id,
                artifact_id=decision.source_artifact_id, text=decision.text, cache=proposal_cache,
            ):
                continue
            items.append(
                BriefItem(
                    id=f"brief-item-{uuid.uuid4().hex}",
                    section="decisions",
                    text=f"Review decision: {decision.text}",
                    source_ref=f"decision:{decision.id}",
                    priority=200,
                    created_at=decision.created_at,
                )
            )

        # Open, due-soon commitments require attention. Their source decision's
        # creation timestamp keeps their row aligned with the decision queue.
        today = self._clock().date()
        horizon = today + datetime.timedelta(days=7)
        with self._db._connection() as conn:
            commitments = conn.execute(
                """SELECT dc.id, dc.decision_id, dc.due_at, d.text, d.created_at
                   FROM decision_commitments AS dc
                   JOIN decisions AS d ON d.id = dc.decision_id
                   WHERE dc.status = 'open' AND dc.due_at IS NOT NULL
                     AND d.deleted = 0
                   ORDER BY dc.due_at ASC, dc.id ASC"""
            ).fetchall()
        for commitment in commitments:
            if str(commitment["id"]) in excluded_commitments:
                continue  # already said under THIS WEEK
            try:
                due_date = datetime.datetime.fromisoformat(
                    str(commitment["due_at"]).replace("Z", "+00:00")
                ).date()
            except ValueError:
                continue
            if due_date > horizon:
                continue
            items.append(
                BriefItem(
                    id=f"brief-item-{uuid.uuid4().hex}",
                    section="decisions",
                    text=f"Commitment due {due_date.isoformat()}: {commitment['text']}",
                    source_ref=f"decision:{commitment['decision_id']}",
                    priority=120 if due_date <= today else 110,
                    created_at=str(commitment["created_at"]),
                )
            )

        return self._sort_section("decisions", items)


    def _collect_calendar_events(
        self, week_start: str, week_end: str, now_iso: str,
        *,
        exclude_event_ids: set[str] | None = None,
        clock_tz: datetime.tzinfo | None = None,
    ) -> list[BriefItem]:
        """Calendar events in the week range.

        HS-175-05: produces items for the ``this_week`` section
        (forward-looking calendar and armed-recording data):
        - ``N meetings`` (count of events in the week).
        - ``Next: [title] at [time]`` (next event after now).
        - ``N armed`` (events with linked armed recordings).

        C11: ``exclude_event_ids`` is the calendar_uid dedup against the
        lookback's "Meeting recorded" rows, keyed by the occurrence (the
        projection id hashes uid + starts_at) so a recurring series' next
        occurrence is never hidden by its last recording.  ``clock_tz``
        renders the ``Next:`` clock in the brief's own zone rather than
        the stored UTC.

        Returns an empty list when no calendar events exist (no
        calendar configured or no events in range).
        """
        items: list[BriefItem] = []
        excluded = exclude_event_ids or set()
        with self._db._connection() as conn:
            # Check that calendar_events table exists (belt -- fresh DBs)
            table_check = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='calendar_events'"
            ).fetchone()
            if table_check is None:
                return items

            event_rows = [
                row for row in conn.execute(
                    """SELECT id, uid, title, starts_at, meeting_url
                       FROM calendar_events
                       WHERE starts_at >= ? AND starts_at < ?
                       ORDER BY starts_at ASC, id ASC""",
                    (week_start, week_end),
                ).fetchall()
                if str(row["id"]) not in excluded
            ]
            if not event_rows:
                return items

            total = len(event_rows)
            items.append(
                BriefItem(
                    id=f"brief-cal-total-{uuid.uuid4().hex}",
                    section="this_week",
                    text=f"{total} meeting{'s' if total != 1 else ''} this week",
                    source_ref="calendar:week",
                    priority=_MEETING_PRIORITY + 10,
                )
            )

            # Next event after now
            for row in event_rows:
                if str(row["starts_at"]) > now_iso:
                    try:
                        next_dt = datetime.datetime.fromisoformat(
                            str(row["starts_at"]).replace("Z", "+00:00")
                        )
                        if clock_tz is not None and next_dt.tzinfo is not None:
                            next_dt = next_dt.astimezone(clock_tz)
                        time_str = next_dt.strftime("%H:%M")
                    except (ValueError, TypeError):
                        time_str = ""
                    title = str(row["title"] or "").strip() or "Untitled"
                    items.append(
                        BriefItem(
                            id=f"brief-cal-next-{uuid.uuid4().hex}",
                            section="this_week",
                            text=f"Next: {title} at {time_str}",
                            source_ref=f"calendar_event:{row['id']}",
                            priority=_MEETING_PRIORITY + 5,
                        )
                    )
                    break

            # Armed recordings count
            sched_table = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='scheduled_recordings'"
            ).fetchone()
            if sched_table is not None:
                event_ids = [str(r["id"]) for r in event_rows]
                placeholders = ",".join("?" * len(event_ids))
                armed_row = conn.execute(
                    f"""SELECT COUNT(*) AS cnt FROM scheduled_recordings
                        WHERE calendar_event_id IN ({placeholders})
                          AND enabled = 1""",
                    event_ids,
                ).fetchone()
                armed = int(armed_row["cnt"]) if armed_row else 0
                if armed:
                    items.append(
                        BriefItem(
                            id=f"brief-cal-armed-{uuid.uuid4().hex}",
                            section="this_week",
                            text=f"{armed} armed",
                            source_ref="calendar:armed",
                            priority=_MEETING_PRIORITY + 3,
                        )
                    )

        return items


    def _collect_meeting_watch(
        self, week_start: str, week_end: str, last_brief_at: str | None,
        *,
        decisions_since: str | None = None,
        due_from: str | None = None,
        due_until: str | None = None,
    ) -> list[BriefItem]:
        """Meeting watch items: new decisions and commitments.

        HS-175-05: reads decisions and commitments from meetings linked
        to any Room, filtered to the week window.

        - Meetings with new decisions since the last brief.
        - Meetings with new commitments.
        - Commitments due this week.

        C11: ``week_start`` is the forward window's start (``now``).  New
        decisions are a "since the last brief" fact, so their fallback
        floor is ``decisions_since`` (the lookback's start), not ``now``.
        Commitments carry due DATES, so they are bounded by the owner's
        local dates ``due_from`` (today) and ``due_until`` (Sunday), not by
        UTC instants.  The calendar_uid dedup lives in the calendar
        collector (``exclude_event_ids``); these items are counts over
        meeting data and name no event.
        """
        items: list[BriefItem] = []
        since = last_brief_at or decisions_since or week_start
        due_lo = due_from or week_start[:10]
        due_hi = due_until or week_end

        with self._db._connection() as conn:
            # Check tables exist
            for table in ("decision_records", "decision_record_sources",
                          "decision_commitments"):
                if conn.execute(
                    f"SELECT 1 FROM sqlite_master WHERE type='table' AND name='{table}'"
                ).fetchone() is None:
                    return items

            # New decisions since last brief
            decision_rows = conn.execute(
                """SELECT r.id, r.decision_text, r.created_at,
                          s.source_ref AS meeting_id
                   FROM decision_records r
                   JOIN decision_record_sources s ON s.record_id = r.id
                   WHERE s.source_type = 'meeting'
                     AND julianday(r.created_at) >= julianday(?) AND julianday(r.created_at) < julianday(?)
                     AND r.deleted = 0
                     -- PHILO-15 08: an action's record is not a new decision.
                     AND COALESCE(r.kind, 'decision') != 'action'
                     AND NOT EXISTS (SELECT 1 FROM follow_through_proposals fp
                                     WHERE fp.decision_record_id = r.id AND fp.kind = 'action')
                   ORDER BY julianday(r.created_at) DESC""",
                (sql_instant(since), sql_instant(week_end)),
            ).fetchall()

            if decision_rows:
                count = len(decision_rows)
                items.append(
                    BriefItem(
                        id=f"brief-mtgwatch-decisions-{uuid.uuid4().hex}",
                        section="this_week",
                        text=f"{count} new decision{'s' if count != 1 else ''} from meetings",
                        source_ref="meeting_watch:decisions",
                        priority=_MEETING_PRIORITY + 2,
                    )
                )

            # Commitments due this week
            commitment_rows = self._commitments_due_rows(conn, due_lo, due_hi)

            if commitment_rows:
                count = len(commitment_rows)
                first = commitment_rows[0]
                first_due = str(first["due_at"] or "")[:10]
                first_text = None
                try:
                    d_row = conn.execute(
                        """SELECT d.text FROM decisions d
                           JOIN decision_commitments dc ON dc.decision_id = d.id
                           WHERE dc.id = ?""",
                        (str(first["id"]),),
                    ).fetchone()
                    if d_row and d_row["text"]:
                        first_text = str(d_row["text"]).strip()
                except Exception:
                    pass
                detail_parts = []
                if first_text:
                    detail_parts.append(first_text)
                if first_due:
                    detail_parts.append(first_due)
                detail = " | ".join(detail_parts) if detail_parts else None
                items.append(
                    BriefItem(
                        id=f"brief-mtgwatch-commitments-{uuid.uuid4().hex}",
                        section="this_week",
                        text=f"{count} commitment{'s' if count != 1 else ''} due this week",
                        detail=detail,
                        source_ref="meeting_watch:commitments_due",
                        priority=_MEETING_PRIORITY + 1,
                    )
                )

        return items


    @staticmethod
    def _commitments_due_rows(conn: Any, due_lo: str, due_hi: str) -> list[Any]:
        """Open commitments due in ``[due_lo, due_hi)`` -- the one query THIS
        WEEK counts and the lookback dedups against (by commitment id)."""
        try:
            return conn.execute(
                """SELECT dc.id, dc.due_at, dc.status, dc.owner
                   FROM decision_commitments dc
                   WHERE dc.status = 'open'
                     AND dc.due_at >= ? AND dc.due_at < ?
                   ORDER BY dc.due_at ASC""",
                (due_lo, due_hi),
            ).fetchall()
        except Exception:
            return []
