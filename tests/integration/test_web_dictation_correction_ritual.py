"""HS-48-03: the one-tap right/wrong correction ritual.

The ritual is a single inline component (`correctionRitual` / `wireFixit`) reused
by the dry-run result and every journal entry. "Right" is a calm client-only
acknowledgement; "Wrong" opens the existing correct path pre-scoped (block /
target in one tap) and reuses `POST /api/dictation/journal/{id}/correct` — no new
write primitive. These assertions read the built bundle + CSS (the ritual DOM is
JS-injected) and exercise the backend correct path the ritual posts to.
"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import holdspeak.config as config_module
from holdspeak.config import Config
from holdspeak.db import Database, reset_database
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

_BUILT = Path(__file__).resolve().parents[2] / "holdspeak" / "static" / "_built" / "_astro"


def _dictation_script() -> str:
    files = list(_BUILT.glob("dictation.astro_astro_type_script*.js"))
    if not files:
        pytest.skip("web bundle not built")
    return "\n".join(p.read_text() for p in files)


def _dictation_css() -> str:
    files = list(_BUILT.glob("dictation*.css"))
    if not files:
        pytest.skip("web bundle not built")
    return "\n".join(p.read_text() for p in files)


@pytest.fixture
def settings_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    target = tmp_path / "config.json"
    monkeypatch.setattr(config_module, "CONFIG_FILE", target)
    return target


@pytest.fixture
def persistent_db():
    temp_dir = Path(tempfile.mkdtemp())
    reset_database()
    database = Database(temp_dir / "ritual.db")
    yield database
    reset_database()
    shutil.rmtree(temp_dir, ignore_errors=True)


def _client(database: Database) -> TestClient:
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})
        ),
        dictation_journal_repository=database.dictation_journal,
        dictation_corrections_repository=database.dictation_corrections,
    )
    return TestClient(server.app)


# ── the ritual ships + is wired into both surfaces ───────────────────────────

def test_ritual_component_is_shipped() -> None:
    js = _dictation_script()
    assert "correctionRitual" in js
    assert "wireFixit" in js
    # right (no write) + wrong (opens the pre-scoped fix), and the scope picker.
    for marker in ("data-fixit-yes", "data-fixit-no", 'data-fixit-scope="intent"', "data-fixit-kind-label"):
        assert marker in js, marker
    # it reuses the existing correct endpoint — no new write primitive.
    assert "/correct" in js
    assert "submitMomentFix" in js  # the existing seam, extended not duplicated


def test_ritual_is_wired_into_dry_run_and_journal() -> None:
    js = _dictation_script()
    # dry-run host wires the ritual it renders…
    assert "wireFixit(host)" in js
    # …and the journal list wires the ritual on each entry.
    assert "wireFixit(list)" in js


def test_ritual_is_focus_safe() -> None:
    # The standing dictation invariant: zero programmatic focus theft.
    assert ".focus()" not in _dictation_script()


def test_ritual_css_is_global() -> None:
    css = _dictation_css()
    assert ".fixit-scope{" in css.replace(" ", ""), (
        "ritual styles must be global (is:global) — the ritual DOM is JS-injected"
    )
    assert "fixit-scope[data-astro-cid" not in css, "fixit-scope is scoped — move it into <style is:global>"


def test_dry_run_moment_host_present(persistent_db: Database, settings_path: Path) -> None:
    Config().save(path=settings_path)
    body = _client(persistent_db).get("/dictation").text
    assert 'id="dry-moment"' in body
    assert "autofocus" not in body.lower()


# ── the path the ritual posts to still teaches (one decision, real write) ────

def test_ritual_correct_path_teaches_and_marks(persistent_db: Database, settings_path: Path) -> None:
    cfg = Config()
    cfg.dictation.pipeline.corrections_enabled = True
    cfg.save(path=settings_path)
    rec = persistent_db.dictation_journal.record(
        source="dictation", transcript="follow up with sam about launch", final_text="x"
    )
    # The "Wrong block -> action_item" one-tap path is a single POST.
    resp = _client(persistent_db).post(
        f"/api/dictation/journal/{rec.id}/correct", json={"kind": "intent", "value": "action_item"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["corrected"] is True and body["taught"] is True
    # the entry is now flagged corrected (the ritual hides the ask for these)
    assert persistent_db.dictation_journal.get(rec.id).corrected is True
    # and the correction landed in the store (teachable across restarts)
    stored = persistent_db.dictation_corrections.recent_corrections()
    assert any(r.kind == "intent" and r.value == "action_item" for r in stored)
