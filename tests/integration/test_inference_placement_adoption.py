"""HS-143-10 Slice 6 — one real-object placement-adoption matrix.

The matrix deliberately joins the same frozen route/controller evidence that a
product surface consumes.  Its first table proves the next-run-only rule for
each migrated capability; its second table invokes each production family.
Only the physical engine factory is substituted.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


from holdspeak.db import Database
from holdspeak.kernel.inference import InferenceRunCodec
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind
from tests.unit.test_engines_run_retirement import _legacy_request


OWNER = Principal(PrincipalKind.OWNER, "placement-matrix-owner")


@dataclass(frozen=True)
class _Case:
    name: str
    capability_id: str
    subject_kind: str | None = None
    subject_id: str | None = None


# These are the canonical placement terms for every Python family Story 10
# migrated. Recipe chat intentionally has both ruled paths; Apple is absent by
# the binding owner descope.
CASES = (
    # S4's Thought contextual editor invokes this same canonical subject writer.
    _Case("thought-ask", "ask.answer", "thought", "thought-matrix"),
    _Case("recipe-run", "recipe.run", "recipe", "recipe-matrix"),
    _Case("chat-turn", "chat.turn", "recipe", "recipe-matrix"),  # HS-151-02: was recipe.chat
    _Case("workbench-item-and-memory", "workbench.item", "workbench", "workbench-matrix"),
    _Case("voice-resolution", "voice.reference_resolve", "workbench", "workbench-matrix"),
)


def test_legacy_operation_refusal_has_no_route_or_provider_attempt(tmp_path: Path) -> None:
    """The descoped Apple row has no substitute: legacy Python operation refuses."""
    db = Database(tmp_path / "legacy-refusal.db")
    broker = _configure(db)
    refused = broker.submit(_legacy_request(target_id="mutable-after-admission"), OWNER)
    assert refused["state"] == "refused"
    assert refused["receipt"]["outcome"] == "inference_run_retired"
    assert InferenceRunCodec(db).read_native("retired-invocation") is None
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='inference_route_attempts'").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM kernel_operations WHERE name='inference.invoke'").fetchone()[0] == 0


# ── merged from tests/integration/test_phase143_voice_resolution_adoption.py ──
# HS-143-10 Slice 3 — voice resolution uses the canonical controller route.


