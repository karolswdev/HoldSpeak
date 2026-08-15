"""Transport-neutral mesh inbox and relay operations.

HS-131-16 (repair R1) makes the relay legs observe themselves.

Generic service observation serializes whatever a method was handed and whatever
it returned. On every other service that is exactly right. On this one the
arguments are a node's bearer credential and a worker's terminal report, and the
return value is a prompt plus a signed hub dispatch offer — so the ordinary
decorator would write a token, a prompt, a completion, and a hub warrant into
``pipeline_events`` on every single poll.

So the relay legs are journaled EXPLICITLY here, with content-free projections:
identifiers, generations, outcomes, and a named refusal class. The sensitive work
stays inside private methods and inside :class:`MeshRelayAuthority`, where no
observer wrapper reaches it. ``list_inbox`` keeps ordinary observation — it
carries no credential and no prompt.
"""
from __future__ import annotations

import json
import time
import uuid
from contextlib import contextmanager
from typing import Any, Iterator

from holdspeak.services.observer import (
    NullObserver,
    PipelineEvent,
    PipelineObserver,
    observed,
)

from ..db.core import Database
from ..principals import Principal, PrincipalKind
from ..mesh_authority import MeshAuthorityRefused
from ..mesh_authority.refusals import NODE_AUTHENTICATION_REQUIRED, NODE_IDENTITY_MISMATCH
from .errors import ConflictError, ServiceError, ValidationError
from .mesh_relay_authority import MeshRelayAuthority

#: Everything a relay-leg journal entry is allowed to say. A key outside this
#: set never reaches an observer row, so the projection cannot drift back into
#: carrying content by someone adding a "helpful" field.
JOURNAL_FIELDS = frozenset(
    {"node_id", "generation", "job_id", "offer_id", "claimed", "duplicate", "settled"}
)


def _who(credential: Any) -> dict[str, Any]:
    """The caller, as two identifiers. Never the credential itself."""
    return {
        "node_id": str(getattr(credential, "node_id", "") or ""),
        "generation": int(getattr(credential, "generation", 0) or 0),
    }


def _settlement_facts(settled: dict[str, Any]) -> dict[str, Any]:
    return {
        "job_id": str(settled.get("job_id") or ""),
        "offer_id": str(settled.get("offer_id") or ""),
        "duplicate": bool(settled.get("duplicate")),
        "settled": bool(settled.get("success")),
    }


def _facts(values: dict[str, Any]) -> str:
    """Render one journal projection, allow-listed field by field."""
    safe = {name: values[name] for name in sorted(values) if name in JOURNAL_FIELDS}
    return json.dumps(safe, separators=(",", ":"), sort_keys=True)


