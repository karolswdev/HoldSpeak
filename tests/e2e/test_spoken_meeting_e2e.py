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
            "risk_heatmap", "dependency_mapper", "scope_guard",
            "customer_signal_extractor",
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
        "risk_heatmap", "dependency_mapper", "scope_guard",
        "customer_signal_extractor",
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
    assert by_id["risk_heatmap"].output.get("risks"), "no risks produced"
    assert by_id["dependency_mapper"].output.get("dependencies"), "no dependencies produced"
    assert by_id["scope_guard"].output.get("findings"), "no scope findings produced"
    assert by_id["customer_signal_extractor"].output.get("signals"), "no customer signals produced"

    # --- 4. persist meeting + transcript + artifacts into a temp DB --------
    reset_database()
    db = get_database(tmp_path / "e2e.db")
    db.meetings.save_meeting(
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
    assert by_type.get("risk_register") and by_type["risk_register"].structured_json.get("risks")
    assert by_type.get("dependency_map") and by_type["dependency_map"].structured_json.get("dependencies")
    assert by_type.get("scope_review") and by_type["scope_review"].structured_json.get("findings")
    assert by_type.get("customer_signals") and by_type["customer_signals"].structured_json.get("signals")
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
            page.wait_for_selector(".risk-table tbody tr", timeout=15000)
            page.wait_for_selector(".dependency-list li", timeout=15000)
            page.wait_for_selector(".scope-list .scope-finding", timeout=15000)
            page.wait_for_selector(".signal-list .signal-item", timeout=15000)
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
            assert page.locator(".risk-table tbody tr").count() >= 1
            assert page.locator(".dependency-list li").count() >= 1
            assert page.locator(".scope-list .scope-finding").count() >= 1
            assert page.locator(".signal-list .signal-item").count() >= 1
            browser.close()
        print(f"[e2e] screenshot saved: {shot}")
    finally:
        server.stop()
        reset_database()


# HS-35-04: a second spoken scenario that exercises the **incident** + **comms**
# plugin chains (the existing scenario covers balanced/architecture/delivery/
# product but never the incident or comms profiles). The script is a short
# incident postmortem — detection, impact, timeline, root cause, a runbook
# change, a risk, a stakeholder note, and a decision to announce — so the
# plugins have material to infer:
#   - chronological events                            → incident_timeline
#   - added/modified runbook steps                    → runbook_delta
#   - cross-cutting risks                             → risk_heatmap
#   - a shareable headline + highlights/risks/next   → stakeholder_update_drafter
#   - decisions to announce, with audience            → decision_announcement_drafter
INCIDENT_EVIDENCE_DIR = "pm/roadmap/holdspeak/phase-35-plugin-frontier/evidence"

INCIDENT_SCRIPT: list[tuple[str, str, str]] = [
    ("Priya", "Samantha",
     "Okay, let's walk through last Tuesday. Checkout was hard down for "
     "thirty eight minutes between two fifteen and two fifty three in the "
     "afternoon. Pager went off at two seventeen after the synthetic check "
     "from the edge probe failed three times in a row."),
    ("Alex", "Alex",
     "Right, and the trigger was the two oh five deploy of the payments "
     "service. It exhausted the database connection pool almost immediately, "
     "so every checkout request piled up waiting for a connection and timed "
     "out. We rolled back at two forty one and the error rate dropped to "
     "normal about ninety seconds later."),
    ("Dana", "Daniel",
     "So the root cause is really that we shipped a change that doubled the "
     "per request connection count without resizing the pool. The runbook "
     "today tells you to roll back, but it doesn't tell you to capture pool "
     "metrics first, which is why we wasted ten minutes guessing. I want to "
     "add a step before the rollback that dumps pool saturation to the "
     "incident channel."),
    ("Alex", "Alex",
     "Agreed. And the bigger risk is that holiday traffic is two weeks out "
     "and the queue capacity is sized for normal load, so a repeat under "
     "peak would be much worse. We should treat that as a high priority "
     "risk this week."),
    ("Priya", "Samantha",
     "Decision then. We're switching the payments service to canary deploys "
     "starting next Monday, no more full rollouts. I'll send a note to the "
     "engineering leadership channel today summarizing the impact, the "
     "rollback time, and the canary decision so everyone hears it from us "
     "first."),
]


def test_spoken_incident_retro_end_to_end(tmp_path):
    """HS-35-04 — incident-retro spoken e2e (incident + comms chains).

    Mirrors `test_spoken_meeting_end_to_end` but exercises a different chain:
    `incident_timeline`, `runbook_delta`, `risk_heatmap`,
    `stakeholder_update_drafter`, `decision_announcement_drafter`.
    """
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
    for idx, (label, voice, line) in enumerate(INCIDENT_SCRIPT):
        wav_path = tmp_path / f"incident_line_{idx}.wav"
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
    print(f"\n[e2e:incident] transcript: {transcript}")

    # --- 3. real incident + comms plugin chain -----------------------------
    host = PluginHost(default_timeout_seconds=30.0, enabled_capabilities={"llm"})
    register_builtin_plugins(host)
    meeting_id = "e2e-spoken-incident"
    context = {
        "transcript": transcript,
        "project_name": "Checkout Payments Incident",
        "active_intents": ["incident", "comms"],
    }
    incident_chain = (
        "incident_timeline",
        "runbook_delta",
        "risk_heatmap",
        "stakeholder_update_drafter",
        "decision_announcement_drafter",
    )
    for window, plugin_id in enumerate(incident_chain):
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
    for pid in incident_chain:
        assert by_id[pid].status == "success", by_id[pid].error
    assert by_id["incident_timeline"].output.get("events"), "no incident events produced"
    assert by_id["runbook_delta"].output.get("changes"), "no runbook changes produced"
    assert by_id["risk_heatmap"].output.get("risks"), "no risks produced"
    update = by_id["stakeholder_update_drafter"].output.get("update")
    assert update and (update.get("headline") or update.get("highlights")), "no stakeholder update produced"
    assert by_id["decision_announcement_drafter"].output.get("announcements"), "no announcements produced"

    # --- 4. persist meeting + transcript + artifacts into a temp DB --------
    reset_database()
    db = get_database(tmp_path / "e2e_incident.db")
    db.meetings.save_meeting(
        MeetingState(
            id=meeting_id,
            started_at=datetime.now(),
            title="Checkout Payments — Incident Retro",
            segments=segments,
        )
    )
    runs = [
        SimpleNamespace(
            id=f"run-{i}", meeting_id=meeting_id, window_id=f"{meeting_id}:w{i}",
            plugin_id=r.plugin_id, plugin_version=r.plugin_version, status="success",
            output=r.output, created_at=f"2026-06-03T14:0{i}:00",
        )
        for i, r in enumerate(results)
    ]
    drafts, _ = synthesize_and_persist(db, meeting_id, plugin_runs=runs)
    by_type = {d.artifact_type: d for d in drafts}
    assert by_type.get("incident_timeline") and by_type["incident_timeline"].structured_json.get("events")
    assert by_type.get("runbook_delta") and by_type["runbook_delta"].structured_json.get("changes")
    assert by_type.get("risk_register") and by_type["risk_register"].structured_json.get("risks")
    su = by_type.get("stakeholder_update") and by_type["stakeholder_update"].structured_json.get("update")
    assert su and (su.get("headline") or su.get("highlights"))
    assert by_type.get("decision_announcement") and by_type["decision_announcement"].structured_json.get("announcements")
    print(f"[e2e:incident] artifacts: {sorted(by_type)}")

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
        os.makedirs(INCIDENT_EVIDENCE_DIR, exist_ok=True)
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 1500})
            page.goto(f"{url}/history", wait_until="networkidle")
            page.locator("button.meeting-card").first.click()
            page.wait_for_selector(".incident-timeline li", timeout=15000)
            page.wait_for_selector(".runbook-list .runbook-change", timeout=15000)
            page.wait_for_selector(".risk-table tbody tr", timeout=15000)
            page.wait_for_selector(".stakeholder-update", timeout=15000)
            page.wait_for_selector(".announcement-artifact .announcement", timeout=15000)
            page.wait_for_selector(".transcript-list .segment", timeout=15000)
            content_height = page.evaluate(
                "() => { const b = document.querySelector('.modal-body');"
                " return b ? Math.ceil(b.scrollHeight) : 1400; }"
            )
            page.set_viewport_size({"width": 1280, "height": min(int(content_height) + 220, 8000)})
            page.wait_for_timeout(400)
            shot = os.path.join(INCIDENT_EVIDENCE_DIR, "spoken_incident_artifacts.png")
            page.screenshot(path=shot)
            assert page.locator(".incident-timeline li").count() >= 1
            assert page.locator(".runbook-list .runbook-change").count() >= 1
            assert page.locator(".risk-table tbody tr").count() >= 1
            assert page.locator(".stakeholder-update").count() >= 1
            assert page.locator(".announcement-artifact .announcement").count() >= 1
            browser.close()
        print(f"[e2e:incident] screenshot saved: {shot}")
    finally:
        server.stop()
        reset_database()


