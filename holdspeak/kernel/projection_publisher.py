"""The retry-aware publishing protocol: one publisher per ADMITTED attempt.

A migrated service hands ``InferenceRunner.invoke`` one ``publish`` callback and
gets one staged projection back. That was exact while an invocation had exactly
one physical attempt. HS-131-10 gave it two: a dialect signal from the provider
is admitted as a SECOND child with its own native id (``<iid>_r2``), its own
ordinal, and its own terminal receipt.

The publisher did not follow. It was a closure over the FIRST invocation id, and
``ProjectionStager.stage`` resolves the operation to stage against by
``native_id`` — so the retry that SUCCEEDED staged its output against the child
that FAILED. Finalization then read that child's ``failed`` receipt, discarded
the stage, and the run produced nothing, having called the provider twice and
been answered the second time.

Faking the result ref would have hidden it. Instead the publisher becomes a
small object that knows which invocation it is bound to and can be rebound:
:class:`StagePublisher` for the kernel's own staging, and
:func:`retarget_publisher` as the ONE place the protocol is spoken. Anything
that does not advertise ``for_invocation`` — a plain function, a test double, a
service that stages nothing — is passed through untouched, so every existing
caller keeps working exactly as before.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from .model import KernelRefused


class StagePublisher:
    """The runner's ``publish`` callback, bound to ONE invocation id — rebindable."""

    __slots__ = ("_stager", "invocation_id", "kind", "_encoder")

    def __init__(
        self, stager: Any, invocation_id: str, kind: str,
        encoder: Callable[[Any], Mapping[str, Any]],
    ) -> None:
        self._stager, self.invocation_id, self.kind, self._encoder = (
            stager, str(invocation_id), str(kind), encoder,
        )

    def __call__(self, result: Any) -> str:
        projection = self._encoder(result)
        if not isinstance(projection, Mapping):
            raise KernelRefused("projection_encoder_not_mapping")
        return self._stager.stage(self.invocation_id, self.kind, projection).result_ref

    def for_invocation(self, invocation_id: str) -> "StagePublisher":
        """The same projection, staged against a DIFFERENT admitted attempt."""
        return StagePublisher(self._stager, invocation_id, self.kind, self._encoder)


def retarget_publisher(publish: Any, invocation_id: str) -> Any:
    """Rebind a publisher onto the attempt about to run; pass anything else through.

    The local is deliberately NOT called ``rebind``: that name belongs to
    ``speech_session/revision_target.py:rebind``, an allowlisted adapter factory
    in the fence's vocabulary, and a local shadowing it reads to the AST census as
    a second, unregistered caller of a factory (``test_one_path_census.py``).
    """
    bind_to_attempt = getattr(publish, "for_invocation", None)
    return bind_to_attempt(invocation_id) if callable(bind_to_attempt) else publish


__all__ = ["StagePublisher", "retarget_publisher"]
