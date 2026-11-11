# PARKED: normalization and canonical creation moved to DecisionRecordService.
class _ParkedBody:
    @router.post("/from-desk")
    def create_from_desk(request: Request, body: dict[str, Any] = Body(default={})) -> Any:
        """Admit one Desk decision, then return its canonical record.

        The admitted ``decision.create`` operation owns the retained source
        row and its canonical record.  This adapter only supplies the
        producer's About/Why context, the deciders and the tags that carry
        the meeting, the Project and the Person. The record writer
        (``DecisionRecordService.create``) files the record in the Project
        and writes the Person reference in the record's own transaction, so
        a caller makes one call.
        """
        title = str(body.get("decision_text") or body.get("title") or "").strip()
        if not title:
            raise HTTPException(status_code=400, detail="decision text is required")
        status = str(body.get("status") or "accepted").strip().lower()
        if status not in {"accepted", "proposed"}:
            raise HTTPException(status_code=400, detail="status must be accepted or proposed")
        project_id = str(body.get("project_id") or "").strip()
        project_name = str(body.get("project_name") or "").strip()
        about = str(body.get("about") or project_name or "").strip()
        why = str(body.get("why") or "").strip()
        if project_id and service().live_project([project_id]) is None:
            return JSONResponse({"error": f"Unknown Project: {project_id}"}, status_code=400)
        tags = [str(tag).strip() for tag in (body.get("tags") or []) if str(tag).strip()]
        if project_id and f"project:{project_id}" not in tags:
            tags.append(f"project:{project_id}")
        meeting_id = str(body.get("meeting_id") or "").strip()
        if meeting_id and f"meeting:{meeting_id}" not in tags:
            tags.append(f"meeting:{meeting_id}")
        owner_person_id = str(body.get("owner_person_id") or "").strip()
        if owner_person_id and f"person:{owner_person_id}" not in tags:
            tags.append(f"person:{owner_person_id}")
        raw_deciders = body.get("deciders") or []
        deciders = list(dict.fromkeys(
            str(name).strip() for name in (raw_deciders if isinstance(raw_deciders, list) else [])
            if str(name).strip()
        ))
        principal_value = principal(request)
        registry = operations.for_context(ctx, "primitive_service")
        args = {
            "title": title,
            "status": status,
            "deciders": deciders,
            "context_markdown": f"About: {about}" if about else "",
            "decision_markdown": title,
            "alternatives": [],
            "consequences_markdown": f"Why: {why}" if why else "",
            "tags": tags,
        }
        try:
            decision, kernel = registry.invoke_receipted(principal_value, "decision.create", args)
            records = service()
            matches = records.records_for_source(principal_value, "desk", str(decision["id"]))
            record = matches[0] if matches else None
            if record is None:
                raise HTTPException(status_code=500, detail="canonical decision record was not created")
            record = records.get(principal_value, record["id"]) or record
            return JSONResponse(
                {"decision": decision, "record": record, **_kernel_fields(kernel)}, status_code=201,
            )
        except operations.OperationRefused as exc:
            kernel = registry.refuse(principal_value, "decision.create", exc.code, body) or {}
            return JSONResponse({"error": str(exc), **kernel}, status_code=400)
        except ServiceError as exc:
            status_code = int(exc.context.get("status") or 409)
            return JSONResponse({"error": exc.code, "detail": exc.detail, **exc.context}, status_code=status_code)
        except ValueError as exc:
            return JSONResponse({"error": str(exc), **_refusal_kernel(exc)}, status_code=400)
        except HTTPException:
            raise
        except Exception as exc:
            return error_500(exc, log, "Failed to create canonical decision")
