"""The doctor speaks plainly: the CLI rows, the hub rows, and the face words the
Setup face shows (moved together by service, the fast diet 2026-10-12).
"""

from __future__ import annotations

import re
from pathlib import Path
from types import SimpleNamespace
from urllib.error import URLError
import pytest
import holdspeak.doctor as hub_doctor
import holdspeak.config as config_module
import holdspeak.setup_status as setup_status
from holdspeak.commands.doctor import DoctorCheck, collect_doctor_checks, face_words
from holdspeak.config import Config


# ── from tests/unit/test_philo15_11_doctor_plain.py (moved whole by the fast diet, 2026-10-12) ──
# PHILO-15 11 (B08): `holdspeak doctor` speaks plainly.
#
# Before the first launch the hub section printed four "[Errno 61] Connection
# refused" rows; the model hint named a different file than the missing one;
# rows used developer words (MIR routing, LLM runtime counters, Mesh edges ...).

REPO = Path(__file__).resolve().parents[2]

#: Developer words a row name must not carry (the owner's words: what it is).
JARGON = re.compile(
    r"\bMIR\b|\bLLM\b|Structured-output|telemetry|\bMesh\b|edges|Runs on destinations|\bKB\b|compilation"
    r"|[a-z]+-[a-z]+"  # a kebab id (hub-health) is a machine name, not a row name
)


def _refuse(*_args, **_kwargs):
    raise URLError(ConnectionRefusedError(61, "Connection refused"))


def _no_hub_env(monkeypatch) -> None:
    monkeypatch.delenv("HOLDSPEAK_URL", raising=False)
    monkeypatch.delenv("HOLDSPEAK_TOKEN", raising=False)
    monkeypatch.setattr(hub_doctor, "discovered_hub_url", lambda: None)
    monkeypatch.setattr(hub_doctor, "_local_owner_token", lambda: "")


def test_hub_not_running_is_one_honest_line(monkeypatch) -> None:
    _no_hub_env(monkeypatch)
    monkeypatch.setattr(hub_doctor, "_get_json", _refuse)
    lines: list[str] = []

    rc = hub_doctor.run_doctor(output=lines.append)

    assert lines == ["HUB · NOT RUNNING · start it with `holdspeak`"]
    assert rc == 0
    assert not any("Errno" in line or "refused" in line for line in lines)


def test_hub_not_running_skips_the_other_network_checks(monkeypatch) -> None:
    _no_hub_env(monkeypatch)
    monkeypatch.setattr(hub_doctor, "_get_json", _refuse)

    def boom(*_a, **_k):  # pragma: no cover - must not run
        raise AssertionError("a network check ran with no hub")

    monkeypatch.setattr(hub_doctor, "_post_json", boom)
    monkeypatch.setattr(hub_doctor, "_get_html", boom)

    results = hub_doctor.run_checks()

    assert [(r.name, r.detail) for r in results] == [("hub-health", hub_doctor.HUB_NOT_RUNNING)]


def test_any_other_hub_failure_still_fails(monkeypatch) -> None:
    _no_hub_env(monkeypatch)
    monkeypatch.setattr(hub_doctor, "run_checks", lambda url=None, token=None: [
        hub_doctor.DoctorResult("FAIL", "hub-health", "HTTP 500")
    ])
    lines: list[str] = []

    assert hub_doctor.run_doctor(output=lines.append) == 1
    assert lines[0].startswith("FAIL  Hub ")


def _preflight_through_the_real_producer(monkeypatch, model_path: str):
    """The hub's own runtime-test payload (``probe_runtime``) for a missing
    llama.cpp model at ``model_path``, read by the doctor's preflight row."""
    from holdspeak.config import Config
    from holdspeak.setup_runtime import probe_runtime

    cfg = Config()
    cfg.dictation.pipeline.enabled = True
    cfg.dictation.runtime.backend = "llama_cpp"
    cfg.dictation.runtime.llama_cpp_model_path = model_path
    monkeypatch.setattr(
        "holdspeak.plugins.dictation.runtime.resolve_backend", lambda requested, **_kw: ("llama_cpp", "stubbed")
    )
    payload = probe_runtime(cfg.dictation)
    assert payload["status"] == "missing_model", payload
    monkeypatch.setattr(hub_doctor, "_post_json", lambda *_a, **_k: (200, payload))
    return hub_doctor._check_runtime_preflight("http://127.0.0.1:1", "")


