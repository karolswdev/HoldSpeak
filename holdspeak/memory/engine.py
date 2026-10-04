"""The ``memory.embed`` engine (docs/internal/MEMORY-DESIGN.md §4).

Every embedding call is one admitted child of ``InferenceRunner.invoke``:
the runner builds the engine from the assigned deployment revision, this
module's adapter runs the batch, and the runner writes the receipt.

* **Assigned explicitly, or not at all.**  The engine exists only when the
  capability ``memory.embed`` has its OWN assignment.  The route planner lets
  a capability inherit a wider assignment (the owner's chat model); an
  embedding call must never fall through to a chat model, so the wider
  assignment is not used here.  With no assignment there is no engine and
  recall is the keyword + relation search.
* **Local deployment:** the GGUF file runs in this process through
  ``llama-cpp-python`` in embedding mode.  Nothing leaves the device.
* **Endpoint deployment:** an OpenAI-compatible ``/v1/embeddings`` call.  The
  deployment's boundary says where the text went.
"""
from __future__ import annotations

import threading
import time
from collections import OrderedDict
from concurrent.futures import Future, ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Any, Optional, Sequence

import numpy as np

from ..logging_config import get_logger
from .embedder import (
    DOCUMENT_PREFIX,
    MEMORY_EMBED_DIM,
    cut_unit,
    model_id_for,
    query_text,
)

log = get_logger("memory.engine")

MEMORY_EMBED_CAPABILITY = "memory.embed"
MEMORY_EMBED_CONTRACT = "memory.embed"
MEMORY_EMBED_CONTRACT_REVISION = "1"
#: Seconds one batch may take before the runner's deadline stops it.
EMBED_DEADLINE_SECONDS = 120.0
_EMBED_N_CTX = 2048
#: Question vectors kept in this process.
QUESTION_CACHE = 256
#: Seconds a search waits for its question vector.  After that the search
#: answers by keyword; it never hangs on the engine.
QUERY_TIMEOUT_SECONDS = 0.5
_QUESTION_POOL = ThreadPoolExecutor(max_workers=2, thread_name_prefix="memory-question")

_MODELS_LOCK = threading.Lock()
#: One embedding model per GGUF path in this process, each with its own lock
#: (a llama context serves one call at a time).
_MODELS: dict[str, tuple[Any, threading.Lock]] = {}


class MemoryEngineError(RuntimeError):
    """The embedding engine could not run this batch."""


class EmbeddingAdapter:
    """The provider adapter for ``memory.embed``: texts in, unit vectors out."""

    connector_id = "inference-provider"
    #: The embedding model is its own small in-process model.  The runner
    #: gives this adapter its own local runtime slot: an embed call takes no
    #: chat lease, so it never refuses a live local call and is never refused
    #: by one (kernel/inference_runner.py, ``_OWN_LOCAL_SLOTS``).
    local_runtime_slot = "embedding"

    def dispatch(self, engine: Any, payload: dict[str, Any], cancellation: threading.Event) -> dict[str, Any]:
        texts = [str(text) for text in payload["texts"]]
        dim = int(payload["dim"])
        if str(getattr(engine, "provider", "")) == "cloud":
            raw = self._endpoint_vectors(engine, texts)
            model = str(getattr(engine, "cloud_model", ""))
            provider = "cloud"
        else:
            raw = self._local_vectors(Path(str(engine.model_path)), texts)
            model = Path(str(engine.model_path)).stem
            provider = "local"
        if cancellation.is_set():
            raise MemoryEngineError("the embedding call was cancelled")
        vectors = cut_unit(raw, dim)
        if vectors.shape[0] != len(texts) or not np.isfinite(vectors).all():
            raise MemoryEngineError("the engine gave vectors that cannot be used")
        return {
            "vectors": [[float(value) for value in row] for row in vectors],
            "dim": dim,
            "provider": provider,
            "model": model,
        }

    def cancel(self) -> str:
        return "cancelled"

    @staticmethod
    def _local_vectors(model_path: Path, texts: Sequence[str]) -> np.ndarray:
        model, lock = EmbeddingAdapter._local_model(model_path)
        with lock:
            raw = model.embed(list(texts), normalize=False, truncate=True)
        return np.asarray(raw, dtype=np.float32)

    @staticmethod
    def _endpoint_vectors(engine: Any, texts: Sequence[str]) -> np.ndarray:
        engine._ensure_openai_client_loaded()
        # The engine's own egress path: the same `external.egress` operation
        # and receipt every other remote model call writes, with the
        # endpoint's host as the destination.
        response = engine._remote_completion(
            engine._openai_client.embeddings.create,
            {"model": str(engine.cloud_model), "input": list(texts)},
        )
        rows = sorted(response.data, key=lambda row: int(row.index))
        return np.asarray([row.embedding for row in rows], dtype=np.float32)

    @staticmethod
    def _local_model(model_path: Path) -> tuple[Any, threading.Lock]:
        """The embedding model for one GGUF file, loaded once.

        The one embedding-mode llama.cpp load.  It runs only inside this
        adapter's dispatch, so only for an admitted ``memory.embed`` child.
        """
        from .. import intel as _intel_pkg

        key = str(model_path)
        with _MODELS_LOCK:
            cached = _MODELS.get(key)
            if cached is not None:
                return cached
            if _intel_pkg.Llama is None:
                raise MemoryEngineError("llama-cpp-python is not installed")
            if not model_path.is_file():
                raise MemoryEngineError("the embedding model file is not on this device")
            model = _intel_pkg.Llama(
                model_path=key,
                embedding=True,
                n_ctx=_EMBED_N_CTX,
                n_batch=_EMBED_N_CTX,
                # An encoder model needs the whole input in one micro-batch.  With
                # the default (512) llama.cpp ABORTS the process on a batch of
                # more than 512 tokens, so this is not optional.
                n_ubatch=_EMBED_N_CTX,
                verbose=False,
            )
            _MODELS[key] = (model, threading.Lock())
            return _MODELS[key]


