"""The signed dispatch offer and the exact capability it mints (design §1–2).

The hub proves ITSELF to the worker here. A node's bearer token authenticates the
node's own requests; it cannot produce this signature, so a stolen node credential
can impersonate a node but never mint hub authority for one.

Verification is the ONLY mint of a :class:`VerifiedMeshOffer`, and that object is
private, identity-registered, and single use — the same shape the kernel already
uses for a claim witness. A caller cannot write one down, copy one, or replay one:
the worker's local kernel consumes it exactly once and derives its own principal
from it.

Everything in a signed offer is content-free authority metadata: identifiers,
content addresses, ordinals, durations, and a secret-slot NAME. No prompt, no
completion, no token, and no key material is ever signed or transported here.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
import uuid
from dataclasses import dataclass
from typing import Any, Mapping, Optional
from weakref import WeakSet

from ..deployment_revisions import DeploymentRevision
from . import ed25519
from .refusals import (
    MeshAuthorityRefused,
    OFFER_DESTINATION_MISMATCH,
    OFFER_EXPECTATION_MISMATCH,
    OFFER_EXPIRED,
    OFFER_GENERATION_MISMATCH,
    OFFER_KEY_UNPINNED,
    OFFER_MALFORMED,
    OFFER_MISSING,
    OFFER_NODE_MISMATCH,
    OFFER_NONCE_MISMATCH,
    OFFER_NOT_VERIFIED,
    OFFER_OPERATION_MISMATCH,
    OFFER_ORDINAL_NOT_PERMITTED,
    OFFER_PAYLOAD_MISMATCH,
    OFFER_REVISION_MISMATCH,
    OFFER_SCHEMA_UNSUPPORTED,
    OFFER_SIGNATURE_INVALID,
)
from .revision import derive_worker_execution_revision

#: The wire schema of one dispatch offer. An exact integer, never a boolean.
OFFER_SCHEMA = 1

#: The ONLY operation kind a dispatch offer can buy. It is signed, and the worker
#: compares it to this constant: an offer that is authentic but names another
#: kind of work is not authority to run a model (repair R5).
OFFER_OPERATION_KIND = "inference.invoke@1"

#: Strict domain separation: these bytes are signed by nothing else.
OFFER_DOMAIN = b"holdspeak.mesh.dispatch-offer.v1"

# ── the wire grammar (repair R11) ────────────────────────────────────
#
# A MAC or a signature is AUTHENTICATION, not sanitization. Every identifier
# that crosses the mesh is a bounded opaque token and every digest is an exact
# lowercase SHA-256, so an authentic message still cannot smuggle a prompt, a
# credential, or a provider exception into a stored proof field.

#: An opaque protocol identifier: bounded, single-token, no whitespace.
#:
#: The alphabet is deliberately the union of every identifier this protocol
#: actually mints — including `secrets.token_urlsafe`, whose base64url output can
#: legitimately BEGIN with ``-`` or ``_``. What the grammar excludes is what
#: matters: whitespace, newlines, quotes, and punctuation that could carry a
#: prompt, a credential, or a provider traceback into a stored proof field.
OPAQUE_ID_PATTERN = re.compile(r"[A-Za-z0-9_.:@-]{1,128}")

#: The exact digest form both nodes compute.
SHA256_PATTERN = re.compile(r"sha256:[0-9a-f]{64}")


def is_opaque_id(value: Any) -> bool:
    """True only for a bounded, whitespace-free protocol identifier."""
    return isinstance(value, str) and bool(OPAQUE_ID_PATTERN.fullmatch(value))


def is_sha256(value: Any) -> bool:
    """True only for the exact ``sha256:<64 lowercase hex>`` form."""
    return isinstance(value, str) and bool(SHA256_PATTERN.fullmatch(value))

#: The offer permits the first ordinal and AT MOST one typed compatibility
#: follow-up (Sol Amendment 2). A third physical attempt has no authority.
MAX_ATTEMPT_BUDGET = 2

#: Every field a schema-1 offer carries. An unknown or missing field is malformed;
#: the protocol is the allow-list, exactly as the node event wire is.
OFFER_FIELDS = (
    "offer_schema",
    "key_id",
    "offer_id",
    "claim_nonce",
    "job_id",
    "hub_operation_id",
    "operation_kind",
    "node_name",
    "node_id",
    "credential_generation",
    "relay_revision",
    "relay_revision_id",
    "execution_revision_id",
    "first_ordinal",
    "max_attempts",
    "dispatch_within_seconds",
    "complete_within_seconds",
    "hub_settlement_deadline",
    "payload_sha256",
    "warrant_binding",
    "authority_expectation_sha256",
)

#: The wire schema of one live-authority expectation.
EXPECTATION_SCHEMA = 1

#: The content-free live-authority projection (repair R2.1).
#:
#: It is derived INDEPENDENTLY — straight from the hub's persisted queue row and
#: its persisted kernel operation, inside the claim transaction — rather than
#: from the same locals that assemble the offer. That independence is the whole
#: value: crossed or stale hub construction, and a wire swap between two
#: authentic offers, both make these fields disagree with the signed body.
#:
#: It is not a third authority factor. There is no warrant, no signature secret,
#: no claim witness, no context, no credential, no prompt, no proof row, no
#: status, no result, and no error here — only identifiers, content addresses,
#: an ordinal, and bounded durations.
EXPECTATION_FIELDS = (
    "expectation_schema",
    "job_id",
    "hub_operation_id",
    "operation_kind",
    "warrant_binding",
    "relay_revision_id",
    "execution_revision_id",
    "destination_node_id",
    "destination_generation",
    "attempt_ordinal",
    "dispatch_within_seconds",
    "complete_within_seconds",
    "hub_settlement_deadline",
)

_REVISION_FIELDS = (
    "destination_id", "kind", "engine", "model", "node",
    "boundary", "endpoint", "model_path", "secret_slot",
)

#: The ONLY fields a worker receives about a job (repair R3). The hub kernel
#: envelope, its warrant, the deployment proof, and every stored proof/status/
#: result column stay hub-side: the worker needs an id and the canonical product
#: payload to execute, and authority comes from the signed offer instead.
WORKER_JOB_FIELDS = (
    "id", "system_prompt", "user_prompt", "temperature", "max_tokens",
)

# The private mint (the `claim_witness` shape): a `VerifiedMeshOffer` cannot be
# constructed without this closure-held token, so opacity is structural.
_MINT = object()

# Live verified offers, held WEAKLY and compared by IDENTITY. A copy, a
# `dataclasses.replace`, or a same-fields duck type is not a member and refuses.
_ISSUED: "WeakSet[VerifiedMeshOffer]" = WeakSet()


# ── canonical bytes ──────────────────────────────────────────────────


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def canonical_job_payload(job: Mapping[str, Any]) -> dict[str, Any]:
    """The exact non-authority payload both nodes hash and the worker executes."""
    temperature = job.get("temperature")
    max_tokens = job.get("max_tokens")
    return {
        "system_prompt": str(job.get("system_prompt") or ""),
        "user_prompt": str(job.get("user_prompt") or ""),
        "temperature": None if temperature is None else float(temperature),
        "max_tokens": None if max_tokens is None else int(max_tokens),
    }


def payload_digest(payload: Mapping[str, Any]) -> str:
    """SHA-256 over the canonical payload. The prompt itself never travels here."""
    return "sha256:" + hashlib.sha256(_canonical(payload).encode()).hexdigest()


def worker_job_view(job: Mapping[str, Any]) -> dict[str, Any]:
    """The dedicated worker projection of one relay row (repair R3).

    The hub used to answer a claim with the whole row — including the kernel
    envelope that carries its own warrant. A worker never needs the hub's
    authority to do its work, and handing it over means a compromised or merely
    chatty node holds a signed hub warrant it was never issued. So the wire
    carries an id and the canonical product payload, and nothing else.
    """
    payload = canonical_job_payload(job)
    return {"id": str(job.get("id") or ""), **payload}


def validate_worker_job(job: Any) -> dict[str, Any]:
    """Allow-list what arrived from the hub before a single field is trusted."""
    if not isinstance(job, Mapping) or set(job) != set(WORKER_JOB_FIELDS):
        raise MeshAuthorityRefused(OFFER_MALFORMED)
    if not is_opaque_id(job.get("id")):
        raise MeshAuthorityRefused(OFFER_MALFORMED)
    for name in ("system_prompt", "user_prompt"):
        if not isinstance(job.get(name), str):
            raise MeshAuthorityRefused(OFFER_MALFORMED)
    temperature = job.get("temperature")
    if temperature is not None and (
        isinstance(temperature, bool) or not isinstance(temperature, (int, float))
    ):
        raise MeshAuthorityRefused(OFFER_MALFORMED)
    max_tokens = job.get("max_tokens")
    if max_tokens is not None and (
        isinstance(max_tokens, bool) or not isinstance(max_tokens, int)
    ):
        raise MeshAuthorityRefused(OFFER_MALFORMED)
    return dict(job)


def build_authority_expectation(
    *,
    job_id: str,
    hub_operation_id: str,
    operation_kind: str,
    warrant_binding: str,
    relay_revision_id: str,
    execution_revision_id: str,
    destination_node_id: str,
    destination_generation: int,
    attempt_ordinal: int,
    dispatch_within_seconds: float,
    complete_within_seconds: float,
    hub_settlement_deadline: float,
) -> dict[str, Any]:
    """Assemble one content-free live-authority expectation (repair R2.1)."""
    expectation = {
        "expectation_schema": EXPECTATION_SCHEMA,
        "job_id": str(job_id),
        "hub_operation_id": str(hub_operation_id),
        "operation_kind": str(operation_kind),
        "warrant_binding": str(warrant_binding),
        "relay_revision_id": str(relay_revision_id),
        "execution_revision_id": str(execution_revision_id),
        "destination_node_id": str(destination_node_id),
        "destination_generation": int(destination_generation),
        "attempt_ordinal": int(attempt_ordinal),
        "dispatch_within_seconds": float(dispatch_within_seconds),
        "complete_within_seconds": float(complete_within_seconds),
        "hub_settlement_deadline": float(hub_settlement_deadline),
    }
    if set(expectation) != set(EXPECTATION_FIELDS):  # pragma: no cover - guard
        raise MeshAuthorityRefused(OFFER_MALFORMED)
    return expectation


def expectation_digest(expectation: Mapping[str, Any]) -> str:
    """The canonical hash the offer binds. Content-free by construction."""
    return "sha256:" + hashlib.sha256(_canonical(dict(expectation)).encode()).hexdigest()


def validate_authority_expectation(expectation: Any) -> dict[str, Any]:
    """Allow-list the expectation before a single field of it is compared."""
    if not isinstance(expectation, Mapping) or set(expectation) != set(EXPECTATION_FIELDS):
        raise MeshAuthorityRefused(OFFER_MALFORMED)
    schema = expectation.get("expectation_schema")
    if not isinstance(schema, int) or isinstance(schema, bool) or schema != EXPECTATION_SCHEMA:
        raise MeshAuthorityRefused(OFFER_MALFORMED)
    for name in (
        "job_id", "hub_operation_id", "relay_revision_id",
        "execution_revision_id", "destination_node_id",
    ):
        if not is_opaque_id(expectation.get(name)):
            raise MeshAuthorityRefused(OFFER_MALFORMED)
    if not is_sha256(expectation.get("warrant_binding")):
        raise MeshAuthorityRefused(OFFER_MALFORMED)
    if not isinstance(expectation.get("operation_kind"), str):
        raise MeshAuthorityRefused(OFFER_MALFORMED)
    _exact_int(expectation, "destination_generation", minimum=1)
    _exact_int(expectation, "attempt_ordinal", minimum=1)
    _exact_seconds(expectation, "dispatch_within_seconds")
    _exact_seconds(expectation, "complete_within_seconds")
    settlement = expectation.get("hub_settlement_deadline")
    if isinstance(settlement, bool) or not isinstance(settlement, (int, float)):
        raise MeshAuthorityRefused(OFFER_MALFORMED)
    return dict(expectation)


def canonical_offer_bytes(offer: Mapping[str, Any]) -> bytes:
    """Domain-separated canonical bytes. Signing and verifying share this one form."""
    return OFFER_DOMAIN + b"\x00" + _canonical(dict(offer)).encode()


def revision_fields(revision: Any) -> dict[str, Any]:
    """The frozen relay revision as signable fields (identifiers, never secrets)."""
    return {name: getattr(revision, name) for name in _REVISION_FIELDS}


# ── strict typed readers (Sol round-four ruling 2) ───────────────────


def _exact_str(source: Mapping[str, Any], key: str, *, allow_empty: bool = False) -> str:
    value = source.get(key)
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        raise MeshAuthorityRefused(OFFER_MALFORMED)
    return value


def _exact_int(source: Mapping[str, Any], key: str, *, minimum: int) -> int:
    value = source.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise MeshAuthorityRefused(OFFER_MALFORMED)
    return value


def _exact_seconds(source: Mapping[str, Any], key: str) -> float:
    value = source.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MeshAuthorityRefused(OFFER_MALFORMED)
    seconds = float(value)
    if seconds <= 0 or seconds != seconds or seconds in (float("inf"), float("-inf")):
        raise MeshAuthorityRefused(OFFER_MALFORMED)
    return seconds


# ── the exact capability ─────────────────────────────────────────────


@dataclass(frozen=True, eq=False)
class VerifiedMeshOffer:
    """One hub offer this worker verified, for one job, once.

    ``eq=False`` is deliberate: two offers are the same offer only when they are
    the SAME object, so a field-for-field copy cannot impersonate the verified one.
    """

    key_id: str
    offer_id: str
    claim_nonce: str
    job_id: str
    hub_operation_id: str
    node_name: str
    node_id: str
    credential_generation: int
    relay_revision_id: str
    execution_revision: DeploymentRevision
    first_ordinal: int
    max_attempts: int
    payload_sha256: str
    warrant_binding: str
    hub_settlement_deadline: float
    monotonic_deadline: float
    mint: Any = None

    def __post_init__(self) -> None:
        if self.mint is not _MINT:
            raise MeshAuthorityRefused(OFFER_NOT_VERIFIED)

    @property
    def permitted_ordinals(self) -> tuple[int, ...]:
        """The exact ordinals this offer buys: the first, plus at most one more."""
        return tuple(
            self.first_ordinal + step for step in range(self.max_attempts)
        )

    def remaining_seconds(self, *, monotonic: float) -> float:
        """What is LEFT of the one end-to-end monotonic budget (ruling 1)."""
        return self.monotonic_deadline - monotonic

    def journal_value(self) -> dict[str, Any]:
        """Content-free identity for diagnostics. Never the payload or the warrant."""
        return {
            "offer_id": self.offer_id,
            "job_id": self.job_id,
            "hub_operation_id": self.hub_operation_id,
            "node_id": self.node_id,
            "generation": self.credential_generation,
            "execution_revision": self.execution_revision.id,
        }


def consume_verified_offer(offer: Any) -> VerifiedMeshOffer:
    """Validate and SPEND one verified offer. Anything else refuses by name.

    Single use is what makes a replayed or captured offer worthless to a second
    local admission: the worker's kernel consumes it before it derives a principal.
    """
    if not isinstance(offer, VerifiedMeshOffer) or offer not in _ISSUED:
        raise MeshAuthorityRefused(OFFER_NOT_VERIFIED)
    _ISSUED.discard(offer)
    return offer


# ── hub side: build and sign ─────────────────────────────────────────


def build_offer(
    *,
    key_id: str,
    claim_nonce: str,
    job_id: str,
    hub_operation_id: str,
    node_name: str,
    node_id: str,
    credential_generation: int,
    relay_revision: Any,
    execution_revision: DeploymentRevision,
    first_ordinal: int,
    payload_sha256: str,
    warrant_binding: str,
    dispatch_within_seconds: float,
    complete_within_seconds: float,
    authority_expectation: Mapping[str, Any],
    now: Optional[float] = None,
    max_attempts: int = MAX_ATTEMPT_BUDGET,
) -> dict[str, Any]:
    """Assemble one schema-1 offer body. The caller signs it inside its transaction.

    The signature covers the canonical hash of ``authority_expectation``, so the
    hub's independently derived live-authority projection is bound to this exact
    offer and cannot be swapped for another authentic one (repair R2.1).
    """
    settlement = float(now if now is not None else time.time()) + float(complete_within_seconds)
    offer = {
        "offer_schema": OFFER_SCHEMA,
        "key_id": str(key_id),
        "offer_id": "offer_" + uuid.uuid4().hex,
        "claim_nonce": str(claim_nonce),
        "job_id": str(job_id),
        "hub_operation_id": str(hub_operation_id),
        "operation_kind": OFFER_OPERATION_KIND,
        "node_name": str(node_name),
        "node_id": str(node_id),
        "credential_generation": int(credential_generation),
        "relay_revision": revision_fields(relay_revision),
        "relay_revision_id": str(relay_revision.id),
        "execution_revision_id": str(execution_revision.id),
        "first_ordinal": int(first_ordinal),
        "max_attempts": int(max_attempts),
        "dispatch_within_seconds": float(dispatch_within_seconds),
        "complete_within_seconds": float(complete_within_seconds),
        "hub_settlement_deadline": settlement,
        "payload_sha256": str(payload_sha256),
        "warrant_binding": str(warrant_binding),
        "authority_expectation_sha256": expectation_digest(authority_expectation),
    }
    if set(offer) != set(OFFER_FIELDS):  # pragma: no cover - structural guard
        raise MeshAuthorityRefused(OFFER_MALFORMED)
    return offer


def sign_offer(offer: Mapping[str, Any], private_key: bytes) -> str:
    """Sign the canonical bytes. The private key never leaves the hub process."""
    return ed25519.sign(private_key, canonical_offer_bytes(offer)).hex()


def warrant_binding(warrant: Mapping[str, Any]) -> str:
    """A binding to the hub warrant that reveals no signing secret."""
    signature = str(warrant.get("signature") or "") if isinstance(warrant, Mapping) else ""
    return "sha256:" + hashlib.sha256(signature.encode()).hexdigest()


# ── worker side: verify ──────────────────────────────────────────────


def verify_offer(
    envelope: Any,
    *,
    pinned_key_id: str,
    pinned_public_key: bytes,
    node_name: str,
    node_id: str,
    credential_generation: int,
    claim_nonce: str,
    job: Mapping[str, Any],
    authority_expectation: Any,
    claim_started_monotonic: float,
    monotonic: float,
) -> VerifiedMeshOffer:
    """The whole worker-side gate, in the order the design fixes.

    Every refusal here happens BEFORE replay reservation, revision persistence,
    runner construction, engine construction, and provider dispatch — a refused
    offer means no local row and no physical work ever existed.
    """
    if not isinstance(envelope, Mapping):
        raise MeshAuthorityRefused(OFFER_MISSING)
    body = envelope.get("offer")
    signature = envelope.get("signature")
    if not isinstance(body, Mapping) or not isinstance(signature, str) or not signature:
        raise MeshAuthorityRefused(OFFER_MISSING)
    if set(body) != set(OFFER_FIELDS):
        raise MeshAuthorityRefused(OFFER_MALFORMED)
    # What arrived beside the offer is the worker projection and nothing else: a
    # hub kernel envelope, a warrant, or a stored proof column here would be a
    # protocol violation before it could be a leak (repair R3).
    job = validate_worker_job(job)

    schema = body.get("offer_schema")
    if not isinstance(schema, int) or isinstance(schema, bool):
        raise MeshAuthorityRefused(OFFER_MALFORMED)
    if schema != OFFER_SCHEMA:
        raise MeshAuthorityRefused(OFFER_SCHEMA_UNSUPPORTED)

    # The pin decides WHICH key may speak for the hub; an unpinned key id never
    # reaches signature verification.
    if _exact_str(body, "key_id") != str(pinned_key_id):
        raise MeshAuthorityRefused(OFFER_KEY_UNPINNED)
    try:
        raw_signature = bytes.fromhex(signature)
    except ValueError:
        raise MeshAuthorityRefused(OFFER_SIGNATURE_INVALID) from None
    if not ed25519.verify(pinned_public_key, canonical_offer_bytes(body), raw_signature):
        raise MeshAuthorityRefused(OFFER_SIGNATURE_INVALID)

    # Authentic, but not yet MINE, FRESH, or EXACT. Every comparison below is a
    # SEMANTIC one: the signature proves the hub wrote these fields, and these
    # checks prove the hub wrote them about THIS worker, THIS poll, and THIS job
    # (repair R5). A correctly re-signed offer with any one of them wrong refuses
    # here — before the replay reservation, the revision, the runner, or dispatch.
    if _exact_str(body, "claim_nonce") != str(claim_nonce):
        raise MeshAuthorityRefused(OFFER_NONCE_MISMATCH)
    if _exact_str(body, "operation_kind") != OFFER_OPERATION_KIND:
        # An offer is authority for ONE kind of act. Nothing else it could name
        # is a licence to run a model on this machine.
        raise MeshAuthorityRefused(OFFER_OPERATION_MISMATCH)
    if _exact_str(body, "node_name") != str(node_name) or _exact_str(body, "node_id") != str(node_id):
        raise MeshAuthorityRefused(OFFER_NODE_MISMATCH)
    # The generation is EXACT, not "at least": the pin and the hub move together
    # through the deliberate pairing transfer, so a replayed pre-rotation offer
    # and an offer minted for a credential this machine has not imported both
    # refuse rather than being accepted as news.
    if _exact_int(body, "credential_generation", minimum=1) != int(credential_generation):
        raise MeshAuthorityRefused(OFFER_GENERATION_MISMATCH)
    if _exact_str(body, "job_id") != str(job.get("id") or ""):
        raise MeshAuthorityRefused(OFFER_NODE_MISMATCH)
    if not is_opaque_id(body.get("offer_id")) or not is_opaque_id(body.get("hub_operation_id")):
        raise MeshAuthorityRefused(OFFER_MALFORMED)
    if not is_opaque_id(body.get("key_id")) or not is_sha256(body.get("warrant_binding")):
        # The hub warrant is bound by DIGEST. A binding of any other shape is not
        # a binding, and the worker refuses rather than executing unbound.
        raise MeshAuthorityRefused(OFFER_MALFORMED)

    if not is_sha256(body.get("payload_sha256")):
        raise MeshAuthorityRefused(OFFER_MALFORMED)
    if _exact_str(body, "payload_sha256") != payload_digest(canonical_job_payload(job)):
        raise MeshAuthorityRefused(OFFER_PAYLOAD_MISMATCH)

    relay_fields = body.get("relay_revision")
    if not isinstance(relay_fields, Mapping) or set(relay_fields) != set(_REVISION_FIELDS):
        raise MeshAuthorityRefused(OFFER_MALFORMED)
    try:
        relay_revision = DeploymentRevision.from_identity(
            _relay_identity(relay_fields)
        )
    except (TypeError, ValueError):
        raise MeshAuthorityRefused(OFFER_MALFORMED) from None
    if relay_revision.id != _exact_str(body, "relay_revision_id"):
        raise MeshAuthorityRefused(OFFER_REVISION_MISMATCH)
    # The DESTINATION is part of the signed authority, and it must be this node
    # by name. An unaddressed relay revision is not "addressed to everyone".
    if relay_revision.node != str(node_name):
        raise MeshAuthorityRefused(OFFER_DESTINATION_MISMATCH)

    execution_revision = derive_worker_execution_revision(relay_revision)
    if execution_revision.id != _exact_str(body, "execution_revision_id"):
        raise MeshAuthorityRefused(OFFER_REVISION_MISMATCH)

    first_ordinal = _exact_int(body, "first_ordinal", minimum=1)
    max_attempts = _exact_int(body, "max_attempts", minimum=1)
    if max_attempts > MAX_ATTEMPT_BUDGET:
        raise MeshAuthorityRefused(OFFER_ORDINAL_NOT_PERMITTED)

    # Freshness is MONOTONIC, never a wall clock: a backward step on either node
    # cannot lengthen the window this worker is allowed to act in.
    dispatch_within = _exact_seconds(body, "dispatch_within_seconds")
    complete_within = _exact_seconds(body, "complete_within_seconds")
    elapsed = float(monotonic) - float(claim_started_monotonic)
    if elapsed < 0 or elapsed > dispatch_within:
        raise MeshAuthorityRefused(OFFER_EXPIRED)

    settlement = body.get("hub_settlement_deadline")
    if isinstance(settlement, bool) or not isinstance(settlement, (int, float)):
        raise MeshAuthorityRefused(OFFER_MALFORMED)

    # The hub's INDEPENDENT live-authority projection (repair R2.1). The offer
    # binds its canonical hash, so it cannot be swapped for another authentic
    # one; every semantic field below is then compared against the signed body
    # and against this worker's own identity, and every one of those comparisons
    # happens BEFORE the replay reservation and before any local work.
    expectation = validate_authority_expectation(authority_expectation)
    if not is_sha256(body.get("authority_expectation_sha256")):
        raise MeshAuthorityRefused(OFFER_MALFORMED)
    if expectation_digest(expectation) != _exact_str(body, "authority_expectation_sha256"):
        raise MeshAuthorityRefused(OFFER_EXPECTATION_MISMATCH)
    if (
        expectation["job_id"] != str(body["job_id"])
        or expectation["hub_operation_id"] != str(body["hub_operation_id"])
        or expectation["operation_kind"] != OFFER_OPERATION_KIND
        or expectation["warrant_binding"] != str(body["warrant_binding"])
        or expectation["relay_revision_id"] != relay_revision.id
        or expectation["execution_revision_id"] != execution_revision.id
        or expectation["destination_node_id"] != str(node_id)
        or int(expectation["destination_generation"]) != int(credential_generation)
        or int(expectation["attempt_ordinal"]) != first_ordinal
        or float(expectation["dispatch_within_seconds"]) != dispatch_within
        or float(expectation["complete_within_seconds"]) != complete_within
        or float(expectation["hub_settlement_deadline"]) != float(settlement)
    ):
        raise MeshAuthorityRefused(OFFER_EXPECTATION_MISMATCH)

    verified = VerifiedMeshOffer(
        key_id=str(body["key_id"]),
        offer_id=_exact_str(body, "offer_id"),
        claim_nonce=str(body["claim_nonce"]),
        job_id=str(body["job_id"]),
        hub_operation_id=str(body["hub_operation_id"]),
        node_name=str(body["node_name"]),
        node_id=str(body["node_id"]),
        credential_generation=int(body["credential_generation"]),
        relay_revision_id=relay_revision.id,
        execution_revision=execution_revision,
        first_ordinal=first_ordinal,
        max_attempts=max_attempts,
        payload_sha256=str(body["payload_sha256"]),
        warrant_binding=str(body["warrant_binding"]),
        hub_settlement_deadline=float(settlement),
        monotonic_deadline=float(claim_started_monotonic) + complete_within,
        mint=_MINT,
    )
    _ISSUED.add(verified)
    return verified


def _relay_identity(fields: Mapping[str, Any]) -> Any:
    from ..inference_targets import DeploymentIdentity

    model_path = fields.get("model_path")
    if model_path is not None and not isinstance(model_path, str):
        raise MeshAuthorityRefused(OFFER_MALFORMED)
    for name in _REVISION_FIELDS:
        if name == "model_path":
            continue
        if not isinstance(fields.get(name), str):
            raise MeshAuthorityRefused(OFFER_MALFORMED)
    return DeploymentIdentity(
        destination_id=str(fields["destination_id"]),
        kind=str(fields["kind"]),
        engine=str(fields["engine"]),
        model=str(fields["model"]),
        node=str(fields["node"]),
        boundary=str(fields["boundary"]),
        model_path=model_path,
        endpoint=str(fields["endpoint"]),
        secret_slot=str(fields["secret_slot"]),
    )


__all__ = [
    "EXPECTATION_FIELDS",
    "EXPECTATION_SCHEMA",
    "MAX_ATTEMPT_BUDGET",
    "OFFER_DOMAIN",
    "OFFER_FIELDS",
    "OFFER_OPERATION_KIND",
    "OFFER_SCHEMA",
    "OPAQUE_ID_PATTERN",
    "SHA256_PATTERN",
    "VerifiedMeshOffer",
    "WORKER_JOB_FIELDS",
    "build_authority_expectation",
    "build_offer",
    "canonical_job_payload",
    "canonical_offer_bytes",
    "consume_verified_offer",
    "expectation_digest",
    "is_opaque_id",
    "is_sha256",
    "payload_digest",
    "revision_fields",
    "sign_offer",
    "validate_authority_expectation",
    "validate_worker_job",
    "verify_offer",
    "warrant_binding",
    "worker_job_view",
]