# HS-36-04: a third spoken scenario — a long, *messy*, human-sounding meeting that
# drifts across many topics with digressions, small talk, interruptions, and callbacks.
# Unlike the two scenarios above (which execute a hardcoded chain over the whole
# transcript), this one drives the **real MIR routing path**
# (`process_meeting_state`: build_intent_windows -> score -> select_active_intents ->
# dispatch per window). That's the point: only the real routing exhibits the
# dilution weakness this phase (Phase 36) is about — a brief-but-clear intent buried
# in a 90s window of chatter is diluted below the 0.6 threshold and silently dropped.
#
# This story (HS-36-04) captures the **BEFORE** baseline (current routing). HS-36-05
# implements segment-aware per-segment intent probing and captures the **AFTER** on the
# same script; the before/after is the phase's headline deliverable.
#
# Assertions are deliberately LOOSE/noise-tolerant (>=1 artifact, no fatal error, no
# exact-type/wording pins): the job here is to *expose* what the old routing drops, not
# to assert richness (that's HS-36-05's bar).
DYNAMIC_EVIDENCE_DIR = (
    "pm/roadmap/holdspeak/phase-36-meeting-artifact-experience/evidence"
)

# A genuinely messy meeting: real substance (a product decision, an architecture aside,
# a prod incident, action items, a risk, a comms plan) is *buried* in small talk,
# tangents, and "anyway, where were we" resets — exactly the shape that dilutes brief
# intents below threshold under fixed 90s windowing.
DYNAMIC_SCRIPT: list[tuple[str, str, str]] = [
    ("Maya", "Samantha",
     "Morning everyone. Ugh, is the coffee machine still broken? I swear it's been a "
     "week. Anyway, how was everyone's weekend? Did you end up going hiking, Jon?"),
    ("Jon", "Alex",
     "Yeah, it rained the whole time so we just stayed in and watched movies. Okay, "
     "okay, let's actually start. So the main thing I wanted to talk about is the "
     "onboarding flow, customers keep telling us the first run is confusing."),
    ("Devi", "Daniel",
     "Right, the feedback has been pretty consistent. People don't understand what the "
     "value is until like three screens in. I think the persona we care about here is "
     "the busy first-time user who just wants the thing to work."),
    ("Maya", "Samantha",
     "Totally. Oh, before I forget, completely unrelated, did anyone see the game last "
     "night? Wild ending. Sorry, sorry. Back to onboarding. What's the actual scope we "
     "want for this quarter?"),
    ("Jon", "Alex",
     "I'd keep it tight. Just the welcome screen and a sample project. Oh and one quick "
     "thing while it's in my head, the onboarding API call is slow, the latency on that "
     "endpoint is like two seconds because the schema does a join it doesn't need. "
     "We should look at that at some point."),
    ("Devi", "Daniel",
     "Noted. Anyway. So are we agreed we ship the welcome screen plus the sample "
     "project, and we punt the template gallery to next quarter? I think that's the "
     "call. Let's just go with that, option B basically."),
    ("Maya", "Samantha",
     "Works for me. I'll write up the onboarding spec and put it in the doc. Jon, can "
     "you own getting the sample project content together? And someone needs to ping "
     "infra about that endpoint, can you take that, Devi?"),
    ("Devi", "Daniel",
     "Sure, I'll ping infra. Oh, totally changing the subject, did you all see prod "
     "fell over on Tuesday afternoon? Checkout was down for like half an hour. We "
     "rolled it back. It was a bad deploy that ate the connection pool."),
    ("Jon", "Alex",
     "Yeah that was rough. Anyway lunch plans? I'm thinking tacos. Wait, no, we're "
     "almost done. My one worry, honestly, is the holiday traffic in two weeks. If "
     "onboarding spikes and that slow endpoint is still there, it could get ugly."),
    ("Maya", "Samantha",
     "Good point, let's keep an eye on that. Okay, last thing, I'll send a note to the "
     "wider team announcing the onboarding changes and the timeline so everyone hears "
     "it from us. Cool? Cool. Alright, I really need coffee now, someone fix that "
     "machine."),
]


