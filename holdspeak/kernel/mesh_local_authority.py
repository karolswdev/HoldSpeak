"""What a verified mesh offer becomes on the WORKER (design §1.6 and §4.1–4.2).

Article XI.3 says the caller supplies neither its principal nor its authority. On
a mesh worker that is a real constraint, not a formality: the process that polls
the hub must not be able to write down a `Principal`, hand it to the kernel, and
have the kernel believe it.

So two single-use capabilities meet here and are both SPENT:

* the :class:`~holdspeak.mesh_authority.offer.VerifiedMeshOffer` that only a valid
  hub Ed25519 signature can mint, and
* the reservation witness that only a winning atomic database insert can mint.

Only after consuming both does this module derive the narrow service principal —
allowed to do exactly one thing, ``inference.invoke@1``, with the offer id as its
authority basis. ``MeshServeWorker`` never imports `Principal`, never constructs
one, and cannot obtain a generic service grant that outlives this job.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from weakref import WeakSet

from ..mesh_authority.offer import VerifiedMeshOffer, consume_verified_offer
from ..mesh_authority.refusals import (
    MeshAuthorityRefused,
    OFFER_NOT_VERIFIED,
    OFFER_REPLAYED,
)
from ..principals import Principal, PrincipalKind

#: The service contract every worker-local physical attempt is admitted under.
MESH_RECEIVER_CONTRACT = "holdspeak.mesh-receiver@1"

# The private mint (the `claim_witness` shape). A reservation witness exists only
# where the worker's own `INSERT … ON CONFLICT DO NOTHING` actually won.
_MINT = object()

_ISSUED: "WeakSet[ReservationWitness]" = WeakSet()


@dataclass(frozen=True, eq=False)
class ReservationWitness:
    """Proof that THIS process won the right to execute THAT offer, once."""

    hub_key_id: str
    hub_operation_id: str
    first_ordinal: int
    mint: Any = None

    def __post_init__(self) -> None:
        if self.mint is not _MINT:
            raise MeshAuthorityRefused(OFFER_NOT_VERIFIED)


@dataclass(frozen=True)
class MeshLocalAuthority:
    """One offer, one reservation, one narrow principal — all already spent."""

    offer: VerifiedMeshOffer
    principal: Principal
    reservation: ReservationWitness

    @property
    def permitted_ordinals(self) -> tuple[int, ...]:
        return self.offer.permitted_ordinals


def reserve_local_execution(database: Any, offer: Any) -> ReservationWitness:
    """Atomically elect this process as the executor of one verified offer.

    Runs BEFORE the execution revision is persisted, before the local runner is
    constructed, and before any engine exists. A replayed offer, a concurrent
    second worker, and a restart all lose the primary-key race and refuse
    ``mesh_offer_replayed`` having done no physical work.
    """
    if not isinstance(offer, VerifiedMeshOffer):
        raise MeshAuthorityRefused(OFFER_NOT_VERIFIED)
    won = database.mesh_worker.reserve(
        hub_key_id=offer.key_id,
        hub_operation_id=offer.hub_operation_id,
        first_ordinal=offer.first_ordinal,
        offer_id=offer.offer_id,
        job_id=offer.job_id,
    )
    if not won:
        raise MeshAuthorityRefused(OFFER_REPLAYED)
    witness = ReservationWitness(
        hub_key_id=offer.key_id,
        hub_operation_id=offer.hub_operation_id,
        first_ordinal=offer.first_ordinal,
        mint=_MINT,
    )
    _ISSUED.add(witness)
    return witness


def derive_local_authority(offer: Any, reservation: Any) -> MeshLocalAuthority:
    """Spend both capabilities and derive the ONE principal this job may use.

    A copied, duck-typed, replayed, or mismatched pair refuses by name. The
    derived principal permits exactly ``inference.invoke@1`` and names the offer
    as its authority basis, so it cannot be reused for another job or another
    kind of operation.
    """
    if not isinstance(reservation, ReservationWitness) or reservation not in _ISSUED:
        raise MeshAuthorityRefused(OFFER_NOT_VERIFIED)
    if not isinstance(offer, VerifiedMeshOffer):
        raise MeshAuthorityRefused(OFFER_NOT_VERIFIED)
    if (
        reservation.hub_key_id != offer.key_id
        or reservation.hub_operation_id != offer.hub_operation_id
        or reservation.first_ordinal != offer.first_ordinal
    ):
        raise MeshAuthorityRefused(OFFER_NOT_VERIFIED)
    spent_offer = consume_verified_offer(offer)
    _ISSUED.discard(reservation)
    principal = Principal(
        PrincipalKind.SERVICE,
        f"mesh-receiver:{spent_offer.hub_operation_id}",
        # Exactly two operations, and no others: the physical attempt, and the
        # admitted signal that cancels it. Without the second the worker could
        # not stop its own work — `perform_cancel` submits an `inference.cancel`
        # child, and a principal that cannot submit it makes the runner treat a
        # real cancellation as refused and dispatch anyway.
        frozenset({("inference.invoke", 1), ("inference.cancel", 1)}),
        f"mesh-offer:{spent_offer.offer_id}",
    )
    return MeshLocalAuthority(
        offer=spent_offer, principal=principal, reservation=reservation
    )


#: No issuance entry: there is nothing here a caller can import and turn into
#: authority. A witness needs a won database race; an offer needs a hub signature.
__all__ = [
    "MESH_RECEIVER_CONTRACT",
    "MeshLocalAuthority",
    "ReservationWitness",
    "derive_local_authority",
    "reserve_local_execution",
]