def test_the_starter_model_not_downloaded_is_a_step_not_a_failure(monkeypatch, tmp_path) -> None:
    from holdspeak.intel.models import DEFAULT_INTEL_MODEL_PATH

    monkeypatch.setenv("HOME", str(tmp_path))
    result = _preflight_through_the_real_producer(monkeypatch, DEFAULT_INTEL_MODEL_PATH)

    assert result.status == "SKIP"
    assert "Qwen3.5-4B-Q4_K_M.gguf is not downloaded yet" in result.detail
    assert "Set up local AI" in result.detail


def test_a_missing_custom_model_is_a_failure_not_the_starter_setup(monkeypatch, tmp_path) -> None:
    """Astra r1 on #986: a model the owner chose, under models/artifacts too,
    is not the starter; Set up local AI downloads a different file."""
    custom = tmp_path / "models" / "artifacts" / "artifact_custom" / "owner-selected-model.gguf"
    result = _preflight_through_the_real_producer(monkeypatch, str(custom))

    assert result.status == "FAIL"
    assert result.detail.startswith("model file missing: owner-selected-model.gguf")
    assert "Set up local AI" not in result.detail


def test_the_dictation_model_row_tells_starter_from_custom(monkeypatch, tmp_path) -> None:
    from holdspeak.commands import doctor
    from holdspeak.config import Config
    from holdspeak.intel.models import DEFAULT_INTEL_MODEL_PATH

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(
        "holdspeak.plugins.dictation.runtime.resolve_backend", lambda requested, **_kw: ("llama_cpp", "stubbed")
    )

    def row(path: str):
        cfg = Config()
        cfg.dictation.pipeline.enabled = True
        cfg.dictation.runtime.backend = "llama_cpp"
        cfg.dictation.runtime.llama_cpp_model_path = path
        return doctor._check_dictation_runtime(cfg)

    starter = row(DEFAULT_INTEL_MODEL_PATH)
    assert starter.fix and "Set up local AI" in starter.fix
    custom = row(str(tmp_path / "models" / "artifacts" / "artifact_custom" / "owner-selected-model.gguf"))
    assert custom.fix and custom.fix.startswith("model file missing: owner-selected-model.gguf")
    assert "Set up local AI" not in custom.fix


def test_every_row_name_is_plain_words() -> None:
    source = (REPO / "holdspeak" / "commands" / "doctor.py").read_text(encoding="utf-8")
    names = set(re.findall(r'name="([^"]+)"', source))
    labels = set(hub_doctor.ROW_LABELS.values())
    assert names and labels
    bad = sorted(n for n in names | labels if JARGON.search(n))
    # `Tool-call gate` and `ffmpeg` / `pactl` name the real tool and command.
    assert [n for n in bad if n != "Tool-call gate"] == []


def test_every_hub_check_has_a_plain_label() -> None:
    source = (REPO / "holdspeak" / "doctor.py").read_text(encoding="utf-8")
    ids = set(re.findall(r'DoctorResult\(\s*"[A-Z]+",\s*"([a-z-]+)"', source))
    assert ids and ids <= set(hub_doctor.ROW_LABELS)


def test_this_device_is_said_once(monkeypatch) -> None:
    from holdspeak.commands import doctor
    from holdspeak.inference_targets import NOT_SET_UP_REASON

    target = SimpleNamespace(
        name="This device", kind="this_device", boundary="same_device", ready=False,
        readiness_reason=NOT_SET_UP_REASON,
    )
    monkeypatch.setattr("holdspeak.db.get_database", lambda: None)
    monkeypatch.setattr("holdspeak.inference_targets.list_inference_targets", lambda _db: [target])

    check = doctor._check_inference_targets()

    assert check.name == "Where AI runs"
    assert check.detail == "This device · not set up yet"
    assert check.fix and "Set up local AI" in check.fix


#: Developer words the PRINTED doctor output (names, details, fix lines) must
#: not carry (Astra r1 on #986: the label fence missed the details).
OUTPUT_JARGON = re.compile(
    r"\bMIR\b|\bLLM\b|Structured-output|telemetry|\bMesh edges\b|Runs on destinations|\+ KB\b|compilation"
    r"|preflight|primitives|llama_cpp|openai_compatible|resolved=|requested=|Errno"
)


