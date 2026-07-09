"""The scenario contract — the unit of UAT, loaded and validated.

A scenario (`uat/scenarios/<pack>/<nn>-<slug>.yaml`) declares the world to
stage (`recipes`), what it covers (`features`, ledger keys), the three-surface
applicability (`surfaces`, default all-yes, opted out only with `{n/a: reason}`),
and ordered `steps` (each an instruction, an honest expectation, an optional
`where` route to open, an optional per-step surface override, and optional
`after` conductor actions performed before the next step).

Validation produces **named, greppable** errors — `ERROR <file>: <issue>` — so a
malformed scenario fails loudly, naming the file and field.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .ledger import SURFACES


def scenarios_dir() -> Path:
    override = os.environ.get("UAT_SCENARIOS_DIR")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[3] / "uat" / "scenarios"


class ScenarioError(ValueError):
    pass


def _parse_surface(value: Any) -> dict:
    """Normalise a surface cell to {applicable: bool, reason: str|None}.

    Allowed forms: ``yes`` / ``true`` (applicable), or ``{n/a: <reason>}`` /
    ``{na: <reason>}`` (opted out, reason required). Anything else raises.
    """
    if value in (True, "yes", "Yes", "y"):
        return {"applicable": True, "reason": None}
    if isinstance(value, dict):
        for k in ("n/a", "na", "n_a"):
            if k in value:
                reason = str(value[k] or "").strip()
                if not reason:
                    raise ScenarioError("n/a surface needs a stated reason")
                return {"applicable": False, "reason": reason}
    raise ScenarioError(
        f"surface value must be 'yes' or {{n/a: <reason>}}, got {value!r}"
    )


@dataclass
class Step:
    index: int
    do: str
    expect: str
    where: str | None = None
    surfaces: dict[str, Any] = field(default_factory=dict)  # raw per-step overrides
    after: list[Any] = field(default_factory=list)

    def resolved_surfaces(self, scenario_surfaces: dict[str, dict]) -> dict[str, dict]:
        """Effective per-surface applicability for this step (step overrides scenario)."""
        out: dict[str, dict] = {}
        for s in SURFACES:
            if s in self.surfaces:
                out[s] = _parse_surface(self.surfaces[s])
            else:
                out[s] = scenario_surfaces.get(s, {"applicable": True, "reason": None})
        return out

    def applicable_surfaces(self, scenario_surfaces: dict[str, dict]) -> list[str]:
        return [s for s, v in self.resolved_surfaces(scenario_surfaces).items() if v["applicable"]]


@dataclass
class Scenario:
    id: str
    title: str
    pack: str
    features: list[str]
    recipes: list[str]
    surfaces: dict[str, dict]  # resolved {surface: {applicable, reason}}
    steps: list[Step]
    manual_setup: list[str] = field(default_factory=list)  # human-run staging when no recipe can
    teardown: list[Any] = field(default_factory=list)
    source: str = ""

    def expected_verdict_count(self) -> int:
        """Total (step, surface) verdicts a full sitting of this scenario casts."""
        return sum(len(step.applicable_surfaces(self.surfaces)) for step in self.steps)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "pack": self.pack,
            "features": self.features,
            "recipes": self.recipes,
            "manual_setup": self.manual_setup,
            "surfaces": self.surfaces,
            "steps": [
                {
                    "index": s.index,
                    "do": s.do,
                    "expect": s.expect,
                    "where": s.where,
                    "surfaces": s.resolved_surfaces(self.surfaces),
                    "after": s.after,
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

    # Scenario-level surfaces: default all-yes, override with {n/a: reason}.
    raw_surfaces = doc.get("surfaces") or {}
    surfaces: dict[str, dict] = {}
    for s in SURFACES:
        try:
            surfaces[s] = _parse_surface(raw_surfaces.get(s, "yes"))
        except ScenarioError as exc:
            raise ScenarioError(f"ERROR {path}: surface {s}: {exc}") from exc

    raw_steps = doc.get("steps") or []
    steps: list[Step] = []
    for i, raw in enumerate(raw_steps):
        if not isinstance(raw, dict):
            raise ScenarioError(f"ERROR {path}: step {i} must be a mapping")
        if "do" not in raw or "expect" not in raw:
            raise ScenarioError(f"ERROR {path}: step {i} needs both 'do' and 'expect'")
        step = Step(
            index=i,
            do=str(raw["do"]),
            expect=str(raw["expect"]),
            where=raw.get("where"),
            surfaces=raw.get("surfaces") or {},
            after=list(raw.get("after") or []),
        )
        # Validate per-step surface overrides eagerly (names the file+step).
        try:
            step.resolved_surfaces(surfaces)
        except ScenarioError as exc:
            raise ScenarioError(f"ERROR {path}: step {i} surface: {exc}") from exc
        steps.append(step)

    return Scenario(
        id=sid,
        title=title,
        pack=pack or path.parent.name,
        features=features,
        recipes=recipes,
        surfaces=surfaces,
        steps=steps,
        manual_setup=[str(x) for x in (doc.get("manual_setup") or [])],
        teardown=list(doc.get("teardown") or []),
        source=str(path),
    )


def validate_scenario(
    scenario: Scenario,
    *,
    ledger_keys: set[str],
    recipe_names: set[str],
    deck_names: set[str] | None = None,
) -> list[str]:
    """Cross-reference a scenario against the ledger + recipe/deck registries."""
    errors: list[str] = []
    src = scenario.source

    if not scenario.features:
        errors.append(f"ERROR {src}: scenario cites no features (need ≥1 ledger key)")
    for key in scenario.features:
        if key not in ledger_keys:
            errors.append(f"ERROR {src}: unknown ledger key: {key}")

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

    if not scenario.steps:
        errors.append(f"ERROR {src}: scenario has no steps")

    for step in scenario.steps:
        applicable = step.applicable_surfaces(scenario.surfaces)
        if not applicable:
            errors.append(
                f"ERROR {src}: step {step.index} has no applicable surface "
                "(every surface n/a — a step must be walked somewhere)"
            )
        for action in step.after:
            errors.extend(_validate_action(action, src, step.index, recipe_names, deck_names))

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
    if not pack_dir.exists():
        raise ScenarioError(f"unknown pack: {pack} (looked in {base})")
    scenarios = [load_scenario(p, pack=pack) for p in sorted(pack_dir.glob("*.yaml"))]
    _check_unique_ids(scenarios, pack_dir)
    return scenarios


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
    return sorted(p.name for p in base.iterdir() if p.is_dir())
