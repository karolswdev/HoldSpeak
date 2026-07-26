"""HS-104-02 — the gate's mechanical censuses (the HS-87 style).

1. One decision chokepoint: every state flip goes through
   ``GateProposalRepository._transition``. Any new module naming the
   transition surface fails this census until deliberately admitted.
2. The ledger consumers: the two capability-bearing routes call
   ``require_capability`` — a gate route file without the call is a
   census failure.
3. Redaction: no gate module ever names the full-payload fields.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

# Files allowed to name the transition internals. Grow only with a
# recorded phase decision.
ALLOWED_TRANSITION = {
    "holdspeak/db/gate.py",  # THE state machine (_transition + its callers)
}

# Files allowed to call the public state-flipping verbs
# (decide / expire_due / invalidate_all_held).
ALLOWED_FLIP_CALLERS = {
    "holdspeak/db/gate.py",
    "holdspeak/web/routes/system/gate_routes.py",  # the decision routes
    "holdspeak/web_server.py",  # startup invalidation only
}


def _mentioning_files(needle: str) -> set[str]:
    hits: set[str] = set()
    for path in (REPO / "holdspeak").rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if needle in text:
            hits.add(path.relative_to(REPO).as_posix())
    return hits


def test_transition_is_named_only_in_the_state_machine() -> None:
    actual = _mentioning_files("_transition")
    gate_files = {f for f in actual if "gate" in f}
    assert gate_files - ALLOWED_TRANSITION == set(), (
        "a second code path names the gate transition surface; "
        "admit it here only with a recorded phase decision"
    )


def test_state_flip_verbs_have_pinned_callers() -> None:
    for verb in ("invalidate_all_held", "expire_due"):
        actual = _mentioning_files(verb)
        unexpected = actual - ALLOWED_FLIP_CALLERS
        assert unexpected == set(), f"{verb} named outside the pinned callers: {unexpected}"
    decide_callers = _mentioning_files(".decide(")
    gate_decide = {f for f in decide_callers if "gate" in f}
    assert gate_decide - ALLOWED_FLIP_CALLERS == set()


def test_gate_routes_go_through_require_capability() -> None:
    text = (REPO / "holdspeak/web/routes/system/gate_routes.py").read_text(encoding="utf-8")
    calls = re.findall(r"require_capability\(\s*\"claude-code-hooks\",\s*Capability\.(\w+)\s*\)", text)
    # HS-104-05 added the usage receiver (USAGE_TOKENS) beside the
    # HS-104-02 pair — a reviewed edit in that story's commit.
    assert sorted(calls) == ["BLOCKING", "TOOL_HOOKS", "USAGE_TOKENS"], (
        "receive requires TOOL_HOOKS, decide BLOCKING, usage USAGE_TOKENS"
    )


def test_redaction_census_gate_modules_never_name_full_payload() -> None:
    """The gate must never store or forward the full tool arguments:
    hub-side modules may not read the hook's ``tool_input`` at all
    (redaction happens agent-side in coder_gate.redact_args)."""
    for rel in (
        "holdspeak/db/gate.py",
        "holdspeak/web/routes/system/gate_routes.py",
    ):
        text = (REPO / rel).read_text(encoding="utf-8")
        code_lines = [
            line for line in text.splitlines()
            if not line.lstrip().startswith("#") and '"""' not in line
        ]
        joined = "\n".join(code_lines)
        assert "tool_input" not in joined, f"{rel} touches the full payload"
