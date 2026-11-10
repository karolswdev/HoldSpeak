# Parked: the separate Today meeting gather was folded into the shared history read.

def since_morning_read(db: Any, now: datetime.datetime | None = None,
                       limit: int = SINCE_MORNING_LIMIT) -> dict[str, Any]:
    """What got done since the local midnight of ``now`` (the hub's clock)."""
    local_now = (now or wall_clock_now()).astimezone()
    morning = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    start = morning.astimezone(datetime.timezone.utc)
    # A coarse SQL bound (a day before the UTC morning, as a date prefix,
    # works for every stamp shape); the exact cut is made on the parsed time.
    floor = (start - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    items: list[dict[str, Any]] = []

    def add(kind: str, ref: str, title: str, word: str, at_value: Any) -> None:
        at = _stamp(at_value)
        if at is None or at < start or at > local_now.astimezone(datetime.timezone.utc) + datetime.timedelta(minutes=5):
            return
        items.append({"kind": kind, "ref": ref, "title": title, "word": word,
                      "at": at.isoformat(timespec="seconds").replace("+00:00", "Z"), "_at": at})

    def rows(conn: Any, sql: str, *args: Any) -> list[Any]:
        try:
            return conn.execute(sql, (*args, floor)).fetchall()
        except Exception:  # a table this hub does not have yet: no rows
            return []

    with db._connection() as conn:
        for row in rows(conn, """SELECT id, task, completed_at FROM action_items
                                 WHERE status = 'done' AND completed_at >= ?"""):
            add("action", f"action_item:{row['id']}", str(row["task"] or "Task"), "Done", row["completed_at"])
        # A proposed Desk decision (a Program's Skip or merge by rule, PG16)
        # is not recorded yet: it waits for his Accept.
        for row in rows(conn, """SELECT r.id, r.decision_text, r.created_at FROM decision_records r
                                 WHERE r.deleted = 0 AND r.kind = 'decision'
                                   AND NOT EXISTS (SELECT 1 FROM desk_decisions dd
                                       WHERE r.source_type = 'desk' AND dd.id = r.source_id
                                         AND dd.deleted = 0 AND LOWER(dd.status) = 'proposed')
                                   AND r.created_at >= ?"""):
            add("decision", f"decision_record:{row['id']}", _first_line(row["decision_text"]) or "Decision",
                "Recorded", row["created_at"])
        for row in rows(conn, """SELECT n.id, n.title, n.body_markdown, d.name, m.last_modified
                                 FROM directory_memberships m
                                 JOIN notes n ON m.primitive_id = 'note:' || n.id
                                 LEFT JOIN directories d ON d.id = m.directory_id
                                 WHERE m.deleted = 0 AND n.deleted = 0 AND m.directory_id != ''
                                   AND m.directory_id != ? AND m.last_modified >= ?""", _INBOX_DIRECTORY_ID):
            name = str(row["name"] or "").strip()
            add("note", f"note:{row['id']}", str(row["title"] or "").strip() or _first_line(row["body_markdown"]) or "Note",
                f"Filed in {name}" if name else "Filed", row["last_modified"])
        for row in rows(conn, """SELECT id, document_ref, document_json, settled_at FROM channel_sends
                                 WHERE state = 'sent' AND settled_at >= ?"""):
            try:
                title = str((json.loads(row["document_json"] or "{}") or {}).get("title") or "")
            except (TypeError, ValueError):
                title = ""
            add("send", str(row["document_ref"]), title.strip() or "Document", "Sent", row["settled_at"])
        for row in rows(conn, """SELECT id, title, started_at, ended_at, intel_status FROM meetings
                                 WHERE parked = 0 AND ended_at IS NOT NULL AND started_at >= ?"""):
            if (_stamp(row["started_at"]) or start) < start:
                continue
            add("meeting", f"meeting:{row['id']}", str(row["title"] or "").strip() or "Meeting",
                "Summary stored" if row["intel_status"] == "ready" else "Held", row["ended_at"])
    items.sort(key=lambda item: item.pop("_at"), reverse=True)
    return {"since": start.isoformat().replace("+00:00", "Z"), "items": items[:max(1, int(limit))]}
