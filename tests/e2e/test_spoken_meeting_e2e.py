"""HS-27-02 — spoken-meeting end-to-end harness (opt-in).

A *real* end-to-end on real endpoints — no mocks:

    say (multi-voice) -> per-line wav -> Whisper (Transcriber) -> transcript
    segments -> PluginHost (real .43 LLM, deferred queue drained) ->
    synthesize_and_persist -> temp SQLite DB (meeting + transcript + artifacts)
    -> MeetingWebServer -> Playwright drives /history -> screenshots the
    transcript, the rendered mermaid SVG, and the action-item checklist.

It is **opt-in** and excluded from the default sweep: it requires
`HOLDSPEAK_SPOKEN_E2E=1` *and* every external piece to be present (macOS `say`,
faster-whisper, a reachable intel endpoint, Playwright+Chromium). Any missing
piece skips the test cleanly rather than failing.

Run it:

    HOLDSPEAK_SPOKEN_E2E=1 uv run pytest -q -m spoken_e2e -s

Assertions are **structural** (the real LLM is non-deterministic): the meeting
has a transcript, a `diagram` artifact with a parseable mermaid block renders an
`<svg>`, and an `action_items` artifact renders a checklist. Exact wording is
never asserted.
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
from datetime import datetime
from types import SimpleNamespace
from urllib.parse import urlparse

import pytest

pytestmark = [pytest.mark.spoken_e2e, pytest.mark.slow]

if not os.environ.get("HOLDSPEAK_SPOKEN_E2E"):
    pytest.skip(
        "opt-in: set HOLDSPEAK_SPOKEN_E2E=1 to run the spoken-meeting e2e",
        allow_module_level=True,
    )

# The spoken e2e is a living demo; its screenshot lands in the active plugin
# phase's evidence dir (Phase 28 — it now exercises the Phase-28 plugins too).
EVIDENCE_DIR = "pm/roadmap/holdspeak/phase-28-plugin-rollout-ii/evidence"

# A *natural* product conversation — nobody reads out a requirements list. The
# need is implied, clarified back and forth, and decisions/owners emerge in
# passing. The plugins have to infer the rest:
#   - the spoken architecture (inbox → classifier → dashboard + store) → mermaid_architecture
#   - "fast", "works on phones", "ship this quarter" → requirements_extractor
#   - "start with a status page, not email" → decision_capture (+ open questions)
#   - "I'll sketch the ingestion this week", "someone needs to confirm…" → action_owner_enforcer
SCRIPT: list[tuple[str, str, str]] = [
    ("Priya", "Samantha",
     "So the thing customers keep complaining about is that after they send us "
     "feedback, they never hear anything back. It just disappears into a black "
     "hole. I'd really love for us to close that loop somehow."),
    ("Alex", "Alex",
     "Okay. When you say close the loop, do you mean we email them back, or more "
     "like a place where they can check what happened to it?"),
    ("Priya", "Samantha",
     "Honestly both eventually, but let's start with somewhere they can see the "
     "status. Their feedback comes in through the support inbox today, and it "
     "would be great if it just got sorted automatically so the right team picks "
     "it up."),
    ("Alex", "Alex",
     "Got it. So we'd pull from the support inbox, run it through some kind of "
     "classifier to tag it, and then surface everything on a dashboard the teams "
     "watch. We'll need somewhere to keep all of it as well. One thing I'd push "
     "on though, it has to feel instant. Nobody refreshes a slow page, so the "
     "dashboard really needs to come up in under a second."),
    ("Dana", "Daniel",
     "Agreed on speed. And it has to work on phones, half the team only ever "
     "checks this from their mobile. Can we get something rough in front of real "
     "users by the end of the month? We did say we'd ship a first cut this "
     "quarter no matter what."),
    ("Alex", "Alex",
     "That's doable. I'll sketch out the ingestion piece this week. We still "
     "haven't figured out who owns the classifier model, that's not decided yet. "
     "And someone needs to confirm we're even allowed to store the raw feedback "
     "text, that might be a privacy question."),
]


def _skip_unless(condition: bool, reason: str) -> None:
    if not condition:
        pytest.skip(reason)


def _endpoint_reachable() -> tuple[bool, str]:
    from holdspeak.config import Config

    base = Config.load().meeting.intel_cloud_base_url or ""
    parsed = urlparse(base)
    host, port = parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80)
    if not host:
        return False, "no intel_cloud_base_url configured"
    try:
        with socket.create_connection((host, port), timeout=2.0):
            return True, base
    except OSError as exc:
        return False, f"intel endpoint {base} unreachable: {exc}"


def _say_to_wav(line: str, voice: str, out_path) -> None:
    subprocess.run(
        ["say", "-v", voice, "--data-format=LEI16@16000", "-o", str(out_path), line],
        check=True,
    )


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_spoken_meeting_end_to_end(tmp_path):
    # --- prerequisites (skip cleanly if any are missing) -------------------
    _skip_unless(shutil.which("say") is not None, "macOS `say` not available")
    wavfile = pytest.importorskip("scipy.io.wavfile", reason="scipy required")
    np = pytest.importorskip("numpy")
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        pytest.skip("playwright not installed (uv pip install playwright && playwright install chromium)")
    reachable, detail = _endpoint_reachable()
    _skip_unless(reachable, detail)

    from holdspeak.db import get_database, reset_database
    from holdspeak.meeting_session import MeetingState, TranscriptSegment
    from holdspeak.plugins.builtin import register_builtin_plugins
    from holdspeak.plugins.host import PluginHost
    from holdspeak.plugins.synthesis import synthesize_and_persist
    from holdspeak.transcribe import Transcriber
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    # --- 1. say -> per-line wav -> 2. Whisper -> transcript segments -------
    transcriber = Transcriber(model_name="base")
    segments: list[TranscriptSegment] = []
    cursor = 0.0
    for idx, (label, voice, line) in enumerate(SCRIPT):
        wav_path = tmp_path / f"line_{idx}.wav"
        _say_to_wav(line, voice, wav_path)
        sr, audio = wavfile.read(wav_path)
        if audio.dtype == np.int16:
            audio = audio.astype(np.float32) / 32768.0
        duration = len(audio) / sr
        text = transcriber.transcribe(audio.astype("float32")).strip()
        segments.append(
            TranscriptSegment(text=text, speaker=label, start_time=cursor, end_time=cursor + duration)
        )
        cursor += duration
    transcript = " ".join(seg.text for seg in segments).strip()
    assert len(transcript) > 60, f"transcript too short: {transcript!r}"
    print(f"\n[e2e] transcript: {transcript}")

    # --- 3. real plugin chain (deferred queue drained, real .43 LLM) -------
    host = PluginHost(default_timeout_seconds=30.0, enabled_capabilities={"llm"})
    register_builtin_plugins(host)
    meeting_id = "e2e-spoken"
    context = {
        "transcript": transcript,
        "project_name": "Customer Feedback Loop",
        "active_intents": ["architecture", "delivery", "product"],
    }
    for window, plugin_id in enumerate(
        (
            "mermaid_architecture", "action_owner_enforcer", "decision_capture",
            "requirements_extractor", "adr_drafter", "milestone_planner",
        )
    ):
        host.execute(
            plugin_id,
            context=context,
            meeting_id=meeting_id,
            window_id=f"{meeting_id}:w{window}",
            transcript_hash=f"h{window}",
        )
    results = []
    while True:
        result = host.process_next_deferred_run(timeout_seconds=30.0)
        if result is None:
            break
        results.append(result)
    by_id = {r.plugin_id: r for r in results}
    for pid in (
        "mermaid_architecture", "action_owner_enforcer", "decision_capture",
        "requirements_extractor", "adr_drafter", "milestone_planner",
    ):
        assert by_id[pid].status == "success", by_id[pid].error
    # The plugins must have produced real content (not their failure shape).
    assert by_id["mermaid_architecture"].output.get("mermaid"), "no mermaid block produced"
    assert by_id["action_owner_enforcer"].output.get("action_items"), "no action items produced"
    decision_out = by_id["decision_capture"].output
    assert decision_out.get("decisions") or decision_out.get("open_questions"), "no decisions produced"
    assert by_id["requirements_extractor"].output.get("requirements"), "no requirements produced"
    assert by_id["adr_drafter"].output.get("adrs"), "no ADRs produced"
    assert by_id["milestone_planner"].output.get("milestones"), "no milestones produced"

    # --- 4. persist meeting + transcript + artifacts into a temp DB --------
    reset_database()
    db = get_database(tmp_path / "e2e.db")
    db.save_meeting(
        MeetingState(
            id=meeting_id,
            started_at=datetime.now(),  # naive — matches the codebase duration math
            title="Customer Feedback Loop — Kickoff",
            segments=segments,
        )
    )
    runs = [
        SimpleNamespace(
            id=f"run-{i}", meeting_id=meeting_id, window_id=f"{meeting_id}:w{i}",
            plugin_id=r.plugin_id, plugin_version=r.plugin_version, status="success",
            output=r.output, created_at=f"2026-06-01T12:0{i}:00",
        )
        for i, r in enumerate(results)
    ]
    drafts, _ = synthesize_and_persist(db, meeting_id, plugin_runs=runs)
    by_type = {d.artifact_type: d for d in drafts}
    assert by_type.get("diagram") and by_type["diagram"].structured_json.get("mermaid")
    assert by_type.get("action_items") and by_type["action_items"].structured_json.get("action_items")
    decisions_sj = by_type.get("decisions") and by_type["decisions"].structured_json
    assert decisions_sj and (decisions_sj.get("decisions") or decisions_sj.get("open_questions"))
    assert by_type.get("requirements") and by_type["requirements"].structured_json.get("requirements")
    assert by_type.get("adr") and by_type["adr"].structured_json.get("adrs")
    assert by_type.get("milestone_plan") and by_type["milestone_plan"].structured_json.get("milestones")
    print(f"[e2e] artifacts: {sorted(by_type)}")

    # --- 5. serve + 6. Playwright screenshot -------------------------------
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *a, **k: {},
            on_stop=lambda *a, **k: {},
            get_state=lambda: {"id": meeting_id, "meeting_active": False},
        ),
        host="127.0.0.1",
        port=_free_port(),
    )
    url = server.start()
    try:
        os.makedirs(EVIDENCE_DIR, exist_ok=True)
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 1500})
            page.goto(f"{url}/history", wait_until="networkidle")
            page.locator("button.meeting-card").first.click()
            page.wait_for_selector(".mermaid-artifact svg", timeout=15000)
            page.wait_for_selector(".action-item-list .action-item", timeout=15000)
            page.wait_for_selector(".decisions-artifact .decision-list li", timeout=15000)
            page.wait_for_selector(".requirement-list .requirement-item", timeout=15000)
            page.wait_for_selector(".adr-artifact .adr-record", timeout=15000)
            page.wait_for_selector(".milestone-artifact .milestone-record", timeout=15000)
            # transcript panel populated from the persisted segments
            page.wait_for_selector(".transcript-list .segment", timeout=15000)
            # The meeting-detail modal is a fixed overlay that scrolls internally
            # (`.modal-body` overflow-y:auto), so a plain full_page screenshot
            # caps at the fold. Grow the viewport to the modal's content height so
            # everything (transcript + all five artifacts) fits on one screen,
            # then screenshot the viewport.
            content_height = page.evaluate(
                "() => { const b = document.querySelector('.modal-body');"
                " return b ? Math.ceil(b.scrollHeight) : 1400; }"
            )
            page.set_viewport_size({"width": 1280, "height": min(int(content_height) + 220, 8000)})
            page.wait_for_timeout(400)  # let the modal reflow to the taller viewport
            shot = os.path.join(EVIDENCE_DIR, "spoken_meeting_artifacts.png")
            page.screenshot(path=shot)
            assert page.locator(".mermaid-artifact svg").count() >= 1
            assert page.locator(".action-item-list .action-item").count() >= 1
            assert page.locator(".decisions-artifact .decision-list li").count() >= 1
            assert page.locator(".requirement-list .requirement-item").count() >= 1
            assert page.locator(".adr-artifact .adr-record").count() >= 1
            assert page.locator(".milestone-artifact .milestone-record").count() >= 1
            browser.close()
        print(f"[e2e] screenshot saved: {shot}")
    finally:
        server.stop()
        reset_database()
