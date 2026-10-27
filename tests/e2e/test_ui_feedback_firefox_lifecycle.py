"""Loaded Settings feedback lifecycle on isolated Firefox glass.

The browser captures real window pixels and fake-device microphone frames.  The
server's existing admitted speech callback is replaced only in this local hub;
no configured external provider is contacted by this test.
"""
from __future__ import annotations

import hashlib
import json
import threading
import time
import wave
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
import numpy as np

from holdspeak.principals import PrincipalKind
from holdspeak.speech_session import SpeechSessionRefused
from tests._evidence import evidence_dir
from .glass_infra import _api, _boot, _ensure_build, _normal_chair, clear_hub_windows
from .test_ui_feedback_glass import _browser_png_facts


TOKEN = "feedback-firefox-lifecycle"


def _feedback_name(width: int) -> str:
    """The title-bar Feedback verb names what the window shows: on the phone
    the title bar names the open Settings pane (#1458), here You."""
    return "Give feedback on Settings" if width >= 720 else "Give feedback on You"
SHOTS = evidence_dir("ui-feedback-firefox-lifecycle")


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _bundle_facts(page: Any, directory: Path, draft: str) -> dict[str, Any]:
    report = json.loads((directory / "report.json").read_text(encoding="utf-8"))
    context = report["context"]
    assert context["owner"]["window_id"] == "surface-settings"
    assert any(field.get("label") == "Your name" and field.get("value") == draft
               for field in context["fields"])
    wav = directory / "audio.wav"
    png = directory / "window.png"
    with wave.open(str(wav), "rb") as audio:
        assert audio.getnchannels() == 1
        assert audio.getsampwidth() == 2
        assert audio.getframerate() == 16_000
        assert audio.getnframes() >= 1600
    png_facts = _browser_png_facts(page, png)
    assert png_facts["colors"] > 8
    window_box = page.locator("[id='surface-settings'][data-layer='window']").bounding_box()
    assert window_box
    pixel_ratio = page.evaluate("Math.min(window.devicePixelRatio || 1, 2)")
    assert abs(png_facts["width"] - window_box["width"] * pixel_ratio) <= 8
    assert abs(png_facts["height"] - window_box["height"] * pixel_ratio) <= 8
    return {
        "id": report["id"],
        "captured_at": report["captured_at"],
        "context_sha256": _digest(json.dumps(context, sort_keys=True).encode()),
        "wav_sha256": _digest(wav.read_bytes()),
        "png_sha256": _digest(png.read_bytes()),
        "png_size": [png_facts["width"], png_facts["height"]],
        "pixel_ratio": pixel_ratio,
        "transcript_status": report["transcript"]["status"],
        "egress_boundary": report["transcript"].get("egress_boundary"),
    }


def _decoded_audio_digest(directory: Path) -> str:
    with wave.open(str(directory / "audio.wav"), "rb") as audio:
        frames = audio.readframes(audio.getnframes())
    decoded = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
    return _digest(decoded.tobytes())


def _capture_ready(page: Any, window: Any, width: int, attempt: int,
                   observations: list[dict[str, Any]]) -> Any:
    page.evaluate("window.__feedbackBeat = {last: performance.now(), max: 0}")
    started = time.monotonic()
    window.get_by_role("button", name=_feedback_name(width), exact=True).click()
    strip = page.locator("[data-ui-feedback]")
    strip.get_by_text("Recording", exact=True).wait_for()
    capture_ms = round((time.monotonic() - started) * 1000)
    heartbeat_gap_ms = page.evaluate("window.__feedbackBeat.max")
    assert capture_ms < 3000, (width, attempt, capture_ms)
    assert heartbeat_gap_ms < 1000, (width, attempt, heartbeat_gap_ms)
    observations.append({"attempt": attempt, "capture_ms": capture_ms,
                         "heartbeat_gap_ms": heartbeat_gap_ms})
    page.screenshot(path=str(SHOTS / f"settings-{width}-{attempt}-recording.png"))
    # Firefox's fake mic must deliver enough real frames for the WAV check.
    page.wait_for_timeout(1200)
    return strip


def _save(page: Any, strip: Any) -> tuple[dict[str, Any], Path]:
    with page.expect_response(
        lambda response: response.url.endswith("/api/ui-feedback")
        and response.request.method == "POST"
    ) as saved:
        strip.get_by_role("button", name="Stop and save", exact=True).click()
    response = saved.value
    assert response.status == 200, response.text()
    receipt = response.json()
    assert receipt["success"] is True
    return receipt, Path(receipt["directory"])


