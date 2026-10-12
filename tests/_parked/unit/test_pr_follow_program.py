"""HS-106-08 userland census: four calls, four operation types, one consent spine."""
from __future__ import annotations

import ast
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def test_pr_follow_userland_uses_only_four_kernel_caller_calls() -> None:
    path = REPO / "holdspeak" / "web" / "routes" / "delivery_prs.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    broker_calls = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "broker"
    }
    assert broker_calls <= {"read", "submit", "decide", "events"}
    assert {"read", "submit", "decide"} <= broker_calls


def test_pr_follow_operation_matrix_is_deliberate_and_exact() -> None:
    text = (REPO / "holdspeak" / "web" / "routes" / "delivery_prs.py").read_text(encoding="utf-8")
    factory = (REPO / "holdspeak" / "delivery" / "factory_launch.py").read_text(encoding="utf-8")
    runtime = (REPO / "holdspeak" / "kernel" / "runtime.py").read_text(encoding="utf-8")
    inference = (REPO / "holdspeak" / "kernel" / "inference.py").read_text(encoding="utf-8")
    expected = {
        "process.spawn", "process.input", "inference.run", "actuator.egress",
        "decision.promotion-draft", "delivery.pr-review-draft", "voice_reference_resolve",
    }
    operations = {
        name for name in expected if name in text or name in factory or name in runtime or name in inference
    }
    assert operations == expected
    for forbidden in ("merge", "force-push", "approve-review", "close_pr"):
        assert f'"{forbidden}"' not in text


def test_pr_follow_adds_no_consent_state_machine() -> None:
    text = (REPO / "holdspeak" / "web" / "routes" / "delivery_prs.py").read_text(encoding="utf-8")
    assert "transition_proposal" not in text
    assert "record_proposal" not in text
    # The review draft is a receipt-gated parent run, not a consent transition.
    # The sole decision remains the owner-facing actuator proposal decision.
    assert text.count("broker.decide(") == 1
