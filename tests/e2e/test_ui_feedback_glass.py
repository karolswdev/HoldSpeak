"""The opt-in UI feedback capture on real Desk glass.

This is a T4 check because the feature's contract includes pointer ownership,
focus-free selection, an actual html-to-image PNG, fake-device microphone
capture, and the 393 px hit geometry of the feedback strip.  The hub, browser
menu, window, audio, screenshot and save route are all real; only Chromium's
microphone device is simulated.
"""
from __future__ import annotations

import base64
import json
import re
import shutil
import wave
from pathlib import Path
from typing import Any

import pytest

from tests._evidence import evidence_dir

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle, clear_hub_windows
from .type_floor_rig import _FAINT_JS, _MEASURE

pytest.importorskip("playwright.sync_api", reason="the UI feedback glass needs Playwright")

pytestmark = [pytest.mark.e2e]

TOKEN = "ui-feedback-glass"
SIZES = {1440: (1440, 900), 393: (393, 852)}
SHOTS = evidence_dir("ui-feedback")
T = 30_000
EMPTY_REFERENCE_ARTIFACT = "art-adr-empty-reference"
EMPTY_REFERENCE_SOURCE = "window-private-adr-reference"
USEFUL_REFERENCE_WINDOW = "pullout:artifact:art-cutover-reqs"


def _select_controls(page: Any) -> None:
    """Choose the retained Controls catalogue through its real selector."""
    page.get_by_test_id("design-reference").wait_for(timeout=T)
    direct = page.get_by_role("button", name="Controls", exact=True)
    if direct.count():
        direct.click()
    else:
        page.get_by_role("button", name=re.compile(r"^Patterns:")).click()
        page.locator("[role^='menuitem']").filter(has_text="Controls").first.click()
    page.get_by_test_id("reference-controls").wait_for(timeout=T)


def _feedback_menu_item(page: Any, width: int) -> Any:
    """Open the live Desk feedback verb (Go is the phone's Desk door)."""
    page.get_by_role("button",name="Help",exact=True).click()
    menu = page.get_by_role("menu",name="Help menu",exact=True)
    item = menu.get_by_role("menuitem",name="Give feedback",exact=True)
    item.wait_for(timeout=T)
    return item


def _start_feedback(page: Any, width: int, target: Any, *, again: bool = False) -> None:
    """Select one rendered control through the actual menu and pointer."""
    target.scroll_into_view_if_needed()
    if again:
        page.locator("[data-ui-feedback]").get_by_role("button", name="Done", exact=True).click()
        _feedback_menu_item(page,width).click()
    else:
        _feedback_menu_item(page, width).click()
    box = target.bounding_box()
    assert box, "the selected rendered control has no hit box"
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.locator("[data-ui-feedback]").get_by_role("button", name="Record", exact=True).click()
    page.locator("[data-ui-feedback]").get_by_role("meter", name="Audio level").wait_for(timeout=T)
    # Let Chromium's fake track deliver real frames before the hold is ended.
    page.wait_for_timeout(500)


def _strip_control_facts(page: Any, button: Any) -> dict[str, Any]:
    return button.evaluate(
        """el => {
          const r = el.getBoundingClientRect();
          const width = Math.max(44, r.width), height = Math.max(44, r.height);
          const left = r.left + (r.width - width) / 2;
          const top = r.top + (r.height - height) / 2;
          const xs = [left + 2, left + width / 2, left + width - 2];
          const ys = [top + 2, top + height / 2, top + height - 2];
          const hits = [];
          for (const y of ys) for (const x of xs) {
            const hit = document.elementFromPoint(x, y);
            hits.push(Boolean(hit && (hit === el || el.contains(hit))));
          }
          return {
            rect: {left: r.left, top: r.top, right: r.right, bottom: r.bottom,
                   width: r.width, height: r.height},
            target: {left, top, width, height, right: left + width, bottom: top + height},
            inViewport: left >= 0 && top >= 0 && left + width <= innerWidth && top + height <= innerHeight,
            hits,
            overflow: document.documentElement.scrollWidth > innerWidth
              || document.body.scrollWidth > innerWidth,
          };
        }"""
    )