def _assignment_head(conn: Any) -> Optional[str]:
    """The live assignment head of ``memory.embed`` as one value, or None."""
    row = conn.execute(
        "SELECT assignment_id,revision FROM inference_assignment_heads"
        " WHERE assignment_key=? AND cleared=0",
        (f"capability:{MEMORY_EMBED_CAPABILITY}",),
    ).fetchone()
    return f"{row[0]}@{row[1]}" if row is not None else None


#: The principal a search runs for.  ``MemoryService.search`` sets it, so the
#: admitted question call names the real caller.
_CALLER: ContextVar[Any] = ContextVar("memory_caller", default=None)


@contextmanager
def memory_caller(principal: Any):
    token = _CALLER.set(principal)
    try:
        yield
    finally:
        _CALLER.reset(token)


#: The boundary words the faces draw a lamp for.
_BOUNDARY_WORDS = {
    "same_device": "local", "local": "local", "": "local",
    "lan": "private_network", "private_network": "private_network",
    "private_mesh": "mesh", "mesh": "mesh", "paired": "mesh",
    "cloud": "cloud", "external_service": "cloud",
}


class MemoryEngineTimeout(MemoryEngineError):
    """The question was not embedded inside the search's time limit."""


class MemoryEngineUnassigned(MemoryEngineError):
    """``memory.embed`` has no assignment now, or a different one."""


def assigned_revision(broker: Any) -> Optional[dict[str, str]]:
    """The deployment revision ``memory.embed`` is assigned to, or None.

    Only the capability's OWN assignment counts (see the module text).
    """
    db = broker.database
    with db._connection() as conn:
        head = _assignment_head(conn)
    if head is None:
        return None
    from ..services.project_update_service import _resolve_for_capability

    try:
        revision_id, assignment_id, _profile = _resolve_for_capability(broker, MEMORY_EMBED_CAPABILITY)
    except RuntimeError as exc:
        log.warning("memory.embed is assigned but its route does not resolve: %s", exc)
        return None
    with db._connection() as conn:
        row = conn.execute(
            "SELECT model,boundary FROM deployment_revisions WHERE id=?", (revision_id,)
        ).fetchone()
    if row is None:
        return None
    return {
        "revision_id": revision_id,
        "assignment_id": assignment_id,
        "model": str(row["model"] or ""),
        "boundary": str(row["boundary"] or ""),
        "head": head,
    }


