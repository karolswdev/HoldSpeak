#!/usr/bin/env python3
"""Build a deterministic index of the PHILO-3-02 rig observations.

The default output is beside this file.  ``--output-dir`` is provided so a
caller can inspect a new index in a temporary directory before retaining it.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Iterable


SCRIPT = Path(__file__).resolve()
REPO = SCRIPT.parents[5]
SHOTS = REPO / "pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-02-shots/rig"
ATLAS = REPO / "docs/internal/philo/graph/atlas.json"
TARGET_JOBS = {"j4", "j5", "j6", "j7"}
WIDTHS = (1440, 393)
SHOT_SUFFIXES = {".gif", ".jpeg", ".jpg", ".png", ".webp"}


def nonempty(value: Any) -> bool:
    return value is not None and value != "" and value != [] and value != {}


def json_pointer(path: str, key: str | int) -> str:
    escaped = str(key).replace("~", "~0").replace("/", "~1")
    return f"{path}/{escaped}"


def walk_values(value: Any, path: str) -> Iterable[tuple[str, str, Any]]:
    """Yield nonempty summary/action fields below a selected payload."""
    if isinstance(value, dict):
        for key in sorted(value):
            child = value[key]
            child_path = json_pointer(path, key)
            lowered = str(key).lower()
            if lowered == "summary" and nonempty(child):
                yield "summary", child_path, child
            elif lowered in {"actions", "action_items", "actionitems"} and nonempty(child):
                yield "actions", child_path, child
            yield from walk_values(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk_values(child, json_pointer(path, index))


def source_payloads(observation: dict[str, Any]) -> Iterable[tuple[str, Any]]:
    """Yield only the after-sources named by the story's usefulness proof."""
    after = observation.get("after")
    if not isinstance(after, dict):
        return

    api_reads = after.get("api_reads")
    if isinstance(api_reads, list):
        for index, read in enumerate(api_reads):
            if isinstance(read, dict) and "payload" in read:
                yield f"/after/api_reads/{index}/payload", read["payload"]

    protocol = after.get("protocol")
    if isinstance(protocol, dict):
        for key in ("payload", "rows"):
            if key in protocol:
                yield f"/after/protocol/{key}", protocol[key]

    restart = after.get("restart")
    if isinstance(restart, dict) and "meeting_after" in restart:
        yield "/after/restart/meeting_after", restart["meeting_after"]

    provenance = observation.get("provenance")
    if isinstance(provenance, dict):
        restarts = provenance.get("restarts")
        if isinstance(restarts, list):
            for index, restart_record in enumerate(restarts):
                if isinstance(restart_record, dict) and "meeting_after" in restart_record:
                    yield f"/provenance/restarts/{index}/meeting_after", restart_record["meeting_after"]