def test_the_printed_setup_list_is_plain_words(monkeypatch, tmp_path, capsys) -> None:
    """The real `collect_doctor_checks` list, as `holdspeak doctor` prints it."""
    from holdspeak.commands import doctor as local_doctor

    monkeypatch.setenv("HOME", str(tmp_path))
    local_doctor.run_doctor_command(SimpleNamespace(connectors=False, strict=False))
    out = capsys.readouterr().out
    assert "Summary:" in out
    assert OUTPUT_JARGON.findall(out) == [], out


def test_the_printed_hub_list_is_plain_words(monkeypatch) -> None:
    """A running hub's rows, through `run_doctor`'s own printer."""
    _no_hub_env(monkeypatch)
    answers = {
        "/health": {"status": "ok"},
        "/api/runtime/status": {"status": "ok"},
        "/api/inference-targets": {"targets": []},
    }
    monkeypatch.setattr(hub_doctor, "_get_json", lambda _url, path, _token="": (200, answers[path]))
    monkeypatch.setattr(
        hub_doctor, "_post_json",
        lambda *_a, **_k: (200, {"ok": True, "detail": "Ready — llama_cpp model at /m/x.gguf."}),
    )
    monkeypatch.setattr(hub_doctor, "_get_html", lambda _url: (200, "<html></html>"))
    monkeypatch.setattr(hub_doctor, "_check_websocket", lambda *_a: hub_doctor.DoctorResult("PASS", "websocket", "pong received in 3ms"))
    monkeypatch.setattr(hub_doctor, "_check_mcp_server", lambda: hub_doctor.DoctorResult("PASS", "mcp-server", "initialization received"))
    monkeypatch.setattr(hub_doctor, "_check_database", lambda: hub_doctor.DoctorResult("PASS", "database", "notes readable"))
    monkeypatch.setattr(hub_doctor, "check_observer", lambda: hub_doctor.DoctorResult("PASS", "observer", "healthy: 24h events: 0"))
    lines: list[str] = []

    assert hub_doctor.run_doctor(token="t", output=lines.append) == 0
    out = "\n".join(lines)
    assert "llama.cpp" in out
    assert OUTPUT_JARGON.findall(out) == [], out
    for line in lines[:-2]:
        assert not re.match(r"\w+\s+[a-z]+-[a-z]+\s", line), line  # a kebab id printed as a row name


def test_the_hub_database_row_says_notes_not_primitives() -> None:
    source = (REPO / "holdspeak" / "doctor.py").read_text(encoding="utf-8")
    assert '"database", "notes readable"' in source


@pytest.mark.parametrize("branch", ["openai_compatible", "unresolvable"])
def test_the_printed_dictation_model_row_is_plain_in_every_branch(branch, monkeypatch, capsys) -> None:
    """Astra r2 on #986: the OpenAI-compatible branch printed `resolved=...`;
    the default-state list never reached it. Each branch, printed."""
    from holdspeak.commands import doctor as local_doctor
    from holdspeak.config import Config
    from holdspeak.plugins.dictation.runtime import RuntimeUnavailableError

    cfg = Config()
    cfg.dictation.pipeline.enabled = True
    cfg.dictation.runtime.backend = "openai_compatible" if branch == "openai_compatible" else "llama_cpp"

    def resolve(requested, **_kw):
        if branch == "unresolvable":
            raise RuntimeUnavailableError("no backend installed")
        return ("openai_compatible", "requested backend")

    monkeypatch.setattr("holdspeak.plugins.dictation.runtime.resolve_backend", resolve)
    check = local_doctor._check_dictation_runtime(cfg)
    monkeypatch.setattr(local_doctor, "collect_doctor_checks", lambda **_k: [check])
    local_doctor.run_doctor_command(SimpleNamespace(connectors=False, strict=False))
    out = capsys.readouterr().out
    assert "Dictation AI model" in out
    assert OUTPUT_JARGON.findall(out) == [], out


