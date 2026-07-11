"""The debrief packet — the joint-review record a sitting produces.

Generated into `uat/_runs/<run_id>/debrief/`:

- `debrief.md` — the human read: the sitting header (date, pack, deck(s),
  product version/commit, surfaces sat), the score **per surface and overall**
  (a surface never sat is named, not averaged away), coverage % against the
  ledger, and every non-pass verdict with its step, surface, note, screenshot
  link, and a slice of the product's own log around that moment. The pass list
  is collapsed.
- `debrief.json` — the same, machine-shaped, on a stable schema (the agent's
  head start for triage).

Each failed/partial/observed step becomes a **finding** with a stable id derived
from ``(run, scenario, step)`` and a triage state that survives regeneration
(the disposition is the human's). A cross-surface disagreement — passed on web,
failed on iPhone — is one finding wearing both verdicts; the split is the signal.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import re

from . import paths
from .contract.coverage import execution_coverage, pack_coverage
from .contract.ledger import FeatureLedger
from .contract.scenarios import load_pack, scenario_from_dict
from .db import Database
from .runs import RunManager

# Fail/partial are acceptance misses. Observe is an explicit, low-friction way
# to capture a bug-hunt note even when the acceptance bar passed. Skip remains a
# deliberate non-answer and does not become a finding.
FINDING_VERDICTS = ("fail", "partial", "observe")
_TS = re.compile(r"(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2})")


def _utcnow() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


class DebriefGenerator:
    def __init__(self, run_manager: RunManager, db: Database, ledger: FeatureLedger | None = None):
        self.runs = run_manager
        self.db = db
        self._ledger = ledger

    def ledger(self) -> FeatureLedger:
        if self._ledger is None:
            self._ledger = FeatureLedger.load()
        return self._ledger

    def generate(self, sitting_id: str) -> dict:
        sitting = self.db.get_sitting(sitting_id)
        if sitting is None:
            raise KeyError(sitting_id)
        run_id = sitting["run_id"]
        run = self.db.get_run(run_id) or {}
        pack = sitting["pack"]
        snapshot = _read_protocol_snapshot(run_id)
        scenarios = (
            [scenario_from_dict(doc) for doc in snapshot.get("scenarios", [])]
            if snapshot
            else load_pack(pack)
        )
        ledger = (
            FeatureLedger.from_dict(snapshot["ledger"])
            if snapshot and snapshot.get("ledger")
            else self.ledger()
        )
        scen_by_id = {s.id: s for s in scenarios}
        verdicts = self.db.list_verdicts(run_id)
        protocol_valid = bool(snapshot and int(snapshot.get("schema") or 1) >= 2)
        expected = sum(scenario.expected_verdict_count() for scenario in scenarios)
        complete = sitting.get("status") == "done" and len(verdicts) >= expected
        protocol_coverage = pack_coverage(scenarios, ledger)
        coverage = execution_coverage(scenarios, ledger, verdicts)

        # Derive + upsert findings (triage preserved by id).
        derived = self._derive_findings(run_id, verdicts, scen_by_id)
        for f in derived:
            self.db.upsert_finding(f)
        self.db.delete_findings_except(run_id, {f["id"] for f in derived})
        stored = {f["id"]: f for f in self.db.list_findings(run_id)}

        logs = self.runs.logs(run_id, 4000)
        product_log = []
        for source in ("application", "stdout", "stderr"):
            product_log.extend(
                f"[{source}] {line}"
                for line in logs.get(source, "").splitlines()
            )

        findings_out = []
        for f in derived:
            merged = {**f, **stored.get(f["id"], {})}
            merged["log_slice"] = _log_slice(product_log, f.get("created_at"))
            merged["cross_slot"] = self._execution_split(f, verdicts)
            findings_out.append(merged)

        scores = self._scores(verdicts)
        header = {
            "generated_at": _utcnow(),
            "sitting_id": sitting_id,
            "pack": pack,
            "deck": sitting.get("deck"),
            "run_id": run_id,
            "product_version": (
                snapshot.get("git_commit")
                if snapshot
                else run.get("config_json") and _version_from_config(run)
            ),
            "git_commit": snapshot.get("git_commit") if snapshot else None,
            "protocol_hash": snapshot.get("protocol_hash") if snapshot else None,
            "protocol_snapshot": (
                str(paths.run_dir(run_id) / "protocol-snapshot.json")
                if snapshot
                else None
            ),
            "execution_slots_sat": sorted(scores.keys()),
            "protocol_schema": snapshot.get("schema") if snapshot else 1,
            "protocol_valid": protocol_valid,
        }
        totals = self._totals(verdicts)
        packet = {
            "header": header,
            "scores": scores,
            "coverage": coverage,
            "protocol_coverage": protocol_coverage,
            "findings": findings_out,
            "verdicts": verdicts,
            "verdict_totals": totals,
            "acceptance_status": _acceptance_status(
                totals, complete=complete, protocol_valid=protocol_valid
            ),
            "complete": complete,
            "device_sessions": self.db.list_device_sessions(sitting_id),
            "native_client_logs": "not captured by conductor; attach native diagnostics to findings",
            "staging": self.db.list_scenario_stages(run_id),
            "transitions": self.db.list_step_transitions(run_id),
        }

        out_dir = paths.run_debrief_dir(run_id)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "debrief.json").write_text(json.dumps(packet, indent=2))
        (out_dir / "debrief.md").write_text(self._render_md(packet, scenarios))
        return {
            "md": str(out_dir / "debrief.md"),
            "json": str(out_dir / "debrief.json"),
            "packet": packet,
        }

    def read(self, sitting_id: str) -> dict:
        sitting = self.db.get_sitting(sitting_id)
        if sitting is None:
            raise KeyError(sitting_id)
        path = paths.run_debrief_dir(sitting["run_id"]) / "debrief.json"
        if not path.exists():
            return self.generate(sitting_id)["packet"]
        return json.loads(path.read_text())

    # --- findings ---------------------------------------------------------

    def _derive_findings(self, run_id: str, verdicts: list[dict], scen_by_id) -> list[dict]:
        run_short = run_id.replace("run-", "").split("-")[-1]
        grouped: dict[tuple[str, int], list[dict]] = {}
        for verdict in verdicts:
            grouped.setdefault(
                (verdict["scenario_id"], verdict["step_index"]), []
            ).append(verdict)
        out = []
        severity = {"fail": 3, "partial": 2, "observe": 1}
        for (scenario_id, step_index), step_verdicts in sorted(grouped.items()):
            actionable = [
                verdict
                for verdict in step_verdicts
                if verdict["verdict"] in FINDING_VERDICTS
            ]
            if not actionable:
                continue
            scenario = scen_by_id.get(scenario_id)
            scenario_title = scenario.title if scenario else scenario_id
            primary = max(
                actionable, key=lambda verdict: severity[verdict["verdict"]]
            )
            slots = sorted(verdict["slot_id"] for verdict in actionable)
            slot_verdicts = {
                verdict["slot_id"]: verdict["verdict"] for verdict in step_verdicts
            }
            notes = [
                f"[{verdict['slot_id']}] {verdict['note']}"
                for verdict in actionable
                if verdict.get("note")
            ]
            identity = f"{run_id}\0{scenario_id}\0{step_index}".encode()
            stable = hashlib.sha256(identity).hexdigest()[:10]
            out.append({
                "id": f"UAT-{run_short}-{stable}",
                "run_id": run_id,
                "pack": primary["pack"],
                "scenario_id": scenario_id,
                "step_index": step_index,
                "surface": ",".join(slots),
                "execution_target": primary.get("execution_target"),
                "form_factor": primary.get("form_factor"),
                "slot_id": primary.get("slot_id"),
                "verdict": primary["verdict"],
                "note": "\n".join(notes) or None,
                "title": (
                    f"{scenario_title} — step {step_index + 1}, "
                    f"{', '.join(slots)}: {primary['verdict']}"
                ),
                "created_at": min(
                    (verdict.get("created_at") or _utcnow())
                    for verdict in actionable
                ),
                "shot_path": next(
                    (verdict.get("shot_path") for verdict in actionable if verdict.get("shot_path")),
                    None,
                ),
                "slot_verdicts": slot_verdicts,
            })
        return out

    def _execution_split(self, finding: dict, verdicts: list[dict]) -> dict:
        """Different results on explicit slots; parity is never inferred."""
        others = {
            v["slot_id"]: v["verdict"]
            for v in verdicts
            if v["scenario_id"] == finding["scenario_id"] and v["step_index"] == finding["step_index"]
        }
        passed = [s for s, vd in others.items() if vd == "pass"]
        return {"all_slots": others, "passed_on": passed, "is_split": bool(passed)}

    # --- scoring ----------------------------------------------------------

    def _scores(self, verdicts: list[dict]) -> dict:
        scores: dict[str, dict] = {}
        for v in verdicts:
            s = scores.setdefault(
                v["slot_id"],
                {"pass": 0, "fail": 0, "partial": 0, "observe": 0, "skip": 0},
            )
            s[v["verdict"]] = s.get(v["verdict"], 0) + 1
        return scores

    def _totals(self, verdicts: list[dict]) -> dict:
        t = {"pass": 0, "fail": 0, "partial": 0, "observe": 0, "skip": 0}
        for v in verdicts:
            t[v["verdict"]] = t.get(v["verdict"], 0) + 1
        return t

    # --- markdown ---------------------------------------------------------

    def _render_md(self, packet: dict, scenarios) -> str:
        h = packet["header"]
        lines = [
            f"# UAT debrief — {h['pack']}",
            "",
            f"- **Sitting:** {h['sitting_id']}  ·  **Run:** {h['run_id']}",
            f"- **Generated:** {h['generated_at']}",
            f"- **Deck (boot):** {h.get('deck')}",
            f"- **Product commit:** {h.get('git_commit') or '(legacy sitting — not captured)'}",
            f"- **Protocol hash:** {h.get('protocol_hash') or '(legacy sitting — not captured)'}",
            f"- **Execution slots sat:** {', '.join(h['execution_slots_sat']) or '(none)'}",
            f"- **Protocol schema:** {h.get('protocol_schema')} "
            f"({'valid' if h.get('protocol_valid') else 'INVALID legacy identity'})",
            f"- **Acceptance:** {packet['acceptance_status']}",
            "",
            "## Score per execution slot",
            "",
        ]
        if not packet["scores"]:
            lines.append("- *(no qualified execution slots sat)*")
        for slot_id, sc in sorted(packet["scores"].items()):
            lines.append(
                f"- **{slot_id}** — {sc.get('pass',0)} pass · {sc.get('fail',0)} fail · "
                f"{sc.get('partial',0)} partial · {sc.get('observe',0)} observe · "
                f"{sc.get('skip',0)} skip"
            )
        cov = packet["coverage"]
        lines += [
            "",
            "## Executed coverage against the ledger",
            "",
            f"- overall: {cov['overall']['covered']}/{cov['overall']['total']} ({cov['overall']['pct']}%)",
        ]
        for slot_id, slot_cov in sorted(cov.get("slots", {}).items()):
            lines.append(
                f"- {slot_id}: {slot_cov['covered']}/{slot_cov['total']} "
                f"({slot_cov['pct']}%) · {cov['unknown_cells'].get(slot_id, 0)} unclassified"
            )
        lines += [
            "",
            "Authored coverage is kept separately in `protocol_coverage`; only exact, "
            "substantively walked execution slots receive credit.",
            "",
            f"## Device attestations ({len(packet.get('device_sessions', []))})",
            "",
        ]
        if not packet.get("device_sessions"):
            lines.append("- none")
        for device in packet.get("device_sessions", []):
            lines.append(
                f"- {device['execution_target']}:{device['form_factor']} · "
                f"{device['device_name']} · {device['os_version']} · "
                f"{device['bundle_id']} build {device['build_number']} · "
                f"pairing attested={bool(device['pairing_verified'])}"
            )
        lines += [
            "",
            f"Native client logs: {packet.get('native_client_logs')}",
            "",
            f"## Findings ({len(packet['findings'])})",
            "",
        ]
        if not packet["findings"]:
            if packet["verdict_totals"].get("skip"):
                lines.append(
                    "No actionable findings, but skipped checks make this sitting inconclusive."
                )
            else:
                lines.append("No acceptance misses or observations were recorded.")
        for f in packet["findings"]:
            lines += [
                f"### {f['id']} — {f['title']}",
                "",
                f"- **Verdict:** {f['verdict']}  ·  **Execution slot:** {f['surface']}  ·  **Triage:** {f.get('triage_state','untriaged')}",
                f"- **Note:** {f.get('note') or '(none)'}",
            ]
            if f.get("shot_path"):
                lines.append(f"- **Screenshot:** {f['shot_path']}")
            if f.get("cross_slot", {}).get("is_split"):
                lines.append(
                    f"- **Execution-slot split:** passed on {', '.join(f['cross_slot']['passed_on'])} "
                    f"but {f['verdict']} on {f['surface']}. This is not called parity "
                    "unless the protocol explicitly defines a parity comparison."
                )
            if f.get("disposition"):
                lines.append(f"- **Disposition:** {f['disposition']}")
            slice_text = f.get("log_slice") or "(no correlated log lines)"
            lines += ["", "```text", slice_text, "```", ""]
        t = packet["verdict_totals"]
        lines += [
            "## Raw measurements",
            "",
        ]
        measured = [verdict for verdict in packet.get("verdicts", []) if verdict.get("measurements")]
        if not measured:
            lines.append("- none")
        for verdict in measured:
            values = ", ".join(
                f"{key}={value}" for key, value in sorted(verdict["measurements"].items())
            )
            lines.append(
                f"- `{verdict['scenario_id']}` step {verdict['step_index'] + 1} "
                f"· `{verdict['slot_id']}` · {values}"
            )
        lines += [
            "",
            "## Totals",
            "",
            f"{t['pass']} pass · {t['fail']} fail · {t['partial']} partial · "
            f"{t['observe']} observe · {t['skip']} skip",
            "",
            "## Harness evidence",
            "",
            f"{len(packet.get('staging', []))} scenario staging record(s) · "
            f"{len(packet.get('transitions', []))} state transition record(s).",
            "Full probe/action results are preserved in `debrief.json`.",
            "",
        ]
        return "\n".join(lines)

    # --- backlog feed -----------------------------------------------------

    def backlog_block(self, run_id: str) -> str:
        findings = [f for f in self.db.list_findings(run_id) if f.get("triage_state") == "fix"]
        debrief_path = str(paths.run_debrief_dir(run_id) / "debrief.md")
        if not findings:
            return (
                "# No `fix` findings in this sitting.\n"
                "# Triage at least one finding to `fix` before generating the BACKLOG block.\n"
            )
        lines = [
            "<!-- Paste into pm/roadmap/holdspeak/BACKLOG.md under ## Candidate phases -->",
            "",
            "| # | Candidate | Type | Source | Signal |",
            "|---|---|---|---|---|",
        ]
        for f in findings:
            title = (f.get("title") or "").replace("|", "/")
            disp = (f.get("disposition") or "").replace("|", "/")
            lines.append(
                f"| _uat_ | {title} | uat-finding | {f['id']} ({debrief_path}) | "
                f"**candidate** — UAT sitting; {disp or 'fix'} |"
            )
        return "\n".join(lines) + "\n"


def _version_from_config(run: dict) -> str | None:
    return None  # product version is read from the run's own /api later; placeholder-honest


def _acceptance_status(
    totals: dict, *, complete: bool = True, protocol_valid: bool = True
) -> str:
    if not protocol_valid:
        return "invalid-protocol"
    if not complete:
        return "in-progress"
    if totals.get("fail"):
        return "failed"
    if totals.get("partial") or totals.get("skip"):
        return "inconclusive"
    if totals.get("observe"):
        return "passed-with-observations"
    return "passed"


def _read_protocol_snapshot(run_id: str) -> dict | None:
    path = paths.run_dir(run_id) / "protocol-snapshot.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def _log_slice(lines: list[str], when: str | None, before: int = 120, after: int = 30) -> str:
    """Product-log lines around a verdict's timestamp; falls back to the tail.

    If the product logs carry parseable timestamps, window to [when-before,
    when+after] seconds; otherwise return the last 30 lines (honest fallback).
    """
    if not lines:
        return ""
    if when:
        try:
            parsed = _dt.datetime.fromisoformat(when.replace("Z", "+00:00"))
            # Product file logs use the host's local wall clock; verdicts are UTC.
            # Compare in local-naive time rather than dropping the UTC offset.
            target = (
                parsed.astimezone().replace(tzinfo=None)
                if parsed.tzinfo is not None
                else parsed
            )
        except ValueError:
            target = None
        if target is not None:
            windowed = []
            for line in lines:
                m = _TS.search(line)
                if not m:
                    continue
                try:
                    ts = _dt.datetime.fromisoformat(m.group(1).replace(" ", "T"))
                except ValueError:
                    continue
                delta = (ts - target).total_seconds()
                if -before <= delta <= after:
                    windowed.append(line)
            if windowed:
                return "\n".join(windowed[-40:])
    return "\n".join(lines[-30:])
