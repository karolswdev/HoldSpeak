# Parked: Today and the brief now share the since_morning_read history gather.

class _ParkedBody:
    def _collect_desk_additions(self, window_start: str, window_end: str) -> list[BriefItem]:
        """PHILO-15-09 (B04, ruling 4): what the owner added to the desk.

        From the durable rows, as ``_collect_meetings`` does: a decision he
        made (a desk decision that is not ``proposed``; a proposed one is a
        DECISIONS row), a Project, and the people added. A person is counted
        from the People store's plain metadata (kind and time): the brief is
        sent to other places, so no People content is written into it.
        """
        items: list[BriefItem] = []
        # Small tables, stamps of mixed shapes: the instant test is exact.
        with self._db._connection() as conn:
            decisions = conn.execute(
                """SELECT id, title, status, created_at FROM desk_decisions
                   WHERE deleted = 0 AND status != 'proposed'"""
            ).fetchall()
            projects = conn.execute(
                "SELECT id, name, created_at FROM projects WHERE is_archived = 0"
            ).fetchall()
        for row in sorted(decisions, key=lambda r: (str(r["created_at"]), str(r["id"]))):
            if not in_window(row["created_at"], window_start, window_end):
                continue
            title = str(row["title"] or "").strip() or "Untitled decision"
            items.append(BriefItem(
                id=f"brief-item-{uuid.uuid4().hex}", section="changed",
                text=f"Decision made: {title}", source_ref=f"desk_decision:{row['id']}",
                detail=_when_words(row["created_at"], _day_of(window_end)),
                priority=_MEETING_PRIORITY - 1, created_at=str(row["created_at"]),
            ))
        for row in sorted(projects, key=lambda r: (str(r["created_at"]), str(r["id"]))):
            if not in_window(row["created_at"], window_start, window_end):
                continue
            name = str(row["name"] or "").strip() or "Untitled Project"
            items.append(BriefItem(
                id=f"brief-item-{uuid.uuid4().hex}", section="changed",
                text=f"Project added: {name}", source_ref=f"project:{row['id']}",
                detail=_when_words(row["created_at"], _day_of(window_end)),
                priority=_MEETING_PRIORITY - 2, created_at=str(row["created_at"]),
            ))
        people = self._people_added(window_start, window_end)
        if people:
            items.append(BriefItem(
                id=f"brief-item-{uuid.uuid4().hex}", section="changed",
                text="Person added" if people == 1 else f"{people} people added",
                source_ref="people:added", priority=_MEETING_PRIORITY - 3,
            ))
        return items


    def _collect_day(
        self, window_start: str, window_end: str, today: datetime.date | None,
    ) -> tuple[list[BriefItem], list[BriefItem]]:
        """PHILO-15 B58: decisions confirmed, actions done, agent launches,
        PRs opened and merged, and updates published or sent, in the window.

        Returns ``(changed rows, NOT READ rows)``: a source that cannot be
        read is never a silent zero.
        """
        items: list[BriefItem] = []
        unread: list[BriefItem] = []

        def inside(stamp: Any) -> bool:
            return bool(stamp) and in_window(stamp, window_start, window_end)

        lo, hi = sql_window(window_start, window_end)
        with self._db._connection() as conn:
            confirmed = conn.execute(
                """SELECT id, meeting_id, kind, text, decided_at FROM follow_through_proposals
                   WHERE state = 'confirmed' AND kind = 'decision'
                     AND decided_at BETWEEN ? AND ?""",
                (lo, hi),
            ).fetchall()
            done = conn.execute(
                """SELECT id, task, completed_at FROM action_items
                   WHERE status = 'done' AND completed_at BETWEEN ? AND ?""",
                (lo, hi),
            ).fetchall()
        for row in sorted(confirmed, key=lambda r: (str(r["decided_at"]), str(r["id"]))):
            if inside(row["decided_at"]):
                title = " ".join(str(row["text"] or "").split())[:160] or "Untitled decision"
                items.append(self._day_item("Decision confirmed", title, row["decided_at"],
                                            f"meeting:{row['meeting_id']}", today))
        for row in sorted(done, key=lambda r: (str(r["completed_at"]), str(r["id"]))):
            if inside(row["completed_at"]):
                title = " ".join(str(row["task"] or "").split())[:160] or "Untitled action"
                items.append(self._day_item("Action done", title, row["completed_at"],
                                            f"action_item:{row['id']}", today))
        try:
            merged_urls = self._collect_launches(items, inside, today)
        except Exception as exc:  # noqa: BLE001 - said as a NOT READ row
            log.warning("brief: the agent launches were not read: %s", exc)
            unread.append(_not_read_item("agents", exc))
            merged_urls = set()
        try:
            self._collect_room_merges(items, inside, today, merged_urls)
        except Exception as exc:  # noqa: BLE001 - said as a NOT READ row
            log.warning("brief: the Room merges were not read: %s", exc)
            unread.append(_not_read_item("room_merges", exc))
        try:
            self._collect_updates(items, inside, today, lo, hi)
        except Exception as exc:  # noqa: BLE001 - said as a NOT READ row
            log.warning("brief: the Room updates were not read: %s", exc)
            unread.append(_not_read_item("updates", exc))
        try:
            self._collect_programs(items, today)
        except Exception as exc:  # noqa: BLE001 - said as a NOT READ row
            log.warning("brief: the Programs were not read: %s", exc)
            unread.append(_not_read_item("programs", exc))
        return items, unread


    def _collect_meetings(self, window_start: str, window_end: str) -> list[BriefItem]:
        """Gather meetings recorded inside the window.

        HS-132-08: the observer's method markers (create/update/delete/…) never
        match the meeting lifecycle, so a week full of recorded meetings used to
        read as an empty brief. Meetings are collected from their own
        durable rows rather than from pipeline receipts, which is the honest
        source: a meeting exists whether or not an observed method ran.
        """
        # Stored stamps mix old local and new UTC text: a padded text
        # prefilter, then the exact instant test and order.
        with self._db._connection() as conn:
            rows = conn.execute(
                """SELECT m.id, m.title, m.started_at, m.ended_at, m.duration_seconds,
                          COALESCE(m.ended_at, m.started_at) AS window_at,
                          (SELECT COUNT(*) FROM action_items a
                            WHERE a.meeting_id = m.id) AS action_count
                   FROM meetings AS m
                   WHERE m.parked = 0
                     AND COALESCE(m.ended_at, m.started_at) BETWEEN ? AND ?
                     AND m.capture_status NOT IN ('recording', 'provisional')""",
                sql_window(window_start, window_end),
            ).fetchall()
        rows = sorted(
            (r for r in rows if in_window(r["window_at"], window_start, window_end)),
            key=lambda r: (parse_stamp(r["window_at"]), str(r["id"])),
        )

        items: list[BriefItem] = []
        for row in rows:
            title = str(row["title"] or "").strip() or "Untitled meeting"
            parts: list[str] = []
            duration = row["duration_seconds"]
            if duration:
                parts.append(f"{max(1, round(float(duration) / 60))} min")
            actions = int(row["action_count"] or 0)
            if actions:
                parts.append(f"{actions} action item{'' if actions == 1 else 's'}")
            # PHILO-15 lane 19 (Astra r1, 6): the meeting row carries its time.
            when = _when_words(row["window_at"], _day_of(window_end))
            if when:
                parts.append(when)
            items.append(
                BriefItem(
                    id=f"brief-item-{uuid.uuid4().hex}",
                    section="changed",
                    text=f"Meeting recorded: {title}",
                    detail=" · ".join(parts) or None,
                    source_ref=f"meeting:{row['id']}",
                    priority=_MEETING_PRIORITY,
                    created_at=str(row["window_at"]),
                )
            )
        return items


    def _recorded_calendar_event_ids(
        self, window_start: str, window_end: str,
    ) -> set[str]:
        """C11: the calendar occurrences already recorded inside the lookback.

        Mirrors ``_collect_meetings``' predicate so an event that is a
        "Meeting recorded" row in SINCE FRIDAY is never also counted or
        named in THIS WEEK.
        """
        with self._db._connection() as conn:
            rows = conn.execute(
                """SELECT m.calendar_event_id AS event_id,
                          COALESCE(m.ended_at, m.started_at) AS window_at
                   FROM meetings AS m
                   WHERE m.parked = 0
                     AND m.calendar_event_id IS NOT NULL
                     AND m.calendar_event_id != ''
                     AND COALESCE(m.ended_at, m.started_at) BETWEEN ? AND ?
                     AND m.capture_status NOT IN ('recording', 'provisional')""",
                sql_window(window_start, window_end),
            ).fetchall()
        return {
            str(r["event_id"]) for r in rows
            if in_window(r["window_at"], window_start, window_end)
        }
