"""RECIPE LINE-6: the Line's speech models in the signed catalogue, their
fetch into the Line's model folder (a fake fetch; no test reaches Hugging
Face), their state, and the concierge's path to them."""
from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Iterator

import pytest

from holdspeak import inference_setup_catalog as catalog
from holdspeak.line import models

NOW = datetime(2026, 10, 29, 12, tzinfo=timezone.utc)


# ── the catalogue ────────────────────────────────────────────────────


def test_the_signed_catalogue_carries_the_two_speech_models_and_round_trips() -> None:
    envelope = catalog.packaged_catalog_envelope_json()
    verified = catalog.verify_catalog_envelope(envelope, now=NOW)
    assert verified["catalog_revision"] == 6 and verified["signing_key_id"] == "holdspeak_catalog_2026_10_29"
    speech = [row for row in verified["entries"] if row["kind"] == "speech_model_preset"]
    assert [(row["role"], row["label"]) for row in speech] == [
        ("stt", "Phone speech in · Parakeet (int8, onnx-asr)"),
        ("tts", "Phone voice · Pocket TTS"),
    ]
    for row in speech:
        assert row["source"]["license"] == "CC-BY-4.0" and row["source"]["code_license"] == "MIT"
        assert row["source"]["download_bytes"] == sum(item["bytes"] for item in row["source"]["files"])
        assert row["target"] == "line"
    assert catalog.speech_presets(now=NOW) == tuple(speech)
    # The canonical body round-trips: parse, write back, same bytes.
    raw = json.loads(envelope)
    assert json.dumps(raw, sort_keys=True, separators=(",", ":"), ensure_ascii=True) == envelope


def test_a_changed_speech_pin_breaks_the_signature() -> None:
    raw = json.loads(catalog.packaged_catalog_envelope_json())
    speech = next(row for row in raw["entries"] if row["kind"] == "speech_model_preset")
    speech["source"]["files"][0]["sha256"] = "sha256:" + "0" * 64
    with pytest.raises(ValueError, match="signature"):
        catalog.verify_catalog_envelope(json.dumps(raw, sort_keys=True, separators=(",", ":")), now=NOW)


def test_the_old_trust_roots_stay_and_revision_five_is_a_rollback() -> None:
    raw = json.loads(catalog.packaged_catalog_envelope_json())
    with pytest.raises(ValueError, match="rolled back"):
        catalog.verify_catalog_envelope(json.dumps({**raw, "catalog_revision": 5}, sort_keys=True, separators=(",", ":")),
                                        now=NOW)


def _speech() -> dict[str, Any]:
    return copy.deepcopy(catalog.speech_presets(now=NOW)[0])


@pytest.mark.parametrize(("change", "message"), [
    (lambda row: row["source"].update(revision="main"), "mutable"),
    (lambda row: row["source"]["files"][0].update(path="../escape"), "path is invalid"),
    (lambda row: row["source"].update(download_bytes=1), "inconsistent"),
    (lambda row: row["source"]["files"][0].update(sha256="abc"), "sha256 is invalid"),
    (lambda row: row.update(runtime_id="pocket_tts"), "speech role"),
    (lambda row: row.update(target="hub"), "speech role"),
    (lambda row: row.update(download_url="https://mutable.invalid"), "invalid fields"),
])
def test_the_validator_refuses_a_bad_speech_row(change: Any, message: str) -> None:
    row = _speech()
    change(row)
    with pytest.raises(ValueError, match=message):
        catalog.validate_catalog([row])


def test_speech_models_are_not_inference_presets() -> None:
    ids = {row["id"] for row in catalog.applicable_presets(platform_id="darwin_arm64", runtime_ids={"llama_cpp_prompt_v1"})}
    assert not {row["id"] for row in catalog.speech_presets()} & ids


# ── the fetch, with a fake ───────────────────────────────────────────