def _assert_phone_strip(page: Any) -> None:
    for label in ("Stop", "Save", "Cancel"):
        facts = _strip_control_facts(page, page.locator("[data-ui-feedback]").get_by_role("button", name=label, exact=True))
        assert facts["target"]["width"] >= 44 and facts["target"]["height"] >= 44, facts
        assert facts["inViewport"], facts
        assert all(facts["hits"]), (label, facts)
        assert not facts["overflow"], facts


def _browser_png_facts(page: Any, path: Path) -> dict[str, int]:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return page.evaluate(
        """encoded => new Promise((resolve, reject) => {
          const image = new Image();
          image.onload = () => {
            const canvas = document.createElement("canvas");
            canvas.width = image.naturalWidth;
            canvas.height = image.naturalHeight;
            const context = canvas.getContext("2d");
            if (!context) { reject(new Error("canvas unavailable")); return; }
            context.drawImage(image, 0, 0);
            const pixels = context.getImageData(0, 0, canvas.width, canvas.height).data;
            const colors = new Set();
            const stride = Math.max(4, Math.floor(pixels.length / 400_000));
            for (let offset = 0; offset < pixels.length; offset += stride * 4) {
              colors.add(`${pixels[offset]},${pixels[offset + 1]},${pixels[offset + 2]}`);
              if (colors.size > 16) break;
            }
            resolve({width: image.naturalWidth, height: image.naturalHeight, colors: colors.size});
          };
          image.onerror = () => reject(new Error("PNG could not be decoded"));
          image.src = `data:image/png;base64,${encoded}`;
        })""",
        encoded,
    )


def _browser_png_region_facts(
    page: Any,
    path: Path,
    regions: dict[str, dict[str, float]],
    window_size: tuple[int, int],
) -> dict[str, dict[str, int]]:
    """Check that named source regions survive in the saved PNG pixels."""
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return page.evaluate(
        """async ({encoded, regions, windowSize}) => {
          const image = await new Promise((resolve, reject) => {
            const value = new Image();
            value.onload = () => resolve(value);
            value.onerror = () => reject(new Error("PNG could not be decoded"));
            value.src = `data:image/png;base64,${encoded}`;
          });
          const canvas = document.createElement("canvas");
          canvas.width = image.naturalWidth;
          canvas.height = image.naturalHeight;
          const context = canvas.getContext("2d");
          if (!context) throw new Error("canvas unavailable");
          context.drawImage(image, 0, 0);
          const pixels = context.getImageData(0, 0, canvas.width, canvas.height).data;
          const sx = canvas.width / windowSize[0];
          const sy = canvas.height / windowSize[1];
          const at = (x, y) => {
            const offset = (y * canvas.width + x) * 4;
            return [pixels[offset], pixels[offset + 1], pixels[offset + 2], pixels[offset + 3]];
          };
          const background = at(0, 0);
          const result = {};
          for (const [name, region] of Object.entries(regions)) {
            const left = Math.max(0, Math.floor(region.x * sx));
            const top = Math.max(0, Math.floor(region.y * sy));
            const right = Math.min(canvas.width, Math.ceil((region.x + region.width) * sx));
            const bottom = Math.min(canvas.height, Math.ceil((region.y + region.height) * sy));
            const colors = new Set();
            let pixelsSeen = 0;
            let changed = 0;
            for (let y = top; y < bottom; y++) for (let x = left; x < right; x++) {
              const pixel = at(x, y);
              colors.add(`${pixel[0]},${pixel[1]},${pixel[2]},${pixel[3]}`);
              pixelsSeen++;
              if (Math.abs(pixel[0] - background[0])
                  + Math.abs(pixel[1] - background[1])
                  + Math.abs(pixel[2] - background[2]) > 18) changed++;
            }
            result[name] = {pixels: pixelsSeen, changed, colors: colors.size};
          }
          return result;
        }""",
        {"encoded": encoded, "regions": regions, "windowSize": list(window_size)},
    )


