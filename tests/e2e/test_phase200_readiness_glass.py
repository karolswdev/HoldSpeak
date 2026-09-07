"""HS-200-04 — the repair states as they are DRAWN.

Four named states on the Concierge, each with ONE verb and the host named where
the repair happens.  Shot at 1440 and 393 so the owner can see each one before
it ships.

Asserts, per state: the row exists, it carries exactly one library Button, the
state chip is not clipped, no raw <button> and no prose paragraph appear inside
the face, and at 393 the page does not scroll sideways.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from .glass_infra import (
    _boot,
    _api,
    _assert_clean,
    _normal_chair,
    _settle,
)

SHOTS = (
    Path(__file__).resolve().parents[2]
    / "pm/roadmap/holdspeak/phase-200-the-working-practice/assets/story-04-shots"
)
SHOTS.mkdir(parents=True, exist_ok=True)

TOKEN = "glass-test"

ENGINES = [
    {
        "id": "lan:box", "kind": "lan", "name": "Qwen3.6 35B", "host": "192.168.1.43",
        "state": "READY", "latencyMs": 41, "profileId": "box",
        "baseUrl": "http://192.168.1.43:8080/v1",
    },
    {
        "id": "local:mlx:whisper-base", "kind": "local", "name": "Whisper base",
        "host": "THIS DEVICE", "state": "READY", "runtimeToken": "MLX",
    },
    {
        "id": "preset:qwen35-08b", "kind": "preset", "name": "Qwen 3.5 0.8B",
        "host": "THIS DEVICE", "state": "WAITING", "sizeBytes": 532_000_000,
        "installed": False, "presetId": "qwen35-08b",
    },
]

GROUPS = (
    ("thoughts_notes", "Thoughts & notes"),
    ("chat_practice", "Chat"),
    ("writing_dictation", "Writing & dictation"),
    ("speech_recognition", "Speech recognition"),
    ("meetings", "Meetings"),
    ("agents_tools", "Agents & tools"),
    ("background", "Background"),
)

PROPOSAL = {
    "rows": [
        {"group": g, "label": label, "engineId": "lan:box", "host": "192.168.1.43",
         "state": "READY"}
        for g, label in GROUPS
    ],
    "receipt": {"groups": 7, "engines": 3, "waiting": 0},
}

# One repair per named state, drawn from the conditions the owner's own desk
# reports (§1.6 of the Phase 200 baseline).
STATES: dict[str, dict[str, Any]] = {
    "credential-expired": {
        "id": "credential-expired:Migrated intel endpoint",
        "token": "CREDENTIAL EXPIRED",
        "subject": "Migrated intel endpoint",
        "host": "api.openai.com",
        "scope": "cloud",
        "groups": ["thoughts_notes", "writing_dictation"],
        "groupLabels": ["Thoughts & notes", "Writing & dictation"],
        "verb": "Connections",
        "control": "connections",
        "engineId": "cloud:legacy-intel",
        "presetId": "",
        "baseUrl": "",
        "detail": "",
    },
    "endpoint-unreachable": {
        "id": "endpoint-unreachable:Qwen3.6 35B",
        "token": "ENDPOINT UNREACHABLE",
        "subject": "Qwen3.6 35B",
        "host": "192.168.1.43",
        "scope": "local",
        "groups": ["meetings"],
        "groupLabels": ["Meetings"],
        "verb": "Check",
        "control": "endpoint_editor",
        "engineId": "lan:box",
        "presetId": "",
        "baseUrl": "http://192.168.1.43:8080/v1",
        "detail": "",
    },
    "model-file-missing": {
        "id": "model-file-missing:Qwen 3.5 0.8B",
        "token": "MODEL FILE MISSING",
        "subject": "Qwen 3.5 0.8B",
        "host": "THIS DEVICE",
        "scope": "local",
        "groups": ["writing_dictation"],
        "groupLabels": ["Writing & dictation"],
        "verb": "Download",
        "control": "model_library",
        "engineId": "local:qwen35-08b",
        "presetId": "qwen35-08b",
        "baseUrl": "",
        "detail": "",
    },
    "tool-incompatible": {
        "id": "tool-incompatible:Whisper base",
        "token": "TOOL INCOMPATIBLE",
        "subject": "Whisper base",
        "host": "THIS DEVICE",
        "scope": "local",
        "groups": ["agents_tools"],
        "groupLabels": ["Agents & tools"],
        "verb": "Choose",
        "control": "engine_picker",
        "engineId": "local:mlx:whisper-base",
        "presetId": "",
        "baseUrl": "",
        "detail": "capability_tools_unsupported",
    },
}


def _open_concierge(page: Any) -> None:
    page.evaluate(
        """([key]) => {
          sessionStorage.setItem(
            "hs.desk.staged-surface-open",
            JSON.stringify({key})
          );
        }""",
        ["open-concierge"],
    )
    page.reload(wait_until="load")
    _normal_chair(page)


def _window(page: Any) -> Any:
    return page.locator(".desk-surface-window").filter(
        has=page.locator('[data-testid="concierge-root"]')
    ).first


def _shot(page: Any, name: str, width: int) -> Path:
    _settle(page)
    old_size = page.viewport_size
    page.set_viewport_size({"width": old_size["width"], "height": 2400})
    _settle(page)
    path = SHOTS / f"repair-{name}-{width}.png"
    win = _window(page)
    if win.count() > 0:
        win.screenshot(path=str(path))
    else:
        page.screenshot(path=str(path), full_page=False)
    page.set_viewport_size(old_size)
    assert path.stat().st_size > 2_000, f"Shot {name} too small ({path.stat().st_size})"
    return path


def _monkeypatch(monkeypatch: Any, repairs: list[dict[str, Any]]) -> None:
    import holdspeak.services.concierge_service as cs

    detection = {
        "engines": ENGINES,
        "hardware": {"capability": {"apple_silicon": True, "system": "darwin",
                                    "architecture": "arm64", "ram_gb": 36}},
        "runtimes": [{"id": "mlx_whisper_v1", "state": "available"}],
        "checkedAt": "2026-09-06T09:41:00Z",
    }
    monkeypatch.setattr(cs, "detect", lambda **_: dict(detection))
    monkeypatch.setattr(cs, "propose", lambda **_: PROPOSAL)
    monkeypatch.setattr(cs, "repairs", lambda **_: [dict(r) for r in repairs])


@pytest.mark.parametrize("state", sorted(STATES))
@pytest.mark.parametrize("width", [1440, 393], ids=["desktop", "phone"])
def test_each_repair_state_is_drawn_with_one_verb(tmp_path, monkeypatch, state, width):
    _monkeypatch(monkeypatch, [STATES[state]])
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright

        height = 900 if width == 1440 else 852
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": height})
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed", token=TOKEN)
            _normal_chair(page)
            _open_concierge(page)
            page.get_by_test_id("concierge-root").wait_for(timeout=10_000)
            _settle(page)

            row = page.get_by_test_id(f"concierge-repair-{state}")
            row.wait_for(timeout=10_000)

            # The state names itself.
            assert STATES[state]["token"] in (row.text_content() or "")

            # ONE verb, and it is the library Button.
            verbs = page.get_by_test_id(f"concierge-repair-verb-{state}")
            assert verbs.count() == 1, f"{state}: {verbs.count()} verbs"
            assert "btn" in (verbs.first.get_attribute("class") or ""), (
                "every verb is the library Button"
            )

            # The section counts what is there, never zero.
            label = page.get_by_test_id("concierge-repairs-label")
            assert (label.text_content() or "").strip() == "NEEDS YOU 1"

            # No raw <button> anywhere in the face.
            root = page.get_by_test_id("concierge-root")
            raw = root.locator(
                "button:not(.btn):not(.surface-ledger-line):not(.gadget-chip-egress)"
            )
            assert raw.count() == 0, f"Raw <button>: {raw.count()}"

            # No prose: no sentence-length paragraph inside the repair row.
            longest = page.evaluate(
                """(id) => {
                  const row = document.querySelector(`[data-testid="${id}"]`);
                  if (!row) return 0;
                  let worst = 0;
                  for (const el of row.querySelectorAll("span,div,p")) {
                    if (el.children.length) continue;
                    worst = Math.max(worst, (el.textContent || "").trim().length);
                  }
                  return worst;
                }""",
                f"concierge-repair-{state}",
            )
            assert longest <= 40, f"{state}: a {longest}-character sentence on the row"

            # Nothing clipped out of its row.
            clipped = page.evaluate(
                """() => {
                  const chips = document.querySelectorAll(
                    '.concierge-repair-list .surface-state-chip'
                  );
                  for (const chip of chips) {
                    const row = chip.closest('.surface-ledger-row');
                    if (!row) continue;
                    const cr = chip.getBoundingClientRect();
                    const rr = row.getBoundingClientRect();
                    if (cr.right > rr.right - 4) return chip.textContent;
                  }
                  return null;
                }"""
            )
            assert clipped is None, f"State chip clipped: {clipped}"

            if width == 393:
                assert page.evaluate(
                    "document.documentElement.scrollWidth <= window.innerWidth"
                )

            _shot(page, state, width)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()
