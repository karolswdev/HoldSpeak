"""The dispatch target of an admitted child, bound to its FROZEN revision (HS-131-09).

A dictation session freezes ONE deployment revision per capability when it opens.
The pipeline, however, builds its ``LLMRuntime`` separately — from whatever
``Config`` said at build time — so a profile edit, an endpoint change, or a
key-slot change between admission and dispatch used to send the call somewhere
the receipt does not name. That is SILENT RETARGETING: an honest receipt over a
dishonest destination.

This module closes it. Before a non-mesh child dispatches, the runtime it was
handed is checked against the frozen revision's own fields:

* **Agrees** — the runtime already IS that revision's target, so it dispatches
  unchanged. Nothing is constructed and no configuration is read.
* **Disagrees** — the backend is REBOUND from the revision's frozen fields
  (endpoint, model, secret slot for an endpoint engine), so the call lands where
  the receipt says.
* **Cannot be rebound** — a named refusal (:data:`REVISION_TARGET_UNBINDABLE`).
  A backend is never dispatched at the wrong target to keep a run alive.

The result is cached per revision id on the provider admission, so one session
pays at most one comparison and one construction per revision, not per call.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from ..logging_config import get_logger
from .plan import REVISION_TARGET_UNBINDABLE, SpeechSessionRefused

log = get_logger("speech_session")

#: The revision engines that mean "run on an OpenAI-compatible endpoint".
ENDPOINT_ENGINES = frozenset({"openai_compatible"})
#: The revision engines that mean "run on this device's configured local engine".
LOCAL_ENGINES = frozenset({"local", "configured_local_engine", "auto", ""})
#: The revision engines that mean "relay to a mesh node" (handled by the mesh leg).
MESH_ENGINES = frozenset({"mesh", "node_runtime", "mesh_relay"})

#: Runtime backends that are NOT the local in-process family.
_REMOTE_BACKENDS = frozenset({"openai_compatible", "mesh_relay", "paired_runtime"})


def innermost(runtime: Any, *, depth: int = 4) -> Any:
    """The real backend under any counting/admitting decorator chain."""
    inner = runtime
    for _ in range(int(depth)):
        nested = getattr(inner, "_inner", None)
        if nested is None or nested is inner:
            return inner
        inner = nested
    return inner


def _path(value: Any) -> str:
    text = str(value or "").strip()
    return "" if not text else str(Path(text).expanduser())


def agrees(runtime: Any, revision: Any) -> bool:
    """True when ``runtime`` already dispatches at exactly ``revision``'s target."""
    inner = innermost(runtime)
    backend = str(getattr(inner, "backend", "") or "")
    engine = str(getattr(revision, "engine", "") or "")
    if engine in ENDPOINT_ENGINES:
        return (
            backend == "openai_compatible"
            and str(getattr(inner, "base_url", "") or "") == str(getattr(revision, "endpoint", "") or "")
            and str(getattr(inner, "model", "") or "") == str(getattr(revision, "model", "") or "")
        )
    if engine in MESH_ENGINES:
        return backend == "mesh_relay" and str(getattr(inner, "node", "") or "") == str(
            getattr(revision, "node", "") or ""
        )
    if engine in LOCAL_ENGINES:
        if backend in _REMOTE_BACKENDS:
            return False
        frozen_path = _path(getattr(revision, "model_path", None))
        observed = _path(getattr(inner, "model_path", None) or getattr(inner, "model", None))
        # An unobservable local model (a seam that exposes neither) cannot
        # contradict the revision; a path that DOES disagree is a retarget.
        return not (frozen_path and observed and frozen_path != observed)
    return False


def rebind(runtime: Any, revision: Any) -> Any:
    """Rebuild ``runtime``'s dispatch target from ``revision``'s frozen fields.

    Refuses by name when the frozen engine has no constructible backend here — a
    paired-device or unknown engine, or a mesh engine reached outside the mesh leg
    that carries the admitted envelope.
    """
    engine = str(getattr(revision, "engine", "") or "")
    if engine in ENDPOINT_ENGINES:
        endpoint = str(getattr(revision, "endpoint", "") or "").strip()
        model = str(getattr(revision, "model", "") or "").strip()
        if not endpoint or not model:
            raise SpeechSessionRefused(REVISION_TARGET_UNBINDABLE, detail=engine)
        from ..plugins.dictation.runtime_openai_compatible import OpenAICompatibleRuntime

        inner = innermost(runtime)
        timeout = float(getattr(inner, "timeout_seconds", 0.0) or 8.0)
        log.info("speech dispatch rebound onto the admitted revision: %s", revision.id)
        return OpenAICompatibleRuntime(
            model=model,
            base_url=endpoint,
            api_key_env=str(getattr(revision, "secret_slot", "") or ""),
            timeout_seconds=timeout,
        )
    raise SpeechSessionRefused(REVISION_TARGET_UNBINDABLE, detail=engine)


def bound_target(runtime: Any, revision: Optional[Any]) -> Any:
    """The object a non-mesh admitted child may dispatch through.

    ``revision`` of ``None`` (a plan that froze no deployment object for this
    capability) leaves the runtime untouched: there are no frozen fields to bind
    against, and inventing some would be a second placement resolution.
    """
    if revision is None:
        return runtime
    if agrees(runtime, revision):
        return runtime
    return rebind(runtime, revision)


__all__ = [
    "ENDPOINT_ENGINES",
    "LOCAL_ENGINES",
    "MESH_ENGINES",
    "agrees",
    "bound_target",
    "innermost",
    "rebind",
]
