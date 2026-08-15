"""The fixed, content-free refusal vocabulary of the mesh authority protocol.

Article V.3: refusal is by name. Every reason here is a stable machine class that
carries no prompt, completion, credential, key, endpoint, or provider exception
text, so the same string is safe in a kernel row, a relay report, a log line, and
an HTTP body.
"""

from __future__ import annotations


class MeshAuthorityRefused(ValueError):
    """A named protocol refusal. ``reason`` is the whole payload."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


# ── edge authentication ──────────────────────────────────────────────
NODE_AUTHENTICATION_REQUIRED = "mesh_node_authentication_required"
NODE_IDENTITY_MISMATCH = "mesh_node_identity_mismatch"
#: The pairing moved (rotate, revoke, or re-pair) while a claim or a settlement
#: was deciding. One of them wins; the loser refuses BY NAME rather than falling
#: out of the service as an untyped 500.
CREDENTIAL_STALE = "mesh_credential_stale"
CREDENTIAL_UNAVAILABLE = "mesh_credential_unavailable"

# ── the signed dispatch offer ────────────────────────────────────────
OFFER_MISSING = "mesh_offer_missing"
OFFER_MALFORMED = "mesh_offer_malformed"
OFFER_SCHEMA_UNSUPPORTED = "mesh_offer_schema_unsupported"
OFFER_KEY_UNPINNED = "mesh_offer_key_unpinned"
OFFER_SIGNATURE_INVALID = "mesh_offer_signature_invalid"
OFFER_NONCE_MISMATCH = "mesh_offer_nonce_mismatch"
OFFER_NODE_MISMATCH = "mesh_offer_node_mismatch"
OFFER_GENERATION_MISMATCH = "mesh_offer_generation_mismatch"
OFFER_DESTINATION_MISMATCH = "mesh_offer_destination_mismatch"
OFFER_OPERATION_MISMATCH = "mesh_offer_operation_mismatch"
OFFER_REVISION_MISMATCH = "mesh_offer_revision_mismatch"
OFFER_PAYLOAD_MISMATCH = "mesh_offer_payload_mismatch"
OFFER_ORDINAL_NOT_PERMITTED = "mesh_offer_ordinal_not_permitted"
OFFER_EXPIRED = "mesh_offer_expired"
OFFER_REPLAYED = "mesh_offer_replayed"
OFFER_NOT_VERIFIED = "mesh_offer_not_verified"
#: The content-free live-authority projection the hub derived from its own
#: PERSISTED queue row and kernel operation disagrees with the offer body the
#: same transaction signed (repair R2.1). Both are authentic; they are not about
#: the same job, node, generation, revision, ordinal, or window.
OFFER_EXPECTATION_MISMATCH = "mesh_offer_expectation_mismatch"

# ── worker execution derivation ──────────────────────────────────────
EXECUTION_TARGET_UNUSABLE = "mesh_execution_target_unusable"
EXECUTION_TARGET_RECURSIVE = "mesh_execution_target_recursive"

# ── the attested terminal report ─────────────────────────────────────
REPORT_MALFORMED = "mesh_report_malformed"
REPORT_MAC_INVALID = "mesh_report_mac_invalid"
REPORT_COHORT_MISMATCH = "mesh_report_cohort_mismatch"
REPORT_CONFLICT = "mesh_report_conflict"
REPORT_RESULT_MISMATCH = "mesh_report_result_mismatch"

# ── hub settlement ───────────────────────────────────────────────────
SETTLEMENT_AUTHORITY_INVALID = "mesh_settlement_authority_invalid"
SETTLEMENT_NOT_AVAILABLE = "mesh_settlement_not_available"
#: The hub's own absolute settlement deadline, enforced inside the first
#: settlement transaction: physical work that finished after it is truthful on
#: the worker and simply too late to be accepted here.
SETTLEMENT_EXPIRED = "mesh_settlement_expired"
RESERVATION_LOST = "mesh_reservation_lost"

# ── the worker's own process ─────────────────────────────────────────
#: A second live `mesh serve` on the same worker database. The first owner holds
#: an OS-released lock for its serving lifetime; the second refuses before it can
#: touch a reservation.
WORKER_OWNER_LOCKED = "mesh_worker_owner_locked"
#: The hub's acknowledgement is not the acknowledgement of THIS report.
ACK_INVALID = "mesh_ack_invalid"
#: Bounded delivery of the FIXED terminal bytes ran out of attempts or window
#: without the hub ever acknowledging (repair R2.8). It is transport loss, not a
#: hub decision: a structured 4xx and a malformed 2xx are terminal instead.
HUB_UNAVAILABLE = "mesh_hub_unavailable"
#: Stop won the terminal-publication election before the first send began, so
#: the fixed report body was discarded and nothing was ever sent (repair R2.3).
PUBLICATION_STOPPED = "mesh_publication_stopped"

# ── the mesh destination, hub-side ───────────────────────────────────
#: The destination names no active pairing on this hub. Under HS-131-16 a job
#: addressed to an unpaired node can never be claimed, so it refuses HERE rather
#: than being queued to expire (repair R2.5).
NODE_UNPAIRED = "mesh_node_unpaired"
#: This hub's node pairing custody could not be read. Refusing is the only honest
#: answer; guessing an unbound destination is not (repair R2.5).
NODE_CUSTODY_UNREADABLE = "mesh_node_custody_unreadable"
#: No worker polled for the EXACT ``(node_id, credential_generation)`` inside the
#: liveness window. A name-only timestamp is not liveness (repair R2.5).
NODE_OFFLINE = "mesh_node_offline"


__all__ = [
    "ACK_INVALID",
    "CREDENTIAL_STALE",
    "CREDENTIAL_UNAVAILABLE",
    "EXECUTION_TARGET_RECURSIVE",
    "EXECUTION_TARGET_UNUSABLE",
    "HUB_UNAVAILABLE",
    "MeshAuthorityRefused",
    "NODE_AUTHENTICATION_REQUIRED",
    "NODE_CUSTODY_UNREADABLE",
    "NODE_IDENTITY_MISMATCH",
    "NODE_OFFLINE",
    "NODE_UNPAIRED",
    "OFFER_DESTINATION_MISMATCH",
    "OFFER_EXPECTATION_MISMATCH",
    "OFFER_EXPIRED",
    "OFFER_GENERATION_MISMATCH",
    "OFFER_KEY_UNPINNED",
    "OFFER_MALFORMED",
    "OFFER_MISSING",
    "OFFER_NODE_MISMATCH",
    "OFFER_NONCE_MISMATCH",
    "OFFER_NOT_VERIFIED",
    "OFFER_OPERATION_MISMATCH",
    "OFFER_ORDINAL_NOT_PERMITTED",
    "OFFER_PAYLOAD_MISMATCH",
    "OFFER_REPLAYED",
    "OFFER_REVISION_MISMATCH",
    "OFFER_SCHEMA_UNSUPPORTED",
    "OFFER_SIGNATURE_INVALID",
    "PUBLICATION_STOPPED",
    "REPORT_COHORT_MISMATCH",
    "REPORT_CONFLICT",
    "REPORT_MAC_INVALID",
    "REPORT_MALFORMED",
    "REPORT_RESULT_MISMATCH",
    "RESERVATION_LOST",
    "SETTLEMENT_AUTHORITY_INVALID",
    "SETTLEMENT_EXPIRED",
    "SETTLEMENT_NOT_AVAILABLE",
    "WORKER_OWNER_LOCKED",
]