def _row(contents: dict[str, bytes]) -> dict[str, Any]:
    files = [{"path": path, "bytes": len(data), "sha256": "sha256:" + hashlib.sha256(data).hexdigest()}
             for path, data in contents.items()]
    row = {
        "kind": "speech_model_preset", "id": "speech_test_voice", "role": "tts", "label": "Phone voice · Test",
        "summary": "A test voice.", "runtime_id": "pocket_tts", "target": "line",
        "source": {"repository": "example/voice", "revision": "a" * 40, "files": files,
                   "download_bytes": sum(len(data) for data in contents.values()), "license": "CC-BY-4.0",
                   "code_license": "MIT", "attribution": "Test"},
        "applicability": {"state": "applicable", "reason": None},
    }
    return catalog.validate_catalog([row])[0]


CONTENTS = {"languages/english/model.safetensors": b"m" * 5000, "languages/english/tokenizer.json": b"{}"}


@pytest.fixture()
def line_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("HOLDSPEAK_LINE_HOME", str(tmp_path / "line"))
    models.forget_jobs()
    yield tmp_path / "line"
    models.forget_jobs()


def _fake(contents: dict[str, bytes], row: dict[str, Any], seen: list[str]) -> Any:
    def fetch(url: str) -> Iterator[bytes]:
        seen.append(url)
        path = url.split(f"/resolve/{row['source']['revision']}/", 1)[1]
        data = contents[path]
        for start in range(0, len(data), 1024):
            yield data[start:start + 1024]
    return fetch


def test_the_fetch_fills_the_line_folder_from_the_pinned_revision_and_says_ready(line_home: Path) -> None:
    row = _row(CONTENTS)
    seen: list[str] = []
    moves: list[tuple[int, int]] = []
    assert models.state(row)["state"] == models.MISSING
    after = models.fetch(row, fetch=_fake(CONTENTS, row, seen), progress=lambda got, total: moves.append((got, total)))
    assert after == {"state": "ready", "received": 5002, "total": 5002}
    assert seen == [f"https://huggingface.co/example/voice/resolve/{'a' * 40}/{path}" for path in CONTENTS]
    folder = line_home / "models" / "speech_test_voice"
    assert (folder / "languages/english/model.safetensors").read_bytes() == CONTENTS["languages/english/model.safetensors"]
    assert moves[-1] == (5002, 5002) and moves == sorted(moves)
    assert not list(folder.rglob("*.part"))
    # A second fetch has nothing to do.
    seen.clear()
    assert models.fetch(row, fetch=_fake(CONTENTS, row, seen))["state"] == "ready" and seen == []


def test_a_file_that_does_not_match_its_pin_is_not_kept(line_home: Path) -> None:
    row = _row(CONTENTS)
    bad = {**CONTENTS, "languages/english/model.safetensors": b"x" * 5000}
    with pytest.raises(ValueError, match="SHA-256"):
        models.fetch(row, fetch=_fake(bad, row, []))
    folder = line_home / "models" / "speech_test_voice"
    assert not (folder / "languages/english/model.safetensors").exists()
    assert not list(folder.rglob("*.part"))
    assert models.state(row)["state"] == models.MISSING


def test_a_changed_file_on_disk_is_hashed_again_and_says_partial(line_home: Path) -> None:
    row = _row(CONTENTS)
    models.fetch(row, fetch=_fake(CONTENTS, row, []))
    target = line_home / "models" / "speech_test_voice" / "languages/english/model.safetensors"
    target.write_bytes(b"y" * 5000)
    word = models.state(row)
    assert word["state"] == models.PARTIAL and "SHA-256" in word["reason"]
    # The fetch mends it.
    assert models.fetch(row, fetch=_fake(CONTENTS, row, []))["state"] == models.READY


