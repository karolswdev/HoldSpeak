"""Typed provider signals the admitted gateway acts on (HS-131-10).

A provider adapter can end an attempt in a way that is not simply "failed": the
endpoint may be telling us it speaks a slightly different dialect and that ONE
more request — with a different parameter — would succeed.

Historically the engine answered that itself, inside one call: a second real
``chat.completions.create`` went out under the SAME admitted child and the SAME
terminal receipt, so the journal recorded one attempt where two physically
happened. Sol Amendment 3 rules that out — every physical attempt has its own
child, ordinal, and receipt.

So the engine now performs exactly one physical request per call and raises
:class:`ProviderCompatibilityRetry` instead of sending a hidden second one. The
runner (``InferenceRunner.invoke``) is what turns that into a SECOND admitted
child with the next attempt ordinal. This module is deliberately dependency-free
so both the kernel and the provider engines can import it.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any


class ProviderIndeterminate(RuntimeError):
    """The provider cannot say whether the work happened. Lives here, with its
    sibling signals, so the runner imports one vocabulary instead of owning it."""


class ProviderCompatibilityRetry(RuntimeError):
    """One physical attempt failed on dialect, and exactly one retry is warranted.

    ``mode`` names the dialect the next attempt must use (for example
    ``"max_completion_tokens"``). The engine has already recorded the endpoint's
    dialect, so the child the runner admits next builds an engine that speaks it
    on its FIRST (and only) physical request.
    """

    def __init__(self, mode: str, detail: str = "") -> None:
        self.mode = str(mode or "")
        self.detail = str(detail or "")
        super().__init__(f"provider compatibility retry: {self.mode}")


class ProviderKnownNoGenerationTransient(RuntimeError):
    """Fixed proof that a provider rejected before generation (for example 429)."""

    code = "provider_rate_limited_before_generation"


class ProviderPermanentNoGeneration(RuntimeError):
    """Typed fixed-status proof that the selected provider/model cannot serve."""

    code = "provider_model_unavailable_before_generation"


class ProviderPermissionDenied(RuntimeError):
    """Typed fixed-status authority refusal; never eligible for fallback."""

    code = "provider_permission_denied"


class InferenceInvalidTypedOutput(RuntimeError):
    """Content-free proof that returned output failed the frozen type contract."""

    code = "inference_invalid_typed_output"


#: The typed signals the RUNNER acts on, which therefore must survive every
#: sanitizing adapter wrapper between the engine and ``InferenceRunner._attempt``.
#:
#: HS-131-10 round 2: the meeting and speech adapters wrap a provider call in
#: ``except BaseException -> <Domain>ProviderFailure`` so that no provider text
#: (transcripts, echoed prompts, endpoint bodies) can reach a kernel journal
#: field. That sanitizer is right about CONTENT and wrong about CONTROL: it also
#: swallowed :class:`ProviderCompatibilityRetry`, so the dialect signal never
#: reached the runner and the second child was never admitted — one physical
#: attempt, one dead receipt, and a working endpoint reported as failed.
#:
#: These classes carry no provider text (``mode`` is a fixed dialect token and
#: ``ProviderIndeterminate`` is raised by the kernel's own cancellation path), so
#: re-raising them leaks nothing. Every adapter that sanitizes MUST list this
#: tuple ahead of its ``BaseException`` clause; ``test_one_path_spine.py`` proves
#: each one does, structurally and at runtime.
CONTROL_SIGNALS: tuple[type[BaseException], ...] = (
    ProviderCompatibilityRetry,
    ProviderKnownNoGenerationTransient,
    ProviderPermanentNoGeneration,
    ProviderPermissionDenied,
    InferenceInvalidTypedOutput,
    ProviderIndeterminate,
)


def retry_invocation_id(invocation_id: str, attempt_ordinal: int) -> str:
    """The follow-up child's invocation id: derived, distinct, and traceable.

    A retry is a NEW operation, so it cannot reuse the first attempt's
    idempotency key; deriving it (rather than minting a random one) keeps the two
    receipts readable as one lineage.
    """
    base = "".join(ch for ch in str(invocation_id or "") if ch.isalnum() or ch == "_")
    return f"{base or 'invoke'}_r{int(attempt_ordinal)}"


def compatibility_follow_up(request: Any, invocation_id: str) -> Any:
    """The SECOND child's request after one dialect signal.

    Same payload, same parent, same frozen revision; the next attempt ordinal and
    a derived (never reused) invocation id, because a retry is a new operation
    with its own idempotency key. Exactly one follow-up is ever built: the engine
    recorded the endpoint's dialect during the first attempt, so the second one
    speaks it on its first and only physical request, and a second signal would
    be a genuine failure rather than a dialect mismatch.
    """
    ordinal = int(getattr(request, "attempt_ordinal", 1)) + 1
    return replace(
        request,
        invocation_id=retry_invocation_id(invocation_id, ordinal),
        attempt_ordinal=ordinal,
    )


__all__ = [
    "CONTROL_SIGNALS",
    "InferenceInvalidTypedOutput",
    "ProviderCompatibilityRetry",
    "ProviderIndeterminate",
    "ProviderKnownNoGenerationTransient",
    "ProviderPermanentNoGeneration",
    "ProviderPermissionDenied",
    "compatibility_follow_up",
    "retry_invocation_id",
]
