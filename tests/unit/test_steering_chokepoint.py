"""The chokepoint census (HS-87-03) — a mechanical rule, not a review.

`send_text_to_pane` is raw input injection into a terminal running
with the owner's rights. Steering must pass through ONE chokepoint
(`coder_steering.deliver`, grant-checked and audited); the only other
callers are the pre-arming voice paths whose consent story is the
agent's own question (the phase decision: the voice-answer flow types
only when a coder asked). Any new caller fails this census until it
is deliberately admitted here.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

# The deliberate call-site allow-list. Grow it only with a recorded
# phase decision.
ALLOWED = {
    "holdspeak/tmux_transport.py",  # the definition + its craft
    "holdspeak/coder_steering.py",  # THE steering chokepoint (deliver)
    # The legacy voice-answer flow (Phase 78 / HSM-13): types only when
    # a coder ASKED — its consent story is the agent's own question.
    "holdspeak/runtime/dictation_capture.py",
    # The cadence Telegram answer leg (CAD-2): the same asked-first rule.
    "holdspeak/web/routes/cadence.py",
    # The cadence collector names the transport in prose (a comment
    # pointing AT the route seam), never calls it.
    "holdspeak/cadence/collector.py",
}


def _mentioning_files() -> set[str]:
    hits: set[str] = set()
    for path in (REPO / "holdspeak").rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if "send_text_to_pane" in text:
            hits.add(path.relative_to(REPO).as_posix())
    return hits


def test_send_text_to_pane_call_sites_are_pinned() -> None:
    actual = _mentioning_files()
    unexpected = actual - ALLOWED
    missing = ALLOWED - actual
    assert not unexpected, (
        "New send_text_to_pane call site(s) outside the steering "
        f"chokepoint: {sorted(unexpected)} — route steering through "
        "coder_steering.deliver or record a phase decision."
    )
    assert not missing, (
        f"Census stale — expected mention(s) vanished: {sorted(missing)}"
    )


def test_the_chokepoint_itself_checks_the_grant_before_the_transport() -> None:
    # Mechanical shape check: inside deliver(), require_grant appears
    # before the send_text_to_pane import/call.
    body = (REPO / "holdspeak" / "coder_steering.py").read_text(encoding="utf-8")
    deliver_src = body.split("def deliver(", 1)[1]
    assert deliver_src.index("require_grant") < deliver_src.index(
        "send_text_to_pane"
    )
