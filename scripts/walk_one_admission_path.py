#!/usr/bin/env python3
"""HS-131-12 — assembled One Admission Path real-model walk.

This harness composes the already-shipped Phase 131 live-LAN walks instead of
copying their service rigs into a tenth implementation. Every real-model leg runs
in its own fresh HOME and asserts its own parent/child/revision/receipt contract.
A focused controlled leg covers fallback, indeterminate, preload, session,
content-hygiene, sync, and restart seams; the unchanged fence closes the walk.

Run with a fresh HOME and a scratch work directory:

    HOME=$(mktemp -d) XDG_DATA_HOME=$HOME/.local/share \
      HS_WALK_LAN=http://192.168.1.43:8080/v1 \
      uv run python scripts/walk_one_admission_path.py \
        --work-dir /path/outside/the/repository

The harness never prints child stdout/stderr because those streams can contain
model text. It reports only return codes, byte counts, and SHA-256 digests.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import time
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
LAN_URL = "http://192.168.1.43:8080/v1"
LAN_MODEL = "Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf"


@dataclass(frozen=True)
class Leg:
    name: str
    label: str
    argv: tuple[str, ...]


@dataclass(frozen=True)
class LegResult:
    name: str
    status: str
    returncode: int
    duration_ms: int
    stdout_bytes: int
    stderr_bytes: int
    output_sha256: str
    ledger: tuple[dict[str, object], ...]


LIVE_WALKS = (
    ("runner", "runner revision/cancellation", "hs-131-12/walk_runner_lan.py"),
    ("ask-agent", "Ask and saved Agent", "hs-131-03/walk_ask_agent_lan.py"),
    ("sequence-workflow", "Sequence and Workflow", "hs-131-12/walk_sequence_workflow_lan.py"),
    ("workbench", "Workbench item and memory", "hs-131-05/walk_workbench_lan.py"),
    ("schedule", "bounded scheduled Workbench", "hs-131-06/walk_bounded_schedule_lan.py"),
    ("services", "finite service callers", "hs-131-07/walk_service_callers_lan.py"),
    ("meeting", "meeting session and deferred intelligence", "hs-131-08/walk_meeting_session_lan.py"),
    ("dictation", "dictation sessions", "hs-131-09/walk_dictation_session_lan.py"),
)
LIVE_NAMES = frozenset(name for name, _label, _path in LIVE_WALKS)

CONTROLLED_TESTS = (
    "tests/unit/test_inference_runner.py::test_fallback_is_two_invocations_not_one_logical_receipt",
    "tests/unit/test_inference_runner.py::test_deadline_unknown_provider_closes_indeterminate_before_dispatch_returns",
    "tests/unit/test_inference_runner.py::test_unknown_cancel_disposition_closes_indeterminate",
    "tests/unit/test_inference_runner.py::test_claim_rechecks_revoked_parent_before_provider_dispatch",
    "tests/unit/test_deployment_revisions.py::test_deployment_revision_sync_round_trip_without_credential",
    "tests/unit/test_actuator_kernel.py::test_approved_operation_survives_hub_restart_before_egress",
    "tests/unit/test_dictation_session_admission.py::test_wake_capture_admits_one_bounded_wake_session",
    "tests/unit/test_dictation_session_admission.py::test_transcribe_runs_one_child_naming_the_frozen_revision",
    "tests/unit/test_dictation_session_admission.py::test_explicit_get_model_is_one_preload_sibling_before_the_transcribe_child",
    "tests/unit/test_dictation_session_admission.py::test_authorized_pre_session_warm_runs_as_the_preload_service",
    "tests/unit/test_dictation_session_admission.py::test_meeting_transcription_children_join_the_existing_meeting_session",
    "tests/unit/test_dictation_session_admission.py::test_a_revoked_warrant_fences_the_session_through_the_durable_read",
    "tests/unit/test_dictation_session_admission.py::test_no_audio_or_transcript_reaches_any_kernel_row",
    "tests/unit/test_meeting_session_admission.py::test_no_transcript_material_reaches_the_kernel_journal",
)

FENCE_TESTS = (
    "tests/unit/test_one_path_census.py",
    "tests/unit/test_one_path_context.py",
    "tests/unit/test_one_path_spine.py",
    "tests/unit/test_one_path_cardinality.py",
    "tests/unit/test_one_path_provenance.py",
)


def _legs() -> tuple[Leg, ...]:
    asset_root = ROOT / "pm/roadmap/holdspeak/phase-131-one-admission-path/assets"
    live = tuple(
        Leg(name, label, (sys.executable, str(asset_root / relative)))
        for name, label, relative in LIVE_WALKS
    )
    return live + (
        Leg(
            "controlled-contracts",
            "fallback, indeterminate, sessions, hygiene, sync, restart",
            (sys.executable, "-m", "pytest", "-q", *CONTROLLED_TESTS),
        ),
        Leg(
            "one-path-fence",
            "literal spine, context, cardinality, provenance, mutation fence",
            (sys.executable, "-m", "pytest", "-q", *FENCE_TESTS),
        ),
    )


def _probe(endpoint: str) -> list[str]:
    request = urllib.request.Request(endpoint.rstrip("/") + "/models")
    with urllib.request.urlopen(request, timeout=8) as response:
        payload = json.loads(response.read().decode("utf-8"))
    rows = payload.get("models") or payload.get("data") or []
    return [str(row.get("name") or row.get("id") or "") for row in rows]


def _isolated_env(home: Path, endpoint: str) -> dict[str, str]:
    config = home / ".config"
    data = home / ".local" / "share"
    temp = home / "tmp"
    for path in (config, data, temp):
        path.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    for key in tuple(env):
        if key in {"HOLDSPEAK_HUB_TOKEN", "HOLDSPEAK_TOKEN", "OPENAI_API_KEY"}:
            env.pop(key, None)
        elif key.startswith("HOLDSPEAK_PROFILE_") and key.endswith("_KEY"):
            env.pop(key, None)
    env.update(
        HOME=str(home),
        XDG_CONFIG_HOME=str(config),
        XDG_DATA_HOME=str(data),
        TMPDIR=str(temp),
        HS_WALK_LAN=endpoint,
        PYTHONUNBUFFERED="1",
    )
    return env


def _digest(stdout: bytes, stderr: bytes) -> str:
    return "sha256:" + hashlib.sha256(stdout + b"\0" + stderr).hexdigest()


def _ledger_excerpt(home: Path) -> tuple[dict[str, object], ...]:
    excerpts: list[dict[str, object]] = []
    for path in sorted(home.rglob("*.db")):
        connection = sqlite3.connect(path)
        connection.row_factory = sqlite3.Row
        try:
            tables = {
                str(row[0])
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            if "kernel_operations" not in tables:
                continue
            operations = [
                dict(row)
                for row in connection.execute(
                    "SELECT operation_id,name,version,principal_kind,target_ref,"
                    "authority_basis,delegator_kind,state,parent_operation_id "
                    "FROM kernel_operations ORDER BY created_at,operation_id"
                )
            ]
            receipts = [
                dict(row)
                for row in connection.execute(
                    "SELECT receipt_id,operation_id,state,outcome,result_ref "
                    "FROM kernel_receipts ORDER BY created_at,receipt_id"
                )
            ]
            parents = []
            if "kernel_parent_runs" in tables:
                parents = [
                    dict(row)
                    for row in connection.execute(
                        "SELECT operation_id,kind,definition_ref,definition_revision,state "
                        "FROM kernel_parent_runs ORDER BY created_at,operation_id"
                    )
                ]
            excerpts.append(
                {
                    "database": path.relative_to(home).as_posix(),
                    "operations": operations,
                    "receipts": receipts,
                    "parents": parents,
                }
            )
        finally:
            connection.close()
    return tuple(excerpts)


def _run_leg(leg: Leg, work_dir: Path, endpoint: str, timeout: float) -> LegResult:
    home = work_dir / leg.name
    home.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    try:
        process = subprocess.run(
            leg.argv,
            cwd=ROOT,
            env=_isolated_env(home, endpoint),
            capture_output=True,
            timeout=timeout,
        )
        stdout = process.stdout
        stderr = process.stderr
        returncode = int(process.returncode)
        status = "passed" if returncode == 0 else "failed"
    except subprocess.TimeoutExpired as exc:
        stdout = bytes(exc.stdout or b"")
        stderr = bytes(exc.stderr or b"")
        returncode = 124
        status = "timeout"
    ledger: tuple[dict[str, object], ...] = ()
    if status == "passed" and leg.name in LIVE_NAMES:
        try:
            ledger = _ledger_excerpt(home)
        except Exception as exc:  # noqa: BLE001 — type only, never row/provider text
            stderr += f"\nledger_error={type(exc).__name__}".encode()
            returncode = 3
            status = "ledger-error"
        if status == "passed" and not ledger:
            returncode = 3
            status = "ledger-missing"
    duration_ms = round((time.monotonic() - started) * 1000)
    result = LegResult(
        name=leg.name,
        status=status,
        returncode=returncode,
        duration_ms=duration_ms,
        stdout_bytes=len(stdout),
        stderr_bytes=len(stderr),
        output_sha256=_digest(stdout, stderr),
        ledger=ledger,
    )
    operation_count = sum(len(row["operations"]) for row in ledger)
    receipt_count = sum(len(row["receipts"]) for row in ledger)
    marker = "PASS" if status == "passed" else "FAIL"
    print(
        f"  {marker}  {leg.name}: {leg.label}; rc={returncode}; "
        f"duration_ms={duration_ms}; operations={operation_count}; "
        f"receipts={receipt_count}; stdout_bytes={len(stdout)}; "
        f"stderr_bytes={len(stderr)}; output={result.output_sha256}"
    )
    if status != "passed":
        print(f"        rerun argv={list(leg.argv)!r}")
    return result


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--work-dir",
        type=Path,
        help="Fresh, empty scratch directory for isolated leg homes",
    )
    parser.add_argument(
        "--summary-json",
        type=Path,
        help="Optional content-free result file",
    )
    parser.add_argument(
        "--only",
        action="append",
        default=[],
        help="Run one named leg (repeatable)",
    )
    parser.add_argument("--timeout", type=float, default=600.0, help="Seconds per leg")
    parser.add_argument("--list", action="store_true", help="List leg names and exit")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    legs = _legs()
    if args.list:
        for leg in legs:
            print(f"{leg.name}\t{leg.label}")
        return 0
    if args.work_dir is None:
        print("FAIL: --work-dir is required so the walk cannot touch owner state")
        return 2
    work_dir = args.work_dir.resolve()
    try:
        work_dir.relative_to(ROOT)
    except ValueError:
        pass
    else:
        print("FAIL: --work-dir must be outside the repository")
        return 2
    if work_dir.exists() and (
        not work_dir.is_dir() or any(work_dir.iterdir())
    ):
        print(f"FAIL: --work-dir must be fresh and empty: {work_dir}")
        return 2
    work_dir.mkdir(parents=True, exist_ok=True)

    endpoint = str(os.environ.get("HS_WALK_LAN") or "").rstrip("/")
    if not endpoint:
        print("FAIL: set HS_WALK_LAN to the real LAN OpenAI-compatible /v1 endpoint")
        return 2
    if endpoint != LAN_URL:
        print(f"FAIL: shipped Phase 131 walk legs are pinned to {LAN_URL}; got {endpoint}")
        return 2
    try:
        models = _probe(endpoint)
    except Exception as exc:  # noqa: BLE001 — report type only, never raw provider text
        print(f"FAIL: LAN endpoint probe failed ({type(exc).__name__})")
        return 1
    if LAN_MODEL not in models:
        print(f"FAIL: expected model is not loaded; model_count={len(models)}")
        return 1
    print(
        f"LIVE endpoint ready: {endpoint}; model={LAN_MODEL}; "
        f"model_count={len(models)}"
    )

    selected = set(args.only)
    known = {leg.name for leg in legs}
    unknown = selected - known
    if unknown:
        print(f"FAIL: unknown leg(s): {sorted(unknown)}")
        return 2
    if selected:
        legs = tuple(leg for leg in legs if leg.name in selected)

    results = [_run_leg(leg, work_dir, endpoint, args.timeout) for leg in legs]
    failed = [result for result in results if result.status != "passed"]
    summary = {
        "schema": "holdspeak.one-admission-walk@1",
        "endpoint": endpoint,
        "model": LAN_MODEL,
        "passed": len(results) - len(failed),
        "failed": len(failed),
        "legs": [asdict(result) for result in results],
    }
    if args.summary_json is not None:
        args.summary_json.parent.mkdir(parents=True, exist_ok=True)
        args.summary_json.write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(f"SUMMARY: {summary['passed']} passed, {summary['failed']} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
