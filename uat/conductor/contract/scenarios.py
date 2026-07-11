"""Protocol-v2 scenario contract.

Every scenario names one concrete implementation target and one or more form
factors.  Their Cartesian product is the execution-slot identity persisted on
every verdict.  There are deliberately no defaults: omitting the target or
form factor is an invalid protocol, and a React viewport can never become a
Swift-device result by choosing a differently labelled button.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

import yaml

from .targets import (
    PROTOCOL_SCHEMA_VERSION,
    TARGETS,
    ExecutionSlot,
    validate_target_form,
)


def scenarios_dir() -> Path:
    override = os.environ.get("UAT_SCENARIOS_DIR")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[3] / "uat" / "scenarios"


def campaigns_dir() -> Path:
    """Directory of ordered owner campaigns composed from authored scenarios."""
    override = os.environ.get("UAT_CAMPAIGNS_DIR")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[3] / "uat" / "campaigns"


class ScenarioError(ValueError):
    pass


def _parse_form_factors(value: Any, *, path: Path, context: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ScenarioError(
            f"ERROR {path}: {context} must be an explicit non-empty list"
        )
    forms = [str(item).strip() for item in value]
    if any(not item for item in forms):
        raise ScenarioError(f"ERROR {path}: {context} contains an empty value")
    if len(forms) != len(set(forms)):
        raise ScenarioError(f"ERROR {path}: {context} contains duplicates")
    return forms


@dataclass
class Step:
    index: int
    do: str
    expect: str
    where: str | None = None
    form_factors: list[str] | None = None
    after: list[Any] = field(default_factory=list)
    verifies: list[str] = field(default_factory=list)

    def execution_slots(self, scenario: "Scenario") -> list[ExecutionSlot]:
        forms = self.form_factors or scenario.form_factors
        return [ExecutionSlot(scenario.execution_target, form) for form in forms]


@dataclass
class Scenario:
    id: str
    title: str
    pack: str
    features: list[str]
    recipes: list[str]
    form_factors: list[str]
    steps: list[Step]
    execution_target: str
    manual_setup: list[str] = field(default_factory=list)  # human-run staging when no recipe can
    teardown: list[Any] = field(default_factory=list)
    source: str = ""

    def expected_verdict_count(self) -> int:
        """Total (step, surface) verdicts a full sitting of this scenario casts."""
        return sum(len(step.execution_slots(self)) for step in self.steps)

    @property
    def execution_slots(self) -> list[ExecutionSlot]:
        return [ExecutionSlot(self.execution_target, form) for form in self.form_factors]

    def to_dict(self) -> dict:
        return {
            "protocol_schema": PROTOCOL_SCHEMA_VERSION,
            "id": self.id,
            "title": self.title,
            "pack": self.pack,
            "features": self.features,
            "recipes": self.recipes,
            "manual_setup": self.manual_setup,
            "execution_target": self.execution_target,
            "form_factors": self.form_factors,
            "execution_slots": [slot.to_dict() for slot in self.execution_slots],
            "steps": [
                {
                    "index": s.index,
                    "do": s.do,
                    "expect": s.expect,
                    "where": s.where,
                    "form_factors": s.form_factors or self.form_factors,
                    "execution_slots": [slot.to_dict() for slot in s.execution_slots(self)],
                    "after": s.after,
                    "verifies": s.verifies,
                }
                for s in self.steps
            ],
            "teardown": self.teardown,
            "expected_verdict_count": self.expected_verdict_count(),
        }


def load_scenario(path: Path, pack: str | None = None) -> Scenario:
    path = Path(path)
    try:
        doc = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError as exc:
        raise ScenarioError(f"ERROR {path}: not valid YAML: {exc}") from exc
    if not isinstance(doc, dict):
        raise ScenarioError(f"ERROR {path}: top level must be a mapping")

    def need(field_name: str) -> Any:
        if field_name not in doc:
            raise ScenarioError(f"ERROR {path}: missing required field '{field_name}'")
        return doc[field_name]

    sid = str(need("id"))
    title = str(need("title"))
    features = list(doc.get("features") or [])
    recipes = list(doc.get("recipes") or [])

    if "surfaces" in doc:
        raise ScenarioError(
            f"ERROR {path}: legacy 'surfaces' is forbidden in protocol v2; "
            "use execution_target + form_factors"
        )
    execution_target = str(need("execution_target")).strip()
    form_factors = _parse_form_factors(
        need("form_factors"), path=path, context="form_factors"
    )

    raw_steps = doc.get("steps") or []
    steps: list[Step] = []
    for i, raw in enumerate(raw_steps):
        if not isinstance(raw, dict):
            raise ScenarioError(f"ERROR {path}: step {i} must be a mapping")
        if "do" not in raw or "expect" not in raw:
            raise ScenarioError(f"ERROR {path}: step {i} needs both 'do' and 'expect'")
        if "surfaces" in raw:
            raise ScenarioError(
                f"ERROR {path}: step {i} uses legacy 'surfaces'; use form_factors"
            )
        step_forms = None
        if "form_factors" in raw:
            step_forms = _parse_form_factors(
                raw["form_factors"], path=path, context=f"step {i} form_factors"
            )
        step = Step(
            index=i,
            do=str(raw["do"]),
            expect=str(raw["expect"]),
            where=raw.get("where"),
            form_factors=step_forms,
            after=list(raw.get("after") or []),
            verifies=[str(key) for key in (raw.get("verifies") or [])],
        )
        steps.append(step)

    return Scenario(
        id=sid,
        title=title,
        pack=pack or path.parent.name,
        features=features,
        recipes=recipes,
        form_factors=form_factors,
        steps=steps,
        execution_target=execution_target,
        manual_setup=[str(x) for x in (doc.get("manual_setup") or [])],
        teardown=list(doc.get("teardown") or []),
        source=str(path),
    )


def scenario_from_dict(doc: dict[str, Any]) -> Scenario:
    """Rehydrate the normalized shape stored in a sitting snapshot."""
    legacy = int(doc.get("protocol_schema") or 1) < PROTOCOL_SCHEMA_VERSION
    if legacy:
        old = doc.get("surfaces") or {}
        form_factors = [
            surface
            for surface in ("web", "ipad", "iphone")
            if (old.get(surface) or {}).get("applicable")
        ] or ["web"]
        target = "legacy_unqualified"
    else:
        form_factors = [str(item) for item in (doc.get("form_factors") or [])]
        target = str(doc["execution_target"])
    steps = []
    for index, raw in enumerate(doc.get("steps") or []):
        if legacy:
            resolved = raw.get("surfaces") or {}
            step_forms = [
                surface
                for surface in ("web", "ipad", "iphone")
                if (resolved.get(surface) or {}).get("applicable")
            ]
        else:
            step_forms = [str(item) for item in (raw.get("form_factors") or [])]
        steps.append(
            Step(
                index=int(raw.get("index", index)),
                do=str(raw.get("do", "")),
                expect=str(raw.get("expect", "")),
                where=raw.get("where"),
                form_factors=step_forms or None,
                after=list(raw.get("after") or []),
                verifies=[str(key) for key in (raw.get("verifies") or [])],
            )
        )
    return Scenario(
        id=str(doc["id"]),
        title=str(doc["title"]),
        pack=str(doc["pack"]),
        features=list(doc.get("features") or []),
        recipes=list(doc.get("recipes") or []),
        form_factors=form_factors,
        steps=steps,
        execution_target=target,
        manual_setup=list(doc.get("manual_setup") or []),
        teardown=list(doc.get("teardown") or []),
        source=str(doc.get("source") or "protocol-snapshot"),
    )


def validate_scenario(
    scenario: Scenario,
    *,
    ledger_keys: set[str],
    recipe_names: set[str],
    deck_names: set[str] | None = None,
    recipe_decks: dict[str, str] | None = None,
) -> list[str]:
    """Cross-reference a scenario against the ledger + recipe/deck registries."""
    errors: list[str] = []
    src = scenario.source

    if not scenario.features:
        errors.append(f"ERROR {src}: scenario cites no features (need ≥1 ledger key)")
    for key in scenario.features:
        if key not in ledger_keys:
            errors.append(f"ERROR {src}: unknown ledger key: {key}")

    if scenario.execution_target not in TARGETS:
        errors.append(
            f"ERROR {src}: unknown execution_target {scenario.execution_target!r}"
        )

    # A scenario stages its world by a recipe OR by a human precondition
    # (manual_setup) — a must-do protocol we can't auto-stage is still a real
    # protocol the person stages by hand and walks. One of the two is required.
    if not scenario.recipes and not scenario.manual_setup:
        errors.append(
            f"ERROR {src}: scenario names no recipes and no manual_setup "
            "(need ≥1 recipe, or manual_setup steps for a hand-staged protocol)"
        )
    for r in scenario.recipes:
        if r not in recipe_names:
            errors.append(f"ERROR {src}: unknown recipe: {r}")
    if recipe_decks is not None and len(scenario.recipes) > 1:
        initial_decks = {
            recipe_decks[r]
            for r in scenario.recipes
            if r in recipe_decks
        }
        if len(initial_decks) > 1:
            errors.append(
                f"ERROR {src}: initial recipes span multiple decks "
                f"({', '.join(sorted(initial_decks))}); only the last deck can be "
                "active before step 1. Use one composite recipe or a step 'after' "
                "transition instead"
            )

    if not scenario.steps:
        errors.append(f"ERROR {src}: scenario has no steps")

    for form in scenario.form_factors:
        error = validate_target_form(scenario.execution_target, form)
        if error:
            errors.append(f"ERROR {src}: {error}")

    for step in scenario.steps:
        forms = step.form_factors or scenario.form_factors
        if step.where and scenario.execution_target != "web_react":
            errors.append(
                f"ERROR {src}: step {step.index} has web route 'where' on "
                f"non-web target {scenario.execution_target!r}"
            )
        if step.form_factors and not set(step.form_factors).issubset(scenario.form_factors):
            errors.append(
                f"ERROR {src}: step {step.index} form_factors must be a subset "
                "of the scenario form_factors"
            )
        for form in forms:
            error = validate_target_form(scenario.execution_target, form)
            if error:
                errors.append(f"ERROR {src}: step {step.index}: {error}")
        for action in step.after:
            errors.extend(_validate_action(action, src, step.index, recipe_names, deck_names))
        for key in step.verifies:
            if key not in scenario.features:
                errors.append(
                    f"ERROR {src}: step {step.index} verifies {key!r}, but the key "
                    "is not declared in scenario.features"
                )

    mapped = {key for step in scenario.steps for key in step.verifies}
    if mapped:
        missing = set(scenario.features) - mapped
        if missing:
            errors.append(
                f"ERROR {src}: step-level verifies mapping misses scenario feature(s): "
                f"{', '.join(sorted(missing))}"
            )

    return errors


def _validate_action(action: Any, src: str, step_index: int, recipe_names, deck_names) -> list[str]:
    if not isinstance(action, dict) or len(action) != 1:
        return [f"ERROR {src}: step {step_index} after-action must be a single-key mapping: {action!r}"]
    (kind, arg), = action.items()
    if kind == "apply_recipe":
        name = arg["name"] if isinstance(arg, dict) else str(arg)
        if name not in recipe_names:
            return [f"ERROR {src}: step {step_index} apply_recipe names unknown recipe: {name}"]
    elif kind == "restart":
        deck = (arg or {}).get("deck") if isinstance(arg, dict) else None
        if deck and deck_names is not None and deck not in deck_names:
            return [f"ERROR {src}: step {step_index} restart names unknown deck: {deck}"]
    elif kind in ("kill_node", "spawn_node", "wait"):
        pass
    else:
        return [f"ERROR {src}: step {step_index} unknown after-action: {kind}"]
    return []


def load_pack(pack: str, directory: Path | None = None) -> list[Scenario]:
    base = Path(directory) if directory else scenarios_dir()
    pack_dir = base / pack
    if pack_dir.exists():
        scenarios = [load_scenario(p, pack=pack) for p in sorted(pack_dir.glob("*.yaml"))]
        _check_unique_ids(scenarios, pack_dir)
        return scenarios

    # Campaigns are executable packs assembled by reference. They reuse the
    # canonical scenario files, so there is one protocol definition to fix and
    # one ordered owner pass to execute. A custom scenarios directory remains
    # hermetic unless a custom campaign directory is explicitly configured.
    campaign_path = campaigns_dir() / f"{pack}.yaml"
    campaigns_enabled = directory is None or os.environ.get("UAT_CAMPAIGNS_DIR")
    if campaigns_enabled and campaign_path.exists():
        doc = _load_campaign_doc(campaign_path)
        scenarios: list[Scenario] = []
        for index, raw_ref in enumerate(doc.get("scenarios") or []):
            source_pack, scenario_id = _parse_campaign_ref(
                raw_ref, campaign_path, index
            )
            source_dir = base / source_pack
            if not source_dir.is_dir():
                raise ScenarioError(
                    f"ERROR {campaign_path}: scenario reference {index} names "
                    f"unknown source pack {source_pack!r}"
                )
            source_scenarios = load_pack(source_pack, directory=base)
            match = next((item for item in source_scenarios if item.id == scenario_id), None)
            if match is None:
                raise ScenarioError(
                    f"ERROR {campaign_path}: scenario reference {index} names "
                    f"unknown id {scenario_id!r} in {source_pack!r}"
                )
            scenarios.append(replace(match, pack=pack))
        if not scenarios:
            raise ScenarioError(f"ERROR {campaign_path}: campaign has no scenarios")
        _check_unique_ids(scenarios, campaign_path)
        return scenarios

    raise ScenarioError(f"unknown pack: {pack} (looked in {base})")


def _check_unique_ids(scenarios: list[Scenario], pack_dir: Path) -> None:
    seen: set[str] = set()
    for s in scenarios:
        if s.id in seen:
            raise ScenarioError(f"ERROR {pack_dir}: duplicate scenario id: {s.id}")
        seen.add(s.id)


def list_packs(directory: Path | None = None) -> list[str]:
    base = Path(directory) if directory else scenarios_dir()
    if not base.exists():
        return []
    names = {p.name for p in base.iterdir() if p.is_dir()}
    campaigns_enabled = directory is None or os.environ.get("UAT_CAMPAIGNS_DIR")
    if campaigns_enabled and campaigns_dir().exists():
        names.update(p.stem for p in campaigns_dir().glob("*.yaml"))
    return sorted(names)


def pack_metadata(pack: str) -> dict[str, Any]:
    """Human execution metadata for a pack/campaign.

    Ordinary authored packs get conservative defaults. Campaign manifests add
    the owner-facing purpose, prerequisites, duration, and completion gate used
    by the guided site's pack picker and the functional runbook.
    """
    path = campaigns_dir() / f"{pack}.yaml"
    if path.exists():
        doc = _load_campaign_doc(path)
        return {
            "title": str(doc.get("title") or pack),
            "purpose": str(doc.get("purpose") or ""),
            "sequence": int(doc.get("sequence") or 0),
            "tier": str(doc.get("tier") or "core"),
            "estimated_minutes": int(doc.get("estimated_minutes") or 0),
            "prerequisites": [str(item) for item in (doc.get("prerequisites") or [])],
            "exit_gate": [str(item) for item in (doc.get("exit_gate") or [])],
            "is_campaign": True,
        }
    return {
        "title": pack.replace("-", " ").title(),
        "purpose": "Authored protocol pack.",
        "sequence": 0,
        "tier": "reference",
        "estimated_minutes": 0,
        "prerequisites": [],
        "exit_gate": [],
        "is_campaign": False,
    }


def _load_campaign_doc(path: Path) -> dict[str, Any]:
    try:
        doc = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError as exc:
        raise ScenarioError(f"ERROR {path}: not valid YAML: {exc}") from exc
    if not isinstance(doc, dict):
        raise ScenarioError(f"ERROR {path}: top level must be a mapping")
    refs = doc.get("scenarios")
    if not isinstance(refs, list) or not refs:
        raise ScenarioError(f"ERROR {path}: 'scenarios' must be a non-empty list")
    return doc


def _parse_campaign_ref(raw: Any, path: Path, index: int) -> tuple[str, str]:
    if isinstance(raw, str) and "/" in raw:
        source_pack, scenario_id = raw.split("/", 1)
    elif isinstance(raw, dict):
        source_pack = str(raw.get("pack") or "")
        scenario_id = str(raw.get("id") or "")
    else:
        source_pack = scenario_id = ""
    if not source_pack or not scenario_id:
        raise ScenarioError(
            f"ERROR {path}: scenario reference {index} must be 'pack/id' or "
            "{pack: ..., id: ...}"
        )
    return source_pack, scenario_id
