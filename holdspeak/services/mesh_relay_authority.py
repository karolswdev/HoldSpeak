"""Hub-side mesh dispatch authority (HS-131-16, design §2 and §6).

Two transactions live here, and nothing else does:

* **Claim.** Inside one ``BEGIN IMMEDIATE`` critical section the hub proves that a
  still-queued job, its stable destination identity, its enqueue-time credential
  generation, the live kernel warrant, the admitted deployment revision, and the
  context-authenticated attempt ordinal are all true TOGETHER, then signs exactly
  one dispatch offer and performs the guarded ``queued → running`` transition.
  Anything less produces no offer at all.

* **Settlement.** The hub independently revalidates the caller, the offer it
  itself signed, the worker's MACed terminal report, the ordinal cohort, the
  result digest, and its own still-live authority before the first guarded
  ``running → terminal`` update. Worker success cannot force hub acceptance.

The hub's warrant secret and the per-node Ed25519 private key never leave this
process. The worker's local receipts are never rewritten from here, and this
module never rewrites the hub receipt from a worker assertion.
"""

from __future__ import annotations

import copy
import time
from contextlib import contextmanager, nullcontext
from datetime import datetime
from typing import Any, Iterator, Mapping, Optional

from ..deployment_revisions import DeploymentRevision
from ..mesh_authority import (
    MeshAuthorityRefused,
    build_authority_expectation,
    build_offer,
    canonical_job_payload,
    derive_worker_execution_revision,
    payload_digest,
    sign_offer,
    validate_report_shape,
    verify_report_mac,
    warrant_binding,
    worker_job_view,
)
from ..mesh_authority.refusals import (
    CREDENTIAL_STALE,
    CREDENTIAL_UNAVAILABLE,
    REPORT_COHORT_MISMATCH,
    REPORT_CONFLICT,
    REPORT_MAC_INVALID,
    REPORT_RESULT_MISMATCH,
    SETTLEMENT_AUTHORITY_INVALID,
    SETTLEMENT_EXPIRED,
    SETTLEMENT_NOT_AVAILABLE,
)
from ..mesh_authority.report import canonical_report_bytes, report_digest, result_digest
from .errors import ConflictError, ValidationError

#: How long a worker has to begin acting on an offer, and the PROTOCOL CAP on how
#: long the whole cohort may take, measured MONOTONICALLY on the worker (design
#: §2, ruling 1). The signed budget is the smallest of this cap, the relay row's
#: own remaining deadline, and the hub warrant's remaining execution lifetime —
#: an offer can never buy more physical time than the authority behind it has.
DISPATCH_WITHIN_SECONDS = 30.0
COMPLETE_WITHIN_SECONDS = 120.0

#: The one operation a mesh relay job may ever be. The hub compares the
#: PERSISTED operation row's own ``name``/``version`` against this, rather than
#: writing the expected constant into an offer regardless of state (repair R2.1).
KERNEL_OPERATION_NAME = "inference.invoke"
KERNEL_OPERATION_VERSION = 1


@contextmanager
def _fixed_connection(conn: Any) -> Iterator[Any]:
    """Hand out one already-open connection and never commit or close it.

    The OUTER ``BEGIN IMMEDIATE`` owns the transaction; this only lets a
    connection-shaped consumer read inside it.
    """
    yield conn


def _bound_store(store: Any, conn: Any) -> Any:
    """The same kernel store, reading on the outer transaction's connection.

    Repair R2.10. A journal store checks a connection out of the shared factory
    per call; on the thread that already holds the claim/settlement transaction
    that yields a SECOND, short-lived connection — and therefore a second
    snapshot of exactly the operation, warrant, and revocation state the
    transaction is deciding against. Re-pointing this one store's connection
    factory at the open transaction keeps every decisive read on one snapshot
    without touching generic connection machinery.

    A store that is not database-backed (it has no connection factory) has no
    second snapshot to create and is used unchanged.
    """
    factory = getattr(store, "_connection", None)
    if factory is None or conn is None:
        return store
    bound = copy.copy(store)
    bound._connection = lambda: _fixed_connection(conn)
    return bound


