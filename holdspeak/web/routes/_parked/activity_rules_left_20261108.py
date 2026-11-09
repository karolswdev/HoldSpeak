"""PARKED 20261108 (late evening, the left-routes pass): routes no client calls; only their own tests held them.

Parked from ``holdspeak/web/routes/activity/rules.py``: POST /api/activity/project-rules, PUT /api/activity/project-rules/{rule_id}, POST /api/activity/project-rules/preview.
Not imported. Kept for history; restore with ``git revert`` of the parking commit.
"""


def _fields(model:Any)->dict[str,Any]:
 present=getattr(model,"model_fields_set",getattr(model,"__fields_set__",set()))
 return {key:getattr(model,key) for key in ("project_id","name","enabled","priority","match_type","pattern","entity_type") if key in present}


 @router.post("/api/activity/project-rules")
 def create(request:Request,payload:_ActivityProjectRuleRequest)->Any:
  try:return JSONResponse(_svc().create(_principal(request),payload.model_dump()))
  except ValidationError as e:return _err(e)
  except Exception as e:return error_500(e,log,"Failed to create activity project rule")
 @router.put("/api/activity/project-rules/{rule_id}")
 def update(request:Request,rule_id:str,payload:_ActivityProjectRuleRequest)->Any:
  try:return JSONResponse(_svc().update(_principal(request),rule_id,_fields(payload)))
  except (NotFound,ValidationError) as e:return _err(e)
  except Exception as e:return error_500(e,log,"Failed to update activity project rule")


 @router.post("/api/activity/project-rules/preview")
 def preview(request:Request,payload:_ActivityProjectRuleRequest)->Any:
  try:return JSONResponse(_svc().preview(_principal(request),payload.model_dump(),None))
  except ValidationError as e:return _err(e)
  except Exception as e:return error_500(e,log,"Failed to preview activity project rule")
