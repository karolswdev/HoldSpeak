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

Each non-pass verdict becomes a **finding** with a stable id (`UAT-<run>-<n>`)
and a triage state that survives regeneration (the disposition is the human's).
A cross-surface disagreement — passed on web, failed on iPhone — is one finding
wearing both verdicts; the split is the signal.
"""

from __future__ import annotations

import datetime as _dt
import json
import re
from pathlib import Path

from . import paths
from .contract.coverage import pack_coverage
from .contract.ledger import FeatureLedger
from .contract.scenarios import load_pack
from .db import Database
from .runs import RunManager

# fail/partial are actionable findings; skip is a deliberate non-answer, listed
# but not filed for triage.
FINDING_VERDICTS = ("fail", "partial")
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
        scenarios = load_pack(pack)
        scen_by_id = {s.id: s for s in scenarios}
        verdicts = self.db.list_verdicts(run_id)
        coverage = pack_coverage(scenarios, self.ledger())

        # Derive + upsert findings (triage preserved by id).
        derived = self._derive_findings(run_id, verdicts, scen_by_id)
        for f in derived:
            self.db.upsert_finding(f)
        stored = {f["id"]: f for f in self.db.list_findings(run_id)}

        logs = self.runs.logs(run_id, 4000)
        product_log = (logs.get("stdout", "") + "\n" + logs.get("stderr", "")).splitlines()

        findings_out = []
        for f in derived:
            merged = {**f, **stored.get(f["id"], {})}
            merged["log_slice"] = _log_slice(product_log, f.get("created_at"))
            merged["cross_surface"] = self._cross_surface(f, verdicts)
            findings_out.append(merged)

        scores = self._scores(verdicts)
        header = {
            "generated_at": _utcnow(),
            "sitting_id": sitting_id,
            "pack": pack,
            "deck": sitting.get("deck"),
            "run_id": run_id,
            "product_version": run.get("config_json") and _version_from_config(run),
            "surfaces_sat": sorted(scores.keys()),
        }
        packet = {
            "header": header,
            "scores": scores,
            "coverage": coverage,
            "findings": findings_out,
            "verdict_totals": self._totals(verdicts),
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
        non_pass = [v for v in verdicts if v["verdict"] in FINDING_VERDICTS]
        non_pass.sort(key=lambda v: (v["scenario_id"], v["step_index"], v["surface"]))
        out = []
        for n, v in enumerate(non_pass, start=1):
            scenario = scen_by_id.get(v["scenario_id"])
            title = scenario.title if scenario else v["scenario_id"]
            out.append({
                "id": f"UAT-{run_short}-{n}",
                "run_id": run_id,
                "pack": v["pack"],
                "scenario_id": v["scenario_id"],
                "step_index": v["step_index"],
                "surface": v["surface"],
                "verdict": v["verdict"],
                "note": v.get("note"),
                "title": f"{title} — step {v['step_index'] + 1}, {v['surface']}: {v['verdict']}",
                "created_at": v.get("created_at") or _utcnow(),
                "shot_path": v.get("shot_path"),
            })
        return out

    def _cross_surface(self, finding: dict, verdicts: list[dict]) -> dict:
        """The same (scenario, step) on other surfaces — a split is the signal."""
        others = {
            v["surface"]: v["verdict"]
            for v in verdicts
            if v["scenario_id"] == finding["scenario_id"] and v["step_index"] == finding["step_index"]
        }
        passed = [s for s, vd in others.items() if vd == "pass"]
        return {"all_surfaces": others, "passed_on": passed, "is_split": bool(passed)}

    # --- scoring ----------------------------------------------------------

    def _scores(self, verdicts: list[dict]) -> dict:
        scores: dict[str, dict] = {}
        for v in verdicts:
            s = scores.setdefault(v["surface"], {"pass": 0, "fail": 0, "partial": 0, "skip": 0})
            s[v["verdict"]] = s.get(v["verdict"], 0) + 1
        return scores

    def _totals(self, verdicts: list[dict]) -> dict:
        t = {"pass": 0, "fail": 0, "partial": 0, "skip": 0}
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
            f"- **Surfaces sat:** {', '.join(h['surfaces_sat']) or '(none)'}",
            "",
            "## Score per surface",
            "",
        ]
        for surface in ("web", "ipad", "iphone"):
            sc = packet["scores"].get(surface)
            if sc is None:
                lines.append(f"- **{surface}** — *not sat*")
            else:
                lines.append(
                    f"- **{surface}** — {sc.get('pass',0)} pass · {sc.get('fail',0)} fail · "
                    f"{sc.get('partial',0)} partial · {sc.get('skip',0)} skip"
                )
        cov = packet["coverage"]
        lines += [
            "",
            "## Coverage against the ledger",
            "",
            f"- overall: {cov['overall']['covered']}/{cov['overall']['total']} ({cov['overall']['pct']}%)",
            f"- web: {cov['web']['covered']}/{cov['web']['total']} ({cov['web']['pct']}%)",
            f"- iPad: {cov['ipad']['covered']}/{cov['ipad']['total']} ({cov['ipad']['pct']}%)",
            f"- iPhone: {cov['iphone']['covered']}/{cov['iphone']['total']} ({cov['iphone']['pct']}%)",
            "",
            f"## Findings ({len(packet['findings'])})",
            "",
        ]
        if not packet["findings"]:
            lines.append("No non-pass verdicts. Every applicable surface passed.")
        for f in packet["findings"]:
            lines += [
                f"### {f['id']} — {f['title']}",
                "",
                f"- **Verdict:** {f['verdict']}  ·  **Surface:** {f['surface']}  ·  **Triage:** {f.get('triage_state','untriaged')}",
                f"- **Note:** {f.get('note') or '(none)'}",
            ]
            if f.get("shot_path"):
                lines.append(f"- **Screenshot:** {f['shot_path']}")
            if f.get("cross_surface", {}).get("is_split"):
                lines.append(
                    f"- **Cross-surface split:** passed on {', '.join(f['cross_surface']['passed_on'])} "
                    f"but {f['verdict']} on {f['surface']} — a parity break."
                )
            if f.get("disposition"):
                lines.append(f"- **Disposition:** {f['disposition']}")
            slice_text = f.get("log_slice") or "(no correlated log lines)"
            lines += ["", "```text", slice_text, "```", ""]
        t = packet["verdict_totals"]
        lines += [
            "## Totals",
            "",
            f"{t['pass']} pass · {t['fail']} fail · {t['partial']} partial · {t['skip']} skip",
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


def _log_slice(lines: list[str], when: str | None, before: int = 120, after: int = 30) -> str:
    """Product-log lines around a verdict's timestamp; falls back to the tail.

    If the product logs carry parseable timestamps, window to [when-before,
    when+after] seconds; otherwise return the last 30 lines (honest fallback).
    """
    if not lines:
        return ""
    if when:
        try:
            target = _dt.datetime.fromisoformat(when.replace("Z", "+00:00")).replace(tzinfo=None)
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
