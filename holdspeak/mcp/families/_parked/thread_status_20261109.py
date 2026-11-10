# PARKED 2026-11-09: ThreadService owns persisted status and thread existence checks.
def _parked_body():
            thread_id = str(arguments.get("thread_id") or "")
            text = str(arguments.get("text") or "")
            if not thread_id:
                raise ServiceError(
                    "thread_request_invalid",
                    "thread_id is required.",
                    context={"status": 400},
                )
            db = db_or(get_database)
            db.threads.patch(thread_id, status_line=text)
            return {"status_line": text, "thread_id": thread_id}
