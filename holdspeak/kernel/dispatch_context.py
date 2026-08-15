"""The opaque dispatch context an admitted child hands its adapters (HS-131-10).

Phase 131 made `InferenceRunner.invoke` the one admission path. A shared helper is
not one path, though, while any module can still *construct* a provider engine and
dispatch through it: the engine factories were reachable with nothing but a
revision object, so a product surface could build the same adapter the runner
builds and skip admission entirely.

This module closes that by making the adapter factories CONTEXT-REQUIRING. The
runner mints ONE :class:`DispatchContext` per claimed child — bound to the
operation it just claimed, the immutable revision it resolved, that revision's
destination, the positive attempt ordinal, and the authenticated warrant basis the
claim returned — and every allowlisted factory refuses BY NAME without it.

The mint itself is not a shape check: it consumes the single-use
:class:`~holdspeak.kernel.claim_witness.ClaimWitness` that ``ExecutorPlane.claim``
issues on success, so a caller who invents an operation id and a warrant-shaped
mapping gets ``adapter_context_required`` rather than a context. The two refusals:

* :data:`CONTEXT_REQUIRED` — missing, ``None``, hand-built, duck-typed, or copied.
  A look-alike is not a context: the class cannot be constructed outside this
  module (construction demands the private mint), and even a real context that was
  copied or ``dataclasses.replace``-d is not the object the runner issued, because
  validation checks membership of the issued registry by IDENTITY.
* :data:`CONTEXT_MISMATCH` — a genuinely issued context presented for a different
  operation, revision, destination, or attempt than the one being built.

Validation is deliberately an IN-MEMORY field comparison. The dictation hot path
pays a handful of string compares per dispatch and reads no row, no config, and no
clock: the context already carries everything the runner proved when it claimed
the child.

:data:`LEGACY_UNCONTEXTUAL` is the ONE named marker for the legacy factories the
census records as blocking findings. It is semantically distinct from a context —
it is not accepted by :func:`require_dispatch_context`, it can never validate, and
it only ever means "this scope has NO admitted child behind it". Exactly ONE named
finding scope carries it today — the mesh receiver
(``commands/mesh_serve.py:MeshServeWorker._engine_for_run``), pinned by the Stage-B
AST census; HS-131-13 retired the second (``build_intel_for_target``), so the family
has only shrunk and can only shrink. Everything else is fail-closed: there is no
optional-context path.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Optional
from weakref import WeakSet

from .claim_witness import consume_claim_witness
from .model import KernelRefused

#: No context, a null context, a hand-built/duck-typed look-alike, or a copy of a
#: real one reached an adapter factory or the dispatch leg.
CONTEXT_REQUIRED = "adapter_context_required"
#: A genuinely issued context reached an adapter it was not issued for.
CONTEXT_MISMATCH = "adapter_context_mismatch"

# The private mint. A `DispatchContext` cannot be constructed without it, so
# "opaque" is structural rather than a naming convention.
_MINT = object()

# Every context this module has issued, held weakly and compared by IDENTITY
# (the dataclass is `eq=False`). A copy, a `dataclasses.replace`, or an object
# smuggled past `__post_init__` is therefore not a member, and refuses.
_ISSUED: "WeakSet[DispatchContext]" = WeakSet()


class _LegacyUncontextual:
    """The marker a NAMED legacy uncontextual factory passes (a finding, not an API)."""

    __slots__ = ()

    def __repr__(self) -> str:  # pragma: no cover - diagnostics only
        return "LEGACY_UNCONTEXTUAL"


#: The one marker for the legacy factory family the fence records as findings.
LEGACY_UNCONTEXTUAL = _LegacyUncontextual()


@dataclass(frozen=True, eq=False)
class DispatchContext:
    """What an admitted child proves to the adapter it is about to construct.

    ``eq=False`` is deliberate: two contexts are the same context only when they
    are the SAME object, so a field-for-field copy cannot impersonate the one the
    runner issued.
    """

    operation_id: str
    revision_id: str
    destination_id: str
    attempt_ordinal: int
    warrant: Mapping[str, Any]
    mint: Any = None

    def __post_init__(self) -> None:
        if self.mint is not _MINT:
            raise KernelRefused(CONTEXT_REQUIRED)

    @property
    def warrant_basis(self) -> str:
        """The authenticated basis this context was minted from (the claim's signature)."""
        try:
            return str(self.warrant.get("signature") or "")
        except AttributeError:  # pragma: no cover - warrant is a Mapping by mint
            return ""

    def journal_value(self) -> dict[str, Any]:
        """Content-free identity for diagnostics (never the warrant material)."""
        return {
            "operation_id": self.operation_id,
            "revision": self.revision_id,
            "destination": self.destination_id,
            "attempt": self.attempt_ordinal,
        }


def _issue_dispatch_context(
    *, witness: Any, revision: Any, attempt_ordinal: int = 1, warrant: Any = None
) -> DispatchContext:
    """Mint the context for ONE claimed child. The runner is its only caller.

    PRIVATE and unexported on purpose (HS-131-10 Terra finding A): the first
    implementation took an operation id and a warrant mapping, so any product
    module could mint a context out of two invented literals — the fence held only
    because nobody had typed them yet. The operation now comes from a
    :class:`~holdspeak.kernel.claim_witness.ClaimWitness`, which exists only where
    ``ExecutorPlane.claim`` succeeded, is validated by identity, and is SPENT here:
    one claim, one context.

    Refuses ``adapter_context_required`` unless every binding is real: an unspent
    witness, the immutable revision id AND its destination, a POSITIVE attempt
    ordinal, and the same authenticated warrant basis the claim witnessed.

    The basis is BOUND here, not re-verified: re-checking the HMAC would need the
    journal secret on every dispatch, and `Executor.claim` already refused an
    invalid, revoked, expired, or payload-mismatched warrant before this runs.
    """
    spent = consume_claim_witness(witness, warrant=warrant)
    operation = spent.operation_id
    revision_id = str(getattr(revision, "id", "") or "").strip()
    destination_id = str(getattr(revision, "destination_id", "") or "").strip()
    try:
        ordinal = int(attempt_ordinal)
    except (TypeError, ValueError):
        raise KernelRefused(CONTEXT_REQUIRED) from None
    basis = warrant.get("signature") if isinstance(warrant, Mapping) else None
    if (
        not operation
        or not revision_id
        or not destination_id
        or ordinal < 1
        or not str(basis or "").strip()
    ):
        raise KernelRefused(CONTEXT_REQUIRED)
    context = DispatchContext(
        operation_id=operation,
        revision_id=revision_id,
        destination_id=destination_id,
        attempt_ordinal=ordinal,
        warrant=MappingProxyType(dict(warrant)),
        mint=_MINT,
    )
    _ISSUED.add(context)
    return context


def require_dispatch_context(
    context: Any,
    revision: Any = None,
    *,
    operation_id: str = "",
    attempt_ordinal: int = 0,
) -> DispatchContext:
    """The one validator every allowlisted adapter factory calls FIRST.

    In-memory only: no database read, no configuration read, no clock. Called
    before the adapter constructs (or dispatches through) anything, so a refusal
    means no provider object, no runtime load, and no request ever existed.
    """
    if not isinstance(context, DispatchContext) or context not in _ISSUED:
        raise KernelRefused(CONTEXT_REQUIRED)
    if (
        not context.operation_id
        or not context.revision_id
        or not context.destination_id
        or context.attempt_ordinal < 1
        or not context.warrant_basis
    ):
        raise KernelRefused(CONTEXT_REQUIRED)
    if operation_id and context.operation_id != str(operation_id):
        raise KernelRefused(CONTEXT_MISMATCH)
    if attempt_ordinal and context.attempt_ordinal != int(attempt_ordinal):
        raise KernelRefused(CONTEXT_MISMATCH)
    if revision is not None:
        revision_id = str(getattr(revision, "id", "") or "")
        destination = str(getattr(revision, "destination_id", "") or "")
        if revision_id and context.revision_id != revision_id:
            raise KernelRefused(CONTEXT_MISMATCH)
        if destination and context.destination_id != destination:
            raise KernelRefused(CONTEXT_MISMATCH)
    return context


def require_bound_context(context: Any, revision: Any) -> Optional[DispatchContext]:
    """What every REAL-context adapter factory calls: validate against THIS revision.

    :func:`require_dispatch_context` compares a revision only when it is given one
    and only for the fields that are nonempty, which is right for the dispatch leg
    (where the operation id is the binding) and wrong for a FACTORY. HS-131-10
    round 2 found the gap: ``local_pinned_meeting_intel`` validated a context with
    no expected revision at all, so a genuine context minted for a REMOTE child
    was sufficient authority to build a LOCAL engine, and
    ``build_meeting_intel_for_profile(..., deployment_revision=None)`` compared
    nothing.

    So a real context must be presented WITH the exact immutable revision the
    factory is about to build for, and that revision must actually name a
    destination. Anything less refuses :data:`CONTEXT_REQUIRED` before
    construction; a mismatch refuses :data:`CONTEXT_MISMATCH`.

    :data:`LEGACY_UNCONTEXTUAL` passes through as ``None`` — it is the ONE named
    marker for the census's blocking findings, never an authority.
    """
    if context is LEGACY_UNCONTEXTUAL:
        return None
    revision_id = str(getattr(revision, "id", "") or "").strip()
    destination_id = str(getattr(revision, "destination_id", "") or "").strip()
    if not revision_id or not destination_id:
        # A real context with nothing to compare it against is not a permit: the
        # caller cannot prove this is the deployment the child was admitted for.
        raise KernelRefused(CONTEXT_REQUIRED)
    return require_dispatch_context(context, revision)


def bind_dispatch_context(engine: Any, context: Any) -> Any:
    """Carry the context ON the constructed adapter so the dispatch leg can prove it.

    Best effort by design: a ``__slots__`` backend that cannot hold the attribute
    still dispatches under the runner's own context (the factory already validated
    it); it simply cannot re-prove it to a later seam, which then falls back to the
    claimed child's context rather than guessing.
    """
    if context is None or not isinstance(context, DispatchContext):
        return engine
    try:
        object.__setattr__(engine, "_dispatch_context", context)
    except Exception:  # pragma: no cover - slotted/exotic backends
        pass
    return engine


def release_dispatch_context(engine: Any, context: Any) -> None:
    """Unbind a context from an engine once ITS attempt is over.

    The counterpart to :func:`bind_dispatch_context`, and the reason a reused
    engine is safe SEQUENTIALLY but never CONCURRENTLY. HS-131-10 round 2: an
    engine that outlived one child kept that child's context, so a second child
    reading it saw someone else's operation. The runner now clears the binding as
    each attempt finishes, so a context can never be found on an engine outside
    the attempt it was minted for; a concurrent second child that arrives while
    the binding is still live refuses instead of borrowing it.

    Only removes the binding when it is still THIS context (identity), so a later
    attempt that has already rebound the engine is never disarmed by an earlier
    one finishing.
    """
    if not isinstance(context, DispatchContext):
        return
    if dispatch_context_of(engine) is not context:
        return
    try:
        object.__delattr__(engine, "_dispatch_context")
    except Exception:  # pragma: no cover - slotted/exotic backends
        pass


def dispatch_context_of(engine: Any) -> Optional[DispatchContext]:
    """The context the runner bound onto this engine, or ``None``."""
    context = getattr(engine, "_dispatch_context", None)
    return context if isinstance(context, DispatchContext) else None


__all__ = [
    "CONTEXT_MISMATCH",
    "CONTEXT_REQUIRED",
    "DispatchContext",
    "LEGACY_UNCONTEXTUAL",
    "bind_dispatch_context",
    "dispatch_context_of",
    "release_dispatch_context",
    "require_bound_context",
    "require_dispatch_context",
]
