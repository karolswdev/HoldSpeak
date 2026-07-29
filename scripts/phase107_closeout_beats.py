#!/usr/bin/env python3
"""Run the eight HS-107-07 closeout beats as one reproducible session."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid
import wave
from collections.abc import Callable
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from typing import Any, ClassVar

import numpy as np
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from holdspeak import agent_context, desktop_typing
from holdspeak.cadence.models import EvidenceRef, OpenLoop
from holdspeak.config import Config
from holdspeak.db import get_database, reset_database
from holdspeak.delivery import direct_gesture_input
from holdspeak.delivery.direct_gesture_input import (
    submit_process_input_from_owner_gesture,
)
from holdspeak.desktop_typing import type_text_from_owner_gesture
from holdspeak.intel_queue import IntelQueueWorker
from holdspeak.kernel import runtime as kernel_runtime
from holdspeak.kernel.external_egress import (
    EGRESS_EXECUTIONS,
    EgressOperationRefused,
    run_external_egress,
)
from holdspeak.kernel.subprocess_exec import (
    EXECUTIONS,
    SubprocessOutcomeIndeterminate,
    run_subprocess_operation,
)
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.text_processor import TextProcessor
from holdspeak.transcribe import Transcriber
from holdspeak.typer import TextTyper
from holdspeak.web.context import WebContext
from holdspeak.web.routes.cadence import build_cadence_router

_REPO = Path(__file__).resolve().parents[1]
_AUDIO = _REPO / "tests" / "fixtures" / "core_path_smoke_16k.wav"
_FENCE_PROBE = _REPO / "holdspeak" / "phase107_unlisted_effect_probe.py"
_OWNER = Principal(PrincipalKind.OWNER, "owner-session")
# Re-pinned to the kernel-path medians by the owner's Phase 107 sitting
# ruling (2026-07-29): the ~25 ms admission price of a receipted typed act
# is accepted; the pre-migration raw-TextTyper numbers (release 926.297,
# type 155.796) no longer describe the shipped path. Comparisons remain
# noise-bound cross-session (±10 ms local, ±40 ms LAN pipeline).
_BASELINE = {
    "capture_stop_ms": 0.056,
    "transcribe_ms": 178.176,
    "punctuation_ms": 0.119,
    "pipeline_ms": 538.813,
    "type_ms": 208.573,
    "release_to_landed_ms": 930.980,
}
# Cross-session noise bands measured 2026-07-29 (evidence-story-07):
# local segments ±10 ms, the LAN pipeline segment ±40 ms. A delta inside the
# band is machine/endpoint drift, not a source regression; deltas beyond it
# still fail the beat by name.
_NOISE_MS = {
    "release_to_landed_ms": 40.0,
    "transcribe_ms": 10.0,
}
_LATENCY_COMMAND = (
    "uv run python scripts/measure_dictation_latency.py --runs 3 --warmups 1 "
    "--typing-mode driver --pipeline active --backend mlx"
)


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))


def _payload(label: str, value: Any) -> None:
    print(f"PAYLOAD {label} {_json(value)}", flush=True)


def _run(command: list[str], *, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=_REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=check,
    )


def _read_operation(operation_id: str) -> dict[str, Any]:
    result = kernel_runtime._service().read(
        [f"operation:{operation_id}"], "full", "committed", _OWNER
    )
    objects = result.get("objects") or []
    if not objects:
        raise RuntimeError(f"journal operation not found: {operation_id}")
    return dict(objects[0])


def _capture_pane(pane: str) -> str:
    completed = _run(["tmux", "capture-pane", "-p", "-t", pane, "-S", "-100"])
    if completed.returncode:
        raise RuntimeError(completed.stdout.strip())
    return completed.stdout.rstrip()


def _load_audio() -> np.ndarray:
    with wave.open(str(_AUDIO), "rb") as source:
        if (
            source.getframerate() != 16000
            or source.getnchannels() != 1
            or source.getsampwidth() != 2
        ):
            raise RuntimeError("fixture is not mono 16-bit PCM at 16 kHz")
        raw = source.readframes(source.getnframes())
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0


def _transcribe_fixture() -> tuple[str, float]:
    config = Config.load()
    started = time.perf_counter()
    transcriber = Transcriber(
        model_name=config.model.name,
        backend="mlx",
        language=config.model.language,
        timeout_seconds=config.model.transcribe_timeout_seconds,
    )
    audio = _load_audio()
    transcript = transcriber.transcribe(audio)
    elapsed_ms = round((time.perf_counter() - started) * 1000.0, 3)
    processed = TextProcessor(spoken_symbols=config.dictation.spoken_symbols).process(transcript)
    if not processed.strip():
        raise RuntimeError("MLX returned an empty fixture transcription")
    return processed, elapsed_ms


def _reset_runtime(db_path: Path) -> None:
    reset_database()
    database = get_database(db_path)
    kernel_runtime._broker = None
    kernel_runtime._database_id = None
    desktop_typing._FOCUS = desktop_typing._FocusTracker()
    direct_gesture_input._SERVICES._targets = None
    direct_gesture_input._SERVICES._commands = None
    direct_gesture_input._SERVICES._database_id = None
    EXECUTIONS._plans.clear()
    EXECUTIONS._operation_ids.clear()
    EXECUTIONS._results.clear()
    EGRESS_EXECUTIONS._plans.clear()
    EGRESS_EXECUTIONS._operation_ids.clear()
    EGRESS_EXECUTIONS._results.clear()
    kernel_runtime._configure(database)


def _beat1(state: dict[str, Any]) -> None:
    print(f"COMMAND beat-1 {_LATENCY_COMMAND}", flush=True)
    completed = _run(_LATENCY_COMMAND.split())
    print("BEGIN beat-1-command-output", flush=True)
    print(completed.stdout.rstrip(), flush=True)
    print("END beat-1-command-output", flush=True)
    if completed.returncode:
        raise RuntimeError(f"latency command exited {completed.returncode}")
    line = next(
        (item for item in completed.stdout.splitlines() if item.startswith("HS107_BASELINE ")),
        None,
    )
    if line is None:
        raise RuntimeError("latency command did not print HS107_BASELINE")
    result = json.loads(line.removeprefix("HS107_BASELINE "))
    summary = {key: float(value["median"]) for key, value in result["summary_ms"].items()}
    state["latency"] = result
    _payload(
        "beat-1-latency-verdict",
        {
            "baseline_ms": _BASELINE,
            "now_median_ms": summary,
            "release_to_landed_delta_ms": round(
                summary["release_to_landed_ms"] - _BASELINE["release_to_landed_ms"], 3
            ),
            "fixture_programmatic_hold_segment": True,
            "owner_sitting_supplies_physical_hold": True,
        },
    )
    if (
        summary["release_to_landed_ms"]
        > _BASELINE["release_to_landed_ms"] + _NOISE_MS["release_to_landed_ms"]
    ):
        raise RuntimeError(
            "release_to_landed regression: "
            f"{_BASELINE['release_to_landed_ms']:.3f} -> "
            f"{summary['release_to_landed_ms']:.3f} ms "
            f"(beyond the measured ±{_NOISE_MS['release_to_landed_ms']:.0f} ms "
            "session-noise band)"
        )


def _osascript(source: str) -> str:
    completed = _run(["osascript", "-e", source])
    if completed.returncode:
        raise RuntimeError(completed.stdout.strip())
    return completed.stdout


def _beat2(state: dict[str, Any]) -> None:
    if sys.platform != "darwin":
        raise RuntimeError("real TextEdit typing requires macOS")
    transcript, model_and_transcribe_ms = _transcribe_fixture()
    marker = "HS107_DICTATION_TYPED " + transcript
    _osascript(
        'tell application "TextEdit"\nactivate\nmake new document\nend tell\ndelay 0.5'
    )
    try:
        result = type_text_from_owner_gesture(
            marker,
            typer=TextTyper(),
            gesture="hold_release",
            submit=False,
            requested_target="focused",
            delivery_method="phase107_closeout_fixture",
            subject_refs=("audio-fixture:core-path-smoke-16k",),
        )
        landed = _osascript('tell application "TextEdit" to get text of front document').strip()
        if marker not in landed:
            raise RuntimeError(f"TextEdit did not receive marker; got {landed!r}")
        readback = _read_operation(result["operation_id"])
        _payload(
            "beat-2-desktop-type-text",
            {
                "mic_segment": "programmatic fixture act; owner sitting supplies human hold",
                "fixture": str(_AUDIO.relative_to(_REPO)),
                "backend": "mlx",
                "model_load_plus_transcribe_ms": model_and_transcribe_ms,
                "transcript": transcript,
                "pane_readback": landed,
                "adapter_result": result,
                "journal_readback": readback,
            },
        )
        if readback.get("receipt", {}).get("outcome") != "succeeded":
            raise RuntimeError("desktop.type_text journal receipt was not succeeded")
    finally:
        try:
            _osascript('tell application "TextEdit" to close front document saving no')
        except RuntimeError as exc:
            print(f"CLEANUP_WARNING TextEdit close failed: {exc}", flush=True)


def _beat3(state: dict[str, Any]) -> None:
    transcript, model_and_transcribe_ms = _transcribe_fixture()
    marker = "HS107_DICTATION_AGENT_LANDED " + transcript
    result = submit_process_input_from_owner_gesture(
        pane=state["pane"],
        text=marker,
        session_key=state["tmux_session"],
        agent="phase107-closeout",
    )
    time.sleep(0.15)
    pane = _capture_pane(state["pane"])
    if marker not in pane:
        raise RuntimeError(f"real tmux pane did not receive dictation marker; got {pane!r}")
    readback = _read_operation(result["operation_id"])
    _payload(
        "beat-3-dictation-process-input",
        {
            "fixture": str(_AUDIO.relative_to(_REPO)),
            "backend": "mlx",
            "model_load_plus_transcribe_ms": model_and_transcribe_ms,
            "transcript": transcript,
            "adapter_result": result,
            "pane_readback": pane,
            "journal_readback": readback,
        },
    )
    if readback.get("receipt", {}).get("outcome") != "succeeded":
        raise RuntimeError("process.input journal receipt was not succeeded")


def _write_agent_state(path: Path, session_id: str, pane: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    path.write_text(
        _json(
            {
                "sessions": {
                    session_id: {
                        "agent": "claude",
                        "session_id": session_id,
                        "cwd": str(_REPO),
                        "updated_at": now,
                        "hook_event_name": "Stop",
                        "repo_root": str(_REPO),
                        "project_name": "holdspeak",
                        "awaiting_response": True,
                        "last_assistant_text": "Should the closeout use the audited number?",
                        "tmux_pane": pane,
                        "pinned": True,
                    }
                }
            }
        ),
        encoding="utf-8",
    )


def _beat4(state: dict[str, Any]) -> None:
    database = get_database()
    session_id = f"hs107-cadence-{uuid.uuid4().hex[:8]}"
    agent_state = Path(state["temp_dir"]) / "agent_sessions.json"
    _write_agent_state(agent_state, session_id, state["pane"])
    prior_state_path = agent_context.AGENT_CONTEXT_FILE
    agent_context.AGENT_CONTEXT_FILE = agent_state
    loop = database.cadence.upsert_loop(
        OpenLoop(
            source_type="agent_question",
            source_id=session_id,
            title="Use the audited closeout number?",
            owner="you",
            priority="urgent",
            evidence=[
                EvidenceRef(
                    kind="agent_session",
                    ref_id=session_id,
                    label="real staged tmux session",
                )
            ],
        )
    )
    marker = f"HS107_CADENCE_REPLY_LANDED_{uuid.uuid4().hex[:10]}"
    app = FastAPI()

    @app.middleware("http")
    async def authenticated_owner(request: Request, call_next: Callable[..., Any]):
        request.state.principal = _OWNER
        return await call_next(request)

    app.include_router(build_cadence_router(WebContext(get_state=dict)))
    try:
        with TestClient(app) as client:
            response = client.post(
                f"/api/cadence/loops/{loop.id}/reply", json={"text": marker}
            )
        body = response.json()
        if response.status_code != 200 or not body.get("delivered"):
            raise RuntimeError(f"Cadence reply route returned {response.status_code}: {body}")
        time.sleep(0.15)
        pane = _capture_pane(state["pane"])
        if marker not in pane:
            raise RuntimeError(f"real tmux pane did not receive Cadence marker; got {pane!r}")
        readback = _read_operation(str(body["operation_id"]))
        _payload(
            "beat-4-cadence-route",
            {
                "http_status": response.status_code,
                "route_response": body,
                "authenticated_principal": _OWNER.identity,
                "awaiting_session_file": str(agent_state),
                "pane_readback": pane,
                "journal_readback": readback,
                "loop_status": database.cadence.get_loop(loop.id).status,
            },
        )
        if readback.get("receipt", {}).get("outcome") != "succeeded":
            raise RuntimeError("Cadence process.input journal receipt was not succeeded")
    finally:
        agent_context.AGENT_CONTEXT_FILE = prior_state_path


def _latest_subprocess_full(operation_id: str) -> dict[str, Any]:
    full = _read_operation(operation_id)
    if not full.get("native_receipts"):
        raise RuntimeError(f"subprocess operation has no native receipt: {operation_id}")
    return full


def _beat5(state: dict[str, Any]) -> None:
    before = set(EXECUTIONS._operation_ids.values())
    success = run_subprocess_operation(
        ["/usr/bin/printf", "HS107_SUBPROCESS_SUCCESS"],
        connector_id="phase107-closeout-success",
        declared_permissions=("shell:exec",),
        allowed_argv_prefixes=(("/usr/bin/printf",),),
        capture_output=True,
        text=True,
    )
    success_op = next(iter(set(EXECUTIONS._operation_ids.values()) - before))

    before = set(EXECUTIONS._operation_ids.values())
    nonzero = run_subprocess_operation(
        ["/bin/sh", "-c", "exit 7"],
        connector_id="phase107-closeout-nonzero",
        declared_permissions=("shell:exec",),
        allowed_argv_prefixes=(("/bin/sh", "-c", "exit 7"),),
        capture_output=True,
        text=True,
    )
    nonzero_op = next(iter(set(EXECUTIONS._operation_ids.values()) - before))

    dispatch_calls = 0

    def once(*args: Any, **kwargs: Any):
        nonlocal dispatch_calls
        dispatch_calls += 1
        return subprocess.run(*args, check=False, **kwargs)

    try:
        run_subprocess_operation(
            ["/bin/sh", "-c", "sleep 1"],
            connector_id="phase107-closeout-indeterminate",
            declared_permissions=("shell:exec",),
            allowed_argv_prefixes=(("/bin/sh", "-c", "sleep 1"),),
            runner=once,
            timeout=0.01,
            capture_output=True,
            text=True,
        )
        raise RuntimeError("timeout subprocess unexpectedly returned")
    except SubprocessOutcomeIndeterminate as exc:
        indeterminate_op = exc.operation_id
        refusal_text = str(exc)

    payload = {
        "success_completed": {
            "returncode": success.returncode,
            "stdout": success.stdout,
            "journal_readback": _latest_subprocess_full(success_op),
        },
        "nonzero_completed": {
            "returncode": nonzero.returncode,
            "journal_readback": _latest_subprocess_full(nonzero_op),
        },
        "indeterminate": {
            "exception": refusal_text,
            "dispatch_calls": dispatch_calls,
            "blind_retries": 0,
            "journal_readback": _latest_subprocess_full(indeterminate_op),
        },
    }
    _payload("beat-5-subprocess-outcomes", payload)
    native_success = payload["success_completed"]["journal_readback"]["native_receipts"][0]
    native_nonzero = payload["nonzero_completed"]["journal_readback"]["native_receipts"][0]
    native_indeterminate = payload["indeterminate"]["journal_readback"]["native_receipts"][0]
    if native_success["process_outcome"] != "exited_zero":
        raise RuntimeError("success receipt did not say exited_zero")
    if native_nonzero["process_outcome"] != "nonzero_exit" or nonzero.returncode != 7:
        raise RuntimeError("non-zero receipt did not preserve exit 7")
    if native_indeterminate["process_outcome"] != "indeterminate" or dispatch_calls != 1:
        raise RuntimeError("indeterminate subprocess was not single-dispatch")


class _SinkHandler(BaseHTTPRequestHandler):
    received: ClassVar[list[dict[str, Any]]] = []

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        self.received.append({"path": self.path, "body": json.loads(body)})
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"ok":true}')

    def log_message(self, _format: str, *_args: Any) -> None:
        return None


def _latest_egress_full() -> dict[str, Any]:
    if not EGRESS_EXECUTIONS._results:
        raise RuntimeError("egress execution store is empty")
    operation_id = list(EGRESS_EXECUTIONS._results.values())[-1]["operation_id"]
    return _read_operation(str(operation_id))


def _beat6(state: dict[str, Any]) -> None:
    config = Config.load()
    telegram = config.cadence_telegram
    success_kind: str
    if telegram.is_active and telegram.allowed_chat_ids:
        from holdspeak.cadence_telegram import call_telegram

        chat = telegram.allowed_chat_ids[0]
        result = call_telegram(
            telegram.bot_token,
            "sendMessage",
            {"chat_id": chat, "text": "HoldSpeak HS-107-07 staged closeout beat"},
        )
        success_kind = "configured Telegram production path"
        sink_evidence: Any = {"telegram_ok": bool(result.get("ok")), "chat": chat}
    else:
        _SinkHandler.received = []
        sink = ThreadingHTTPServer(("127.0.0.1", 0), _SinkHandler)
        thread = threading.Thread(target=sink.serve_forever, daemon=True)
        thread.start()
        host, port = sink.server_address
        worker = object.__new__(IntelQueueWorker)
        worker.failure_alert_webhook_url = f"http://{host}:{port}/failure-alert"
        worker.failure_alert_webhook_header_name = None
        worker.failure_alert_webhook_header_value = None
        worker.failure_alert_percent = 50.0
        worker.failure_alert_hysteresis_seconds = 0.0
        summary = SimpleNamespace(
            total_jobs=2,
            queued_jobs=0,
            running_jobs=0,
            failed_jobs=2,
            queued_due_jobs=0,
            scheduled_retry_jobs=0,
            next_retry_at=None,
        )
        try:
            worker._post_failure_alert_webhook(
                summary=summary,
                failure_rate_percent=100.0,
                now=datetime.now(timezone.utc),
            )
        finally:
            sink.shutdown()
            sink.server_close()
            thread.join(timeout=2)
        success_kind = "Telegram unconfigured; migrated intel-queue production path to local HTTP sink"
        sink_evidence = list(_SinkHandler.received)
        if not sink_evidence:
            raise RuntimeError("local HTTP sink received no production webhook")

    success_full = _latest_egress_full()
    called = False

    def forbidden_sender() -> None:
        nonlocal called
        called = True

    try:
        run_external_egress(
            connector_id="phase107-closeout-refusal",
            destination="blocked.example:443",
            data_classes=("connector_request",),
            payload_material={"proof": "digest-only"},
            sender=forbidden_sender,
            allowed_destinations=("allowed.example:443",),
        )
        raise RuntimeError("blocked egress unexpectedly ran")
    except EgressOperationRefused as exc:
        refusal = {
            "destination": exc.destination,
            "reason": exc.reason,
            "receipt": exc.receipt,
            "sender_called": called,
        }
    _payload(
        "beat-6-egress",
        {
            "production_path": success_kind,
            "sink_evidence": sink_evidence,
            "success_journal_readback": success_full,
            "honest_refusal": refusal,
        },
    )
    native = success_full.get("native_receipts") or []
    if not native or not native[0].get("destination"):
        raise RuntimeError("successful egress receipt did not name its destination")
    if called or not refusal["reason"].startswith("external_egress_destination_not_allowed:"):
        raise RuntimeError("blocked egress was not honestly refused before sender")


def _beat7(state: dict[str, Any]) -> None:
    latency = state.get("latency")
    if not latency:
        raise RuntimeError("beat 1 produced no contemporaneous latency result")
    now = {
        key: float(value["median"]) for key, value in latency["summary_ms"].items()
    }
    table = [
        {
            "segment": key,
            "baseline_ms": value,
            "now_ms": now[key],
            "delta_ms": round(now[key] - value, 3),
        }
        for key, value in _BASELINE.items()
    ]
    _payload(
        "beat-7-transcription-latency",
        {
            "source": "beat 1 exact contemporaneous command",
            "table": table,
            "transcription_verdict": "no regression"
            if now["transcribe_ms"]
            <= _BASELINE["transcribe_ms"] + _NOISE_MS["transcribe_ms"]
            else "REGRESSION",
        },
    )
    if now["transcribe_ms"] > _BASELINE["transcribe_ms"] + _NOISE_MS["transcribe_ms"]:
        raise RuntimeError(
            f"transcription regression: {_BASELINE['transcribe_ms']:.3f} -> "
            f"{now['transcribe_ms']:.3f} ms "
            f"(beyond the measured ±{_NOISE_MS['transcribe_ms']:.0f} ms "
            "session-noise band)"
        )


def _beat8(state: dict[str, Any]) -> None:
    if _FENCE_PROBE.exists():
        raise RuntimeError(f"refusing to overwrite existing fence probe: {_FENCE_PROBE}")
    probe_output = ""
    try:
        _FENCE_PROBE.write_text(
            "import subprocess\n\n"
            "def phase107_new_unlisted_effect():\n"
            "    return subprocess.run(['/usr/bin/true'], check=False)\n",
            encoding="utf-8",
        )
        caught = _run(
            [
                "uv",
                "run",
                "pytest",
                "-q",
                "tests/unit/test_kernel_effect_fence.py::test_effect_ledger_is_complete_and_current",
            ]
        )
        probe_output = caught.stdout.rstrip()
        catch_line = next(
            (line.strip() for line in caught.stdout.splitlines() if "UNLEDGERED effect site:" in line),
            "",
        )
        if caught.returncode == 0 or "phase107_unlisted_effect_probe.py" not in catch_line:
            raise RuntimeError(
                "fence did not fail by probe filename: "
                f"exit={caught.returncode} output={probe_output!r}"
            )
    finally:
        _FENCE_PROBE.unlink(missing_ok=True)
    green = _run(
        [
            "uv",
            "run",
            "pytest",
            "-q",
            "tests/unit/test_kernel_effect_fence.py::test_effect_ledger_is_complete_and_current",
        ]
    )
    _payload(
        "beat-8-fence",
        {
            "fence_catch_line": catch_line,
            "probe_exit": caught.returncode,
            "probe_removed": not _FENCE_PROBE.exists(),
            "green_exit": green.returncode,
            "green_output": green.stdout.rstrip(),
        },
    )
    if green.returncode:
        raise RuntimeError(f"fence stayed red after probe removal: {green.stdout.rstrip()}")


_BEATS: tuple[tuple[str, Callable[[dict[str, Any]], None]], ...] = (
    ("hold-key dictation latency", _beat1),
    ("dictation desktop.type_text receipt", _beat2),
    ("dictation to agent pane through process.input", _beat3),
    ("Cadence reply through real route", _beat4),
    ("subprocess terminal outcomes", _beat5),
    ("egress destination and refusal", _beat6),
    ("transcription latency unchanged", _beat7),
    ("new effect fence caught then green", _beat8),
)


def main() -> int:
    os.chdir(_REPO)
    if shutil.which("tmux") is None:
        print("SESSION_ABORT tmux is not installed", flush=True)
        return 1
    temp_dir = tempfile.TemporaryDirectory(prefix="holdspeak-hs107-closeout-")
    session = f"hs107-closeout-{os.getpid()}-{uuid.uuid4().hex[:6]}"
    pane = f"{session}:0.0"
    state: dict[str, Any] = {
        "temp_dir": temp_dir.name,
        "tmux_session": session,
        "pane": pane,
    }
    results: list[dict[str, Any]] = []
    print(f"SESSION_START hs-107-07 tmux={pane}", flush=True)
    try:
        _reset_runtime(Path(temp_dir.name) / "closeout.db")
        started = _run(["tmux", "new-session", "-d", "-s", session, "-x", "120", "-y", "30", "cat"])
        if started.returncode:
            print(f"SESSION_ABORT tmux start failed: {started.stdout.strip()}", flush=True)
            return 1
        for index, (name, function) in enumerate(_BEATS, 1):
            try:
                function(state)
            except Exception as exc:  # noqa: BLE001 - every beat must report and continue
                results.append({"beat": index, "name": name, "status": "FAIL", "reason": str(exc)})
                print(f"BEAT {index} FAIL {name} :: {type(exc).__name__}: {exc}", flush=True)
            else:
                results.append({"beat": index, "name": name, "status": "PASS", "reason": ""})
                print(f"BEAT {index} PASS {name}", flush=True)
    finally:
        _FENCE_PROBE.unlink(missing_ok=True)
        _run(["tmux", "kill-session", "-t", session])
        reset_database()
        kernel_runtime._broker = None
        kernel_runtime._database_id = None
        temp_dir.cleanup()
    passed = sum(item["status"] == "PASS" for item in results)
    print(f"SESSION_SUMMARY {passed}/8 passed", flush=True)
    _payload("session-results", results)
    return 0 if passed == 8 else 1


if __name__ == "__main__":
    raise SystemExit(main())
