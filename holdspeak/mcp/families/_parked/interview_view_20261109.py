# PARKED 2026-11-09: InterviewService owns the model-context projection.
def _parked_body():
        def model_view() -> dict[str, Any]:
            path = service._db.threads.list_path(arguments["thread_id"])
            user_id = next((message.id for message in reversed(path) if message.role == "user" and not service._db.threads.is_draft_message(message.id)), "")
            return service.context(arguments["thread_id"], user_id)
        if name == "interview.get":
            return model_view()
