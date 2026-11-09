"""PARKED 20261109 (ops/programs-work): four hand-written note-window routes, now produced.

GET /api/thoughts/for-note/{note_id}, POST /api/thoughts/open-note,
GET /api/thoughts/{thought_id}/original and
GET /api/thoughts/{thought_id}/reviews/{review_result_id} are rows in
``holdspeak/thought_operations.py``: each produces its route (same method,
path, status and answer) and its MCP tool. Kept here as they stood in
``web/routes/primitives/thoughts.py``.

Not imported. Restore with git revert of the parking commit.
"""
# ruff: noqa
# fmt: off
PARKED = True

'''
    # Static Note lookup must precede `/{thought_id}` so a Note id can never be
    # mistaken for a thought id by route matching.
    @router.get("/api/thoughts/for-note/{note_id}")
    def for_note(note_id: str, request: Request) -> Any:
        try:
            return JSONResponse(service().for_note(principal(request), note_id))
        except ServiceError as exc:
            return _error(exc)

    # Betterment Q8 (one note): every note opens in the one note window. This
    # returns the note's thought, adopting a plain note and resuming a
    # finished one; the note's drawer never changes.
    @router.post("/api/thoughts/open-note")
    async def open_note(request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            if set(body) - {"note_id"}:
                raise ValidationError("thought open-note schema is closed", code="note_open_request_invalid")
            return JSONResponse(application().open_note(principal(request), note_id=body.get("note_id")))
        except ServiceError as exc:
            return _error(exc)

    @router.get("/api/thoughts/{thought_id}/original")
    def original(thought_id: str, request: Request) -> Any:
        try:
            return JSONResponse(application().get_original(
                principal(request), thought_id=thought_id
            ))
        except ServiceError as exc:
            return _error(exc)

    @router.get("/api/thoughts/{thought_id}/reviews/{review_result_id}")
    def review(thought_id: str, review_result_id: str, request: Request) -> Any:
        try:
            return JSONResponse(
                application().review(
                    principal(request),
                    thought_id=thought_id,
                    review_result_id=review_result_id,
                )
            )
        except ServiceError as exc:
            return _error(exc)

'''