class MeshRelayAuthority:
    """The hub's half of the two-proof protocol."""

    def __init__(
        self,
        db: Any,
        kernel: Any | None = None,
        *,
        token_store: Any | None = None,
        clock: Any = time.time,
    ) -> None:
        self._db = db
        self._kernel = kernel
        self._token_store = token_store
        self._clock = clock

    # ── shared authority reads ───────────────────────────────────────

    def _broker(self) -> Any:
        if self._kernel is not None:
            return self._kernel
        from ..kernel.runtime import _service

        return _service()

    def _live_authority(
        self, envelope: Any, *, conn: Any = None
    ) -> Optional[tuple[Mapping[str, Any], DeploymentRevision, int, Mapping[str, Any]]]:
        """The hub's own truth about one queued envelope, or ``None``.

        Returns ``(warrant, revision, attempt_ordinal, operation)`` only when the
        warrant verifies, the PERSISTED operation is still ``inference.invoke@1``,
        claimed, and unrevoked, the target binds the exact admitted revision, and
        execution has not expired. The ordinal comes from the envelope the
        CONTEXT-gated enqueue wrote, never from a claim request field.

        With ``conn`` the kernel reads happen on the caller's open transaction
        (repair R2.10); without one — the standalone liveness probe — they use
        the broker's ordinary connection.
        """
        if not isinstance(envelope, Mapping):
            return None
        warrant = envelope.get("warrant")
        fields = envelope.get("deployment_revision")
        ordinal = envelope.get("attempt_ordinal")
        if not isinstance(warrant, Mapping) or not isinstance(fields, Mapping):
            return None
        if not isinstance(ordinal, int) or isinstance(ordinal, bool) or ordinal < 1:
            return None
        try:
            stated = DeploymentRevision(**dict(fields))
        except (KeyError, TypeError, ValueError):
            return None
        if stated.id != DeploymentRevision.from_identity(stated.identity()).id:
            return None
        binding = f"deployment-revision:{stated.id}"
        store = _bound_store(self._broker().store, conn)
        operation_id = str(warrant.get("operation_id") or "")
        if not operation_id or not store.valid_warrant(warrant):
            return None
        operation = store.operation(operation_id)
        if operation is None:
            return None
        if (
            operation.get("warrant") != warrant
            or warrant.get("target_binding") != binding
            or operation.get("target_ref") != binding
            or operation.get("warrant_revoked")
            or operation.get("state") != "claimed"
            or float(warrant.get("execution_expires_at") or 0) <= self._clock()
        ):
            return None
        # The STORED operation says what kind of act this authority is for
        # (repair R2.1). Writing `inference.invoke@1` into an offer because the
        # relay leg only ever means that would make the field a decoration; read
        # it, and an operation that is something else signs nothing.
        if (
            str(operation.get("name") or "") != KERNEL_OPERATION_NAME
            or int(operation.get("version") or 0) != KERNEL_OPERATION_VERSION
        ):
            return None
        return warrant, stated, ordinal, operation

    @staticmethod
    def _stored_operation_kind(operation: Mapping[str, Any]) -> str:
        """``name@version`` as the kernel row actually stores them."""
        return f"{str(operation.get('name') or '')}@{int(operation.get('version') or 0)}"

    def warrant_live(self, job_id: str) -> bool:
        """The established hub-side liveness check, kept for the relay result gate."""
        job = self._db.mesh_relay.get(job_id)
        return job is not None and self._live_authority(job.envelope) is not None

    # ── the claim transaction ────────────────────────────────────────

    def claim(self, snapshot: Any, claim_nonce: str) -> Optional[dict[str, Any]]:
        """Sign at most one dispatch offer for this authenticated node.

        The node-custody lock is held from the signing-key read through the SQL
        commit (repair R4), so a rotate, revoke, or re-pair either lands entirely
        before this claim or waits for it: there is one winner, and the loser is
        a NAMED refusal rather than an offer signed under a credential that has
        already stopped existing.
        """
        nonce = str(claim_nonce or "").strip()
        if not nonce:
            raise ValidationError("claim_nonce must be a non-empty string")

        def authorize(job: Any, conn: Any) -> Optional[dict[str, Any]]:
            live = self._live_authority(job.envelope, conn=conn)
            if live is None:
                return None
            warrant, relay_revision, ordinal, operation = live
            # The relay revision must actually name THIS node, and the derived
            # execution revision must be constructible; a mesh destination that
            # cannot execute locally never becomes an offer.
            if relay_revision.node != snapshot.name:
                return None
            try:
                execution_revision = derive_worker_execution_revision(relay_revision)
            except MeshAuthorityRefused:
                return None
            now = self._clock()
            complete_within = self._signed_budget(job, warrant, now)
            if complete_within <= 0:
                # There is no time left to buy. The row expires honestly at its
                # own deadline instead of dispatching physical work that could
                # never be settled.
                return None
            dispatch_within = min(DISPATCH_WITHIN_SECONDS, complete_within)
            # Derived from the PERSISTED row and the PERSISTED kernel operation,
            # not from the locals that assemble the offer below (repair R2.1).
            # The destination pair is what the queue row itself says, and the
            # operation id/kind and warrant binding are what the kernel row
            # itself says — so crossed or stale construction disagrees with the
            # body the very same transaction signs.
            expectation = build_authority_expectation(
                job_id=job.id,
                hub_operation_id=str(operation.get("operation_id") or ""),
                operation_kind=self._stored_operation_kind(operation),
                warrant_binding=warrant_binding(operation.get("warrant") or {}),
                relay_revision_id=relay_revision.id,
                execution_revision_id=execution_revision.id,
                destination_node_id=str(job.destination_node_id or ""),
                destination_generation=int(job.destination_generation or 0),
                attempt_ordinal=ordinal,
                dispatch_within_seconds=dispatch_within,
                complete_within_seconds=complete_within,
                hub_settlement_deadline=float(now) + float(complete_within),
            )
            offer = build_offer(
                key_id=snapshot.key_id,
                claim_nonce=nonce,
                job_id=job.id,
                hub_operation_id=str(warrant.get("operation_id") or ""),
                node_name=snapshot.name,
                node_id=snapshot.node_id,
                credential_generation=snapshot.generation,
                relay_revision=relay_revision,
                execution_revision=execution_revision,
                first_ordinal=ordinal,
                payload_sha256=payload_digest(canonical_job_payload(job.to_dict())),
                warrant_binding=warrant_binding(warrant),
                dispatch_within_seconds=dispatch_within,
                complete_within_seconds=complete_within,
                authority_expectation=expectation,
                now=now,
            )
            signing = self._db_signing_snapshot(snapshot)
            signature = sign_offer(offer, bytes.fromhex(signing.offer_private_key))
            return {
                "offer": offer,
                "signature": signature,
                "authority_expectation": expectation,
            }

        with self._custody_lock():
            claimed = self._db.mesh_relay.claim_signed(
                node_name=snapshot.name,
                node_id=snapshot.node_id,
                generation=snapshot.generation,
                claim_nonce=nonce,
                authorize=authorize,
            )
        if claimed is None:
            return None
        job, signed = claimed
        # Repair R3: the worker receives an id and the canonical product payload.
        # The hub's kernel envelope, its warrant, the deployment proof, and every
        # stored proof column stay here. Repair R2.1 adds ONE content-free
        # sibling — the live-authority expectation whose canonical hash the
        # signature already covers.
        return {
            "job": worker_job_view(job.to_dict()),
            "dispatch_offer": {
                "offer": signed["offer"], "signature": signed["signature"]
            },
            "authority_expectation": signed["authority_expectation"],
        }

    def _signed_budget(self, job: Any, warrant: Mapping[str, Any], now: float) -> float:
        """The smallest of the row deadline, the warrant lifetime, and the cap.

        A worker must never be told it has 120 seconds of authority when the
        relay row expires in 8 or the hub warrant's execution lifetime ends in
        3 (repair R5). Physical work that outlives its authority cannot be
        settled, so it must not be authorized in the first place.
        """
        remaining = [float(COMPLETE_WITHIN_SECONDS)]
        try:
            deadline = datetime.fromisoformat(str(job.deadline_at or ""))
        except (TypeError, ValueError):
            deadline = None
        if deadline is not None:
            remaining.append((deadline - datetime.now()).total_seconds())
        expires = warrant.get("execution_expires_at")
        if isinstance(expires, (int, float)) and not isinstance(expires, bool):
            remaining.append(float(expires) - float(now))
        return min(remaining)

    def _custody_lock(self) -> Any:
        """Hold pairing custody across a decision, when there is custody to hold."""
        store = self._token_store
        lock = getattr(store, "custody_lock", None)
        return lock() if callable(lock) else nullcontext()

    def _db_signing_snapshot(self, snapshot: Any) -> Any:
        """Re-read the private signing key at the commit boundary, never cache it."""
        store = self._token_store
        if store is None:
            raise ConflictError(
                "the hub cannot sign a dispatch offer for this node",
                code=CREDENTIAL_UNAVAILABLE,
            )
        try:
            fresh = store.signing_snapshot(snapshot.name)
        except ValueError:
            # Revoked, unpaired, unreadable custody, or carrying no offer key (a
            # migrated v1 pairing) — `NodeLinkError` and `NodeCustodyError` are
            # both `ValueError`. Every one of those is a named protocol refusal,
            # not an untyped failure escaping the service as a 500.
            raise ConflictError(
                "this node has no signing credential on the hub",
                code=CREDENTIAL_UNAVAILABLE,
            ) from None
        if (
            fresh.node_id != snapshot.node_id
            or fresh.generation != snapshot.generation
            or fresh.key_id != snapshot.key_id
        ):
            # The credential moved under the transaction. Refusing here is what
            # keeps a rotate/re-pair race from signing under a stale snapshot.
            raise ConflictError(
                "the node credential changed during the claim",
                code=CREDENTIAL_STALE,
            )
        return fresh

    def _revalidated_credential(self, snapshot: Any) -> Any:
        """Fresh-authenticate the settling caller, holding custody (repair R4).

        The same credential that authenticated the HTTP request must still be
        the live one when the settlement commits. A revoke or rotate that won
        first therefore prevents acceptance instead of racing it, and the MAC is
        verified against the token custody currently holds — never a copy that
        travelled with the request.
        """
        store = self._token_store
        if store is None:
            return snapshot
        try:
            fresh = store.identify(getattr(snapshot, "token", ""))
        except ValueError:
            raise ConflictError(
                "this hub's node pairing custody is unreadable",
                code=CREDENTIAL_UNAVAILABLE,
            ) from None
        if (
            fresh is None
            or fresh.node_id != snapshot.node_id
            or fresh.generation != snapshot.generation
            or fresh.name != snapshot.name
        ):
            raise ConflictError(
                "the node credential changed before this settlement",
                code=CREDENTIAL_STALE,
            )
        return fresh

    def bind_token_store(self, store: Any) -> None:
        """Hand the hub's pairing custody to this authority (composition only)."""
        self._token_store = store

    # ── the settlement transaction ───────────────────────────────────

    def settle(
        self,
        snapshot: Any,
        job_id: str,
        payload: Mapping[str, Any],
        *,
        success: bool,
    ) -> dict[str, Any]:
        """Independently revalidate a terminal report and settle it exactly once.

        Everything below happens inside ONE ``BEGIN IMMEDIATE`` election (repair
        R6): the stored proof load, the exact-duplicate comparison, the hub's own
        signature over the offer it issued, the report MAC and ordinal cohort,
        the still-live warrant and its absolute settlement deadline, and the
        guarded terminal update. Whatever commits first — a cancellation, a
        revocation, an expiry, a competing report — wins, and this transaction
        finds nothing left to settle rather than overwriting it.
        """
        report = validate_report_shape(payload.get("report"))
        result = payload.get("result")
        result = result if isinstance(result, str) else ""
        mac = payload.get("mac")
        accepted: dict[str, Any] = {}

        def decide(proof: Optional[Mapping[str, Any]], conn: Any) -> Optional[dict[str, Any]]:
            if proof is None:
                raise ConflictError(
                    f"relay job {job_id} is unknown", code=SETTLEMENT_NOT_AVAILABLE
                )
            if not verify_report_mac(report, mac, fresh.token):
                raise ConflictError(
                    "the worker terminal report is not authentic",
                    code=REPORT_MAC_INVALID,
                )
            offer_envelope = proof.get("dispatch_offer")
            if not isinstance(offer_envelope, Mapping):
                raise ConflictError(
                    "no dispatch offer was ever signed for this job",
                    code=SETTLEMENT_AUTHORITY_INVALID,
                )
            offer = self._revalidate_offer(offer_envelope, fresh, proof)
            self._revalidate_cohort(report, offer, fresh, proof, result, success=success)
            accepted["offer_id"] = offer["offer_id"]

            stored = proof.get("worker_terminal")
            if isinstance(stored, Mapping) and stored:
                # Exact duplicate: read-only idempotency AFTER authentication.
                # The hub operation is terminal now, so the live-authority check
                # would refuse a report that was already accepted — the byte
                # comparison is the whole gate, and a conflicting retry refuses.
                if canonical_report_bytes(stored) != canonical_report_bytes(report):
                    raise ConflictError(
                        "a different terminal report was already settled for this job",
                        code=REPORT_CONFLICT,
                    )
                if str(proof.get("result") or "") != result:
                    raise ConflictError(
                        "a different result was already settled for this job",
                        code=REPORT_CONFLICT,
                    )
                accepted["duplicate"] = True
                return None

            # The hub's OWN wall clock decides whether this settlement is in
            # time. The worker's monotonic budget bounds its physical work; this
            # absolute deadline bounds what the hub will still accept (repair R8).
            if self._clock() > float(offer.get("hub_settlement_deadline") or 0):
                raise ConflictError(
                    "the hub settlement deadline for this job has passed",
                    code=SETTLEMENT_EXPIRED,
                )
            live = self._live_authority(proof.get("envelope"), conn=conn)
            if live is None:
                raise ConflictError(
                    "relay result warrant is invalid or no longer live",
                    code="mesh_result_warrant_invalid",
                )
            self._revalidate_live_binding(offer, live)
            return {
                "status": "completed" if success else "failed",
                "result": result if success else "",
                "error": "" if success else str(report.get("failure_class") or "node reported failure"),
                "worker_terminal": dict(report),
            }

        with self._custody_lock():
            fresh = self._revalidated_credential(snapshot)
            settled = self._db.mesh_relay.settle_first(
                job_id,
                node_id=fresh.node_id,
                generation=fresh.generation,
                decide=decide,
            )
        if settled is False:
            raise ConflictError(
                f"relay job {job_id} is not settleable by this node",
                code=SETTLEMENT_NOT_AVAILABLE,
            )
        return {
            "success": True,
            "duplicate": bool(accepted.get("duplicate")),
            "job_id": str(job_id),
            "offer_id": str(accepted.get("offer_id") or ""),
            "report_digest": report_digest(report),
        }

    @staticmethod
    def _revalidate_live_binding(
        offer: Mapping[str, Any],
        live: tuple[Mapping[str, Any], DeploymentRevision, int, Mapping[str, Any]],
    ) -> None:
        """The offer the hub signed must still describe the authority it has.

        Signature verification proves the hub wrote the offer; this proves the
        offer is about the operation, warrant, revision, and ordinal that are
        live RIGHT NOW, inside the settlement transaction (repair R5).
        """
        warrant, relay_revision, ordinal, operation = live
        if (
            str(offer.get("hub_operation_id") or "") != str(warrant.get("operation_id") or "")
            or str(offer.get("warrant_binding") or "") != warrant_binding(warrant)
            or str(offer.get("relay_revision_id") or "") != relay_revision.id
            or int(offer.get("first_ordinal") or 0) != int(ordinal)
            or str(operation.get("name") or "") != KERNEL_OPERATION_NAME
            or int(operation.get("version") or 0) != KERNEL_OPERATION_VERSION
        ):
            raise ConflictError(
                "the signed offer does not describe this job's live authority",
                code=SETTLEMENT_AUTHORITY_INVALID,
            )

    def _revalidate_offer(
        self, envelope: Mapping[str, Any], snapshot: Any, proof: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        """Verify the hub's OWN signature and the exact identity it was issued to."""
        from ..mesh_authority import ed25519
        from ..mesh_authority.offer import canonical_offer_bytes

        offer = envelope.get("offer")
        signature = envelope.get("signature")
        if not isinstance(offer, Mapping) or not isinstance(signature, str):
            raise ConflictError(
                "the stored dispatch offer is unreadable",
                code=SETTLEMENT_AUTHORITY_INVALID,
            )
        try:
            raw = bytes.fromhex(signature)
            public = bytes.fromhex(snapshot.offer_public_key)
        except ValueError:
            raise ConflictError(
                "the stored dispatch offer is unreadable",
                code=SETTLEMENT_AUTHORITY_INVALID,
            ) from None
        if not ed25519.verify(public, canonical_offer_bytes(offer), raw):
            raise ConflictError(
                "the stored dispatch offer does not verify",
                code=SETTLEMENT_AUTHORITY_INVALID,
            )
        if (
            str(offer.get("node_id")) != snapshot.node_id
            or str(offer.get("node_name")) != snapshot.name
            or int(offer.get("credential_generation") or 0) != snapshot.generation
            or str(offer.get("key_id")) != snapshot.key_id
            or str(proof.get("claimed_by_node_id") or "") != snapshot.node_id
            or int(proof.get("claimed_generation") or 0) != snapshot.generation
        ):
            raise ConflictError(
                "this node did not claim that job",
                code=SETTLEMENT_AUTHORITY_INVALID,
            )
        return offer

    @staticmethod
    def _revalidate_cohort(
        report: Mapping[str, Any],
        offer: Mapping[str, Any],
        snapshot: Any,
        proof: Mapping[str, Any],
        result: str,
        *,
        success: bool,
    ) -> None:
        """Every binding the report asserts must equal what the hub signed."""
        for field in (
            "offer_id", "job_id", "hub_operation_id", "claim_nonce",
            "node_name", "node_id", "relay_revision_id", "execution_revision_id",
        ):
            if str(report.get(field)) != str(offer.get(field)):
                raise ConflictError(
                    "the terminal report does not match the signed offer",
                    code=REPORT_COHORT_MISMATCH,
                )
        if int(report.get("credential_generation") or 0) != int(offer.get("credential_generation") or 0):
            raise ConflictError(
                "the terminal report names another credential generation",
                code=REPORT_COHORT_MISMATCH,
            )
        if str(report.get("claim_nonce")) != str(proof.get("claim_nonce") or ""):
            raise ConflictError(
                "the terminal report replays another claim",
                code=REPORT_COHORT_MISMATCH,
            )

        first = int(offer.get("first_ordinal") or 0)
        budget = int(offer.get("max_attempts") or 1)
        permitted = [first + step for step in range(budget)]
        ordinals = [int(attempt["ordinal"]) for attempt in report["local_attempts"]]
        if ordinals != permitted[: len(ordinals)] or not ordinals:
            # Ordered, contiguous, starting at the signed first ordinal, and
            # never longer than the signed budget: a gap, a repeat, or a third
            # attempt all land here.
            raise ConflictError(
                "the reported attempt cohort is not the signed ordinal budget",
                code=REPORT_COHORT_MISMATCH,
            )

        terminal = str(report.get("terminal_outcome") or "")
        if str(report["local_attempts"][-1]["outcome"]) != terminal:
            raise ConflictError(
                "the terminal outcome is not the last attempt's receipt",
                code=REPORT_COHORT_MISMATCH,
            )
        if success and terminal != "succeeded":
            raise ConflictError(
                "a completion needs a succeeded final local receipt",
                code=REPORT_COHORT_MISMATCH,
            )
        if not success and terminal == "succeeded":
            raise ConflictError(
                "a failure cannot carry a succeeded final local receipt",
                code=REPORT_COHORT_MISMATCH,
            )
        if success and str(report.get("result_sha256")) != result_digest(result):
            raise ConflictError(
                "the returned result is not the result the worker receipted",
                code=REPORT_RESULT_MISMATCH,
            )


__all__ = [
    "COMPLETE_WITHIN_SECONDS",
    "DISPATCH_WITHIN_SECONDS",
    "KERNEL_OPERATION_NAME",
    "KERNEL_OPERATION_VERSION",
    "MeshRelayAuthority",
]