@pytest.mark.slow
@pytest.mark.parametrize("width", [1440, 393])
def test_loaded_settings_cancel_retry_generation_and_return(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int
) -> None:
    from playwright.sync_api import sync_playwright
    import holdspeak.web_server as web_server

    monkeypatch.setenv("HOLDSPEAK_UI_FEEDBACK", "1")
    _ensure_build()
    calls: list[dict[str, Any]] = []
    closes: list[str] = []
    call_lock = threading.Lock()

    def admitted(audio: Any, *, principal: Any, mic_handle: str, verbatim: bool) -> Any:
        assert principal.kind is PrincipalKind.OWNER
        assert mic_handle == ""
        assert verbatim is True
        assert len(audio) >= 1600
        with call_lock:
            calls.append({"audio_sha256": _digest(audio.tobytes()), "principal": principal.kind.value})
            ordinal = len(calls)
        if ordinal == 1:
            raise SpeechSessionRefused("binding_not_ready")

        def close(outcome: str) -> None:
            with call_lock:
                closes.append(outcome)

        return SimpleNamespace(
            text=f"Isolated feedback transcript {ordinal}",
            provider=SimpleNamespace(egress_boundary="local"),
            close=close,
        )

    original_callbacks = web_server.WebRuntimeCallbacks
    monkeypatch.setattr(
        web_server, "WebRuntimeCallbacks",
        lambda **kwargs: original_callbacks(**kwargs, on_transcribe_admitted=admitted),
    )
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    try:
        with sync_playwright() as pw:
            browser = pw.firefox.launch(headless=True, firefox_user_prefs={
                "media.navigator.streams.fake": True,
                "media.navigator.permission.disabled": True,
                "media.autoplay.default": 0,
                "media.autoplay.block-webaudio": False,
            })
            try:
                page = browser.new_page(
                    viewport={"width": width, "height": 900 if width == 1440 else 852},
                    device_scale_factor=2,
                    reduced_motion="reduce",
                )
                page.set_default_timeout(20_000)
                page.add_init_script("""(() => {
                  window.__feedbackBeat = {last: performance.now(), max: 0};
                  setInterval(() => {
                    const now = performance.now(), beat = window.__feedbackBeat;
                    beat.max = Math.max(beat.max, now - beat.last); beat.last = now;
                  }, 25);
                })()""")
                requests: list[str] = []
                page.on("request", lambda request: requests.append(request.url)
                        if request.method == "POST" and "/api/ui-feedback" in request.url else None)
                page.goto(f"{base}/?token={TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
                assert _api(page, "GET", "/api/ui-feedback/status", token=TOKEN) == {"enabled": True}
                clear_hub_windows(page, TOKEN)
                _api(page, "POST", "/api/desk/windows/surface-settings/open", {}, token=TOKEN)
                page.reload(wait_until="load")
                _normal_chair(page)
                window = page.locator("[id='surface-settings'][data-layer='window']")
                name = window.get_by_role("textbox", name="Your name", exact=True)
                if width < 720:
                    # Settings on the phone opens on its rail (#1458, the native
                    # preference window); the You pane holds the name field.
                    window.get_by_test_id("settings-index-you").click()
                name.wait_for()
                window.locator("[data-settings-section='this-mac']").wait_for(state="attached")
                initial_box = window.bounding_box()
                assert initial_box
                page.evaluate("""() => {
                  const media = navigator.mediaDevices;
                  const original = media?.getUserMedia;
                  if (typeof original !== 'function') throw new Error('getUserMedia unavailable');
                  window.__feedbackMicRequests = 0;
                  Object.defineProperty(media, 'getUserMedia', {
                    configurable: true,
                    value: (...args) => {
                      window.__feedbackMicRequests += 1;
                      return original.apply(media, args);
                    },
                  });
                }""")
                mic_before_cancel = page.evaluate("window.__feedbackMicRequests")
                assert mic_before_cancel == 0

                # FontFaceSet.ready is an awaited browser platform seam in the
                # actual PNG capture. Hold it only after Settings has loaded.
                page.evaluate("""() => {
                  const fonts = document.fonts;
                  const original = Object.getOwnPropertyDescriptor(fonts, 'ready');
                  let release;
                  const held = new Promise(resolve => { release = resolve; });
                  Object.defineProperty(fonts, 'ready', {configurable: true, get: () => held});
                  window.__releaseFeedbackFonts = () => {
                    if (original) Object.defineProperty(fonts, 'ready', original);
                    else delete fonts.ready;
                    release(fonts);
                  };
                }""")
                window.get_by_role("button", name=_feedback_name(width), exact=True).click()
                strip = page.locator("[data-ui-feedback]")
                strip.get_by_text("Capturing", exact=True).wait_for()
                page.wait_for_function("() => !!document.querySelector('body > div[style*=\"-100000px\"]')")
                mic_during_capture = page.evaluate("window.__feedbackMicRequests")
                assert mic_during_capture == 0
                strip.get_by_role("button", name="Cancel", exact=True).click()
                page.wait_for_function("() => !document.querySelector('body > div[style*=\"-100000px\"]')")
                mic_after_cancel = page.evaluate("window.__feedbackMicRequests")
                assert mic_after_cancel == 0
                page.evaluate("async () => { window.__releaseFeedbackFonts(); await Promise.resolve(); await Promise.resolve(); }")
                mic_after_release = page.evaluate("window.__feedbackMicRequests")
                assert mic_after_release == 0
                assert strip.count() == 0
                cancelled_save_requests = sum(url.endswith("/api/ui-feedback") for url in requests)
                cancelled_wrapper_count = page.locator("body > div[style*='-100000px']").count()
                assert cancelled_save_requests == 0
                assert cancelled_wrapper_count == 0

                observations: list[dict[str, Any]] = []
                bundles: list[tuple[Path, dict[str, Any]]] = []
                draft_one = "Isolated Settings report one"
                name.fill(draft_one)
                strip = _capture_ready(page, window, width, 1, observations)
                mic_before_retry = page.evaluate("window.__feedbackMicRequests")
                assert mic_before_retry > 0, "Recording did not request the real fake-device stream"
                receipt_one, directory_one = _save(page, strip)
                assert receipt_one["transcript_status"] == "pending"
                strip.get_by_role("button", name="Retry transcription", exact=True).wait_for()
                before_retry = _bundle_facts(page, directory_one, draft_one)
                assert before_retry["transcript_status"] == "failed"
                posts_before_retry = sum(url.endswith("/api/ui-feedback") for url in requests)
                with page.expect_response(lambda response: response.url.endswith(
                    f"/api/ui-feedback/{receipt_one['id']}/transcribe"
                )) as retried:
                    strip.get_by_role("button", name="Retry transcription", exact=True).click()
                assert retried.value.json()["transcript_status"] == "complete"
                strip.get_by_text("Saved", exact=True).wait_for()
                after_retry = _bundle_facts(page, directory_one, draft_one)
                for key in ("id", "captured_at", "context_sha256", "wav_sha256", "png_sha256"):
                    assert after_retry[key] == before_retry[key], key
                assert after_retry["egress_boundary"] == "local"
                mic_after_retry = page.evaluate("window.__feedbackMicRequests")
                assert mic_after_retry == mic_before_retry, "ASR-only retry recaptured microphone audio"
                assert sum(url.endswith("/api/ui-feedback") for url in requests) == posts_before_retry
                assert len([url for url in requests if "/transcribe" in url]) == 2
                assert calls[0]["audio_sha256"] == calls[1]["audio_sha256"] == _decoded_audio_digest(directory_one)
                bundles.append((directory_one, after_retry))
                page.screenshot(path=str(SHOTS / f"settings-{width}-1-saved.png"))

                held_routes: list[Any] = []
                def hold_one_transcription(route: Any) -> None:
                    if not held_routes:
                        held_routes.append(route)
                    else:
                        route.continue_()
                page.route("**/api/ui-feedback/*/transcribe", hold_one_transcription)
                draft_two = "Isolated Settings report two"
                name.fill(draft_two)
                strip = _capture_ready(page, window, width, 2, observations)
                receipt_two, directory_two = _save(page, strip)
                strip.get_by_text("Transcribing", exact=True).wait_for()
                assert held_routes, "Second report's transcription was not held"
                facts_two = _bundle_facts(page, directory_two, draft_two)
                assert facts_two["transcript_status"] == "pending"
                bundles.append((directory_two, facts_two))

                # The direct window verb is available while old ASR is pending.
                # It starts a newer generation without cancelling server work.
                draft_three = "Isolated Settings report three"
                name.fill(draft_three)
                strip = _capture_ready(page, window, width, 3, observations)
                receipt_three, directory_three = _save(page, strip)
                strip.get_by_text("Saved", exact=True).wait_for()
                facts_three = _bundle_facts(page, directory_three, draft_three)
                assert facts_three["transcript_status"] == "complete"
                assert facts_three["egress_boundary"] == "local"
                bundles.append((directory_three, facts_three))

                # Observe Copy path through an in-page stub; never touch the
                # machine clipboard. It exposes which saved bundle owns strip.
                page.evaluate("""() => {
                  Object.defineProperty(navigator, 'clipboard', {
                    configurable: true, value: {writeText: async value => { window.__feedbackCopiedPath = value; }}
                  });
                }""")
                strip.get_by_role("button", name="Copy path", exact=True).click()
                assert page.evaluate("window.__feedbackCopiedPath") == str(directory_three)
                with page.expect_response(lambda response: response.url.endswith(
                    f"/api/ui-feedback/{receipt_two['id']}/transcribe"
                )) as old_transcription:
                    held_routes.pop().continue_()
                assert old_transcription.value.json()["transcript_status"] == "complete"
                page.evaluate("""async () => {
                  await new Promise(requestAnimationFrame);
                  await new Promise(requestAnimationFrame);
                }""")
                strip.get_by_role("button", name="Copy path", exact=True).click()
                assert page.evaluate("window.__feedbackCopiedPath") == str(directory_three)
                completed_two = _bundle_facts(page, directory_two, draft_two)
                assert completed_two["transcript_status"] == "complete"
                for key in ("id", "captured_at", "context_sha256", "wav_sha256", "png_sha256"):
                    assert completed_two[key] == facts_two[key], key
                assert _bundle_facts(page, directory_three, draft_three) == facts_three
                assert len({facts["id"] for _, facts in bundles}) == 3
                assert sum(url.endswith("/api/ui-feedback") for url in requests) == 3
                assert len([url for url in requests if "/transcribe" in url]) == 4
                assert len(calls) == 4
                assert calls[2]["audio_sha256"] == _decoded_audio_digest(directory_three)
                assert calls[3]["audio_sha256"] == _decoded_audio_digest(directory_two)
                assert closes == ["succeeded"] * 3
                assert page.locator("body > div[style*='-100000px']").count() == 0
                page.screenshot(path=str(SHOTS / f"settings-{width}-3-saved.png"))

                strip.get_by_role("button", name="Done", exact=True).click()
                assert strip.count() == 0
                assert window.is_visible()
                name.fill("Isolated Settings return")
                if width < 720:
                    # The phone shows one pane at a time (#1458): the title
                    # bar's Back returns to the rail between panes.
                    window.get_by_test_id("settings-back").click()
                window.get_by_test_id("settings-index-speak").click()
                if width < 720:
                    window.get_by_test_id("settings-back").click()
                window.get_by_test_id("settings-index-you").click()
                assert name.input_value() == "Isolated Settings return"
                return_box = window.bounding_box()
                assert return_box
                page.screenshot(path=str(SHOTS / f"settings-{width}-returned.png"))
                (SHOTS / f"settings-{width}-facts.json").write_text(json.dumps({
                    "viewport_width": width,
                    "settings_box_before": initial_box,
                    "settings_box_after_return": return_box,
                    "cancelled_capture": {
                        "mic_requests_before": mic_before_cancel,
                        "mic_requests_during": mic_during_capture,
                        "mic_requests_after_cancel": mic_after_cancel,
                        "mic_requests_after_late_release": mic_after_release,
                        "recording_started": mic_after_release > 0,
                        "save_requests": cancelled_save_requests,
                        "wrapper_remaining": cancelled_wrapper_count,
                    },
                    "mic_requests_before_asr_retry": mic_before_retry,
                    "mic_requests_after_asr_retry": mic_after_retry,
                    "mic_requests_total": page.evaluate("window.__feedbackMicRequests"),
                    "captures": observations,
                    "first_before_asr_retry": before_retry,
                    "bundles": [facts for _, facts in bundles],
                    "second_after_delayed_asr": completed_two,
                    "save_posts": sum(url.endswith("/api/ui-feedback") for url in requests),
                    "transcribe_posts": len([url for url in requests if "/transcribe" in url]),
                    "admitted_calls": len(calls),
                    "admitted_closes": closes,
                    "current_strip_bundle_after_old_reply": str(directory_three.name),
                }, indent=2) + "\n", encoding="utf-8")
            finally:
                browser.close()
    finally:
        server.stop()
