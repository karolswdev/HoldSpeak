"""The unforgeable proof that THIS process just claimed THAT child (HS-131-10).

The dispatch context is what an adapter factory demands before it will construct
a provider engine. Its first implementation minted one from plain arguments: an
operation id string and a warrant mapping with a nonempty ``signature``. Both are
things a product caller can simply *write down*, so "the runner admitted a child"
was proven by a shape rather than by an event — the fence held only because no
production module had typed the literal yet.

A witness closes that — but only if the witness itself cannot be written down.
The first attempt exported ``mint_claim_witness(operation_id=..., warrant=...)``,
which any module could import and hand two invented literals; that simply moved
the forgeable shape one function along, and HS-131-10 round 2 removes it.

There is now no mint FUNCTION at all. :func:`_install_claim_issuer` hands the
process's single issuer closure to its single caller — ``executor.py``, at import
— and refuses every call after the first, so there is no second issuer to obtain
and no public/private helper that turns strings and mappings into authority. The
issuer is a local of ``ExecutorPlane.claim``'s module, reached only after the
kernel has verified the warrant signature, the revocation state, the expiry, the
payload binding, and the whole ancestor chain.

A :class:`ClaimWitness` therefore comes into existence in exactly one place: the
class refuses construction without the private mint token (a closure-held object,
never an argument), and validation is by IDENTITY against the issued registry, so
a copy, a ``dataclasses.replace``, or a same-fields look-alike is not the witness
the claim issued.

The witness is SINGLE USE. :func:`consume_claim_witness` removes it from the
registry, so one claim mints one dispatch context: a witness captured from an
earlier child cannot be replayed to build an engine for a later one (each attempt
of a retry claims again, and therefore gets its own witness).

Everything here is in-memory: a ``dict`` pop and two string compares. No row, no
config, no secret, no clock — the claim already paid for all of that.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping
from weakref import WeakSet

from .model import KernelRefused

#: The claim that would have to exist for this context to be mintable never did.
CLAIM_WITNESS_REQUIRED = "adapter_context_required"

# The private mint. `ClaimWitness` cannot be constructed without it, so opacity
# is structural rather than a naming convention.
_MINT = object()

# Live witnesses, held WEAKLY and compared by IDENTITY (the dataclass is
# `eq=False`, so membership is object identity, and a field-for-field copy is not
# a member). Weak because every claim in the process mints one and only the
# runner's spends it: a strong registry would grow without bound.
_ISSUED: "WeakSet[ClaimWitness]" = WeakSet()


@dataclass(frozen=True, eq=False)
class ClaimWitness:
    """What a successful claim hands back: this operation, that verified basis."""

    operation_id: str
    warrant_basis: str
    mint: Any = None

    def __post_init__(self) -> None:
        if self.mint is not _MINT:
            raise KernelRefused(CLAIM_WITNESS_REQUIRED)


def warrant_basis(warrant: Any) -> str:
    """The authenticated basis of a warrant the kernel has already verified."""
    if not isinstance(warrant, Mapping):
        return ""
    return str(warrant.get("signature") or "").strip()


ClaimIssuer = Callable[..., ClaimWitness]

# Flipped by the ONE successful `_install_claim_issuer()` call, at import of
# `executor.py`. Module state rather than a parameter, so "who may issue" is not
# something a caller can supply.
_ISSUER_INSTALLED = False


def _install_claim_issuer() -> ClaimIssuer:
    """Hand the process's ONE witness issuer to its ONE caller. Then never again.

    Called at import of :mod:`holdspeak.kernel.executor`, whose
    ``ExecutorPlane.claim`` is the only scope that verifies a warrant. Every later
    call — from a product module, a plugin, a route, or a test — raises
    :class:`~holdspeak.kernel.model.KernelRefused`, because the issuer has already
    been given away and this function cannot make a second one.

    That is the whole difference from the retired ``mint_claim_witness``: the
    authority to create a witness is a capability handed out once at import, not
    an importable function that accepts an operation id and a warrant-shaped
    mapping. The census (``test_one_path_census.py``) pins this call to
    ``holdspeak/kernel/executor.py`` and keeps the retired name in its vocabulary,
    so a reappearance of either is a fence failure rather than a quiet regression.
    """
    global _ISSUER_INSTALLED
    if _ISSUER_INSTALLED:
        raise KernelRefused(CLAIM_WITNESS_REQUIRED)
    _ISSUER_INSTALLED = True

    def issue(*, operation_id: str, warrant: Any) -> ClaimWitness:
        """Mint the witness for ONE successfully claimed operation."""
        operation = str(operation_id or "").strip()
        basis = warrant_basis(warrant)
        if not operation or not basis:
            raise KernelRefused(CLAIM_WITNESS_REQUIRED)
        witness = ClaimWitness(
            operation_id=operation, warrant_basis=basis, mint=_MINT
        )
        _ISSUED.add(witness)
        return witness

    return issue


def consume_claim_witness(witness: Any, *, warrant: Any = None) -> ClaimWitness:
    """Validate and SPEND a witness. Anything but the real, unspent one refuses.

    The optional ``warrant`` is the mapping the caller is about to bind onto the
    context; it must be the same authenticated basis the claim witnessed, so a
    caller cannot pair a real witness with a different (or invented) warrant.
    """
    if not isinstance(witness, ClaimWitness) or witness not in _ISSUED:
        raise KernelRefused(CLAIM_WITNESS_REQUIRED)
    if warrant is not None and warrant_basis(warrant) != witness.warrant_basis:
        raise KernelRefused(CLAIM_WITNESS_REQUIRED)
    _ISSUED.discard(witness)
    return witness


#: Deliberately WITHOUT an issuance entry: there is nothing here a caller can
#: import and turn into authority. `_install_claim_issuer` is private, one-shot,
#: and already spent by `executor.py` before any other module imports this.
__all__ = [
    "CLAIM_WITNESS_REQUIRED",
    "ClaimWitness",
    "consume_claim_witness",
    "warrant_basis",
]
