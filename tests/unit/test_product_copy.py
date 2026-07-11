"""HS-93-03 — controlled primary-journey product-copy census."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from holdspeak.product_copy import (
    COPY_CLASSIFICATIONS,
    CopyCandidate,
    inventory,
    iter_surface_paths,
    violations,
)
from holdspeak.product_language import PRODUCT_LANGUAGE


REPO = Path(__file__).resolve().parents[2]


def test_every_declared_primary_surface_expands_and_is_classified() -> None:
    paths = list(iter_surface_paths(REPO))
    assert paths
    assert {client for client, _ in paths} == {"web", "swift", "cli_and_guides"}
    assert len(paths) == len(set(paths))

    candidates = inventory(REPO)
    assert len(candidates) >= 250
    assert {candidate.client for candidate in candidates} == {
        "web",
        "swift",
        "cli_and_guides",
    }
    assert {candidate.classification for candidate in candidates} <= COPY_CLASSIFICATIONS
    assert {candidate.classification for candidate in candidates} <= set(
        PRODUCT_LANGUAGE.copy_contract.classifications
    )


def test_primary_copy_has_no_prohibited_operational_drift() -> None:
    problems = violations(inventory(REPO))
    assert not problems, "Primary product-copy drift:\n  " + "\n  ".join(
        f"{item.path}:{item.line}: {item.rule_id}: {item.text}"
        for item in problems
    )


def test_each_prohibited_product_copy_rule_is_exercised() -> None:
    examples = {
        "legacy-product-nouns": "Agent Desk",
        "raw-control-mode-labels": "Safe",
        "unqualified-state": "pending",
        "promotional-narration": "The Desk comes alive",
        "paired-as-local": "Paired desktop is local",
    }
    for rule_id, value in examples.items():
        candidate = CopyCandidate(
            client="web",
            path="web/src/example.tsx",
            line=1,
            text=value,
            classification="label",
            context="label",
        )
        assert {item.rule_id for item in violations([candidate])} == {rule_id}

    for value in ("Approve", "Apply", "Open", "Run"):
        candidate = CopyCandidate(
            client="web",
            path="web/src/example.tsx",
            line=1,
            text=value,
            classification="label",
            context="action",
        )
        assert {item.rule_id for item in violations([candidate])} == {
            "generic-consequential-verb"
        }


def test_generic_open_exception_is_exact_and_bounded() -> None:
    allowed = CopyCandidate(
        client="swift",
        path="apple/App/MeetingCapture/ReviewUI.swift",
        line=1,
        text="Open",
        classification="label",
        context="action",
    )
    assert not violations([allowed])
    assert violations(
        [
            CopyCandidate(
                client="swift",
                path="apple/App/MeetingCapture/QueuePresence.swift",
                line=1,
                text="Open",
                classification="label",
                context="action",
            )
        ]
    )


def test_markdown_code_is_not_copy_and_does_not_exempt_surrounding_prose(
    tmp_path: Path,
) -> None:
    guide = tmp_path / "guide.md"
    guide.write_text("Use `ControlMode` on the wire; never render Agent Desk.\n")
    contract = replace(
        PRODUCT_LANGUAGE.copy_contract,
        primary_surfaces={"cli_and_guides": ("guide.md",)},
    )
    items = inventory(tmp_path, contract)
    assert all(item.text != "ControlMode" for item in items)
    assert {item.rule_id for item in violations(items, contract)} == {
        "legacy-product-nouns"
    }


def test_copy_contract_covers_postures_failures_and_bounded_exceptions() -> None:
    contract = PRODUCT_LANGUAGE.copy_contract
    assert contract.generic_consequential_verbs == (
        "Approve",
        "Apply",
        "Open",
        "Run",
    )
    assert contract.failure_requirements == (
        "failed_operation",
        "retained_work",
        "next_action",
        "destination_when_relevant",
    )
    assert {pattern.id for pattern in contract.prohibited_operational_patterns} == {
        "legacy-product-nouns",
        "raw-control-mode-labels",
        "unqualified-state",
        "promotional-narration",
        "paired-as-local",
    }
    exception_ids: set[str] = set()
    for exception in contract.exceptions:
        exception_id = str(exception["id"])
        assert exception_id not in exception_ids
        exception_ids.add(exception_id)
        assert str(exception["path"]).endswith((".swift", ".tsx", ".md"))
        assert exception["literals"]
        assert len(str(exception["reason"]).strip()) >= 40


def test_inventory_contains_shared_product_language_in_real_surfaces() -> None:
    values = {(item.client, item.text) for item in inventory(REPO)}
    assert ("web", "Secure") in values
    assert ("web", "Normal") in values
    assert ("swift", "Secure") in values
    assert ("swift", "Normal") in values
    assert any(client == "web" and "Runs on" in text for client, text in values)
    assert any(client == "swift" and "Coder session" in text for client, text in values)
