"""The Meetings face's intelligence and aftercare verbs on the one declared contract (2026-11-08).

Imported into ``DESCRIPTORS`` by ``holdspeak/operations.py``, as ``meeting_operations.py`` is (and
built by its ``_op``). ``web/routes/meetings/intel.py`` and ``aftercare.py`` produce the routes,
``mcp/families/declared.py`` the tools. The services validate, as behind the hand-written routes.
"""
from __future__ import annotations

from typing import Any

from holdspeak.meeting_operations import Call, _op
from holdspeak.operations import _CONTRACT_REFUSALS
from holdspeak.services.errors import ConflictError

_UNAVAILABLE = {"status": "unavailable", "reason_code": "route unavailable", "selection_hash": None, "legs": []}
_HASH = {"expected_selection_hash": {"description": "planned_route.selection_hash from meeting.get."}}


def with_route(service: Any, meeting_id: Any, exc: ConflictError) -> ConflictError:
    """A refused run carries the meeting's current planned route (the face re-reads its hash there)."""
    context = dict(exc.context or {})
    if not (context.get("current_planned_route") or context.get("planned_route")):
        try:
            context["current_planned_route"] = service.get_recovery(None, meeting_id).get("planned_route")
        except Exception:
            context["current_planned_route"] = _UNAVAILABLE
        exc.context = context
    return exc


def conflict_body(exc: ConflictError) -> dict[str, Any]:
    """The 409 answer of a run gesture: the words, the route and the receipts."""
    context = dict(exc.context or {})
    route = context.get("current_planned_route") or context.get("planned_route") or context.get("current_planned_route")
    return {"success": False, "error": str(exc), "plainReason": str(exc), "code": getattr(exc, "code", "conflict"),
            "planned_route": route, "current_planned_route": route,
            "run_receipt": context.get("run_receipt"), "last_refusal": context.get("last_refusal")}


def _routed(call: Call) -> Call:
    def run(service: Any, principal: Any, args: dict[str, Any]) -> Any:
        try:
            return call(service, principal, args)
        except ConflictError as exc:
            raise with_route(service, args.get("meeting_id"), exc) from None
    return run


_M = "/api/meetings/{meeting_id}"
_I = {"service": "meeting_intel_service", "result": "the MeetingIntelService answer", "refusals": _CONTRACT_REFUSALS + (
    "NotFound: unknown meeting", "ValidationError",
    "ConflictError: reserved | running | ready | stale selection hash (with planned_route, run_receipt, last_refusal)")}
_A = {"service": "meeting_aftercare_service", "result": "the MeetingAftercareService answer",
      "refusals": _CONTRACT_REFUSALS + ("NotFound: unknown meeting, proposal or action item", "ValidationError")}

MEETING_INTEL_OPERATIONS = (
    _op("meeting.intel_jobs", "list_jobs", ("GET", "/api/intel/jobs"), "api_list_intel_jobs",
        lambda s, p, a: s.list_jobs(p, {"status": a.get("status") or "all", "limit": int(a.get("limit", 20)),
                                        "history_limit": int(a.get("history_limit", 5))}),
        "List the deferred meeting intelligence jobs with their retry history.", **_I,
        properties={"status": {"type": "string", "description": "Default all."},
                    "limit": {"type": "integer", "minimum": 1, "description": "Default 20."},
                    "history_limit": {"type": "integer", "minimum": 1, "maximum": 20, "description": "Default 5."}}),
    _op("meeting.intel_retry", "retry_job", ("POST", "/api/intel/retry/{meeting_id}"), "api_retry_intel_job",
        _routed(lambda s, p, a: s.retry_job(p, a.get("meeting_id"),
                                            expected_selection_hash=a.get("expected_selection_hash"))),
        "Queue the meeting's intelligence job again, on the selection hash read from meeting.get.", **_I,
        write=True, properties=_HASH),
    _op("meeting.intel_recovery", "get_recovery", ("GET", _M + "/intel-recovery"), "api_get_meeting_intel_recovery",
        lambda s, p, a: s.get_recovery(p, a.get("meeting_id")),
        "Read the intelligence recovery state of one meeting: its job, planned route and what is left.", **_I),
    _op("meeting.intel_recovery_retry", "retry_recovery", ("POST", _M + "/intel-recovery/retry"),
        "api_retry_meeting_intel_recovery",
        _routed(lambda s, p, a: s.retry_recovery(p, a.get("meeting_id"),
                                                 {k: v for k, v in a.items() if k != "meeting_id"})),
        "Retry the remaining intelligence of one meeting, on the selection hash read from meeting.get.", **_I,
        write=True, properties=_HASH),
    _op("meeting.intel_recovery_skip", "skip_recovery", ("POST", _M + "/intel-recovery/skip"),
        "api_skip_meeting_intel_recovery", lambda s, p, a: s.skip_recovery(p, a.get("meeting_id")),
        "Skip the remaining intelligence of one meeting (final for its summary backlog).", **_I, write=True),
    _op("meeting.aftercare", "get_aftercare", ("GET", _M + "/aftercare"), "api_get_meeting_aftercare",
        lambda s, p, a: s.get_aftercare(p, a.get("meeting_id")),
        "Read the aftercare of one meeting: action items to triage, decisions and proposals.", **_A),
    _op("meeting.aftercare_proposals", "list_proposals", ("GET", _M + "/proposals"), "api_get_meeting_proposals",
        lambda s, p, a: s.list_proposals(p, a.get("meeting_id"), a.get("status")),
        "List the actuator proposals of one meeting.", **_A, properties={"status": {"type": "string"}}),
    _op("meeting.aftercare_decide", "decide_proposal", ("POST", _M + "/proposals/{proposal_id}/decision"),
        "api_decide_meeting_proposal",
        lambda s, p, a: s.decide_proposal(p, a.get("meeting_id"), a.get("proposal_id"),
                                          {k: a.get(k) for k in ("decision", "decided_by", "grant_id")}),
        "Approve or reject one actuator proposal of a meeting. Approving only records the decision.", **_A,
        write=True, properties={"decision": {"enum": ["approved", "rejected"]}, "decided_by": {"type": "string"},
                                "grant_id": {"type": "string"}}, required=("decision",)),
)

__all__ = ["MEETING_INTEL_OPERATIONS", "conflict_body", "with_route"]
