"""PARKED 20261108 (late evening, the left-routes pass): routes no client calls; only their own tests held them.

Parked from ``holdspeak/web/routes/activity/candidates.py``: POST and DELETE /api/activity/meeting-candidates.
Not imported. Kept for history; restore with ``git revert`` of the parking commit.
"""


def _parked_body(router=None, ctx=None, **_):  # parked 2026-11-08: kept at handler indent, never mounted
 @router.post("/api/activity/meeting-candidates")
 def create(request:Request,payload:_ActivityMeetingCandidateRequest)->Any:
  try:return JSONResponse(_svc().create(_principal(request),payload.model_dump()))
  except ValidationError as e:return _err(e)
  except Exception as e:return error_500(e,log,"Failed to create activity meeting candidate")


 @router.delete("/api/activity/meeting-candidates")
 def delete(request:Request,source_connector_id:Optional[str]=None,status:Optional[str]=None)->Any:
  try:return JSONResponse(_svc().delete(_principal(request),source_connector_id,status))
  except ValidationError as e:return _err(e)
  except Exception as e:return error_500(e,log,"Failed to delete activity meeting candidates")
