# Parked: digest due tasks now come from the same Follow-through board as the Door.

class _ParkedBody:
    def digest_lines(self, given: Any = None) -> list[dict[str, str]]:
        """DIR10: the digest's plain lines, no buttons: the Door tasks due
        today or late (read here), then the caller's lines (a blocker's words
        from Needs you), each in his words; a raw line is left out."""
        from . import brief_words as words

        out: list[dict[str, str]] = []
        today = self._now().astimezone().date().isoformat()
        try:
            rows = self.db.meetings.list_action_items(include_completed=False)
            due = [row for row in rows if str(getattr(row, "due", "") or "")[:10] and
                   str(getattr(row, "due", ""))[:10] <= today]
        except Exception as exc:
            log.debug(f"briefing: the Door's tasks were not read: {exc}")
            due = []
        if due:
            out.append({"kind": "door", "line": "1 task is due today." if len(due) == 1 else
                        f"{len(due)} tasks are due today."})
        for raw in given if isinstance(given, (list, tuple)) else []:
            text = words.sentence(" ".join(str(raw or "").split())[:160])
            if text and not words.fence_hits(text):
                out.append({"kind": "line", "line": text})
        return out[:6]