def test_spoken_dynamic_meeting_end_to_end(tmp_path):
    """HS-36-04 — dynamic/messy multi-topic spoken e2e via the REAL routing path.

    say (multi-voice messy meeting) -> Whisper -> MeetingState ->
    process_meeting_state (build_intent_windows -> score -> select -> dispatch ->
    synthesize) -> temp SQLite -> MeetingWebServer -> Playwright BEFORE screenshot.

    Loose, noise-tolerant assertions: a long transcript, no fatal pipeline error, and
    >=1 artifact. Records the produced intents + artifact types for the before/after.
    """
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
    from holdspeak.plugins.pipeline import process_meeting_state
    from holdspeak.plugins.router import select_active_intents
    from holdspeak.transcribe import Transcriber
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    # --- 1. say -> per-line wav -> 2. Whisper -> timed transcript segments --------
    transcriber = Transcriber(model_name="base")
    segments: list[TranscriptSegment] = []
    cursor = 0.0
    for idx, (label, voice, line) in enumerate(DYNAMIC_SCRIPT):
        wav_path = tmp_path / f"dyn_line_{idx}.wav"
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
    assert len(transcript) > 200, f"transcript too short: {transcript!r}"
    print(f"\n[e2e:dynamic] meeting spans {cursor:.0f}s across {len(segments)} segments")
    print(f"[e2e:dynamic] transcript: {transcript}")

    # --- 3. REAL MIR routing path (the dilution weakness lives here) --------------
    host = PluginHost(default_timeout_seconds=30.0, enabled_capabilities={"llm"})
    register_builtin_plugins(host)
    meeting_id = "e2e-spoken-dynamic"

    state = MeetingState(
        id=meeting_id,
        started_at=datetime.now(),
        title="Dynamic Meeting — onboarding, an incident, and a lot of digressions",
        segments=segments,
    )
    reset_database()
    db = get_database(tmp_path / "e2e_dynamic.db")
    db.meetings.save_meeting(state)

    # defer_heavy=False runs the deferred LLM plugins inline so a single call produces
    # persisted runs + synthesized artifacts. profile="balanced" is the product default;
    # its base chain always runs, while incident/risk/comms only fire if their intent
    # clears the threshold — so what the messy meeting *drops* is exactly visible.
    result = process_meeting_state(
        state,
        host,
        profile="balanced",
        db=db,
        synthesize=True,
        defer_heavy=False,
        timeout_seconds=30.0,
    )

    # Pipeline must not have fatally failed (windowing/scoring produced something).
    assert result.windows, f"no intent windows built; errors={result.errors}"
    fatal = [e for e in result.errors if e.startswith(("windowing", "state.id"))]
    assert not fatal, f"fatal pipeline errors: {fatal}"

    # What did the OLD routing actually surface? (the before/after record)
    # Active intents = the union of per-window threshold-gated intents (the same
    # router gate dispatch uses). With fixed-window lexical scoring, brief/paraphrased
    # intents (incident, comms) are diluted below threshold and never appear here.
    active_intents = sorted(
        {
            intent
            for s in result.scores
            for intent in select_active_intents(s.scores, threshold=s.threshold)
        }
    )
    ran_plugins = sorted({r.plugin_id for r in result.runs if r.status == "success"})
    artifact_types = sorted({a.artifact_type for a in result.artifacts})
    print(f"[e2e:dynamic] windows={len(result.windows)} active_intents={active_intents}")
    print(f"[e2e:dynamic] plugins_ran={ran_plugins}")
    print(f"[e2e:dynamic] BEFORE artifact_types={artifact_types} (count={len(artifact_types)})")
    if result.errors:
        print(f"[e2e:dynamic] non-fatal errors: {result.errors}")

    # Loose bar: the pipeline produced *something*. Richness is HS-36-05's bar.
    assert result.artifacts, "expected at least one artifact from the balanced base chain"

    # --- 4. serve + 5. Playwright BEFORE screenshot ------------------------------
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
        os.makedirs(DYNAMIC_EVIDENCE_DIR, exist_ok=True)
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 1500})
            page.goto(f"{url}/history", wait_until="networkidle")
            page.locator("button.meeting-card").first.click()
            # The modal + transcript always render; artifacts may be sparse (the point).
            page.wait_for_selector(".modal", timeout=15000)
            page.wait_for_selector(".transcript-list .segment", timeout=15000)
            page.wait_for_timeout(700)  # let any artifact renderers settle
            rendered_cards = page.locator(".detail-side .segment").count()
            print(f"[e2e:dynamic] rendered artifact cards (BEFORE) = {rendered_cards}")
            content_height = page.evaluate(
                "() => { const b = document.querySelector('.modal-body');"
                " return b ? Math.ceil(b.scrollHeight) : 1400; }"
            )
            page.set_viewport_size({"width": 1280, "height": min(int(content_height) + 220, 8000)})
            page.wait_for_timeout(400)
            shot = os.path.join(DYNAMIC_EVIDENCE_DIR, "dynamic_meeting_before.png")
            page.screenshot(path=shot)
            browser.close()
        print(f"[e2e:dynamic] BEFORE screenshot saved: {shot}")
    finally:
        server.stop()
        reset_database()
