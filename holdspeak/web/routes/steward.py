"""HS-163-04: Project Steward routes -- runs on HTTP.

POST /api/projects/{id}/steward/runs       -- run_once (async boundary; immediate-id)
GET  /api/projects/{id}/steward/runs       -- list runs
GET  /api/steward/runs/{run_id}            -- pollable state (phase, steps, receipts)
POST /api/steward/runs/{run_id}/stop       -- STW-003 on the wire
GET  /api/projects/{id}/steward/policy     -- get steward policy
PUT  /api/projects/{id}/steward/policy     -- update steward policy
POST /api/projects/{id}/steward/trigger    -- HS-167-02: evaluate_due + run_due NOW

Parse-and-serialize ONLY; the service owns logic.
Owner-scoped; typed errors -> correct statuses.
"""
from __future__ import annotations

import hashlib
import json
import threading
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...db.steward import ActiveRunExistsError
from ...services.project_steward_service import (
    CooldownActiveError,
    StewardDisabledError,
)
from ...logging_config import get_logger
from ...principals import UNAUTHENTICATED
from ...project_contracts import (
    generate_pcmd_id,
    generate_pstpol_id,
)
from ...services.errors import ConflictError, NotFound, ValidationError
from ...services.project_steward_service import EFFECT_KINDS
from ..context import WebContext
from ..runtime_support import error_500

log = get_logger("web.routes.steward")


def _request_hash(payload: dict[str, Any]) -> str:
    """Deterministic hash for idempotency (mirrors project_update_service)."""
    material = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=True, default=str)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:32]


