"""The attested terminal report (design §6).

What the worker sends back is an ordered, content-free assertion about its OWN
local receipts: which ordinals it physically attempted, which local operation and
receipt each one produced, and how the cohort ended. The product result travels
as a separate relay field, outside the kernel and outside this report — only its
SHA-256 is attested, so the hub can prove the answer it stores is the answer the
worker's receipts describe.

The node token MACs these bytes. That is an authenticated worker assertion, not
hardware attestation: a compromised paired node can lie about its own database
(recorded in the design's notes). What it cannot do is forge the hub's offer,
another node's identity, or a settlement for work it never claimed.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
from typing import Any, Mapping, Sequence

from .offer import MAX_ATTEMPT_BUDGET, is_opaque_id, is_sha256
from .refusals import (
    EXECUTION_TARGET_RECURSIVE,
    EXECUTION_TARGET_UNUSABLE,
    MeshAuthorityRefused,
    OFFER_EXPIRED,
    OFFER_NOT_VERIFIED,
    OFFER_ORDINAL_NOT_PERMITTED,
    OFFER_REPLAYED,
    REPORT_MALFORMED,
    RESERVATION_LOST,
)

#: The wire schema of one terminal report.
REPORT_SCHEMA = 1

#: Strict domain separation: the node token MACs these bytes and nothing else.
REPORT_DOMAIN = b"holdspeak.mesh.terminal-report.v1"

REPORT_FIELDS = (
    "report_schema",
    "offer_id",
    "job_id",
    "hub_operation_id",
    "claim_nonce",
    "node_name",
    "node_id",
    "credential_generation",
    "relay_revision_id",
    "execution_revision_id",
    "local_attempts",
    "terminal_outcome",
    "result_sha256",
    "failure_class",
)

ATTEMPT_FIELDS = (
    "ordinal",
    "operation_id",
    "receipt_id",
    "principal_identity",
    "claim_identity",
    "outcome",
)

#: The immutable terminal outcomes one physical attempt can end in.
TERMINAL_OUTCOMES = frozenset(
    {"succeeded", "failed", "refused", "cancelled", "indeterminate"}
)

#: A failure/refusal CLASS is a machine token: lowercase, bounded, no spaces.
#: The shape gate, kept as the cheap first check (repair R11).
SAFE_CLASS_PATTERN = re.compile(r"[a-z][a-z0-9_]{0,63}")

#: What an unknown local exception, kernel control class, or provider reason
#: BECOMES on the worker. Mapping rather than passing through is the whole point:
#: a class the protocol did not define carries information the protocol never
#: agreed to transport (repair R2.7).
GENERIC_FAILURE_CLASS = "unspecified"

#: The ONE fixed terminal failure/refusal vocabulary, shared by both nodes
#: (repair R2.7). A shape regex was never a vocabulary: ``credential``,
#: ``prompt``, and ``token`` all satisfy it while saying something the protocol
#: never defined. The worker maps everything outside this set to
#: :data:`GENERIC_FAILURE_CLASS`, and the hub REJECTS anything outside it —
#: before a byte of it is persisted — even under a valid node MAC.
SAFE_FAILURE_CLASSES = frozenset(
    {
        # the immutable terminal outcome words themselves
        "failed",
        "refused",
        "cancelled",
        "indeterminate",
        # the fixed generic every unknown reason collapses to
        GENERIC_FAILURE_CLASS,
        # the worker-side protocol refusals this story defines
        EXECUTION_TARGET_RECURSIVE,
        EXECUTION_TARGET_UNUSABLE,
        OFFER_EXPIRED,
        OFFER_NOT_VERIFIED,
        OFFER_ORDINAL_NOT_PERMITTED,
        OFFER_REPLAYED,
        RESERVATION_LOST,
    }
)


def safe_failure_class(reason: Any) -> str:
    """Map any local reason onto the fixed vocabulary (repair R2.7)."""
    value = str(reason or "")
    return value if value in SAFE_FAILURE_CLASSES else GENERIC_FAILURE_CLASS


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def canonical_report_bytes(report: Mapping[str, Any]) -> bytes:
    """Domain-separated canonical bytes. MACing and verifying share this one form."""
    return REPORT_DOMAIN + b"\x00" + _canonical(dict(report)).encode()


def result_digest(result: str) -> str:
    """SHA-256 of the product result. The body itself never enters the report.

    Every string is a result, including the empty one: an empty completion that
    the worker's own receipts call ``succeeded`` is an honest success, and its
    digest is what both nodes bind (repair R10). Refusing it only at the hub
    would leave a truthful local receipt facing a rejected settlement.
    """
    return "sha256:" + hashlib.sha256(str(result if result is not None else "").encode()).hexdigest()


def report_digest(report: Mapping[str, Any]) -> str:
    """The canonical digest of one terminal report.

    This is the value the hub echoes in its acknowledgement and the value the
    worker recomputes to decide whether that acknowledgement is about the report
    it actually sent (repair R9). Both sides derive it from the same
    domain-separated bytes the MAC covers.
    """
    return "sha256:" + hashlib.sha256(canonical_report_bytes(report)).hexdigest()


def build_report(
    *,
    offer: Any,
    local_attempts: Sequence[Mapping[str, Any]],
    terminal_outcome: str,
    result: str = "",
    failure_class: str = "",
) -> dict[str, Any]:
    """Assemble one schema-1 terminal report from durable local receipts."""
    if terminal_outcome not in TERMINAL_OUTCOMES:
        raise MeshAuthorityRefused(REPORT_MALFORMED)
    attempts = [
        {name: attempt[name] for name in ATTEMPT_FIELDS} for attempt in local_attempts
    ]
    report = {
        "report_schema": REPORT_SCHEMA,
        "offer_id": offer.offer_id,
        "job_id": offer.job_id,
        "hub_operation_id": offer.hub_operation_id,
        "claim_nonce": offer.claim_nonce,
        "node_name": offer.node_name,
        "node_id": offer.node_id,
        "credential_generation": int(offer.credential_generation),
        "relay_revision_id": offer.relay_revision_id,
        "execution_revision_id": offer.execution_revision.id,
        "local_attempts": attempts,
        "terminal_outcome": terminal_outcome,
        "result_sha256": result_digest(result) if terminal_outcome == "succeeded" else "",
        "failure_class": "" if terminal_outcome == "succeeded" else str(failure_class or terminal_outcome),
    }
    if set(report) != set(REPORT_FIELDS):  # pragma: no cover - structural guard
        raise MeshAuthorityRefused(REPORT_MALFORMED)
    return report


def report_mac(report: Mapping[str, Any], node_token: str) -> str:
    """The worker's authenticated assertion over exactly these bytes."""
    return hmac.new(
        str(node_token).encode(), canonical_report_bytes(report), hashlib.sha256
    ).hexdigest()


