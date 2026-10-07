"""PHILO-15 11 (B08): `holdspeak doctor` speaks plainly.

Before the first launch the hub section printed four "[Errno 61] Connection
refused" rows; the model hint named a different file than the missing one;
rows used developer words (MIR routing, LLM runtime counters, Mesh edges ...).
"""

from __future__ import annotations

import re
from pathlib import Path
from types import SimpleNamespace
from urllib.error import URLError

import holdspeak.doctor as hub_doctor

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


def test_the_products_model_not_downloaded_is_a_step_not_a_failure(monkeypatch) -> None:
    path = "/h/.local/share/holdspeak/models/artifacts/artifact_8eee/Qwen3.5-4B-Q4_K_M.gguf"
    monkeypatch.setattr(
        hub_doctor, "_post_json", lambda *_a, **_k: (200, {"ok": False, "detail": f"Model not found at {path}."})
    )

    result = hub_doctor._check_runtime_preflight("http://127.0.0.1:1", "")

    assert result.status == "SKIP"
    assert "Qwen3.5-4B-Q4_K_M.gguf is not downloaded yet" in result.detail
    assert "Set up local AI" in result.detail


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