def build_steward_router(ctx: WebContext) -> APIRouter:
    router = APIRouter(tags=["steward"])

    def principal(request: Request) -> Any:
        return getattr(request.state, "principal", UNAUTHENTICATED)

    # ── POST /api/projects/{project_id}/steward/runs ───────────────
    # SS9.2: persist and return a run ID immediately.
    # The async boundary: insert the queued run on the request path
    # (so STW-002 ActiveRunExistsError surfaces synchronously as 409),
    # then hand phase execution to a daemon thread.

    @router.post("/api/projects/{project_id}/steward/runs")
    async def api_start_steward_run(
        project_id: str, request: Request,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        try:
            body = payload or {}
            cmd_id = body.get("command_id")
            watermark = str(body.get("watermark", "") or "")

            req_hash = _request_hash({
                "project_id": project_id,
                "action": "run_once",
                "watermark": watermark,
            })

            # command_id replay
            if cmd_id is not None:
                existing = ctx.project_steward_service._db.projects.get_project_command(cmd_id)
                if existing is not None:
                    if (existing["status"] == "completed"
                            and existing["request_hash"] == req_hash):
                        if existing["result_json"]:
                            return JSONResponse(json.loads(existing["result_json"]))
                        return JSONResponse({"success": True, "run_id": None})
                    if existing["request_hash"] != req_hash:
                        return JSONResponse(
                            {"success": False, "code": "idempotency_conflict",
                             "message": "same command_id with different request hash"},
                            status_code=409,
                        )

            svc = ctx.project_steward_service
            p = principal(request)

            # SS9.2 immediate-id contract: insert the queued run on the
            # request thread (STW-002 surfaces here), then spawn a
            # daemon thread for phase execution.
            run_id = svc.insert_run(p, project_id, watermark=watermark)

            # Record command for replay
            _record_steward_command(
                svc._db, cmd_id or generate_pcmd_id(),
                project_id, "run_once", req_hash,
                {"success": True, "run_id": run_id},
            )

            # Phase execution on a daemon thread (conductor pattern).
            def _execute() -> None:
                try:
                    svc.execute_phases(p, run_id, project_id)
                except Exception:
                    # The engine already marks runs failed with an honest
                    # summary; the exception must not kill the server.
                    pass

            t = threading.Thread(target=_execute, daemon=True)
            t.start()

            return JSONResponse({"success": True, "run_id": run_id})

        except ActiveRunExistsError:
            return JSONResponse(
                {"success": False, "code": "active_run_exists",
                 "message": f"Project {project_id} already has an active steward run (STW-002)"},
                status_code=409,
            )
        except StewardDisabledError:
            return JSONResponse(
                {"success": False, "code": "steward_disabled",
                 "message": "The steward policy is disabled for this project"},
                status_code=409,
            )
        except CooldownActiveError as exc:
            return JSONResponse(
                {"success": False, "code": "cooldown_active",
                 "message": f"Cooling down: {exc.seconds_remaining}s remaining"},
                status_code=409,
            )
        except NotFound as exc:
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=404,
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to start steward run")

    # ── GET /api/projects/{project_id}/steward/runs ────────────────

    @router.get("/api/projects/{project_id}/steward/runs")
    async def api_list_steward_runs(
        project_id: str, request: Request,
        state: str | None = None,
        limit: int = 100,
    ) -> Any:
        try:
            svc = ctx.project_steward_service
            runs = svc._db.steward_runs.list_runs(
                project_id, state=state, limit=limit,
            )
            return JSONResponse({"runs": _serialize_runs(runs)})
        except Exception as exc:
            return error_500(exc, log, "Failed to list steward runs")

    # ── GET /api/steward/runs/{run_id} ─────────────────────────────
    # Pollable state: phase, steps, receipts.

    @router.get("/api/steward/runs/{run_id}")
    async def api_get_steward_run(run_id: str, request: Request) -> Any:
        try:
            svc = ctx.project_steward_service
            run = svc._db.steward_runs.get_run(run_id)
            if run is None:
                return JSONResponse(
                    {"code": "not_found", "message": f"Unknown steward run: {run_id}"},
                    status_code=404,
                )
            steps = svc._db.steward_steps.list_steps(run_id)
            return JSONResponse({
                "run": _serialize_run(run),
                "steps": _serialize_steps(steps),
            })
        except Exception as exc:
            return error_500(exc, log, "Failed to get steward run")

    # ── POST /api/steward/runs/{run_id}/stop ───────────────────────
    # STW-003 on the wire: set the durable stop request and return.

    @router.post("/api/steward/runs/{run_id}/stop")
    async def api_stop_steward_run(run_id: str, request: Request) -> Any:
        try:
            svc = ctx.project_steward_service
            run = svc._db.steward_runs.get_run(run_id)
            if run is None:
                return JSONResponse(
                    {"code": "not_found", "message": f"Unknown steward run: {run_id}"},
                    status_code=404,
                )
            svc.stop(run_id)
            return JSONResponse({"success": True, "run_id": run_id})
        except Exception as exc:
            return error_500(exc, log, "Failed to stop steward run")

    # ── GET /api/projects/{project_id}/steward/policy ──────────────

    @router.get("/api/projects/{project_id}/steward/policy")
    async def api_get_steward_policy(
        project_id: str, request: Request,
    ) -> Any:
        try:
            svc = ctx.project_steward_service
            policy = svc._db.steward_policies.get_policy_for_project(project_id)
            if policy is None:
                return JSONResponse({"policy": None})
            return JSONResponse({"policy": _serialize_policy(policy)})
        except Exception as exc:
            return error_500(exc, log, "Failed to get steward policy")

    # ── PUT /api/projects/{project_id}/steward/policy ──────────────
    # Typed validation: eligible effect kinds against EFFECT_KINDS,
    # bounds are ints with sane ranges.

    @router.put("/api/projects/{project_id}/steward/policy")
    async def api_put_steward_policy(
        project_id: str, payload: dict[str, Any], request: Request,
    ) -> Any:
        try:
            svc = ctx.project_steward_service

            # Validate eligible_effect_kinds
            eligible = payload.get("eligible_effect_kinds")
            if eligible is not None:
                if not isinstance(eligible, list):
                    return JSONResponse(
                        {"success": False, "code": "validation_error",
                         "message": "eligible_effect_kinds must be a list"},
                        status_code=400,
                    )
                invalid_kinds = [k for k in eligible if k not in EFFECT_KINDS]
                if invalid_kinds:
                    return JSONResponse(
                        {"success": False, "code": "validation_error",
                         "message": f"Invalid effect kinds: {invalid_kinds}. "
                                    f"Valid: {list(EFFECT_KINDS)}"},
                        status_code=400,
                    )

            # Validate int bounds
            for field in ("max_retries", "max_actions_per_run", "cooldown_seconds"):
                val = payload.get(field)
                if val is not None:
                    if not isinstance(val, int) or val < 0:
                        return JSONResponse(
                            {"success": False, "code": "validation_error",
                             "message": f"{field} must be a non-negative integer"},
                            status_code=400,
                        )
                    if field == "max_retries" and val > 100:
                        return JSONResponse(
                            {"success": False, "code": "validation_error",
                             "message": "max_retries cannot exceed 100"},
                            status_code=400,
                        )
                    if field == "max_actions_per_run" and val > 1000:
                        return JSONResponse(
                            {"success": False, "code": "validation_error",
                             "message": "max_actions_per_run cannot exceed 1000"},
                            status_code=400,
                        )
                    if field == "cooldown_seconds" and val > 86400:
                        return JSONResponse(
                            {"success": False, "code": "validation_error",
                             "message": "cooldown_seconds cannot exceed 86400"},
                            status_code=400,
                        )

            enabled = payload.get("enabled")
            if enabled is not None and not isinstance(enabled, bool):
                return JSONResponse(
                    {"success": False, "code": "validation_error",
                     "message": "enabled must be a boolean"},
                    status_code=400,
                )

            # HS-164-04: unattended_enabled validation
            unattended_enabled = payload.get("unattended_enabled")
            if unattended_enabled is not None and not isinstance(unattended_enabled, bool):
                return JSONResponse(
                    {"success": False, "code": "validation_error",
                     "message": "unattended_enabled must be a boolean"},
                    status_code=400,
                )

            # HS-167-02: evaluation_cadence_minutes validation + range fence.
            # Floor = 1 minute (conductor tick = 60s can honor this).
            # Ceiling = 10080 minutes (7 days).
            cadence_minutes = payload.get("evaluation_cadence_minutes")
            if cadence_minutes is not None:
                if not isinstance(cadence_minutes, int) or cadence_minutes < 1:
                    return JSONResponse(
                        {"success": False, "code": "validation_error",
                         "message": "evaluation_cadence_minutes must be an integer >= 1"},
                        status_code=400,
                    )
                if cadence_minutes > 10080:
                    return JSONResponse(
                        {"success": False, "code": "validation_error",
                         "message": "evaluation_cadence_minutes cannot exceed 10080 (7 days)"},
                        status_code=400,
                    )

            # Upsert: get or create policy
            existing = svc._db.steward_policies.get_policy_for_project(project_id)
            if existing is None:
                policy_id = generate_pstpol_id()
                svc._db.steward_policies.insert_policy(
                    policy_id=policy_id,
                    project_id=project_id,
                    eligible_effect_kinds_json=json.dumps(eligible or []),
                    max_retries=payload.get("max_retries", 3),
                    max_actions_per_run=payload.get("max_actions_per_run", 10),
                    cooldown_seconds=payload.get("cooldown_seconds", 0),
                    bounds_json=json.dumps(payload.get("bounds", {})),
                    enabled=1 if payload.get("enabled", True) else 0,
                    unattended_enabled=1 if payload.get("unattended_enabled", False) else 0,
                )
            else:
                policy_id = existing["id"]
                update_kwargs: dict[str, Any] = {}
                if eligible is not None:
                    update_kwargs["eligible_effect_kinds_json"] = json.dumps(eligible)
                if payload.get("max_retries") is not None:
                    update_kwargs["max_retries"] = payload["max_retries"]
                if payload.get("max_actions_per_run") is not None:
                    update_kwargs["max_actions_per_run"] = payload["max_actions_per_run"]
                if payload.get("cooldown_seconds") is not None:
                    update_kwargs["cooldown_seconds"] = payload["cooldown_seconds"]
                if payload.get("bounds") is not None:
                    update_kwargs["bounds_json"] = json.dumps(payload["bounds"])
                if enabled is not None:
                    update_kwargs["enabled"] = 1 if enabled else 0
                if unattended_enabled is not None:
                    update_kwargs["unattended_enabled"] = 1 if unattended_enabled else 0
                if update_kwargs:
                    svc._db.steward_policies.update_policy(
                        policy_id, **update_kwargs,
                    )

            # HS-167-02: apply cadence to all watches for this project.
            if cadence_minutes is not None:
                try:
                    watches = svc._db.automations.list_project_watches(project_id)
                    for w in watches:
                        svc._db.automations.update_watch_spec(
                            w["id"],
                            evaluation_cadence_minutes=cadence_minutes,
                        )
                except Exception:
                    pass  # Best-effort; the policy save must succeed.

            # Return the updated policy
            policy = svc._db.steward_policies.get_policy(policy_id)

            # HS-164-04: steward.configured event at the policy PUT seam.
            try:
                from ...services.service_event_ledger import ServiceEventLedger
                ledger = ServiceEventLedger(svc._db)
                p = principal(request)
                with svc._db._connection() as conn:
                    ledger.append_in_transaction(
                        conn,
                        p,
                        event_type="steward.configured",
                        producer="steward.routes",
                        subject_ref=f"steward_policy:{policy_id}",
                        source_revision="",
                        facts={
                            "policy_id": policy_id,
                            "project_id": project_id,
                            "enabled": bool(policy["enabled"]) if policy else False,
                            "unattended_enabled": bool(
                                policy.get("unattended_enabled", 0)
                            ) if policy else False,
                        },
                        refs=[
                            f"project:{project_id}",
                            f"steward_policy:{policy_id}",
                        ],
                    )
            except Exception:
                pass  # Event emission must never fail the policy response.

            return JSONResponse({"success": True, "policy": _serialize_policy(policy)})
        except Exception as exc:
            return error_500(exc, log, "Failed to update steward policy")

    # ── POST /api/projects/{project_id}/steward/trigger ──────────────
    # HS-167-02: evaluate_due + run_due NOW through set_scheduler_services.
    # Unwired = typed refusal (honest).  Reuses the 163 same-watermark
    # contract -- never route-level dedup.

    @router.post("/api/steward/trigger")
    async def api_trigger_steward(request: Request) -> Any:
        try:
            from ...workbench_conductor import get_scheduler_services
            p = principal(request)
            wired_watch, wired_steward = get_scheduler_services()

            if wired_watch is None and wired_steward is None:
                return JSONResponse(
                    {"success": False, "code": "scheduler_not_wired",
                     "message": "The conductor's scheduler services are not wired "
                                "(set_scheduler_services has not been called)"},
                    status_code=503,
                )

            # Desk-wide by contract: evaluate_due/run_due are principal-
            # scoped and never raise (per-watch isolation inside); an
            # exception here is a real fault and is surfaced, not dressed
            # as success.
            eval_outcomes = wired_watch.evaluate_due(p) if wired_watch is not None else []
            run_outcomes = wired_steward.run_due(p) if wired_steward is not None else []

            return JSONResponse({
                "success": True,
                "evaluate_outcomes": eval_outcomes,
                "run_outcomes": run_outcomes,
            })
        except Exception as exc:
            return error_500(exc, log, "Failed to trigger steward")

    return router


# ── Serialization helpers ────────────────────────────────────────────


def _serialize_run(run: dict[str, Any]) -> dict[str, Any]:
    """Serialize a run row for the wire (no raw internal IDs beyond house conventions)."""
    summary = {}
    if run.get("summary_json"):
        try:
            summary = json.loads(run["summary_json"])
        except (json.JSONDecodeError, TypeError):
            pass
    return {
        "id": run["id"],
        "project_id": run["project_id"],
        "policy_id": run.get("policy_id"),
        "state": run["state"],
        "phase": run["phase"],
        "requested_by": run.get("requested_by", ""),
        "watermark": run.get("watermark", ""),
        "summary": summary,
        "created_at": run.get("created_at"),
        "updated_at": run.get("updated_at"),
        "started_at": run.get("started_at"),
        "completed_at": run.get("completed_at"),
        "stop_requested_at": run.get("stop_requested_at"),
    }


def _serialize_runs(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_serialize_run(r) for r in runs]


def _serialize_step(step: dict[str, Any]) -> dict[str, Any]:
    """Serialize a step row for the wire: phase, seq, state, effect_kind,
    idempotency_key, expected/observed, receipt, error."""
    expected = {}
    if step.get("expected_state_json"):
        try:
            expected = json.loads(step["expected_state_json"])
        except (json.JSONDecodeError, TypeError):
            pass
    observed = {}
    if step.get("observed_state_json"):
        try:
            observed = json.loads(step["observed_state_json"])
        except (json.JSONDecodeError, TypeError):
            pass
    receipt = {}
    if step.get("receipt_json"):
        try:
            receipt = json.loads(step["receipt_json"])
        except (json.JSONDecodeError, TypeError):
            pass
    error = None
    if step.get("error_json"):
        try:
            error = json.loads(step["error_json"])
        except (json.JSONDecodeError, TypeError):
            pass
    return {
        "id": step["id"],
        "phase": step["phase"],
        "seq": step["seq"],
        "state": step["state"],
        "effect_kind": step["effect_kind"],
        "idempotency_key": step["idempotency_key"],
        "expected": expected,
        "observed": observed,
        "receipt": receipt,
        "error": error,
    }


def _serialize_steps(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_serialize_step(s) for s in steps]


def _serialize_policy(policy: dict[str, Any] | None) -> dict[str, Any] | None:
    if policy is None:
        return None
    eligible = []
    if policy.get("eligible_effect_kinds_json"):
        try:
            eligible = json.loads(policy["eligible_effect_kinds_json"])
        except (json.JSONDecodeError, TypeError):
            pass
    bounds = {}
    if policy.get("bounds_json"):
        try:
            bounds = json.loads(policy["bounds_json"])
        except (json.JSONDecodeError, TypeError):
            pass
    yolo = {}
    if policy.get("yolo_flags_json"):
        try:
            yolo = json.loads(policy["yolo_flags_json"])
        except (json.JSONDecodeError, TypeError):
            pass
    return {
        "id": policy["id"],
        "project_id": policy["project_id"],
        "eligible_effect_kinds": eligible,
        "yolo_flags": yolo,
        "max_retries": policy["max_retries"],
        "max_actions_per_run": policy["max_actions_per_run"],
        "cooldown_seconds": policy["cooldown_seconds"],
        "bounds": bounds,
        "enabled": bool(policy["enabled"]),
        "unattended_enabled": bool(policy.get("unattended_enabled", 0)),
        "created_at": policy.get("created_at"),
        "updated_at": policy.get("updated_at"),
    }


def _record_steward_command(
    db: Any,
    command_id: str,
    project_id: str,
    command_kind: str,
    request_hash: str,
    result: dict[str, Any],
) -> None:
    """Record a completed steward command in the project_commands ledger."""
    from datetime import datetime
    now_iso = datetime.now().isoformat()
    result_json = json.dumps(result, ensure_ascii=False, default=str)
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO project_commands (
                id, project_id, command_kind, request_hash,
                status, result_json, completed_at, created_at
            ) VALUES (?, ?, ?, ?, 'completed', ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                status = 'completed',
                result_json = excluded.result_json,
                completed_at = excluded.completed_at
            """,
            (
                command_id, project_id, command_kind, request_hash,
                result_json, now_iso, now_iso,
            ),
        )