# ── from tests/unit/test_philo17_doctor_face_words.py (moved whole by the fast diet, 2026-10-12) ──
# PHILO-17 REFIT: a doctor check's face words.
#
# `face_words(check)` is the short plain sentence the Setup face and the Guide
# show; `/api/setup/status` sends it as a section's `detail` and the check's
# own technical detail as `raw`. The check's name, status and detail (what the
# CLI prints) do not change.

@pytest.mark.parametrize(
    ("check", "words"),
    [
        (DoctorCheck("Dictation AI model", "PASS", "the model file q.gguf is on this device (llama_cpp; auto: fallback to llama_cpp)"),
         "with llama.cpp"),
        (DoctorCheck("Dictation AI model", "PASS", "off (dictation clean-up is disabled; it is optional)"),
         "Off. Dictation clean-up is optional."),
        (DoctorCheck("Speech model", "FAIL", "Speech is not set up: Whisper base (mlx) is not on this device"),
         "No speech model yet"),
        (DoctorCheck("Transcription backend", "PASS", "`auto` resolves to `mlx`"), "Speech to text uses MLX"),
        (DoctorCheck("Where AI runs", "WARN", "This device · not set up yet"), "No AI engine is set up yet"),
        (DoctorCheck("Where AI runs", "WARN", "This device · not set up yet; lan: private endpoint · ready"),
         "1 ready. Some places for AI are not set up or not available"),
        (DoctorCheck("Coding agents", "PASS", "Claude Code hooks installed; Codex does not trust the HoldSpeak hooks yet (it does not run them)"),
         "Some agent hooks are not installed"),
        (DoctorCheck("Some new check", "WARN", "x=1; y_z (raw)"), "Needs a check"),
        (DoctorCheck("Some new check", "PASS", "All good."), "All good"),
    ],
)
def test_face_words_are_plain(check: DoctorCheck, words: str) -> None:
    assert words in face_words(check)


def test_every_real_check_has_short_plain_words(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config_module, "CONFIG_FILE", tmp_path / "config.json")
    for check in collect_doctor_checks(skip_network=True):
        words = face_words(check)
        assert words and len(words) <= 80, (check.name, words)
        assert not any(mark in words for mark in (";", "=", "`", "_cpp")), (check.name, words)


def test_the_setup_section_carries_words_and_raw(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "holdspeak.commands.doctor.collect_doctor_checks",
        lambda **_: [DoctorCheck(name="ffmpeg", status="WARN", detail="Not found in PATH", fix="brew install ffmpeg")],
    )
    section = setup_status.build_setup_status(config=Config())["sections"][0]
    assert section["label"] == "ffmpeg" and section["status"] == "warn"
    assert section["detail"] == "ffmpeg is not installed"
    assert section["raw"] == "Not found in PATH"


# Astra MUST on #1111: the face words never carry a filesystem path or a URL.
@pytest.mark.parametrize(
    ("model", "base_url", "node"),
    [
        ("/srv/models/q.gguf", "http://10.0.0.5:8080/v1", None),
        ("http://models.example.net:9000/v1/qwen-27b", "https://api.example.net/v1", None),
        ("/opt/weights/llama/model.bin", None, "studio"),
    ],
)
def test_an_adopted_profile_never_puts_a_path_or_url_in_the_face_words(
    monkeypatch: pytest.MonkeyPatch, model: str, base_url: str | None, node: str | None
) -> None:
    from types import SimpleNamespace

    from holdspeak.commands.doctor import _check_dictation_runtime

    effective = SimpleNamespace(
        profile_id="p1", profile_name="lab", node=node, base_url=base_url, model=model, reason=None
    )
    monkeypatch.setattr("holdspeak.intel.providers.effective_dictation_llm", lambda _runtime: effective)
    cfg = Config()
    cfg.dictation.pipeline.enabled = True
    check = _check_dictation_runtime(cfg)
    assert check.name == "Dictation AI model" and check.status == "PASS"
    assert model in check.detail  # the CLI's technical fact keeps the whole path

    monkeypatch.setattr("holdspeak.commands.doctor.collect_doctor_checks", lambda **_: [check])
    section = setup_status.build_setup_status(config=Config())["sections"][0]
    assert "/" not in section["detail"] and "://" not in section["detail"], section["detail"]
    assert section["detail"].startswith("Runs on ")
    assert model in section["raw"]