def verify_report_mac(report: Mapping[str, Any], mac: Any, node_token: str) -> bool:
    """Constant-time MAC check. A malformed MAC is a plain ``False``."""
    if not isinstance(mac, str) or not mac:
        return False
    return hmac.compare_digest(report_mac(report, node_token), mac)


def validate_report_shape(report: Any) -> dict[str, Any]:
    """Allow-list the whole report before any field of it is trusted.

    An unknown field, a boolean where an integer belongs, or an out-of-vocabulary
    outcome is malformed — never partially accepted. The ordinal COHORT (no gaps,
    nothing outside the signed budget) is the hub settlement's own check, because
    only the hub holds the offer that says what the budget was.
    """
    if not isinstance(report, Mapping) or set(report) != set(REPORT_FIELDS):
        raise MeshAuthorityRefused(REPORT_MALFORMED)
    schema = report.get("report_schema")
    if not isinstance(schema, int) or isinstance(schema, bool) or schema != REPORT_SCHEMA:
        raise MeshAuthorityRefused(REPORT_MALFORMED)
    generation = report.get("credential_generation")
    if not isinstance(generation, int) or isinstance(generation, bool) or generation < 1:
        raise MeshAuthorityRefused(REPORT_MALFORMED)
    for name in (
        "offer_id", "job_id", "hub_operation_id", "claim_nonce", "node_name",
        "node_id", "relay_revision_id", "execution_revision_id",
    ):
        # Bounded opaque identifiers, never free text: this is where an authentic
        # MAC over a content-bearing report stops.
        if not is_opaque_id(report.get(name)):
            raise MeshAuthorityRefused(REPORT_MALFORMED)
    outcome = report.get("terminal_outcome")
    if outcome not in TERMINAL_OUTCOMES:
        raise MeshAuthorityRefused(REPORT_MALFORMED)
    result_sha256 = report.get("result_sha256")
    failure_class = report.get("failure_class")
    if outcome == "succeeded":
        # A success binds an exact digest and names no failure class.
        if not is_sha256(result_sha256) or failure_class != "":
            raise MeshAuthorityRefused(REPORT_MALFORMED)
    else:
        if result_sha256 != "" or not isinstance(failure_class, str):
            raise MeshAuthorityRefused(REPORT_MALFORMED)
        # The SHAPE, then the VOCABULARY (repair R2.7). `credential`, `prompt`,
        # and `token` are all well-shaped lowercase tokens; none of them is a
        # class this protocol defined, so an otherwise valid MACed report
        # carrying one refuses before the hub persists it.
        if not SAFE_CLASS_PATTERN.fullmatch(failure_class):
            raise MeshAuthorityRefused(REPORT_MALFORMED)
        if failure_class not in SAFE_FAILURE_CLASSES:
            raise MeshAuthorityRefused(REPORT_MALFORMED)
    attempts = report.get("local_attempts")
    if not isinstance(attempts, (list, tuple)) or not attempts:
        raise MeshAuthorityRefused(REPORT_MALFORMED)
    if len(attempts) > MAX_ATTEMPT_BUDGET:
        # The protocol cap is structural. The exact signed budget is the hub
        # settlement's own cohort check, because only the hub holds the offer.
        raise MeshAuthorityRefused(REPORT_MALFORMED)
    for attempt in attempts:
        if not isinstance(attempt, Mapping) or set(attempt) != set(ATTEMPT_FIELDS):
            raise MeshAuthorityRefused(REPORT_MALFORMED)
        ordinal = attempt.get("ordinal")
        if not isinstance(ordinal, int) or isinstance(ordinal, bool) or ordinal < 1:
            raise MeshAuthorityRefused(REPORT_MALFORMED)
        if attempt.get("outcome") not in TERMINAL_OUTCOMES:
            raise MeshAuthorityRefused(REPORT_MALFORMED)
        for name in ("operation_id", "receipt_id", "principal_identity", "claim_identity"):
            if not is_opaque_id(attempt.get(name)):
                raise MeshAuthorityRefused(REPORT_MALFORMED)
    return dict(report)


__all__ = [
    "ATTEMPT_FIELDS",
    "GENERIC_FAILURE_CLASS",
    "REPORT_DOMAIN",
    "REPORT_FIELDS",
    "REPORT_SCHEMA",
    "SAFE_CLASS_PATTERN",
    "SAFE_FAILURE_CLASSES",
    "TERMINAL_OUTCOMES",
    "build_report",
    "canonical_report_bytes",
    "report_digest",
    "report_mac",
    "result_digest",
    "safe_failure_class",
    "validate_report_shape",
    "verify_report_mac",
]
