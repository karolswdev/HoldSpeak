"""One way for a TEST to hold what only a claim can produce (HS-131-10).

Round 1 of this story imported ``mint_claim_witness`` and handed it two
literals. That was a forge, and a forge in the test tree is worse than useless:
it made the fence's central claim — "the only way to hold a dispatch context is
to have been admitted" — true of production and false of the proof.

So this helper does the real thing. It runs an actual kernel admission against
a real (module-cached) journal — submit, decide, claim — and mints the context
out of the single-use :class:`~holdspeak.kernel.claim_witness.ClaimWitness` that
``ExecutorPlane.claim`` issued. There is no other way in: the witness issuer is
handed out once, at import of ``holdspeak/kernel/executor.py``, and
``_install_claim_issuer`` refuses every later caller — including this file.

Two consequences worth stating, because they are the point:

* ``operation_id`` is no longer an argument. The context names whatever
  operation the kernel actually claimed; a caller that needs the id reads
  ``context.operation_id``.
* ``warrant`` defaults to the warrant that claim VERIFIED. Passing a different
  one is how a test probes the basis check, and it refuses — which is the
  behaviour under test, not a limitation.

The revision stays the caller's, because that is the thing being tested: which
frozen deployment the factory will accept this context for.
"""

from __future__ import annotations

import tempfile
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from holdspeak.kernel.dispatch_context import _issue_dispatch_context
from holdspeak.principals import Principal, PrincipalKind

_OWNER = Principal(PrincipalKind.OWNER, "admitted-context-owner")
_LOCK = threading.Lock()
_RIG: dict[str, Any] = {}

#: The shape a verified warrant has. Kept exported because several suites assert
#: against a basis; the real one now comes from the claim, and this is what a
#: DIFFERENT (therefore refused) warrant looks like.
SIGNED_WARRANT: dict[str, Any] = {"expires_at": 1.0, "signature": "e3b0c44298fc1c14"}

# A sentinel, so an EXPLICIT `warrant=None` still reaches the mint and refuses
# there (several suites probe exactly that).
_DEFAULT = object()


def _rig() -> tuple[Any, Any]:
    """One real database + broker for the whole test session (claims are cheap)."""
    with _LOCK:
        if not _RIG:
            from holdspeak.db import Database
            from holdspeak.deployment_revisions import capture_deployment_revision
            from holdspeak.inference_targets import resolve_inference_target

            # `_build`, NOT `_configure`: `_configure` assigns the PROCESS-GLOBAL
            # broker and disposes the previous one, so building this rig inside a
            # running test would tear down that test's own live broker (its
            # parent-run controller, its issued contexts, its lease refreshers)
            # and silently send its later work to this database instead.
            from holdspeak.kernel.runtime import _build

            root = Path(tempfile.mkdtemp(prefix="admitted-context-"))
            database = Database(root / "admitted-context.db")
            database.profiles.upsert(
                profile_id="admitted-context", name="Admitted context",
                kind="onDevice", model_file="/model.gguf",
            )
            revision = capture_deployment_revision(
                database, resolve_inference_target(database, "admitted-context")
            )
            _RIG["database"] = database
            _RIG["broker"] = _build(database)
            _RIG["revision"] = revision.id
        return _RIG["database"], _RIG["broker"]


def _real_claim() -> tuple[Any, Any]:
    """Admit and CLAIM one ``inference.invoke`` child; return (witness, warrant)."""
    from holdspeak.kernel.inference import executor_identity

    _database, broker = _rig()
    native = "admitted" + uuid.uuid4().hex
    raw = {
        "request_schema": 1,
        "request_id": "request_" + uuid.uuid4().hex,
        "idempotency_key": native,
        "operation": {"name": "inference.invoke", "version": 1},
        "target": {},
        "arguments": {
            "invocation_id": native,
            "deployment_revision": _RIG["revision"],
            "definition_origin": {
                "kind": "service", "contract": "admitted-context", "revision": "1",
                "payload_hash": "sha256:" + "0" * 64,
            },
            "deadline_at": time.time() + 300,
            "attempt_ordinal": 1,
        },
    }
    submitted = broker.submit(raw, _OWNER)
    assert submitted["state"] != "refused", submitted
    broker.decide(submitted["operation_id"], "approve", submitted["revision"], _OWNER)
    node = Principal(PrincipalKind.NODE, executor_identity("admitted-context"))
    claimed = broker.claim(node, native)
    operations = claimed.get("operations") or []
    assert operations, f"the rig failed to claim its own child: {claimed}"
    child = operations[0]
    return child["claim_witness"], child["warrant"]


def admitted_context(
    *,
    revision: Any,
    attempt_ordinal: int = 1,
    warrant: Any = _DEFAULT,
) -> Any:
    """The context a claimed child carries, out of a REAL claim's witness."""
    witness, claimed_warrant = _real_claim()
    basis = claimed_warrant if warrant is _DEFAULT else warrant
    return _issue_dispatch_context(
        witness=witness,
        revision=revision,
        attempt_ordinal=attempt_ordinal,
        warrant=basis,
    )


def claimed_witness() -> tuple[Any, Any]:
    """A REAL, unspent witness and the warrant that claim verified."""
    return _real_claim()


def claimed_warrant() -> Any:
    """The verified warrant a fresh claim hands back (for basis assertions)."""
    return _real_claim()[1]


__all__ = ["SIGNED_WARRANT", "admitted_context", "claimed_warrant", "claimed_witness"]