def test_the_job_reports_progress_then_ready_and_the_cli_shares_the_state(line_home: Path,
                                                                          monkeypatch: pytest.MonkeyPatch,
                                                                          capsys: pytest.CaptureFixture[str]) -> None:
    row = _row(CONTENTS)
    monkeypatch.setattr(models, "presets", lambda: (row,))
    first = models.start(row["id"], fetch_fn=_fake(CONTENTS, row, []))
    assert first["state"] in {models.DOWNLOADING, models.READY} and first["label"] == "Phone voice · Test"
    models.wait(row["id"])
    [after] = models.rows()
    assert after["state"] == models.READY and after["host"] == "huggingface.co"
    assert after["license"] == "CC-BY-4.0" and after["code_license"] == "MIT"
    # `holdspeak line models` reads the same folder: nothing left to fetch.
    from holdspeak.line.node import fetch_models, machine_block

    seen: list[str] = []
    assert fetch_models(fetch=_fake(CONTENTS, row, seen)) == [row["id"]] and seen == []
    assert "Ready" in capsys.readouterr().out
    monkeypatch.setattr("holdspeak.line.node.find_baresip", lambda: None)
    assert machine_block()["models"] == [{"id": "line-tts", "name": "Phone voice · Test", "state": "downloaded"}]


def test_a_failed_job_says_so_and_keeps_nothing(line_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    row = _row(CONTENTS)
    monkeypatch.setattr(models, "presets", lambda: (row,))

    def broken(url: str) -> Iterator[bytes]:
        yield b"m" * 10
        raise OSError("connection reset")

    models.start(row["id"], fetch_fn=broken)
    models.wait(row["id"])
    [after] = models.rows()
    assert after["state"] == models.FAILED and "Try again" in after["reason"]


# ── the concierge's path ─────────────────────────────────────────────


def _client() -> Any:
    from fastapi import FastAPI, Request
    from fastapi.testclient import TestClient

    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.web.routes.concierge import build_concierge_router

    app = FastAPI()

    @app.middleware("http")
    async def owner(request: Request, call_next: Any) -> Any:
        request.state.principal = Principal(PrincipalKind.OWNER, "owner")
        return await call_next(request)

    app.include_router(build_concierge_router(SimpleNamespace(model_library_service=None)))  # type: ignore[arg-type]
    return TestClient(app)


def test_the_concierge_routes_read_the_rows_and_start_the_line_fetch(line_home: Path,
                                                                     monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak.services import concierge_service

    real = [models.preset(row["id"]) for row in catalog.speech_presets()]
    client = _client()
    rows = client.get("/api/concierge/speech").json()["rows"]
    assert [(row["role"], row["state"]) for row in rows] == [("stt", "missing"), ("tts", "missing")]
    assert rows[0]["bytes"] == real[0]["source"]["download_bytes"]

    started: list[tuple[str, Any]] = []
    monkeypatch.setattr(models, "start", lambda preset_id, fetch_fn=None: (started.append((preset_id, fetch_fn)),
                                                                           models.model_row(models.preset(preset_id)))[1])
    answer = client.post("/api/concierge/download", json={"presetId": real[1]["id"]})
    assert answer.status_code == 202
    body = answer.json()
    assert body["jobId"] == f"line:{real[1]['id']}" and body["row"]["role"] == "tts"
    assert started == [(real[1]["id"], None)]
    # The MCP family reaches the same service function.
    assert concierge_service.download(preset_id=real[0]["id"], model_library_service=None, principal=None,
                                      catalog_revision=6)["jobId"] == f"line:{real[0]['id']}"


def test_a_non_owner_reads_nothing(line_home: Path) -> None:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from holdspeak.web.routes.concierge import build_concierge_router

    app = FastAPI()

    @app.middleware("http")
    async def nobody(request: Any, call_next: Any) -> Any:
        from holdspeak.principals import UNAUTHENTICATED

        request.state.principal = UNAUTHENTICATED
        return await call_next(request)

    app.include_router(build_concierge_router(SimpleNamespace(model_library_service=None)))  # type: ignore[arg-type]
    assert TestClient(app).get("/api/concierge/speech").status_code == 403
