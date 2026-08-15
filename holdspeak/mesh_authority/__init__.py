"""The mesh dispatch-authority protocol (HS-131-16).

One side door closes here: the mesh worker's physical model attempt. The hub
authenticates each worker with its per-node pairing token, signs ONE
destination-bound dispatch offer with a hub-held Ed25519 key whose public half the
worker pinned at pairing, and the worker's own kernel consumes that offer once to
admit and receipt every physical attempt locally.

The modules split by what they protect:

* :mod:`.ed25519` — the signature primitive, stdlib only.
* :mod:`.offer` — canonical offer bytes, signing, verification, and the private
  single-use :class:`~holdspeak.mesh_authority.offer.VerifiedMeshOffer`.
* :mod:`.report` — the content-free attested terminal report and its node MAC.
* :mod:`.revision` — the pure worker execution-revision derivation.
* :mod:`.refusals` — the fixed named refusal vocabulary shared by all of them.
"""

from __future__ import annotations

from .offer import (
    MAX_ATTEMPT_BUDGET,
    OFFER_OPERATION_KIND,
    OFFER_SCHEMA,
    VerifiedMeshOffer,
    build_authority_expectation,
    build_offer,
    canonical_job_payload,
    consume_verified_offer,
    expectation_digest,
    payload_digest,
    sign_offer,
    verify_offer,
    warrant_binding,
    worker_job_view,
)
from .refusals import MeshAuthorityRefused
from .report import (
    REPORT_SCHEMA,
    SAFE_FAILURE_CLASSES,
    build_report,
    report_digest,
    report_mac,
    result_digest,
    safe_failure_class,
    validate_report_shape,
    verify_report_mac,
)
from .revision import derive_worker_execution_revision

__all__ = [
    "MAX_ATTEMPT_BUDGET",
    "MeshAuthorityRefused",
    "OFFER_OPERATION_KIND",
    "OFFER_SCHEMA",
    "REPORT_SCHEMA",
    "SAFE_FAILURE_CLASSES",
    "VerifiedMeshOffer",
    "build_authority_expectation",
    "build_offer",
    "build_report",
    "canonical_job_payload",
    "consume_verified_offer",
    "derive_worker_execution_revision",
    "expectation_digest",
    "payload_digest",
    "report_digest",
    "report_mac",
    "result_digest",
    "safe_failure_class",
    "sign_offer",
    "validate_report_shape",
    "verify_offer",
    "verify_report_mac",
    "warrant_binding",
    "worker_job_view",
]