def output_values(observation: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract real-engine completed output, deduplicating summaries per run."""
    if observation.get("complete") is not True:
        return []
    provenance = observation.get("provenance")
    if not isinstance(provenance, dict) or provenance.get("engine_mode") != "real":
        return []

    values: list[dict[str, Any]] = []
    summary_indexes: dict[str, int] = {}
    for source_path, payload in source_payloads(observation):
        for kind, path, value in walk_values(payload, source_path):
            if kind == "summary":
                # A restart record repeats the same meeting summary in several
                # payloads. Keep every evidence path while retaining one value.
                text = value if isinstance(value, str) else json.dumps(
                    value, ensure_ascii=False, sort_keys=True
                )
                prior = summary_indexes.get(text)
                if prior is not None:
                    values[prior]["json_paths"].append(path)
                    continue
                summary_indexes[text] = len(values)
                values.append({"kind": kind, "text": text, "json_paths": [path]})
            else:
                values.append({"kind": kind, "value": value, "json_paths": [path]})
    return values


def repo_path(path: Path) -> str:
    return path.resolve().relative_to(REPO).as_posix()


def existing_shots(observation_path: Path, raw_shots: Any) -> list[str]:
    found: set[Path] = set()
    if isinstance(raw_shots, list):
        for raw in raw_shots:
            if not isinstance(raw, str):
                continue
            candidate = (REPO / raw).resolve()
            if candidate.is_file():
                found.add(candidate)
    for candidate in observation_path.parent.iterdir():
        if candidate.is_file() and candidate.suffix.lower() in SHOT_SUFFIXES:
            found.add(candidate.resolve())
    return sorted(repo_path(path) for path in found)


def build_hash(provenance: dict[str, Any]) -> str | None:
    frontend = provenance.get("frontend_build")
    if isinstance(frontend, dict):
        value = frontend.get("index_sha256") or frontend.get("build_hash")
        if isinstance(value, str) and value:
            return value
    for key in ("build_hash", "frontend_build_hash"):
        value = provenance.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def run_entry(path: Path, observation: dict[str, Any]) -> dict[str, Any]:
    relative = repo_path(path)
    provenance = observation.get("provenance")
    if not isinstance(provenance, dict):
        provenance = {}
    parts = path.resolve().relative_to(SHOTS.resolve()).parts
    area = parts[0] if parts else ""
    retention = "superseded" if "_superseded" in parts else ("final" if area == "final" else "historical")
    return {
        "observation_path": relative,
        "area": area,
        "retention": retention,
        "id": observation.get("id"),
        "run_id": observation.get("run_id"),
        "case_id": observation.get("case_id"),
        "job": observation.get("job"),
        "viewport": observation.get("viewport"),
        "brain": observation.get("brain"),
        "pass": observation.get("pass"),
        "result": observation.get("result"),
        "status": observation.get("status"),
        "verdict": observation.get("verdict"),
        "complete": observation.get("complete"),
        "error": observation.get("error"),
        "state_id": observation.get("state_id"),
        "terminal_outcome": observation.get("terminal_outcome"),
        "notes": observation.get("notes"),
        "engine_mode": provenance.get("engine_mode"),
        "revision": provenance.get("revision"),
        "build_hash": build_hash(provenance),
        "shots": existing_shots(path, observation.get("shots")),
        "outputs": output_values(observation),
    }


def atlas_cases() -> list[str]:
    try:
        atlas = json.loads(ATLAS.read_text(encoding="utf-8"))
        cases = atlas.get("cases", [])
        result = []
        for case in cases:
            if not isinstance(case, dict):
                continue
            case_id = case.get("id")
            job = case.get("job")
            if isinstance(case_id, str) and (job in TARGET_JOBS or case_id.split(".")[1] in TARGET_JOBS):
                result.append(case_id)
        return sorted(set(result))
    except (OSError, json.JSONDecodeError, TypeError, IndexError):
        return []


def collect() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    runs: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for path in sorted(SHOTS.rglob("observation.json")):
        try:
            observation = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(observation, dict):
                raise ValueError("observation root is not an object")
            runs.append(run_entry(path, observation))
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            errors.append({
                "observation_path": repo_path(path),
                "area": path.resolve().relative_to(SHOTS.resolve()).parts[0],
                "retention": "superseded" if "_superseded" in path.parts else "historical",
                "error": f"{type(exc).__name__}: {exc}",
            })
    return runs, errors


def latest_complete(runs: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    cases = atlas_cases()
    candidates = {
        (run.get("case_id"), run.get("viewport")): run
        for run in runs
        if run.get("area") == "final"
        and run.get("complete") is True
        and run.get("case_id") in cases
        and run.get("viewport") in WIDTHS
    }
    latest: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    for case_id in cases:
        for width in WIDTHS:
            run = candidates.get((case_id, width))
            key = {"case_id": case_id, "viewport": width}
            if run is None:
                missing.append(key)
            else:
                latest.append({**key, "latest_complete_final": True, "run": run})
    return latest, missing


def md_path(output_dir: Path, relative: str) -> str:
    return Path(os.path.relpath(REPO / relative, output_dir)).as_posix()


def link(output_dir: Path, relative: str, label: str | None = None) -> str:
    return f"[{label or Path(relative).name}]({md_path(output_dir, relative)})"


def render_markdown(report: dict[str, Any], output_dir: Path) -> str:
    runs = report["runs"]
    lines = [
        "# PHILO-3-02 observation index",
        "",
        f"Observation root: `{report['observation_root']}`.",
        f"Retained observations: **{len(runs)}**; parse errors: **{len(report['errors'])}**.",
        "",
        "## Missing actual atlas case-widths",
        "",
    ]
    missing = report["missing_case_widths"]
    if missing:
        lines.extend(f"- `{item['case_id']}` × `{item['viewport']}`" for item in missing)
    else:
        lines.append("- None.")

    lines.extend(["", "## Latest complete result from `final/`", "", "| Case | Width | Verdict | Pass | Revision | Build hash | Observation | Shots |", "| --- | ---: | --- | --- | --- | --- | --- | --- |"])
    for item in report["latest_complete_final"]:
        run = item["run"]
        shots = ", ".join(link(output_dir, shot) for shot in run["shots"]) or "—"
        lines.append(
            f"| `{item['case_id']}` | {item['viewport']} | `{run['verdict']}` | `{run['pass']}` | `{run['revision'] or '—'}` | `{run['build_hash'] or '—'}` | {link(output_dir, run['observation_path'], 'observation')} | {shots} |"
        )

    lines.extend(["", "## Every retained run", "", "| Area | Case | Width | Pass | Verdict | Complete | Revision | Build hash | Observation | Shots |", "| --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- |"])
    for run in runs:
        shots = ", ".join(link(output_dir, shot) for shot in run["shots"]) or "—"
        lines.append(
            f"| `{run['area']}` | `{run['case_id'] or '—'}` | {run['viewport'] or '—'} | `{run['pass']}` | `{run['verdict']}` | `{run['complete']}` | `{run['revision'] or '—'}` | `{run['build_hash'] or '—'}` | {link(output_dir, run['observation_path'], 'observation')} | {shots} |"
        )

    if report["errors"]:
        lines.extend(["", "### Observation read errors", ""])
        for error in report["errors"]:
            lines.append(f"- `{error['observation_path']}` — {error['error']}")

    lines.extend(["", "## Real-engine completed summaries and actions", ""])
    output_count = 0
    for run in runs:
        if not run["outputs"]:
            continue
        output_count += len(run["outputs"])
        lines.extend([f"### `{run['case_id']}` × `{run['viewport']}` — `{run['run_id']}`", "", f"Run: {link(output_dir, run['observation_path'], 'observation')}", ""])
        for index, output in enumerate(run["outputs"], start=1):
            paths = ", ".join(f"`{path}`" for path in output["json_paths"])
            lines.extend([f"#### {output['kind']} {index}", "", f"Source paths: {paths}", ""])
            if output["kind"] == "summary":
                lines.extend(["```text", output["text"], "```", ""])
            else:
                lines.extend(["```json", json.dumps(output["value"], ensure_ascii=False, indent=2, sort_keys=True), "```", ""])
    if output_count == 0:
        lines.append("- None retained yet.")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=SCRIPT.parent, help="directory for observations-index.json and .md")
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    runs, errors = collect()
    latest, missing = latest_complete(runs)
    report = {
        "schema": "holdspeak-philo/phase-3/summary-observations-index/v1",
        "observation_root": repo_path(SHOTS),
        "atlas_path": repo_path(ATLAS),
        "atlas_cases": atlas_cases(),
        "widths": list(WIDTHS),
        "run_count": len(runs),
        "errors": errors,
        "runs": runs,
        "latest_complete_final": latest,
        "missing_case_widths": missing,
    }
    json_path = output_dir / "observations-index.json"
    md_path_out = output_dir / "observations-index.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path_out.write_text(render_markdown(report, output_dir), encoding="utf-8")
    print(f"indexed {len(runs)} observations; wrote {json_path} and {md_path_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