class RouterEmbedder:
    """``MemoryEmbedder`` over the router: one admitted call per batch.

    * **The assignment is checked at every call.**  The engine is bound to
      the assignment head it was resolved from.  When the owner clears or
      changes the assignment, ``live()`` is false at once: no call is made,
      a search answers by keyword, and the next conductor tick resolves
      whatever is assigned then.
    * **A question never waits long.**  ``embed_query`` runs the admitted
      call on a worker thread and waits ``QUERY_TIMEOUT_SECONDS``.  After
      that the search goes on without the vector list; the call still ends,
      and its vector serves the same question next time.
    * **The caller is named.**  A question runs as the principal the search
      runs for; a background batch runs as the conductor.
    """

    dim = MEMORY_EMBED_DIM

    def __init__(self, broker: Any, principal: Any, revision: dict[str, str]) -> None:
        self._broker = broker
        self._principal = principal
        self.revision_id = revision["revision_id"]
        self.assignment_id = revision["assignment_id"]
        self.assignment_head = revision.get("head")
        self.deployment_boundary = revision["boundary"]
        #: local | private_network | mesh | cloud: the word a face shows.
        self.boundary = _BOUNDARY_WORDS.get(revision["boundary"], revision["boundary"])
        self.model_id = model_id_for(revision["model"] or self.revision_id, self.dim)
        self.last_operation_id = ""
        # The same question asked again (a palette keystroke, a retry, two
        # drafters in one turn) is not a second admitted call.
        self._questions: "OrderedDict[str, np.ndarray]" = OrderedDict()
        self._in_flight: dict[str, Future] = {}
        self._questions_lock = threading.Lock()

    def live(self) -> bool:
        """True while ``memory.embed`` is still assigned as it was."""
        try:
            with self._broker.database._connection() as conn:
                return _assignment_head(conn) == self.assignment_head
        except Exception:
            return False

    def _caller(self) -> Any:
        caller = _CALLER.get()
        if caller is not None:
            return caller
        from ..kernel.runtime import _principal as kernel_principal
        from ..principals import PrincipalKind

        ambient = kernel_principal.get()
        if getattr(ambient, "kind", PrincipalKind.NONE) is PrincipalKind.OWNER:
            return ambient
        return self._principal

    def _invoke(self, prefixed: Sequence[str], principal: Any) -> np.ndarray:
        from ..kernel.inference_runner import InvocationRequest, ServiceContract
        from ..kernel.runtime import _as_principal

        if not self.live():
            raise MemoryEngineUnassigned("memory.embed is not assigned to this engine now")
        payload = {"texts": list(prefixed), "dim": self.dim}
        request = InvocationRequest(
            deployment_revision=self.revision_id,
            definition_origin=ServiceContract.for_payload(
                MEMORY_EMBED_CONTRACT, MEMORY_EMBED_CONTRACT_REVISION, payload
            ),
            deadline_at=time.time() + EMBED_DEADLINE_SECONDS,
            payload=payload,
        )
        captured: list[Any] = []

        def _capture(value: Any) -> str:
            captured.append(value)
            return f"memory-embed:{self.assignment_id or self.revision_id}"

        with _as_principal(principal):
            outcome = self._broker.inference_runner.invoke(request, EmbeddingAdapter(), publish=_capture)
        self.last_operation_id = str(getattr(outcome, "operation_id", "") or "")
        if str(getattr(outcome, "outcome", "")) != "succeeded" or not captured:
            raise MemoryEngineError(
                "memory.embed did not complete: "
                + str(getattr(outcome, "error", "") or getattr(outcome, "outcome", ""))
            )
        vectors = np.asarray(captured[0]["vectors"], dtype=np.float32)
        if vectors.shape != (len(prefixed), self.dim):
            raise MemoryEngineError("memory.embed gave the wrong number of values")
        return vectors

    def embed_documents(self, texts: Sequence[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        return self._invoke([DOCUMENT_PREFIX + str(text) for text in texts], self._principal)

    def _embed_question(self, prefixed: str, principal: Any) -> np.ndarray:
        try:
            vector = self._invoke([prefixed], principal)[0]
            with self._questions_lock:
                self._questions[prefixed] = vector
                while len(self._questions) > QUESTION_CACHE:
                    self._questions.popitem(last=False)
            return vector
        finally:
            with self._questions_lock:
                self._in_flight.pop(prefixed, None)

    def embed_query(self, text: str, *, timeout: Optional[float] = None) -> np.ndarray:
        if not self.live():
            raise MemoryEngineUnassigned("memory.embed is not assigned to this engine now")
        prefixed = query_text(text)
        with self._questions_lock:
            held = self._questions.get(prefixed)
            if held is not None:
                self._questions.move_to_end(prefixed)
                return held
            future = self._in_flight.get(prefixed)
            if future is None:
                # The caller is read HERE: a worker thread does not carry the
                # search's context.
                future = _QUESTION_POOL.submit(self._embed_question, prefixed, self._caller())
                self._in_flight[prefixed] = future
        try:
            return future.result(QUERY_TIMEOUT_SECONDS if timeout is None else timeout)
        except FutureTimeout:
            raise MemoryEngineTimeout(
                f"memory.embed did not answer in {QUERY_TIMEOUT_SECONDS} s"
            ) from None


def resolve_embedder(broker: Any, principal: Any) -> Optional[RouterEmbedder]:
    """The engine for the current assignment, or None when none is assigned."""
    revision = assigned_revision(broker)
    return RouterEmbedder(broker, principal, revision) if revision else None


__all__ = [
    "EMBED_DEADLINE_SECONDS",
    "EmbeddingAdapter",
    "MEMORY_EMBED_CAPABILITY",
    "MemoryEngineError",
    "MemoryEngineTimeout",
    "MemoryEngineUnassigned",
    "QUERY_TIMEOUT_SECONDS",
    "memory_caller",
    "RouterEmbedder",
    "assigned_revision",
    "resolve_embedder",
]
