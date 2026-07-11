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
import hashlib
import json
import re
import secrets
import subprocess
import threading
import time
from pathlib import Path

from . import paths
from .contract.coverage import execution_coverage, pack_coverage
from .contract.ledger import FeatureLedger
from .contract.scenarios import (
    Scenario,
    campaigns_dir,
    load_pack,
    scenario_from_dict,
    validate_scenario,
)
from .contract.targets import PROTOCOL_SCHEMA_VERSION, TARGETS
from .db import Database
from .induction.recipes import RecipeVerifyError
from .runs import RunManager


def _utcnow() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def _new_sitting_id() -> str:
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%S")
    return f"sit-{stamp}-{secrets.token_hex(2)}"


def _new_device_session_id() -> str:
    return f"device-{secrets.token_hex(6)}"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _asset_label(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(paths.repo_root().resolve()))
    except ValueError:
        return str(path.resolve())


def _git_commit() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=paths.repo_root(),
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=5,
        ).strip()
    except (OSError, subprocess.SubprocessError):
        return None


class SittingError(RuntimeError):
    pass


class SittingManager:
    def __init__(self, run_manager: RunManager, db: Database, ledger: FeatureLedger | None = None):
        self.runs = run_manager
        self.db = db
        self._ledger = ledger
        self._transition_lock = threading.RLock()

    def ledger(self) -> FeatureLedger:
        if self._ledger is None:
            self._ledger = FeatureLedger.load()
        return self._ledger

    # --- lifecycle --------------------------------------------------------

    def create(self, pack: str, *, deck_override: str | None = None, lan: bool = False) -> dict:
        scenarios = load_pack(pack)  # raises ScenarioError (→ 404 at the route)
        if not scenarios:
            raise SittingError(f"pack {pack!r} has no scenarios")
        errors: list[str] = []
        ledger = self.ledger()
        recipe_names = set(self.runs.recipes.registry.names())
        recipe_decks = {
            name: self.runs.recipes.registry.load(name).deck
            for name in recipe_names
        }
        deck_names = set(self.runs.decks.names())
        for scenario in scenarios:
            errors.extend(
                validate_scenario(
                    scenario,
                    ledger_keys=ledger.keys(),
                    recipe_names=recipe_names,
                    deck_names=deck_names,
                    recipe_decks=recipe_decks,
                )
            )
            for slot in scenario.execution_slots:
                if slot.quarantined:
                    continue
                for key in scenario.features:
                    feature = ledger.get(key)
                    if feature is None:
                        continue
                    applicability = feature.applicability_on_slot(slot)
                    if applicability == "no" or (
                        slot.native and applicability != "yes"
                    ):
                        errors.append(
                            f"ERROR {scenario.source}: feature {key!r} is "
                            f"{applicability} on {slot.id}; target-qualified "
                            "coverage must be explicit"
                        )
        if errors:
            raise SittingError(
                f"pack {pack!r} is invalid and cannot start:\n" + "\n".join(errors)
            )
        quarantined_targets = {
            scenario.execution_target
            for scenario in scenarios
            if TARGETS.get(scenario.execution_target, {}).get("quarantined")
        }
        if quarantined_targets:
            raise SittingError(
                f"pack {pack!r} contains unresolved quarantined target(s): "
                f"{', '.join(sorted(quarantined_targets))}; classify the exact "
                "installed Swift root before executing it"
            )
        device_targets = {
            scenario.execution_target
            for scenario in scenarios
            if TARGETS.get(scenario.execution_target, {}).get("native")
        }
        if device_targets and not lan:
            raise SittingError(
                f"pack {pack!r} requires a device sitting for "
                f"{', '.join(sorted(device_targets))}; start it with LAN mode enabled"
            )
        sitting_id = _new_sitting_id()
        # Boot golden-local; each scenario's recipes restart onto their own deck.
        boot_deck = deck_override or "golden-local"
        run = self.runs.create_run(deck=boot_deck, lan=lan)
        try:
            self._write_protocol_snapshot(run.id, pack, scenarios, ledger)
        except Exception as exc:
            self.runs.teardown(run.id)
            raise SittingError(f"could not snapshot pack {pack!r}: {exc}") from exc
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
        if sitting["status"] in {"done", "aborted"}:
            raise SittingError("a closed sitting is immutable")
        scenario = self._scenario(sitting, scenario_id)
        run_id = sitting["run_id"]
        existing_stage = self.db.get_scenario_stage(
            run_id, sitting["pack"], scenario_id
        )
        started = _utcnow()
        self.db.upsert_scenario_stage(
            {
                "run_id": run_id,
                "pack": sitting["pack"],
                "scenario_id": scenario_id,
                "status": "running",
                "result_json": None,
                "error": None,
                "manual_confirmed": int(
                    bool(existing_stage and existing_stage.get("manual_confirmed"))
                ),
                "created_at": existing_stage.get("created_at") if existing_stage else started,
                "updated_at": started,
            }
        )
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
                packet = {"ok": False, "scenario_id": scenario_id, "staging": staging}
                self._record_stage(sitting, scenario_id, packet, error=str(exc))
                return packet
            except Exception as exc:  # boot/apply failure — show the log tail, never hang
                logs = self.runs.logs(run_id, 40)
                staging.append({"recipe": recipe, "ok": False, "error": str(exc), "log_tail": logs})
                packet = {"ok": False, "scenario_id": scenario_id, "staging": staging}
                self._record_stage(sitting, scenario_id, packet, error=str(exc))
                return packet
        packet = {"ok": True, "scenario_id": scenario_id, "staging": staging}
        self._record_stage(sitting, scenario_id, packet)
        return packet

    def confirm_manual_setup(self, sitting_id: str, scenario_id: str) -> dict:
        """Persist the human's manual-preflight confirmation for this scenario."""
        sitting = self._require(sitting_id)
        if sitting["status"] in {"done", "aborted"}:
            raise SittingError("a closed sitting is immutable")
        scenario = self._scenario(sitting, scenario_id)
        if not scenario.manual_setup:
            raise SittingError(f"scenario {scenario_id!r} has no manual setup")
        existing = self.db.get_scenario_stage(
            sitting["run_id"], sitting["pack"], scenario_id
        )
        now = _utcnow()
        self.db.upsert_scenario_stage(
            {
                "run_id": sitting["run_id"],
                "pack": sitting["pack"],
                "scenario_id": scenario_id,
                "status": existing.get("status") if existing else "done",
                "result_json": existing.get("result_json") if existing else "[]",
                "error": existing.get("error") if existing else None,
                "manual_confirmed": 1,
                "created_at": existing.get("created_at") if existing else now,
                "updated_at": now,
            }
        )
        return self.get(sitting_id)

    def run_after_actions(self, sitting_id: str, scenario_id: str, step_index: int) -> list[dict]:
        with self._transition_lock:
            return self._run_after_actions_locked(
                sitting_id, scenario_id, step_index
            )

    def _run_after_actions_locked(
        self, sitting_id: str, scenario_id: str, step_index: int
    ) -> list[dict]:
        """Perform and durably record a step transition exactly once.

        A failed transition remains retryable and blocks progress. A completed
        transition is returned from the database without repeating side effects.
        """
        sitting = self._require(sitting_id)
        if sitting["status"] in {"done", "aborted"}:
            raise SittingError("a closed sitting is immutable")
        scenario = self._scenario(sitting, scenario_id)
        if step_index < 0 or step_index >= len(scenario.steps):
            raise SittingError(
                f"invalid step {step_index} for scenario {scenario_id!r}"
            )
        step = scenario.steps[step_index]
        if not step.after:
            return []
        existing = self.db.get_step_transition(
            sitting["run_id"], sitting["pack"], scenario_id, step_index
        )
        if existing and existing["status"] == "done":
            return json.loads(existing.get("result_json") or "[]")
        now = _utcnow()
        self.db.upsert_step_transition(
            {
                "run_id": sitting["run_id"],
                "pack": sitting["pack"],
                "scenario_id": scenario_id,
                "step_index": step_index,
                "status": "running",
                "result_json": existing.get("result_json") if existing else None,
                "error": None,
                "created_at": existing.get("created_at") if existing else now,
                "updated_at": now,
            }
        )
        performed: list[dict] = []
        for action in step.after:
            (kind, arg), = action.items() if isinstance(action, dict) else (("", None),)
            try:
                if kind == "apply_recipe":
                    name = arg["name"] if isinstance(arg, dict) else str(arg)
                    res = self.runs.apply_recipe(sitting["run_id"], name)
                    performed.append({"action": "apply_recipe", "name": name, "ok": res.probe.get("ok", False), "result": res.to_dict()})
                elif kind == "kill_node":
                    name = arg["name"] if isinstance(arg, dict) else str(arg)
                    performed.append({"action": "kill_node", "name": name, "killed": self.runs.kill_node(sitting["run_id"], name), "ok": True})
                elif kind == "spawn_node":
                    name = arg["name"] if isinstance(arg, dict) else str(arg)
                    node = self.runs.spawn_node(sitting["run_id"], name)
                    performed.append({"action": "spawn_node", "name": name, "node": node, "ok": True})
                elif kind == "restart":
                    deck = (arg or {}).get("deck") if isinstance(arg, dict) else None
                    run = self.runs.restart(sitting["run_id"], deck=deck)
                    performed.append({"action": "restart", "deck": deck, "ok": run.status == "up"})
                elif kind == "wait":
                    seconds = float(arg)
                    time.sleep(seconds)
                    performed.append({"action": "wait", "seconds": seconds, "ok": True})
                else:
                    performed.append({"action": kind, "ok": False, "error": "unknown action"})
            except Exception as exc:
                performed.append({"action": kind, "ok": False, "error": str(exc)})
                break
        failed = next(
            (
                result
                for result in performed
                if result.get("error") or result.get("ok") is False
            ),
            None,
        )
        self.db.upsert_step_transition(
            {
                "run_id": sitting["run_id"],
                "pack": sitting["pack"],
                "scenario_id": scenario_id,
                "step_index": step_index,
                "status": "failed" if failed else "done",
                "result_json": json.dumps(performed),
                "error": failed.get("error") if failed else None,
                "created_at": existing.get("created_at") if existing else now,
                "updated_at": _utcnow(),
            }
        )
        return performed

    # --- native device attestations + verdicts ---------------------------

    def register_device_session(
        self,
        sitting_id: str,
        *,
        execution_target: str,
        form_factor: str,
        device_name: str,
        os_version: str,
        bundle_id: str,
        build_number: str,
        install_source: str | None = None,
        pairing_verified: bool = False,
    ) -> dict:
        sitting = self._require(sitting_id)
        if sitting["status"] in {"done", "aborted"}:
            raise SittingError("a closed sitting is immutable")
        spec = TARGETS.get(execution_target)
        if not spec or not spec.get("native"):
            raise SittingError("device sessions are only valid for Swift native targets")
        if form_factor not in spec["form_factors"]:
            raise SittingError(
                f"form factor {form_factor!r} is invalid for {execution_target!r}"
            )
        allowed = {
            (scenario.execution_target, form)
            for scenario in self._scenarios(sitting)
            for form in scenario.form_factors
        }
        if (execution_target, form_factor) not in allowed:
            raise SittingError(
                f"{execution_target}:{form_factor} is not part of this sitting"
            )
        run = self.runs.get(sitting["run_id"])
        if run is None or not run.lan:
            raise SittingError("native attestation requires a LAN-bound device sitting")
        facts = {
            "device_name": device_name,
            "os_version": os_version,
            "bundle_id": bundle_id,
            "build_number": build_number,
        }
        missing = [name for name, value in facts.items() if not str(value or "").strip()]
        if missing:
            raise SittingError(
                "native attestation is missing: " + ", ".join(sorted(missing))
            )
        row = {
            "id": _new_device_session_id(),
            "sitting_id": sitting_id,
            "run_id": sitting["run_id"],
            "execution_target": execution_target,
            "form_factor": form_factor,
            "device_name": device_name.strip(),
            "os_version": os_version.strip(),
            "bundle_id": bundle_id.strip(),
            "build_number": build_number.strip(),
            "install_source": (install_source or "").strip() or None,
            # This is an explicit human attestation, not cryptographic device
            # identity. The debrief names that limitation.
            "pairing_verified": int(bool(pairing_verified)),
            "created_at": _utcnow(),
        }
        self.db.upsert_device_session(row)
        return self.get(sitting_id)

    def cast_verdict(
        self,
        sitting_id: str,
        *,
        scenario_id: str,
        step_index: int,
        slot_id: str,
        verdict: str,
        note: str | None = None,
        shot_path: str | None = None,
        started_at: str | None = None,
        device_session_id: str | None = None,
    ) -> dict:
        if verdict not in ("pass", "fail", "partial", "observe", "skip"):
            raise SittingError(f"invalid verdict: {verdict!r}")
        if verdict == "observe" and not (note or "").strip():
            raise SittingError("an observation needs a note describing what you saw")
        sitting = self._require(sitting_id)
        if sitting["status"] in {"done", "aborted"}:
            raise SittingError("a closed sitting is immutable")
        scenario = self._scenario(sitting, scenario_id)
        if scenario.execution_target == "legacy_unqualified":
            raise SittingError(
                "legacy unqualified sittings are review-only and cannot accept new verdicts"
            )
        if step_index < 0 or step_index >= len(scenario.steps):
            raise SittingError(
                f"invalid step {step_index} for scenario {scenario_id!r}"
            )
        step = scenario.steps[step_index]
        stage = self.db.get_scenario_stage(
            sitting["run_id"], sitting["pack"], scenario_id
        )
        prior_verdicts = [
            item
            for item in self.db.list_verdicts(sitting["run_id"])
            if item["scenario_id"] == scenario_id
        ]
        # Legacy sittings created before durable staging are grandfathered once
        # they already contain a verdict; new scenarios must prove their world.
        if scenario.recipes and not prior_verdicts and (
            stage is None or stage["status"] != "done"
        ):
            raise SittingError(
                f"scenario {scenario_id!r} has not completed recipe staging"
            )
        if scenario.manual_setup and not prior_verdicts and not (
            stage and stage.get("manual_confirmed")
        ):
            raise SittingError(
                f"scenario {scenario_id!r} manual setup has not been confirmed"
            )
        slots = {slot.id: slot for slot in step.execution_slots(scenario)}
        if slot_id not in slots:
            raise SittingError(
                f"execution slot {slot_id!r} is not applicable to "
                f"{scenario_id!r} step {step_index}"
            )
        slot = slots[slot_id]
        if slot.quarantined:
            raise SittingError(
                f"{slot.label} is quarantined and cannot produce acceptance evidence"
            )
        device_session = None
        if slot.native:
            if not device_session_id:
                raise SittingError("native verdicts require a matching device attestation")
            device_session = self.db.get_device_session(device_session_id)
            if not device_session or device_session.get("sitting_id") != sitting_id:
                raise SittingError("device attestation does not belong to this sitting")
            if (
                device_session.get("execution_target") != slot.target
                or device_session.get("form_factor") != slot.form_factor
            ):
                raise SittingError("device attestation does not match the execution slot")
            if not device_session.get("pairing_verified"):
                raise SittingError("native device pairing has not been attested")
        if shot_path:
            shot = Path(shot_path).expanduser().resolve()
            root = paths.run_shots_dir(sitting["run_id"]).resolve()
            if not shot.is_relative_to(root) or not shot.exists():
                raise SittingError("shot_path must name an uploaded artifact for this run")
        self.db.cast_verdict({
            "run_id": sitting["run_id"],
            "pack": sitting["pack"],
            "scenario_id": scenario_id,
            "step_index": step_index,
            "surface": slot.form_factor,
            "execution_target": slot.target,
            "form_factor": slot.form_factor,
            "slot_id": slot.id,
            "device_session_id": device_session.get("id") if device_session else None,
            "verdict": verdict,
            "note": note,
            "shot_path": shot_path,
            "started_at": started_at,
            "created_at": _utcnow(),
        })
        verdict_index = {
            (item["scenario_id"], item["step_index"], item["slot_id"]): item
            for item in self.db.list_verdicts(sitting["run_id"])
        }
        if step.after and all(
            (scenario_id, step_index, slot.id) in verdict_index
            for slot in step.execution_slots(scenario)
        ):
            self.run_after_actions(sitting_id, scenario_id, step_index)
        self.db.upsert_sitting({**sitting, "updated_at": _utcnow(), "status": "walking"})
        return self.get(sitting_id)

    def save_shot(self, sitting_id: str, scenario_id: str, step_index: int, slot_id: str, data: bytes, suffix: str = ".png") -> str:
        sitting = self._require(sitting_id)
        if sitting["status"] in {"done", "aborted"}:
            raise SittingError("a closed sitting is immutable")
        scenario = self._scenario(sitting, scenario_id)
        if step_index < 0 or step_index >= len(scenario.steps):
            raise SittingError(
                f"invalid step {step_index} for scenario {scenario_id!r}"
            )
        slot_ids = {
            slot.id for slot in scenario.steps[step_index].execution_slots(scenario)
        }
        if slot_id not in slot_ids:
            raise SittingError(
                f"execution slot {slot_id!r} is not applicable to "
                f"{scenario_id!r} step {step_index}"
            )
        suffix = suffix.lower()
        if suffix not in {".png", ".jpg", ".jpeg", ".webp", ".heic"}:
            raise SittingError(f"unsupported screenshot type: {suffix}")
        if len(data) > 20 * 1024 * 1024:
            raise SittingError("screenshot exceeds the 20 MiB limit")
        shots = paths.run_shots_dir(sitting["run_id"])
        shots.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256(data).hexdigest()[:12]
        safe_slot = re.sub(r"[^a-zA-Z0-9_.-]+", "-", slot_id)
        name = f"{scenario_id}-step{step_index}-{safe_slot}-{digest}{suffix}"
        (shots / name).write_bytes(data)
        return str((shots / name))

    def transcribe(self, sitting_id: str, wav: bytes) -> dict:
        """Speak-to-fill a note: proxy browser audio to the run's OWN transcribe
        route (its local Whisper, no egress). Honest when the product is down or
        transcription is unavailable on this run — never a fake."""
        sitting = self._require(sitting_id)
        run = self.runs.get(sitting["run_id"])
        if run is None or run.status != "up":
            return {"ok": False, "error": "The product under test is not up on this run."}
        client = self.runs.product_client(sitting["run_id"])
        try:
            resp = client.post_bytes("/api/dictation/transcribe", wav, content_type="audio/wav")
        except Exception as exc:
            return {"ok": False, "error": f"Could not reach the product: {exc}"}
        if resp.status_code == 503:
            return {"ok": False, "error": "Transcription is unavailable on this run (no model)."}
        if resp.status_code != 200:
            detail = ""
            try:
                detail = resp.json().get("error", "")
            except Exception:
                pass
            return {"ok": False, "error": detail or f"Transcribe failed (HTTP {resp.status_code})."}
        return {"ok": True, "text": resp.json().get("text", "")}

    def finish(self, sitting_id: str) -> dict:
        sitting = self._require(sitting_id)
        snapshot = self._read_protocol_snapshot(sitting["run_id"])
        if not snapshot or int(snapshot.get("schema") or 1) < PROTOCOL_SCHEMA_VERSION:
            raise SittingError(
                "legacy unqualified sittings are preserved for review but cannot be accepted"
            )
        scenarios = self._scenarios(sitting)
        verdict_index = {
            (v["scenario_id"], v["step_index"], v["slot_id"]): v
            for v in self.db.list_verdicts(sitting["run_id"])
        }
        transitions = self.db.list_step_transitions(sitting["run_id"])
        progress = self._progress(scenarios, verdict_index, transitions)
        if not progress["complete"]:
            raise SittingError(
                "cannot finish an incomplete sitting "
                f"({progress['cast']}/{progress['expected']} verdicts cast)"
            )
        self.db.upsert_sitting({**sitting, "status": "done", "finished_at": _utcnow(), "updated_at": _utcnow()})
        # A completed sitting is evidence, not a live environment. Tear down the
        # product, mesh workers, and tracked tmux sessions so UAT leaves no residue.
        self.runs.teardown(sitting["run_id"])
        return self.get(sitting_id)

    def supersede(self, sitting_id: str) -> dict:
        """Close an in-progress snapshot and restart its pack from current sources.

        Verdicts and screenshots on the old sitting remain immutable evidence.
        The replacement receives a fresh protocol snapshot, so feedback-driven
        scenario corrections never rewrite the protocol that produced a finding.
        """
        sitting = self._require(sitting_id)
        if sitting["status"] in {"done", "aborted"}:
            raise SittingError("a closed sitting cannot be superseded")
        run = self.runs.get(sitting["run_id"])
        replacement = self.create(
            sitting["pack"],
            deck_override=sitting.get("deck"),
            lan=bool(run and run.lan),
        )
        now = _utcnow()
        self.db.upsert_sitting(
            {
                **sitting,
                "status": "aborted",
                "updated_at": now,
                "finished_at": now,
            }
        )
        self.runs.teardown(sitting["run_id"])
        return {**replacement, "superseded_sitting_id": sitting_id}

    # --- reads ------------------------------------------------------------

    def get(self, sitting_id: str) -> dict:
        sitting = self._require(sitting_id)
        scenarios = self._scenarios(sitting)
        verdicts = self.db.list_verdicts(sitting["run_id"])
        verdict_index = {
            (v["scenario_id"], v["step_index"], v["slot_id"]): v for v in verdicts
        }
        transitions = self.db.list_step_transitions(sitting["run_id"])
        stages = self.db.list_scenario_stages(sitting["run_id"])
        run = self.runs.get(sitting["run_id"])
        resume = self._resume_point(scenarios, verdict_index)
        ledger = self._ledger_for(sitting)
        protocol_cov = pack_coverage(scenarios, ledger)
        cov = execution_coverage(scenarios, ledger, verdicts)
        snapshot = self._read_protocol_snapshot(sitting["run_id"])
        return {
            "id": sitting["id"],
            "pack": sitting["pack"],
            "status": sitting["status"],
            "created_at": sitting["created_at"],
            "finished_at": sitting.get("finished_at"),
            "run": run.to_public() if run else None,
            "scenarios": [s.to_dict() for s in scenarios],
            "verdicts": verdicts,
            "device_sessions": self.db.list_device_sessions(sitting_id),
            "transitions": transitions,
            "stages": stages,
            "blocked_transition": self._blocked_transition(
                scenarios, verdict_index, transitions
            ),
            "resume": resume,
            "coverage": cov,
            "protocol_coverage": protocol_cov,
            "protocol": {
                "schema": snapshot.get("schema") if snapshot else None,
                "hash": snapshot.get("protocol_hash") if snapshot else None,
                "git_commit": snapshot.get("git_commit") if snapshot else None,
                "snapshot": str(self._snapshot_path(sitting["run_id"])) if snapshot else None,
            },
            "legacy_invalid": bool(
                not snapshot
                or int(snapshot.get("schema") or 1) < PROTOCOL_SCHEMA_VERSION
            ),
            "progress": self._progress(scenarios, verdict_index, transitions),
        }

    def list(self) -> list[dict]:
        out = []
        for s in self.db.list_sittings():
            verdicts = self.db.list_verdicts(s["run_id"]) if s.get("run_id") else []
            snapshot = self._read_protocol_snapshot(s["run_id"]) if s.get("run_id") else None
            out.append({
                "id": s["id"],
                "pack": s["pack"],
                "status": s["status"],
                "created_at": s["created_at"],
                "finished_at": s.get("finished_at"),
                "verdicts_cast": len(verdicts),
                "legacy_invalid": bool(
                    not snapshot
                    or int(snapshot.get("schema") or 1) < PROTOCOL_SCHEMA_VERSION
                ),
            })
        return out

    # --- internals --------------------------------------------------------

    def _require(self, sitting_id: str) -> dict:
        sitting = self.db.get_sitting(sitting_id)
        if sitting is None:
            raise SittingError(f"no such sitting: {sitting_id}")
        return sitting

    def _record_stage(
        self, sitting: dict, scenario_id: str, packet: dict, error: str | None = None
    ) -> None:
        existing = self.db.get_scenario_stage(
            sitting["run_id"], sitting["pack"], scenario_id
        )
        now = _utcnow()
        self.db.upsert_scenario_stage(
            {
                "run_id": sitting["run_id"],
                "pack": sitting["pack"],
                "scenario_id": scenario_id,
                "status": "failed" if error else "done",
                "result_json": json.dumps(packet),
                "error": error,
                "manual_confirmed": int(
                    bool(existing and existing.get("manual_confirmed"))
                ),
                "created_at": existing.get("created_at") if existing else now,
                "updated_at": now,
            }
        )

    def _scenario(self, sitting: dict, scenario_id: str) -> Scenario:
        for s in self._scenarios(sitting):
            if s.id == scenario_id:
                return s
        raise SittingError(
            f"no scenario {scenario_id!r} in pack {sitting['pack']!r}"
        )

    def _snapshot_path(self, run_id: str) -> Path:
        return paths.run_dir(run_id) / "protocol-snapshot.json"

    def _write_protocol_snapshot(
        self,
        run_id: str,
        pack: str,
        scenarios: list[Scenario],
        ledger: FeatureLedger,
    ) -> None:
        recipe_names = {
            recipe for scenario in scenarios for recipe in scenario.recipes
        }
        for scenario in scenarios:
            for step in scenario.steps:
                for action in step.after:
                    if isinstance(action, dict) and "apply_recipe" in action:
                        arg = action["apply_recipe"]
                        recipe_names.add(
                            str(arg.get("name")) if isinstance(arg, dict) else str(arg)
                        )
        expanded_recipes: set[str] = set()
        for name in recipe_names:
            try:
                expanded_recipes.update(
                    self.runs.recipes.registry.resolve_order(name)
                )
            except Exception:
                expanded_recipes.add(name)
        assets: dict[str, str] = {}
        campaign_path = campaigns_dir() / f"{pack}.yaml"
        if campaign_path.exists():
            assets[_asset_label(campaign_path)] = _sha256(campaign_path)
        for scenario in scenarios:
            source = Path(scenario.source)
            if source.exists():
                assets[_asset_label(source)] = _sha256(source)
        for name in sorted(expanded_recipes):
            recipe_path = self.runs.recipes.registry.directory / f"{name}.yaml"
            if recipe_path.exists():
                assets[_asset_label(recipe_path)] = _sha256(recipe_path)
            try:
                recipe = self.runs.recipes.registry.load(name)
                deck = recipe.deck
            except Exception:
                continue
            for seed in recipe.seeds:
                seed_path = self.runs.recipes.seed_registry.directory / f"{seed}.yaml"
                if seed_path.exists():
                    assets[_asset_label(seed_path)] = _sha256(seed_path)
            deck_path = self.runs.decks.directory / f"{deck}.yaml"
            if deck_path.exists():
                assets[_asset_label(deck_path)] = _sha256(deck_path)
        normalized = [scenario.to_dict() for scenario in scenarios]
        protocol_bytes = json.dumps(
            {"scenarios": normalized, "ledger": ledger.raw},
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        packet = {
            "schema": PROTOCOL_SCHEMA_VERSION,
            "created_at": _utcnow(),
            "pack": pack,
            "git_commit": _git_commit(),
            "protocol_hash": hashlib.sha256(protocol_bytes).hexdigest(),
            "scenarios": normalized,
            "ledger": ledger.raw,
            "asset_hashes": assets,
        }
        path = self._snapshot_path(run_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(packet, indent=2, sort_keys=True))

    def _read_protocol_snapshot(self, run_id: str) -> dict | None:
        path = self._snapshot_path(run_id)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text())
        except (OSError, ValueError):
            return None

    def _scenarios(self, sitting: dict) -> list[Scenario]:
        snapshot = self._read_protocol_snapshot(sitting["run_id"])
        if snapshot:
            return [scenario_from_dict(doc) for doc in snapshot.get("scenarios", [])]
        return load_pack(sitting["pack"])

    def _ledger_for(self, sitting: dict) -> FeatureLedger:
        snapshot = self._read_protocol_snapshot(sitting["run_id"])
        if snapshot and snapshot.get("ledger"):
            return FeatureLedger.from_dict(snapshot["ledger"])
        return self.ledger()

    def _resume_point(self, scenarios: list[Scenario], verdict_index: dict) -> dict | None:
        for scenario in scenarios:
            for step in scenario.steps:
                for slot in step.execution_slots(scenario):
                    if (scenario.id, step.index, slot.id) not in verdict_index:
                        return {
                            "scenario_id": scenario.id,
                            "step_index": step.index,
                            "slot_id": slot.id,
                        }
        return None  # sitting complete

    def _progress(
        self, scenarios: list[Scenario], verdict_index: dict, transitions: list[dict] | None = None
    ) -> dict:
        expected = sum(sc.expected_verdict_count() for sc in scenarios)
        cast = 0
        for scenario in scenarios:
            for step in scenario.steps:
                for slot in step.execution_slots(scenario):
                    if (scenario.id, step.index, slot.id) in verdict_index:
                        cast += 1
        transition_index = {
            (row["scenario_id"], row["step_index"]): row
            for row in (transitions or [])
        }
        required = 0
        done = 0
        for scenario in scenarios:
            for step in scenario.steps:
                if not step.after:
                    continue
                applicable = step.execution_slots(scenario)
                answered = all(
                    (scenario.id, step.index, slot.id) in verdict_index
                    for slot in applicable
                )
                if not answered:
                    continue
                required += 1
                row = transition_index.get((scenario.id, step.index))
                if row and row["status"] == "done":
                    done += 1
        return {
            "cast": cast,
            "expected": expected,
            "transitions_done": done,
            "transitions_required": required,
            "complete": cast >= expected and done >= required,
        }

    def _blocked_transition(
        self, scenarios: list[Scenario], verdict_index: dict, transitions: list[dict]
    ) -> dict | None:
        transition_index = {
            (row["scenario_id"], row["step_index"]): row for row in transitions
        }
        for scenario in scenarios:
            for step in scenario.steps:
                if not step.after:
                    continue
                if not all(
                    (scenario.id, step.index, slot.id) in verdict_index
                    for slot in step.execution_slots(scenario)
                ):
                    continue
                row = transition_index.get((scenario.id, step.index))
                if row is None or row["status"] != "done":
                    return {
                        "scenario_id": scenario.id,
                        "step_index": step.index,
                        "status": row["status"] if row else "pending",
                        "error": row.get("error") if row else None,
                        "actions": step.after,
                    }
        return None