def _read_saved_report(
    page: Any,
    directory: str,
    *,
    window_id: str,
    draft: str | None,
    window_size: tuple[int, int],
    shot_stem: str,
    png_regions: dict[str, dict[str, float]] | None = None,
) -> dict[str, Any]:
    root = Path(directory)
    assert root.is_dir() and ".local/share/holdspeak/feedback" in str(root), root
    for filename in ("report.json", "audio.wav", "window.png", "README.md"):
        assert (root / filename).is_file(), (root, filename)

    report = json.loads((root / "report.json").read_text(encoding="utf-8"))
    context = report["context"]
    assert context["owner"]["window_id"] == window_id, context["owner"]
    assert context["selected_element"]["sensitive"] is False, context["selected_element"]
    if draft is not None:
        fields = context["fields"]
        assert any(field.get("label") == "Gallery text" and field.get("value") == draft for field in fields), fields

    with wave.open(str(root / "audio.wav"), "rb") as audio:
        assert audio.getnchannels() == 1
        assert audio.getframerate() == 16_000
        assert audio.getsampwidth() == 2
        assert audio.getnframes() > 0
        assert audio.getnframes() / audio.getframerate() >= 0.1

    png = _browser_png_facts(page, root / "window.png")
    assert png["width"] > 120 and png["height"] > 120, png
    assert abs(png["width"] - window_size[0]) <= 8, (png, window_size)
    assert abs(png["height"] - window_size[1]) <= 8, (png, window_size)
    assert png["colors"] > 4, "the saved window image is blank or flat"
    if png_regions:
        region_facts = _browser_png_region_facts(page, root / "window.png", png_regions, window_size)
        for name, facts in region_facts.items():
            assert facts["pixels"] > 20 and facts["changed"] > 20 and facts["colors"] > 2, (name, facts)
    shutil.copy2(root / "window.png", SHOTS / f"{shot_stem}-{window_id}-window.png")

    return report


def _save_feedback(
    page: Any,
    width: int,
    *,
    shot_stem: str,
    window_id: str,
    draft: str | None,
    global_stop: bool = False,
    png_regions: dict[str, Any] | None = None,
) -> dict[str, Any]:
    stop = page.get_by_test_id("desk-mic-lamp-stop") if global_stop else page.locator("[data-ui-feedback]").get_by_role("button", name="Stop", exact=True)
    page.screenshot(path=str(SHOTS / f"{shot_stem}-{width}-recording.png"))
    metrics = page.evaluate(_MEASURE, page.evaluate(_FAINT_JS))
    for key in ("small", "contrast"):
        faults = [row for row in metrics[key] if "hs-feedback-strip" in row["path"]]
        assert not faults, (key, faults)
    if width == 393:
        _assert_phone_strip(page)

    window = page.locator(f"[id='{window_id}'][data-layer='window']")
    root_box = window.bounding_box()
    assert root_box, "the owning window has no hit box before capture"
    region_boxes: dict[str, dict[str, float]] = {}
    for name, locator in (png_regions or {}).items():
        box = locator.bounding_box()
        assert box, f"the PNG source region {name!r} has no hit box"
        region_boxes[name] = {
            "x": box["x"] - root_box["x"],
            "y": box["y"] - root_box["y"],
            "width": box["width"],
            "height": box["height"],
        }

    with page.expect_response(
        lambda response: response.url.endswith("/api/ui-feedback")
        and response.request.method == "POST"
    ) as saved:
        stop.click()
        page.locator("[data-ui-feedback]").get_by_role("button",name="Save",exact=True).click()
    response = saved.value
    assert response.status == 200, response.text()
    payload = response.json()
    assert payload["success"] is True, payload
    page.locator("[data-ui-feedback]").get_by_text("Saved.", exact=True).wait_for(timeout=T)
    page.screenshot(path=str(SHOTS / f"{shot_stem}-{width}-saved.png"))
    window = page.locator(f"[id='{window_id}'][data-layer='window']")
    box = window.bounding_box()
    assert box, "the owning window disappeared before the saved report was read"
    return _read_saved_report(
        page,
        payload["directory"],
        window_id=window_id,
        draft=draft,
        window_size=(round(box["width"]), round(box["height"])),
        shot_stem=f"{shot_stem}-{width}",
        png_regions=region_boxes or None,
    )


