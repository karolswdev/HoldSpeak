"""Story 142 isolated-HOME two-width glass for projected AI capability truth."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("playwright.sync_api", reason="AI setup glass needs Playwright")
pytest.importorskip("fastapi.testclient", reason="AI setup glass needs web dependencies")

TOKEN = "hs141-models-setup-glass"


def _api(page: Any, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    result = page.evaluate(
        """async ([method, path, body]) => {
          const response = await fetch(path, {
            method,
            headers: {
              authorization: 'Bearer hs141-models-setup-glass',
              ...(body ? {'content-type': 'application/json'} : {}),
            },
            body: body ? JSON.stringify(body) : undefined,
          });
          return {status: response.status, payload: await response.json()};
        }""",
        [method, path, body],
    )
    assert result["status"] < 300, result
    return result["payload"]


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_models_setup_is_projected_truth_with_one_action_seat(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    from playwright.sync_api import sync_playwright
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    import holdspeak.services.inference_acquisition_service as acquisition_module
    import holdspeak.services.inference_setup_service as setup_module
    from holdspeak.db import reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    home = tmp_path / "home"
    home.mkdir()
    existing_model = home / "Models" / "gguf" / "Qwen3-4B-Existing-Q6_K.gguf"
    existing_model.parent.mkdir(parents=True)
    existing_model.write_bytes(b"GGUF" + b"glass-existing-model")
    browser_cache = Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH", Path.home() / "Library/Caches/ms-playwright"))
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(browser_cache))
    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
    original_package_revision = setup_module._package_revision
    monkeypatch.setattr(
        setup_module,
        "_package_revision",
        lambda distribution, fallback: "0.3.34"
        if distribution == "llama-cpp-python"
        else original_package_revision(distribution, fallback),
    )
    original_runtime_version = acquisition_module.importlib.metadata.version
    monkeypatch.setattr(
        acquisition_module.importlib.metadata,
        "version",
        lambda distribution: "0.3.34"
        if distribution == "llama-cpp-python"
        else original_runtime_version(distribution),
    )
    reset_database()

    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=lambda *_: None, on_stop=lambda: None, get_state=lambda: {}),
        auth_token=TOKEN,
    )
    url = server.start()
    errors: list[str] = []
    console_errors: list[str] = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"})
            page.goto(f"{url}/profiles", wait_until="load")

            heading = page.get_by_role("heading", name="Choose your AI", exact=True)
            heading.wait_for(timeout=10000)
            setup = page.locator(".models-setup")
            projection = _api(page, "GET", "/api/inference/setup")["setup"]
            assert setup.get_by_text("This device", exact=True).first.is_visible()
            assert setup.get_by_text("Choose AI for each job", exact=True).is_visible()
            assert setup.get_by_text("Runs on", exact=True).count() == 0
            assert setup.get_by_role("heading", name="Choose an experience", exact=True).is_visible()
            assert setup.get_by_text(projection["current_thought_deployment"]["target"]["name"], exact=True).first.is_visible()
            body = setup.inner_text()
            for forbidden in ["Ready to configure", "Recommended", str(home), "/Users/"]:
                assert forbidden not in body
            surface_body = page.locator(".desk-settings-window .desk-surface-body")
            if width == 393:
                assert surface_body.evaluate("element => element.scrollTop") == 0
                heading_box = heading.bounding_box()
                body_box = surface_body.bounding_box()
                assert heading_box and body_box
                assert heading_box["y"] >= max(0, body_box["y"])
                assert heading_box["y"] + heading_box["height"] <= min(
                    900, body_box["y"] + body_box["height"]
                )
            page.screenshot(path=f"/tmp/holdspeak-inference-setup-{width}.png", full_page=False)

            hosted = [row for row in projection["presets"] if row["kind"] == "hosted_profile_preset"]
            catalog = projection["presets"]
            detected = projection["detected_local_artifacts"]
            choices = [*detected, *catalog]
            radios = setup.get_by_role("radiogroup", name="AI choices").get_by_role("radio")
            assert radios.count() == len(choices)
            if choices:
                expected = next(
                    (row for row in hosted if row["existing_profile"]["target_id"] == projection["current_routes"]["thoughts"]["target_id"]),
                    choices[0],
                )
                expected_radio = setup.locator(f'input[type="radio"][value="{expected["id"]}"]')
                assert expected_radio.is_checked()
                if len(choices) > 1:
                    expected_index = choices.index(expected)
                    next_row = choices[(expected_index + 1) % len(choices)]
                    expected_radio.focus()
                    expected_radio.press("ArrowRight")
                    assert setup.locator(
                        f'input[type="radio"][value="{next_row["id"]}"]'
                    ).is_checked()
                    assert (
                        _api(page, "GET", "/api/settings")["thoughts"][
                            "inference_target_id"
                        ]
                        == projection["current_routes"]["thoughts"]["target_id"]
                    )

            detection = projection["artifact_detection"]["state"]
            if not projection["detected_local_artifacts"]:
                if detection == "complete":
                    assert setup.get_by_text("No local AI detected", exact=True).is_visible()
                else:
                    assert setup.get_by_text(f"Local AI inspection {'incomplete' if detection == 'partial' else 'unavailable'}", exact=True).is_visible()

            primary = setup.locator(".models-capability-action button")
            assert primary.count() <= 1
            if width == 1440:
                seat_box = setup.locator(".models-capability-action").bounding_box()
                body_box = surface_body.bounding_box()
                selected_box = setup.locator(".models-capability-card[data-selected]").bounding_box()
                assert seat_box and body_box and selected_box
                assert selected_box["y"] >= body_box["y"]
                assert seat_box["y"] + seat_box["height"] <= body_box["y"] + body_box["height"]
            connections = setup.get_by_text("AI connections", exact=True).locator("xpath=ancestor::details")
            assert connections.get_attribute("open") is None

            assert detected and detected[0]["activation"]["action"] == "use_existing"
            setup.locator(f'input[type="radio"][value="{detected[0]["id"]}"]').click()
            setup.get_by_role("button", name="USE THIS MODEL", exact=True).click()
            setup.get_by_text("Ready · in use for Thoughts", exact=True).wait_for(timeout=10000)
            used = _api(page, "GET", "/api/inference/setup")["setup"]
            acquisition = next(row for row in used["acquisitions"] if row["preset_id"] == detected[0]["id"])
            assert acquisition["state"] == "ready"
            assert acquisition["activation_state"] == "in_use"
            assert str(home) not in str(used)
            assert setup.locator(".models-capability-action button").count() == 0

            if hosted:
                chosen = hosted[-1]
                radio = setup.locator(f'input[type="radio"][value="{chosen["id"]}"]')
                radio.click()
                key = setup.get_by_label("OpenRouter key")
                key.fill("glass-only-openrouter-key")
                action = setup.get_by_role("button", name=f"ADD & USE {chosen['experience'].upper()}", exact=True)
                action.click()
                page.wait_for_timeout(1200)
                assert key.count() == 0 or key.input_value() == "", setup.inner_text()
                config = _api(page, "GET", "/api/settings")
                assert config["thoughts"]["inference_target_id"] == chosen["existing_profile"]["target_id"]
                setup.get_by_text("IN USE FOR THOUGHTS", exact=True).wait_for(timeout=10000)
                targets = _api(page, "GET", "/api/inference-targets")["targets"]
                selected = next(row for row in targets if row["id"] == chosen["existing_profile"]["target_id"])
                assert selected["model"] == chosen["existing_profile"]["model"]
                assert selected["secret"] == {"required": True, "present": True}
                assert "glass-only-openrouter-key" not in str(targets)
                assert setup.get_by_text("IN USE FOR THOUGHTS", exact=True).is_visible()
                assert setup.locator(".models-capability-action button").count() == 0
                page.screenshot(path=f"/tmp/holdspeak-inference-setup-configured-{width}.png", full_page=False)

            setup.get_by_text("AI connections", exact=True).click()
            assert connections.get_attribute("open") is not None
            assert setup.get_by_text("Define any OpenAI-compatible provider, private endpoint, paired device, or mesh node here.", exact=True).is_visible()
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            if width == 393:
                for index in range(radios.count()):
                    box = radios.nth(index).locator("xpath=ancestor::label").bounding_box()
                    assert box and box["height"] >= 44
                summary_box = setup.get_by_text("AI connections", exact=True).locator("xpath=ancestor::summary").bounding_box()
                assert summary_box and summary_box["height"] >= 44
            page.screenshot(path=f"/tmp/holdspeak-inference-setup-connections-{width}.png", full_page=False)
            assert errors == []
            assert console_errors == []
            browser.close()
    finally:
        server.stop()
