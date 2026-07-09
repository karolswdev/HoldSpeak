"""The sitting — one human UAT run of a pack, its verdicts landing durably.

A sitting boots one isolated run, walks a pack scenario by scenario, and
captures a verdict per (step, surface) the moment it is cast. It is crash-safe:
every verdict is written immediately, and the sitting resumes at the first
unanswered (scenario, step, surface) — a browser refresh or a product crash
loses nothing.

The site talks only to this manager (via the conductor API); the manager talks
to the product. One trust boundary: the site keeps working while the product is
being deliberately broken mid-sitting.
"""

from __future__ import annotations

import datetime as _dt
import secrets
from pathlib import Path
from typing import Any

from . import paths
from .contract.coverage import pack_coverage
from .contract.ledger import FeatureLedger
from .contract.scenarios import Scenario, load_pack
from .db import Database
from .induction.recipes import RecipeVerifyError
from .runs import RunManager


def _utcnow() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def _new_sitting_id() -> str:
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%S")
    return f"sit-{stamp}-{secrets.token_hex(2)}"


class SittingError(RuntimeError):
    pass


class SittingManager:
    def __init__(self, run_manager: RunManager, db: Database, ledger: FeatureLedger | None = None):
        self.runs = run_manager
        self.db = db
        self._ledger = ledger

    def ledger(self) -> FeatureLedger:
        if self._ledger is None:
            self._ledger = FeatureLedger.load()
        return self._ledger

    # --- lifecycle --------------------------------------------------------

    def create(self, pack: str, *, deck_override: str | None = None, lan: bool = False) -> dict:
        scenarios = load_pack(pack)  # raises ScenarioError (→ 404 at the route)
        if not scenarios:
            raise SittingError(f"pack {pack!r} has no scenarios")
        sitting_id = _new_sitting_id()
        # Boot golden-local; each scenario's recipes restart onto their own deck.
        boot_deck = deck_override or "golden-local"
        run = self.runs.create_run(deck=boot_deck, lan=lan)
        row = {
            "id": sitting_id,
            "run_id": run.id,
            "pack": pack,
            "deck": boot_deck,
            "status": "walking" if run.status == "up" else "staging",
            "created_at": _utcnow(),
            "updated_at": _utcnow(),
            "finished_at": None,
        }
        self.db.upsert_sitting(row)
        return self.get(sitting_id)

    def stage(self, sitting_id: str, scenario_id: str) -> dict:
        """Apply a scenario's recipes to the run, honestly reporting the outcome."""
        sitting = self.db.get_sitting(sitting_id)
        if sitting is None:
            raise SittingError(f"no such sitting: {sitting_id}")
        scenario = self._scenario(sitting["pack"], scenario_id)
        run_id = sitting["run_id"]
        staging: list[dict] = []
        for recipe in scenario.recipes:
            try:
                result = self.runs.apply_recipe(run_id, recipe)
                staging.append({"recipe": recipe, "ok": result.probe.get("ok", False), "result": result.to_dict()})
            except RecipeVerifyError as exc:
                logs = self.runs.logs(run_id, 40)
                staging.append({
                    "recipe": recipe,
                    "ok": False,
                    "error": str(exc),
                    "result": exc.result.to_dict(),
                    "log_tail": logs,
                })
                return {"ok": False, "scenario_id": scenario_id, "staging": staging}
            except Exception as exc:  # boot/apply failure — show the log tail, never hang
                logs = self.runs.logs(run_id, 40)
                staging.append({"recipe": recipe, "ok": False, "error": str(exc), "log_tail": logs})
                return {"ok": False, "scenario_id": scenario_id, "staging": staging}
        return {"ok": True, "scenario_id": scenario_id, "staging": staging}

    def run_after_actions(self, sitting_id: str, scenario_id: str, step_index: int) -> list[dict]:
        """Perform a step's mid-run conductor actions (apply recipe, kill node)."""
        sitting = self._require(sitting_id)
        scenario = self._scenario(sitting["pack"], scenario_id)
        step = scenario.steps[step_index]
        performed: list[dict] = []
        for action in step.after:
            (kind, arg), = action.items() if isinstance(action, dict) else (("", None),)
            if kind == "apply_recipe":
                name = arg["name"] if isinstance(arg, dict) else str(arg)
                try:
                    res = self.runs.apply_recipe(sitting["run_id"], name)
                    performed.append({"action": "apply_recipe", "name": name, "ok": res.probe.get("ok", False), "result": res.to_dict()})
                except Exception as exc:
                    performed.append({"action": "apply_recipe", "name": name, "ok": False, "error": str(exc)})
            elif kind == "kill_node":
                name = arg["name"] if isinstance(arg, dict) else str(arg)
                performed.append({"action": "kill_node", "name": name, "killed": self.runs.kill_node(sitting["run_id"], name)})
            elif kind == "restart":
                deck = (arg or {}).get("deck")
                self.runs.restart(sitting["run_id"], deck=deck)
                performed.append({"action": "restart", "deck": deck})
            else:
                performed.append({"action": kind, "error": "unknown action"})
        return performed

    # --- verdicts ---------------------------------------------------------

    def cast_verdict(
        self,
        sitting_id: str,
        *,
        scenario_id: str,
        step_index: int,
        surface: str,
        verdict: str,
        note: str | None = None,
        shot_path: str | None = None,
        started_at: str | None = None,
    ) -> dict:
        if verdict not in ("pass", "fail", "partial", "skip"):
            raise SittingError(f"invalid verdict: {verdict!r}")
        if surface not in ("web", "ipad", "iphone"):
            raise SittingError(f"invalid surface: {surface!r}")
        sitting = self._require(sitting_id)
        self.db.cast_verdict({
            "run_id": sitting["run_id"],
            "pack": sitting["pack"],
            "scenario_id": scenario_id,
            "step_index": step_index,
            "surface": surface,
            "verdict": verdict,
            "note": note,
            "shot_path": shot_path,
            "started_at": started_at,
            "created_at": _utcnow(),
        })
        self.db.upsert_sitting({**sitting, "updated_at": _utcnow(), "status": "walking"})
        return self.get(sitting_id)

    def save_shot(self, sitting_id: str, scenario_id: str, step_index: int, surface: str, data: bytes, suffix: str = ".png") -> str:
        sitting = self._require(sitting_id)
        shots = paths.run_shots_dir(sitting["run_id"])
        shots.mkdir(parents=True, exist_ok=True)
        name = f"{scenario_id}-step{step_index}-{surface}{suffix}"
        (shots / name).write_bytes(data)
        return str((shots / name))

    def finish(self, sitting_id: str) -> dict:
        sitting = self._require(sitting_id)
        self.db.upsert_sitting({**sitting, "status": "done", "finished_at": _utcnow(), "updated_at": _utcnow()})
        return self.get(sitting_id)

    # --- reads ------------------------------------------------------------

    def get(self, sitting_id: str) -> dict:
        sitting = self._require(sitting_id)
        scenarios = load_pack(sitting["pack"])
        verdicts = self.db.list_verdicts(sitting["run_id"])
        verdict_index = {
            (v["scenario_id"], v["step_index"], v["surface"]): v for v in verdicts
        }
        run = self.runs.get(sitting["run_id"])
        resume = self._resume_point(scenarios, verdict_index)
        cov = pack_coverage(scenarios, self.ledger())
        return {
            "id": sitting["id"],
            "pack": sitting["pack"],
            "status": sitting["status"],
            "created_at": sitting["created_at"],
            "finished_at": sitting.get("finished_at"),
            "run": run.to_public() if run else None,
            "scenarios": [s.to_dict() for s in scenarios],
            "verdicts": verdicts,
            "resume": resume,
            "coverage": cov,
            "progress": self._progress(scenarios, verdict_index),
        }

    def list(self) -> list[dict]:
        out = []
        for s in self.db.list_sittings():
            verdicts = self.db.list_verdicts(s["run_id"]) if s.get("run_id") else []
            out.append({
                "id": s["id"],
                "pack": s["pack"],
                "status": s["status"],
                "created_at": s["created_at"],
                "finished_at": s.get("finished_at"),
                "verdicts_cast": len(verdicts),
            })
        return out

    # --- internals --------------------------------------------------------

    def _require(self, sitting_id: str) -> dict:
        sitting = self.db.get_sitting(sitting_id)
        if sitting is None:
            raise SittingError(f"no such sitting: {sitting_id}")
        return sitting

    def _scenario(self, pack: str, scenario_id: str) -> Scenario:
        for s in load_pack(pack):
            if s.id == scenario_id:
                return s
        raise SittingError(f"no scenario {scenario_id!r} in pack {pack!r}")

    def _resume_point(self, scenarios: list[Scenario], verdict_index: dict) -> dict | None:
        for scenario in scenarios:
            for step in scenario.steps:
                for surface in step.applicable_surfaces(scenario.surfaces):
                    if (scenario.id, step.index, surface) not in verdict_index:
                        return {
                            "scenario_id": scenario.id,
                            "step_index": step.index,
                            "surface": surface,
                        }
        return None  # sitting complete

    def _progress(self, scenarios: list[Scenario], verdict_index: dict) -> dict:
        expected = sum(sc.expected_verdict_count() for sc in scenarios)
        cast = 0
        for scenario in scenarios:
            for step in scenario.steps:
                for surface in step.applicable_surfaces(scenario.surfaces):
                    if (scenario.id, step.index, surface) in verdict_index:
                        cast += 1
        return {"cast": cast, "expected": expected, "complete": cast >= expected}
