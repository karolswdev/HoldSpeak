"""Target-qualified authored and executed UAT coverage."""

from __future__ import annotations

from typing import Any

from .ledger import FeatureLedger
from .scenarios import Scenario
from .targets import ExecutionSlot


def _slots(scenarios: list[Scenario]) -> list[ExecutionSlot]:
    by_id: dict[str, ExecutionSlot] = {}
    for scenario in scenarios:
        for step in scenario.steps:
            for slot in step.execution_slots(scenario):
                by_id[slot.id] = slot
    return [by_id[key] for key in sorted(by_id)]


def cited_keys(scenarios: list[Scenario]) -> set[str]:
    keys: set[str] = set()
    for scenario in scenarios:
        if not any(slot.quarantined for slot in scenario.execution_slots):
            keys.update(scenario.features)
    return keys


def cited_keys_on_slot(scenarios: list[Scenario], slot_id: str) -> set[str]:
    keys: set[str] = set()
    for scenario in scenarios:
        if any(step.verifies for step in scenario.steps):
            for step in scenario.steps:
                if slot_id in {slot.id for slot in step.execution_slots(scenario)}:
                    keys.update(step.verifies)
        elif slot_id in {slot.id for slot in scenario.execution_slots}:
            keys.update(scenario.features)
    return keys


def _slot_report(
    scenarios: list[Scenario], ledger: FeatureLedger, keys_by_slot: dict[str, set[str]]
) -> tuple[dict[str, dict], dict[str, int]]:
    report: dict[str, dict] = {}
    unknown: dict[str, int] = {}
    for slot in _slots(scenarios):
        result = ledger.coverage_slot(keys_by_slot.get(slot.id, set()), slot).to_dict()
        result["target"] = slot.target
        result["form_factor"] = slot.form_factor
        result["label"] = slot.label
        result["native"] = slot.native
        result["quarantined"] = slot.quarantined
        report[slot.id] = result
        unknown[slot.id] = ledger.unknown_on_slot(slot)
    return report, unknown


def pack_coverage(scenarios: list[Scenario], ledger: FeatureLedger) -> dict[str, Any]:
    """Authored coverage; never execution evidence."""
    keys_by_slot = {
        slot.id: cited_keys_on_slot(scenarios, slot.id) for slot in _slots(scenarios)
    }
    slots, unknown = _slot_report(scenarios, ledger, keys_by_slot)
    credited = set().union(
        *(
            keys
            for slot_id, keys in keys_by_slot.items()
            if not slots[slot_id]["quarantined"]
        ),
        set(),
    )
    return {
        "scenario_count": len(scenarios),
        "cited_features": sorted(credited),
        "overall": ledger.coverage_overall(credited).to_dict(),
        "slots": slots,
        "unknown_cells": unknown,
        "expected_verdicts": sum(scenario.expected_verdict_count() for scenario in scenarios),
        "kind": "authored",
    }


def executed_keys_on_slot(
    scenarios: list[Scenario], verdicts: list[dict], slot_id: str
) -> set[str]:
    """Feature keys substantively exercised on one exact execution slot."""
    index = {
        (verdict.get("scenario_id"), verdict.get("step_index"), verdict.get("slot_id")):
        verdict.get("verdict")
        for verdict in verdicts
    }
    keys: set[str] = set()
    for scenario in scenarios:
        if any(step.verifies for step in scenario.steps):
            for step in scenario.steps:
                if slot_id not in {slot.id for slot in step.execution_slots(scenario)}:
                    continue
                outcome = index.get((scenario.id, step.index, slot_id))
                if outcome is not None and outcome != "skip":
                    keys.update(step.verifies)
            continue
        applicable = [
            step
            for step in scenario.steps
            if slot_id in {slot.id for slot in step.execution_slots(scenario)}
        ]
        if not applicable:
            continue
        outcomes = [index.get((scenario.id, step.index, slot_id)) for step in applicable]
        if all(outcome is not None and outcome != "skip" for outcome in outcomes):
            keys.update(scenario.features)
    return keys


def execution_coverage(
    scenarios: list[Scenario], ledger: FeatureLedger, verdicts: list[dict]
) -> dict[str, Any]:
    slots_list = _slots(scenarios)
    keys_by_slot = {
        slot.id: executed_keys_on_slot(scenarios, verdicts, slot.id)
        for slot in slots_list
    }
    slots, unknown = _slot_report(scenarios, ledger, keys_by_slot)
    credited = set().union(
        *(
            keys
            for slot_id, keys in keys_by_slot.items()
            if not slots[slot_id]["quarantined"]
        ),
        set(),
    )
    return {
        "scenario_count": len(scenarios),
        "cited_features": sorted(credited),
        "overall": ledger.coverage_overall(credited).to_dict(),
        "slots": slots,
        "unknown_cells": unknown,
        "expected_verdicts": sum(scenario.expected_verdict_count() for scenario in scenarios),
        "verdicts_cast": len(verdicts),
        "kind": "executed",
    }