@pytest.fixture(params=[1440, 393], ids=["desktop", "phone"])
def feedback_page(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest):
    from playwright.sync_api import sync_playwright

    width = int(request.param)
    monkeypatch.setenv("HOLDSPEAK_UI_FEEDBACK", "1")
    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                headless=True,
                args=["--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream"],
            )
            context = browser.new_context(
                viewport={"width": width, "height": SIZES[width][1]},
                device_scale_factor=1,
                has_touch=width < 720,
                is_mobile=width < 720,
                reduced_motion="reduce",
                permissions=["microphone"],
            )
            page = context.new_page()
            page.set_default_timeout(T)
            page.goto(f"{base}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            assert _api(page, "GET", "/api/ui-feedback/status", token=TOKEN) == {"enabled": True, "transcription_egress": []}
            clear_hub_windows(page, TOKEN)
            _api(page, "POST", "/api/desk/windows/surface-components/open", {}, token=TOKEN)
            page.reload(wait_until="load")
            _normal_chair(page)
            window = page.locator("[id='surface-components'][data-layer='window']")
            window.wait_for(timeout=T)
            _settle(page)
            _select_controls(page)
            _settle(page)
            yield page, width, window
            browser.close()
    finally:
        server.stop()


@pytest.fixture(params=[1440, 393], ids=["desktop", "phone"])
def artifact_reference_page(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest):
    """Real artifact paper, Send rows, and feedback capture in one hub."""
    from holdspeak.db import get_database
    from playwright.sync_api import sync_playwright

    from .test_send_glass import _seed

    width = int(request.param)
    monkeypatch.setenv("HOLDSPEAK_UI_FEEDBACK", "1")
    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    db = get_database()
    _seed(db)
    db.plugins.record_artifact(
        artifact_id=EMPTY_REFERENCE_ARTIFACT,
        meeting_id="m-standup",
        artifact_type="adr",
        title="ADR Drafter",
        body_markdown="# ADR Drafter\n\nadr_drafter: no architectural decisions found.\n",
        status="accepted",
        plugin_id="adr_drafter",
        confidence=1.0,
        sources=[{"source_type": "workbench", "source_ref": EMPTY_REFERENCE_SOURCE}],
    )
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                headless=True,
                args=["--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream"],
            )
            context = browser.new_context(
                viewport={"width": width, "height": SIZES[width][1]},
                device_scale_factor=1,
                has_touch=width < 720,
                is_mobile=width < 720,
                reduced_motion="reduce",
                permissions=["microphone"],
            )
            page = context.new_page()
            page.set_default_timeout(T)
            page.goto(f"{base}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            folder = tmp_path / "Team updates"
            folder.mkdir()
            made = _api(
                page,
                "POST",
                "/api/channels/destinations",
                {"name": "Team updates", "channel": "file", "folder": str(folder)},
                token=TOKEN,
            )
            assert made["destination"]["channel"] == "file", made
            clear_hub_windows(page, TOKEN)
            page.goto(
                f"{base}/?token={TOKEN}&open=artifact:{EMPTY_REFERENCE_ARTIFACT}",
                wait_until="load",
            )
            _normal_chair(page)
            yield page, base, width
            browser.close()
    finally:
        server.stop()


def test_real_feedback_selection_capture_and_second_report(feedback_page: Any) -> None:
    page, width, window = feedback_page
    draft = "unsaved glass feedback draft"
    text_box = window.get_by_role("textbox", name="Gallery text")
    text_box.fill(draft)
    target = window.get_by_role("checkbox", name="Gallery boolean")
    before = target.is_checked()
    window_id = str(window.get_attribute("id"))

    _start_feedback(page, width, target)
    assert target.is_checked() is before, "feedback selection activated the selected control"
    first = _save_feedback(page, width, shot_stem="feedback", window_id=window_id, draft=draft)

    # A second report starts through the saved strip, without reloading the desk.
    target = window.get_by_role("checkbox", name="Gallery boolean")
    before = target.is_checked()
    _start_feedback(page, width, target, again=True)
    assert target.is_checked() is before, "second selection activated the selected control"
    second = _save_feedback(page, width, shot_stem="feedback-second", window_id=window_id, draft=draft, global_stop=True)

    assert first["id"] != second["id"], (first["id"], second["id"])
    assert first["context"]["owner"]["window_id"] == second["context"]["owner"]["window_id"] == window_id


def test_window_feedback_button_records_its_window_without_picking(feedback_page: Any) -> None:
    page, width, window = feedback_page
    draft = "unsaved window button feedback draft"
    window.get_by_role("textbox", name="Gallery text").fill(draft)
    window_id = str(window.get_attribute("id"))
    button = window.get_by_role("button", name="Give feedback on Components", exact=True)
    button.wait_for(timeout=T)
    page.screenshot(path=str(SHOTS / f"feedback-button-{width}.png"))
    if width == 393:
        facts = _strip_control_facts(page, button)
        assert facts["rect"]["width"] >= 44 and facts["rect"]["height"] >= 44, facts
        assert facts["inViewport"] and all(facts["hits"]), facts

    button.click()
    strip = page.locator("[data-ui-feedback]")
    strip.get_by_role("button",name="Record",exact=True).click()
    strip.get_by_role("meter", name="Audio level").wait_for(timeout=T)
    assert strip.get_by_text("Select a part", exact=True).count() == 0
    page.wait_for_timeout(500)
    report = _save_feedback(page, width, shot_stem="feedback-direct", window_id=window_id, draft=draft)
    assert report["context"]["selected_element"]["id"] == window_id


def test_reference_artifact_feedback_png(artifact_reference_page: Any) -> None:
    """The empty ADR result and useful Send artifact keep their real window identity."""
    page, base, width = artifact_reference_page
    empty_id = f"pullout:artifact:{EMPTY_REFERENCE_ARTIFACT}"
    empty = page.locator(f"[id='{empty_id}'][data-layer='window']")
    empty.wait_for(timeout=T)
    _settle(page)
    assert empty.get_by_text("No architecture decisions found", exact=True).is_visible()
    assert empty.locator("[data-testid=send-well]").count() == 0
    empty.locator(".artifact-sources-fold > summary").click()
    unresolved = empty.locator("[data-testid=artifact-source-unresolved]")
    unresolved.wait_for(timeout=T)
    assert EMPTY_REFERENCE_SOURCE in unresolved.inner_text()
    page.screenshot(path=str(SHOTS / f"artifact-reference-empty-{width}.png"))

    # Reuse the same private hub and browser. The useful artifact is a real
    # producer row, and its FILE destination is local-only; no send is pressed.
    clear_hub_windows(page, TOKEN)
    page.goto(
        f"{base}/?token={TOKEN}&open=artifact:art-cutover-reqs",
        wait_until="load",
    )
    _normal_chair(page)
    window_id = USEFUL_REFERENCE_WINDOW
    window = page.locator(f"[id='{window_id}'][data-layer='window']")
    window.wait_for(timeout=T)
    _settle(page)
    paper = window.locator(".artifact-reading .surface-well")
    paper.wait_for(timeout=T)
    assert "Freeze the old ledger on Nov 5." in paper.inner_text()

    # W4-PHONE (2026-10-27): the toolbar's Send… opens the one Send sheet
    # in place of the words (the reader grammar).
    window.locator("[data-testid=artifact-send]").click()
    send = window.locator("[data-testid=send-well]")
    send.wait_for(timeout=T)
    rows = send.locator("[data-testid=destination-row]")
    rows.nth(1).wait_for(timeout=T)
    assert rows.count() >= 2, "the reference artifact needs the built-in and local FILE destinations"
    assert rows.nth(1).locator("[data-destination]").first.get_attribute("data-destination") == "Team updates"
    # The kept destination moves to the head of the list after selection.
    # Follow its identity through that render, rather than its old position.
    second = send.locator("[data-testid=destination-row]:has([data-destination='Team updates'])")
    second.locator(".send-destination-chip").click()
    preview = second.locator("[data-testid=send-preview]")
    preview.wait_for(timeout=T)
    assert second.get_attribute("data-open") == "true"
    preview.scroll_into_view_if_needed()
    assert preview.is_visible()
    assert "Freeze the old ledger on Nov 5." in preview.inner_text()
    controls = second.locator(".send-destination-chip")
    assert controls.is_visible()
    # The selected destination must survive the host Button cascade, and the
    # preview must use the same reading material as the artifact itself.
    page.wait_for_function(
        """el => {
            const probe = document.createElement('span');
            probe.hidden = true;
            probe.style.color = 'var(--wb-blue)';
            document.body.append(probe);
            const expected = getComputedStyle(probe).color;
            const actual = getComputedStyle(el).backgroundColor;
            probe.remove();
            return actual === expected;
        }""",
        arg=controls.element_handle(),
        timeout=T,
    )
    facts = controls.evaluate("""el => {
        const probe = document.createElement('span');
        probe.hidden = true;
        probe.style.color = 'var(--wb-blue)';
        document.body.append(probe);
        const expected = getComputedStyle(probe).color;
        const actual = getComputedStyle(el).backgroundColor;
        probe.remove();
        return {actual, expected};
    }""")
    assert facts["actual"] == facts["expected"], facts
    # The preview is the document on the window's paper: no frame of its own.
    assert second.locator(".send-open").evaluate(
        "el => getComputedStyle(el).backgroundColor"
    ) == "rgba(0, 0, 0, 0)"
    # Send is the sheet's toolbar verb; with no receipt yet the status line
    # folds away, and it is never a second deep window foot.
    assert send.locator("[data-testid=send-sheet-header] [data-testid=send-verb]").is_visible()
    action_frame = window.locator(".surface-footer:has([data-send=actions])")
    if action_frame.count() and action_frame.first.is_visible():
        assert action_frame.first.bounding_box()["height"] <= 72, "Send must not add a second deep window foot"

    feedback_button = window.get_by_role(
        "button", name="Give feedback on Cutover requirements", exact=True
    )
    feedback_button.wait_for(timeout=T)
    feedback_button.click()
    page.locator("[data-ui-feedback]").get_by_role("button",name="Record",exact=True).click()
    page.locator("[data-ui-feedback]").get_by_role("meter", name="Audio level").wait_for(timeout=T)
    page.wait_for_timeout(500)
    report = _save_feedback(
        page,
        width,
        shot_stem="artifact-reference-send",
        window_id=window_id,
        draft=None,
        png_regions={"send_controls": controls, "send_preview": preview},
    )
    assert report["context"]["selected_element"]["id"] == window_id


def test_capture_note_states_with_typed_words(feedback_page: Any) -> None:
    """The same capture supports speech or text, stays in its owner and retries."""
    from playwright.sync_api import expect
    from .test_desk_sweep import _GUIDE_FENCES_JS
    page,width,window=feedback_page
    shots=Path(__file__).resolve().parents[2]/'.tmp/evidence-shots/showme4'
    shots.mkdir(parents=True,exist_ok=True)
    if width==1440:
        _api(page,'POST','/api/desk/windows/surface-components/set_geometry',{'rect':{'x':'-1/2 + 100','y':'-1/2 + 80','w':'900px','h':'600px'}},token=TOKEN)
        _settle(page)
    from holdspeak.db import get_database
    from tests.unit._speech_door import assign_profile
    db=get_database()
    db.profiles.upsert(profile_id="feedback-speech",name="Lab speech",kind="openAICompatible",base_url="http://192.168.1.99:8080/v1",model="whisper")
    assign_profile(db,"speech.transcribe","feedback-speech")
    seat=900 if width==1440 else width
    _feedback_menu_item(page,width).click()
    target=window.get_by_role('checkbox',name='Gallery boolean')
    target.click()
    capture=page.locator('[data-ui-feedback]')
    capture.get_by_role('button',name='Record',exact=True).wait_for(timeout=T)
    def shot(state: str) -> None:
        from .test_guide_seat_glass import _seat_facts
        _seat_facts(page, 'surface-components')
        # Every ring edge and all capture controls belong to this window.
        assert not page.evaluate(_GUIDE_FENCES_JS,'surface-components'),page.evaluate(_GUIDE_FENCES_JS,'surface-components')
        if state == 'recording':
            expect(capture.get_by_text('Lab speech',exact=True)).to_be_visible()
            page.screenshot(path=str(shots/f'feedback-{state}-{seat}.png'))
    shot('idle')
    capture.get_by_role('button',name='Record',exact=True).click()
    capture.get_by_role('meter',name='Audio level').wait_for(timeout=T)
    expect(capture.get_by_role('status')).to_contain_text('Recording 0:')
    page.wait_for_function("() => Number(document.querySelector('[data-ui-feedback] [role=meter]')?.getAttribute('aria-valuenow')) > 0", timeout=T)
    page.wait_for_function("() => /Recording 0:0[1-9]/.test(document.querySelector('[data-ui-feedback] [role=status]')?.textContent||'')", timeout=T)
    shot('recording')
    capture.get_by_role('button',name='Stop',exact=True).click()
    capture.get_by_role('button',name='Cancel',exact=True).click()
    _feedback_menu_item(page,width).click()
    target.click()
    field=capture.get_by_role('textbox',name='Feedback words')
    field.fill('The actions touch on this window.')
    shot('typed')
    def failed(route: Any) -> None:
        route.fulfill(status=503,json={'detail':'Feedback not saved. Your words are kept. Retry Save.'})
    page.route('**/api/ui-feedback',failed)
    capture.get_by_role('button',name='Save',exact=True).click()
    expect(capture.locator('[role=alert]')).to_be_visible()
    expect(field).to_have_value('The actions touch on this window.')
    shot('failed')
    page.unroute('**/api/ui-feedback',failed)
    # Hold the request at the browser boundary for a shot of the real saving state.
    held=[]
    def hold(route: Any) -> None:held.append(route)
    page.route('**/api/ui-feedback',hold)
    capture.get_by_role('button',name='Save',exact=True).click()
    capture.get_by_text('Saving',exact=True).wait_for(timeout=T)
    shot('saving')
    assert held
    with page.expect_response(lambda response:response.url.endswith('/api/ui-feedback') and response.request.method=='POST') as result:
        held[0].continue_()
    payload=result.value.json()
    assert payload['success'] and payload['transcript_status']=='complete',payload
    capture.get_by_text('Saved.',exact=True).wait_for(timeout=T)
    shot('saved')
    directory=Path(payload['directory'])
    report=json.loads((directory/'report.json').read_text())
    assert report['words']=='The actions touch on this window.'
    assert not (directory/'audio.wav').exists()
    assert (directory/'transcript.txt').read_text()==report['words']


def test_guide_feedback_keeps_the_seen_note_in_one_bundle(feedback_page: Any) -> None:
    from playwright.sync_api import expect
    from .test_desk_sweep import _start_app_walk, _finish_app_walk, _GUIDE_FENCES_JS
    page,width,_window=feedback_page
    _api(page,'POST','/api/decision-records/from-desk',{'title':'Adopt tracing for every service','status':'proposed','why':'Use one collector.'},token=TOKEN)
    clear_hub_windows(page,TOKEN)
    _api(page,'POST','/api/desk/windows/surface-decisions/open',{},token=TOKEN)
    if width==1440:
        _api(page,'POST','/api/desk/windows/surface-decisions/set_geometry',{'rect':{'x':'-1/2 + 100','y':'-1/2 + 80','w':'900px','h':'600px'}},token=TOKEN)
    page.reload(wait_until='load');_normal_chair(page);_settle(page)
    window=page.locator('#surface-decisions')
    window.get_by_test_id('decisions-row').wait_for(timeout=T)
    _start_app_walk(page)
    note=page.get_by_test_id('guide-note')
    step=1
    if width==393:
        note.get_by_test_id('walk-next').click()
        step=2
    expect(note.get_by_test_id('walk-count')).to_have_text(f'{step} of 3')
    writes=[]
    page.on('request',lambda req:writes.append(req.url) if req.method=='POST' else None)
    caption=note.get_by_test_id('walk-caption').inner_text()
    win_box=window.bounding_box();note_box=note.bounding_box();ring_box=page.get_by_test_id('guide-ring').bounding_box()
    assert win_box and note_box and ring_box
    note.get_by_role('button',name='Say what is off').click()
    field=note.get_by_role('textbox',name='Feedback words')
    field.fill('The action needs more space.')
    assert not page.evaluate(_GUIDE_FENCES_JS,'surface-decisions')
    with page.expect_response(lambda response:response.url.endswith('/api/ui-feedback') and response.request.method=='POST') as response:
        note.get_by_role('button',name='Save',exact=True).click()
    saved=response.value.json();directory=Path(saved['directory'])
    expect(note.get_by_test_id('walk-count')).to_have_text('Saved.')
    shots=Path(__file__).resolve().parents[2]/'.tmp/evidence-shots/showme3'
    shots.mkdir(parents=True,exist_ok=True)
    page.screenshot(path=str(shots/f'feedback-guide-saved-{900 if width==1440 else width}.png'))
    expect(note.get_by_test_id('walk-caption')).to_have_text(caption)
    assert writes and all(url.endswith('/api/ui-feedback') for url in writes),writes
    report=json.loads((directory/'report.json').read_text())
    assert report['context']['guide']=={'app':'Decisions','step':step,'of':3,'target':json.loads((Path(__file__).resolve().parents[2]/'web/src/desk/walks/decisions.walk.json').read_text())['steps'][step-1]['highlight']['target'],'words':caption}
    assert caption in report['context']['owner']['window_text']
    assert report['words']=='The action needs more space.'
    assert not (directory/'audio.wav').exists()
    regions={name:{'x':box['x']-win_box['x'],'y':box['y']-win_box['y'],'width':box['width'],'height':box['height']} for name,box in [('note',note_box),('ring',ring_box)]}
    facts=_browser_png_region_facts(page,directory/'window.png',regions,(round(win_box['width']),round(win_box['height'])))
    assert all(value['colors']>4 and value['changed']>20 for value in facts.values()),facts
    shots=Path(__file__).resolve().parents[2]/'.tmp/evidence-shots/showme3'
    shutil.copy2(directory/'window.png',shots/f'feedback-guide-window-{900 if width==1440 else width}.png')
    _finish_app_walk(page)


def test_recorded_feedback_names_its_destination_inline_and_the_ring_hugs_the_checkbox(feedback_page: Any) -> None:
    from playwright.sync_api import expect
    from holdspeak.db import get_database
    from tests.unit._speech_door import assign_profile
    page, width, window = feedback_page
    # This is a real configured but inert engine. The rig cancels the audio;
    # no transcription or external request is made.
    db = get_database()
    db.profiles.upsert(profile_id='feedback-speech', name='Lab speech', kind='openAICompatible', base_url='http://192.168.1.99:8080/v1', model='whisper')
    assign_profile(db, 'speech.transcribe', 'feedback-speech')
    if width == 1440:
        from .test_ui_feedback_glass import TOKEN as FEEDBACK_TOKEN
        _api(page, 'POST', '/api/desk/windows/surface-components/set_geometry', {'rect': {'x':'-1/2 + 100','y':'-1/2 + 80','w':'900px','h':'600px'}}, token=FEEDBACK_TOKEN)
        from .test_desk_sweep import SETTLED_JS
        page.wait_for_function(SETTLED_JS, arg='surface-components', timeout=T)
    target = window.get_by_role('checkbox', name='Gallery boolean')
    target.scroll_into_view_if_needed()
    _feedback_menu_item(page, width).click()
    target.click()
    capture = page.locator('[data-ui-feedback]')
    capture.get_by_role('button', name='Record', exact=True).wait_for(timeout=T)
    expect(capture.get_by_text('Audio goes to')).to_have_count(0)
    capture.get_by_role('button', name='Record', exact=True).click()
    capture.get_by_role('meter', name='Audio level').wait_for(timeout=T)
    chip = capture.get_by_text('Lab speech', exact=True)
    expect(chip).to_be_visible()
    expect(capture.get_by_text('Audio goes to', exact=True)).to_be_visible()
    assert chip.evaluate('(e) => e.getBoundingClientRect().width < e.parentElement.getBoundingClientRect().width / 2')
    page.wait_for_function("() => Number(document.querySelector('[data-ui-feedback] [role=meter]')?.getAttribute('aria-valuenow')) > 0", timeout=T)
    from .test_guide_seat_glass import _seat_shot
    # Recording has the same bound when the words well has reached four lines.
    field = capture.get_by_role('textbox', name='Feedback words')
    field.fill('One.\nTwo.\nThree.\nFour.')
    page.wait_for_function('el => el.offsetHeight > 60', arg=field.element_handle(), timeout=T)
    from .test_guide_seat_glass import _seat_facts
    _seat_facts(page, 'surface-components')
    field.fill('')
    _seat_shot(page, 'surface-components', f'capture-audio-{900 if width == 1440 else width}')
    capture.get_by_role('button', name='Stop', exact=True).click()
    expect(chip).to_be_visible()
    if width == 393:
        facts = page.get_by_test_id('guide-ring').evaluate('''ring => {
          const box=ring.getBoundingClientRect(), well=document.querySelector('input[aria-label="Gallery boolean"]').closest('.gadget-check').querySelector('.gadget-check-well').getBoundingClientRect();
          return {ring:box.toJSON(),well:well.toJSON()};
        }''')
        assert abs(facts['ring']['width']-facts['well']['width']) <= 1, facts
        assert abs(facts['ring']['height']-facts['well']['height']) <= 1, facts
        page.screenshot(path=str(evidence_dir('guide5') / 'feedback-ring-393.png'))
    capture.get_by_role('button', name='Cancel', exact=True).click()
    expect(page.get_by_test_id('guide-note')).to_have_count(0)