class MeshService:
    def __init__(
        self,
        db: Database,
        kernel: Any | None = None,
        *,
        observer: PipelineObserver | None = None,
        token_store: Any | None = None,
        authority: Any | None = None,
    ) -> None:
        self._db, self._kernel = db, kernel
        self._observer = observer or NullObserver()
        self._authority = authority or MeshRelayAuthority(db, kernel, token_store=token_store)

    # ── content-free journaling (repair R1) ──────────────────────────

    @contextmanager
    def _journal(
        self, method: str, principal: Any, facts: dict[str, Any]
    ) -> Iterator[dict[str, Any]]:
        """Journal one relay leg by IDENTIFIER, never by content.

        What lands in ``pipeline_events`` is the node id, the credential
        generation, the job and offer ids, and — when the leg refuses — the fixed
        refusal class. The node token, the prompt, the completion, the hub
        warrant, the signed offer, the worker report, and any raw exception text
        are structurally absent: they are never put into ``facts``.
        """
        started = time.time()
        summary: dict[str, Any] = {}
        error: str | None = None
        code: str | None = None
        try:
            yield summary
        except ServiceError as exc:
            error = code = str(exc.code)
            raise
        except MeshAuthorityRefused as exc:
            error = code = str(exc.reason)
            raise
        except BaseException as exc:
            # The CLASS of the failure, never its message: an unexpected
            # exception can carry a prompt or a credential in its text.
            error = type(exc).__name__
            raise
        finally:
            self._emit(method, principal, facts, summary, error, code, started)

    def _emit(
        self,
        method: str,
        principal: Any,
        facts: dict[str, Any],
        summary: dict[str, Any],
        error: str | None,
        code: str | None,
        started: float,
    ) -> None:
        try:
            kind = principal.kind.value
            identity = principal.identity
        except AttributeError:
            kind, identity = "unknown", ""
        event = PipelineEvent(
            event_id=str(uuid.uuid4()),
            timestamp=started,
            service=type(self).__name__,
            method=method,
            principal_kind=kind,
            principal_identity=identity,
            args_summary=_facts(facts),
            result_summary=_facts(summary),
            error=error,
            error_code=code,
            duration_ms=(time.time() - started) * 1000,
            correlation_id=str(uuid.uuid4()),
            is_async=False,
        )
        try:
            self._observer.on_event(event)
        except Exception:  # pragma: no cover - an observer never breaks a leg
            pass

    def _relay_warrant_live(self, job_id: str) -> bool:
        return self._authority.warrant_live(job_id)

    @staticmethod
    def _require_node(principal: Principal, credential: Any) -> Any:
        """The relay edge belongs to an authenticated NODE and to nobody else.

        Article XI.3: the caller supplies neither its principal nor its
        authority. A browser owner token, an agent credential, an unauthenticated
        request, and a ``node`` field in the request body all refuse HERE —
        before any queue mutation, any signature, and any settlement.
        """
        if principal is None or principal.kind is not PrincipalKind.NODE:
            raise ServiceError(
                NODE_AUTHENTICATION_REQUIRED,
                "the mesh relay edge requires an authenticated node credential",
                context={"status": 403},
            )
        if credential is None or not getattr(credential, "node_id", ""):
            raise ServiceError(
                NODE_AUTHENTICATION_REQUIRED,
                "the mesh relay edge requires an authenticated node credential",
                context={"status": 403},
            )
        if credential.node_id != principal.identity:
            raise ServiceError(
                NODE_IDENTITY_MISMATCH,
                "the presented node credential is not this principal",
                context={"status": 403},
            )
        return credential

    @observed
    def list_inbox(self, principal: Principal, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        from ..intel_queue import build_runtime_queue_frame
        from ..operation_policy import commitment_labels, operation_for_proposal

        jobs: list[dict[str, Any]] = []
        intel_frame = build_runtime_queue_frame(self._db)
        for job in intel_frame["jobs"]:
            if str(job.get("status") or "") in ("queued", "running"):
                jobs.append({
                    "kind": "intel", "id": str(job.get("id") or ""),
                    "label": str(job.get("label") or ""),
                    "status": str(job.get("status") or "queued"),
                    "meeting_id": job.get("meeting_id"), "attempts": int(job.get("attempts") or 0),
                })
        for job in self._db.plugins.list_plugin_run_jobs(status="queued", limit=20):
            jobs.append({
                "kind": "plugin", "id": f"plugin:{job.id}", "label": job.plugin_id,
                "status": job.status, "meeting_id": job.meeting_id, "attempts": int(job.attempts or 0),
            })
        proposals = []
        for proposal in self._db.actuators.list_pending_proposals(limit=50):
            operation = operation_for_proposal(proposal)
            policy = dict(getattr(proposal, "policy_snapshot", {}) or {})
            if policy.get("outcome") == "refused":
                continue
            proposals.append({
                "id": proposal.id, "origin": proposal.origin, "meeting_id": proposal.meeting_id,
                "target": proposal.target, "action": proposal.action, "preview": proposal.preview,
                "status": proposal.status, "review_decision": proposal.review_decision,
                "authorization_state": proposal.authorization_state,
                "execution_state": proposal.execution_state, "operation": operation.to_dict(),
                "policy_snapshot": policy, "commitment": commitment_labels(operation),
                "created_at": proposal.created_at,
            })
        return {"jobs": jobs, "proposals": proposals, "counts": {
            "queued": int(intel_frame.get("queued") or 0),
            "running": int(intel_frame.get("running") or 0),
            "failed": int(intel_frame.get("failed") or 0),
            "pending_approvals": len(proposals),
        }}

    def claim_relay(
        self, principal: Principal, payload: dict[str, Any], *, credential: Any = None
    ) -> dict[str, Any]:
        """One authenticated poll: stamp liveness, and sign at most one offer.

        The node the queue is searched for comes from the CREDENTIAL, never from
        ``payload["node"]`` — that field was the whole side door.
        """
        with self._journal("claim_relay", principal, _who(credential)) as summary:
            snapshot = self._require_node(principal, credential)
            claimed = self._authority.claim(snapshot, payload.get("claim_nonce"))
            if claimed is None:
                summary["claimed"] = False
                return {"job": None, "dispatch_offer": None}
            summary.update(
                claimed=True,
                job_id=str((claimed.get("job") or {}).get("id") or ""),
                offer_id=str(
                    ((claimed.get("dispatch_offer") or {}).get("offer") or {}).get("offer_id") or ""
                ),
            )
            return claimed

    def complete_relay(
        self, principal: Principal, job_id: str, payload: dict[str, Any], *, credential: Any = None
    ) -> dict[str, Any]:
        facts = {**_who(credential), "job_id": str(job_id)}
        with self._journal("complete_relay", principal, facts) as summary:
            snapshot = self._require_node(principal, credential)
            result = payload.get("result")
            # EVERY string is a result, including the empty one (repair R10).
            # The worker already receipted this attempt as succeeded and bound
            # the digest of exactly this string; refusing it only here would
            # leave a truthful local receipt facing a rejected settlement.
            if not isinstance(result, str):
                raise ValidationError("result must be a string")
            settled = self._settle(snapshot, job_id, payload, success=True)
            summary.update(_settlement_facts(settled))
            return settled

    def fail_relay(
        self, principal: Principal, job_id: str, payload: dict[str, Any], *, credential: Any = None
    ) -> dict[str, Any]:
        facts = {**_who(credential), "job_id": str(job_id)}
        with self._journal("fail_relay", principal, facts) as summary:
            snapshot = self._require_node(principal, credential)
            settled = self._settle(snapshot, job_id, payload, success=False)
            summary.update(_settlement_facts(settled))
            return settled

    def _settle(
        self, snapshot: Any, job_id: str, payload: dict[str, Any], *, success: bool
    ) -> dict[str, Any]:
        """The report-bearing half, private so no observer wrapper sees it."""
        try:
            return self._authority.settle(snapshot, job_id, payload, success=success)
        except MeshAuthorityRefused as exc:
            raise ConflictError(str(exc.reason), code=exc.reason) from None
