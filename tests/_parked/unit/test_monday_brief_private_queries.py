# Parked: private-query fixtures are replaced by real Room producers and hub parity properties.

class TestCollectMeetingWatch:

    def _seed_decision_record(self, db, *, meeting_id, text="Decision",
                              created_at="2026-09-03T11:00:00"):
        rid = f"dr-{uuid.uuid4().hex[:8]}"
        sid = f"drs-{uuid.uuid4().hex[:8]}"
        with db._connection() as conn:
            conn.execute(
                """INSERT INTO decision_records
                   (id, decision_text, source_type, source_id, created_at, updated_at)
                   VALUES (?, ?, 'meeting', ?, ?, ?)""",
                (rid, text, meeting_id, created_at, created_at),
            )
            conn.execute(
                """INSERT INTO decision_record_sources
                   (id, record_id, source_type, source_ref, created_at)
                   VALUES (?, ?, 'meeting', ?, ?)""",
                (sid, rid, meeting_id, created_at),
            )
        return rid

    def _seed_commitment(self, db, *, due_at="2026-09-04", status="open"):
        cid = f"dc-{uuid.uuid4().hex[:8]}"
        did = f"d-{uuid.uuid4().hex[:8]}"
        aid = f"ai-{uuid.uuid4().hex[:8]}"
        art_id = f"art-{uuid.uuid4().hex[:8]}"
        with db._connection() as conn:
            conn.execute(
                """INSERT INTO decisions
                   (id, text, rationale, source_artifact_id, source_meeting_id,
                    lifecycle, project_key, decided_at)
                   VALUES (?, 'test', '', ?, '', 'recorded', '', datetime('now'))""",
                (did, art_id),
            )
            conn.execute(
                """INSERT INTO decision_commitments
                   (id, decision_id, action_item_id, owner, due_at, status, created_at, updated_at)
                   VALUES (?, ?, ?, 'karol', ?, ?, datetime('now'), datetime('now'))""",
                (cid, did, aid, due_at, status),
            )
        return cid

    def test_new_decisions(self, db):
        svc = MondayBriefService(db)
        mid = f"mtg-{uuid.uuid4().hex[:8]}"
        with db._connection() as conn:
            conn.execute(
                """INSERT INTO meetings
                   (id, title, started_at, capture_status)
                   VALUES (?, 'Test', '2026-09-03T10:00:00', 'finalized')""",
                (mid,),
            )
        self._seed_decision_record(db, meeting_id=mid, created_at="2026-09-03T11:00:00")
        self._seed_decision_record(db, meeting_id=mid, created_at="2026-09-03T11:05:00")

        items = svc._collect_meeting_watch(
            "2026-08-31T00:00:00", "2026-09-06T23:59:59",
            "2026-08-31T00:00:00",
        )

        decision_items = [i for i in items if "decision" in i.text.lower()]
        assert len(decision_items) == 1
        assert "2 new decisions" in decision_items[0].text

    def test_commitments_due_this_week(self, db):
        svc = MondayBriefService(db)
        self._seed_commitment(db, due_at="2026-09-02", status="open")
        self._seed_commitment(db, due_at="2026-09-04", status="open")
        # Commitment outside the week
        self._seed_commitment(db, due_at="2026-09-10", status="open")

        items = svc._collect_meeting_watch(
            "2026-08-31T00:00:00", "2026-09-06T23:59:59",
            None,
        )

        due_items = [i for i in items if "commitment" in i.text.lower() and "due" in i.text.lower()]
        assert len(due_items) == 1
        assert "2 commitments due this week" in due_items[0].text

    def test_empty_when_no_data(self, db):
        svc = MondayBriefService(db)
        items = svc._collect_meeting_watch(
            "2026-08-31T00:00:00", "2026-09-06T23:59:59", None,
        )
        assert items == []


class TestCommitmentSaidOnce:
    """C11 follow-up: a commitment THIS WEEK counts is dropped from the
    lookback's `Commitment due` items -- dedup by commitment id, not text."""

    def _seed(self, db, cid: str, due: str, text: str) -> None:
        art = f"art-{uuid.uuid4().hex[:8]}"
        did = f"d-{cid}"
        with db._connection() as conn:
            conn.execute(
                """INSERT INTO decisions (id, text, rationale, source_artifact_id, source_meeting_id,
                                          lifecycle, project_key, decided_at)
                   VALUES (?, ?, '', ?, '', 'recorded', '', datetime('now'))""",
                (did, text, art),
            )
            conn.execute(
                """INSERT INTO decision_commitments
                   (id, decision_id, action_item_id, owner, due_at, status, created_at, updated_at)
                   VALUES (?, ?, ?, 'karol', ?, 'open', datetime('now'), datetime('now'))""",
                (cid, did, f"ai-{cid}", due),
            )

    def test_commitment_due_today_appears_once_in_this_week(self, db):
        svc = MondayBriefService(db)
        now = datetime.datetime(2026, 9, 7, 14, 0, tzinfo=UTC)  # Monday
        self._seed(db, "dc-today", "2026-09-07", "Ship the spec")   # THIS WEEK's
        self._seed(db, "dc-past", "2026-09-01", "Ship the spec")    # overdue: the lookback's, same TEXT

        brief = svc.generate(OWNER, now=now)

        due = _this_week(brief, "meeting_watch:commitments_due")
        assert [i.text for i in due] == ["1 commitment due this week"]
        lookback_due = [i for i in brief.sections["decisions"] if i.text.startswith("Commitment due")]
        # The same text is no dedup key: the overdue one (a different id) stays.
        assert [i.text for i in lookback_due] == ["Commitment due 2026-09-01: Ship the spec"]
        assert not any("2026-09-07" in i.text for i in lookback_due)
