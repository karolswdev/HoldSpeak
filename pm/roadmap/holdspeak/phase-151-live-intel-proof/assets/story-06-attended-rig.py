"""HS-151-06 — THE ATTENDED LEG.

HONESTY HEADER (counsel M6, verbatim law): simulated meeting (played
recording — "Sample one on one meeting with Ms. Rachel Peller and
Dr. Peter Bakken", the owner's pick), REAL capture path (live mic +
PortAudio through the PRODUCTION `holdspeak web` runtime), REAL
transcription (mlx-whisper), REAL intel dispatch (.43:8080, the
owner's pinned resident 35B). Never "a real meeting".

The one-tap loop runs the production conductor for real: the owner's
recording plays through the speakers, the desk's [Record this]
button is clicked on glass, the countdown fires, the mic hears the
room, and everything downstream is the same production tail story 03
proved. Orchestrator-run with the owner present.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
SHOTS = REPO / "pm/roadmap/holdspeak/phase-151-live-intel-proof/assets/story-06-attended-shots"
SCRATCH = Path("/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/5ce49957-4ec2-4c69-803c-324206b30a97/scratchpad")
CLIP = SCRATCH / "attended-clip.wav"
RECORD = REPO / "pm/roadmap/holdspeak/phase-151-live-intel-proof/assets/story-06-attended-record.json"

HEADER = (
    "simulated meeting (played recording), real capture path (live mic), "
    "real transcription (mlx-whisper), real intel (.43)"
)


def main() -> int:
    assert CLIP.exists(), "the trimmed clip must exist"
    home = Path(os.environ["HOME"])  # caller supplies the isolated HOME
    assert os.environ.get("HOLDSPEAK_PEOPLE_KEYSTORE_FILE"), "the keystore seam is required"
    SHOTS.mkdir(parents=True, exist_ok=True)
    record: dict = {"honesty_header": HEADER, "clip": str(CLIP), "events": []}
    failures: list[str] = []

    def note(msg: str) -> None:
        print(msg, flush=True)
        record["events"].append({"t": time.time(), "msg": msg})

    # 1. Wire the metal intel binding BEFORE the hub boots (fresh
    #    connections read committed rows; the cross-process gotcha is
    #    about concurrent singletons).
    wired = subprocess.run(
        [sys.executable, str(REPO / "scripts/wire_metal_intel.py")],
        capture_output=True, text=True, env=os.environ.copy(), cwd=str(REPO),
    )
    note(f"wire_metal_intel: rc={wired.returncode}")
    if wired.returncode != 0:
        print(wired.stdout[-2000:], wired.stderr[-2000:])
        return 1

    # 1a2. Run the production startup migration BEFORE boot so the
    #      speech.transcribe head exists in the same pre-boot commit set
    #      as the wire's meeting heads (the cross-process JOIN gotcha:
    #      post-boot writes from another process may be invisible to the
    #      hub's long-lived resolution connection).
    mig = subprocess.run(
        [sys.executable, "-c",
         "from pathlib import Path; import os; "
         "from holdspeak.db import Database; "
         "from holdspeak.kernel.runtime import _configure; "
         "db = Database(); "
         "_configure(db); print('speech migration ran')"],
        capture_output=True, text=True, env=os.environ.copy(), cwd=str(REPO),
    )
    note(f"speech pre-boot migration: rc={mig.returncode} {mig.stdout.strip()[-80:]} {mig.stderr.strip()[-200:]}")
    if mig.returncode != 0:
        return 1

    # 1b. Seed the calendar BEFORE boot — "Boot is an actual refresh"
    #     (calendar_ingest_conductor._loop): a configured source at boot
    #     is ingested within seconds, the lawful Tuesday state. The event
    #     starts ~3 min out to cover model preload + the arm gesture.
    starts = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(seconds=180)
    fixture = home / "attended.ics"
    fixture.write_text("\r\n".join([
        "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//HS151//EN", "BEGIN:VEVENT",
        "UID:hs151-attended-11",
        f"DTSTART:{starts.strftime('%Y%m%dT%H%M%SZ')}",
        f"DTEND:{(starts + timedelta(minutes=4)).strftime('%Y%m%dT%H%M%SZ')}",
        "SUMMARY:1:1 w/ Rachel & Peter", "END:VEVENT", "END:VCALENDAR", "",
    ]), encoding="utf-8")
    seed = subprocess.run(
        [sys.executable, "-c",
         "import sys; from holdspeak.config import Config; "
         "from holdspeak.config.integrations import CalendarSource; "
         "cfg = Config.load(); "
         f"cfg.calendar.sources = [CalendarSource(id='attended', label='Attended', url={str(fixture)!r}, enabled=True)]; "
         "cfg.save(); print('seeded')"],
        capture_output=True, text=True, env=os.environ.copy(), cwd=str(REPO),
    )
    note(f"calendar pre-seed: rc={seed.returncode} {seed.stdout.strip()} {seed.stderr.strip()[-300:]}")
    if seed.returncode != 0:
        return 1

    # 2. Boot the PRODUCTION runtime.
    hub = subprocess.Popen(
        # -u: the child's stdout is a pipe — without unbuffered mode its
        # prints (including the URL line) sit in the block buffer forever.
        [sys.executable, "-u", "-c",
         "import sys; sys.argv = ['holdspeak', 'web', '--no-open']; "
         "from holdspeak.main import main; main()"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        env=os.environ.copy(), cwd=str(REPO),
    )
    import threading
    hub_lines: list[str] = []
    assert hub.stdout is not None

    def _reader() -> None:
        for line in hub.stdout:  # type: ignore[union-attr]
            hub_lines.append(line)
    threading.Thread(target=_reader, daemon=True).start()

    owner_url = None
    deadline = time.time() + 180
    scanned = 0
    while time.time() < deadline and owner_url is None:
        while scanned < len(hub_lines):
            m = re.search(r"running at: (\S+)", hub_lines[scanned])
            scanned += 1
            if m:
                owner_url = m.group(1)
                break
        if hub.poll() is not None:
            break
        time.sleep(0.5)
    if not owner_url:
        hub.terminate()
        print("hub never printed its URL; last output:")
        print("".join(hub_lines[-30:]))
        return 1
    note(f"hub up: {owner_url}")
    base = owner_url.split("?")[0].rstrip("/")
    token = owner_url.split("token=")[-1] if "token=" in owner_url else ""

    from playwright.sync_api import sync_playwright

    prev_vol = subprocess.run(["osascript", "-e", "output volume of (get volume settings)"],
                              capture_output=True, text=True).stdout.strip()
    subprocess.run(["osascript", "-e", "set volume output volume 62"], check=False)
    player = None
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)

            def open_desk(width=1440, height=900):
                ctx = browser.new_context(viewport={"width": width, "height": height})
                page = ctx.new_page()
                page.emulate_media(reduced_motion="reduce")
                page.goto(f"{base}/?token={token}", wait_until="load")
                chair = page.locator(".chair")
                chair.wait_for(timeout=30000)
                if chair.evaluate("el => el.classList.contains('chair-first-value')"):
                    page.get_by_role("button", name="Continue later", exact=True).click()
                page.locator(".chair:not(.chair-first-value)").wait_for()
                return ctx, page

            def api(page, method, path, body=None):
                r = page.evaluate(
                    """async ([m, p, b, t]) => {
                      const r = await fetch(p, {method: m,
                        headers: {authorization: `Bearer ${t}`,
                                  ...(b ? {"content-type": "application/json"} : {})},
                        body: b ? JSON.stringify(b) : undefined});
                      const ct = r.headers.get("content-type") || "";
                      return {status: r.status,
                              payload: ct.includes("json") ? await r.json() : await r.text()};
                    }""",
                    [method, path, body, token],
                )
                if r["status"] >= 300:
                    raise RuntimeError(f"{method} {path}: {r}")
                return r["payload"]

            ctx, page = open_desk()
            try:
                api(page, "POST", "/api/people/setup")
                # 3. The pre-seeded event rides the conductor's boot refresh.
                row = page.locator('[data-upcoming-source="calendar_event"]', has_text="1:1 w/ Rachel & Peter")
                row.wait_for(timeout=90000)

                # 4. ONE TAP, on glass, for real.
                row.get_by_role("button", name="Record this", exact=True).click()
                page.get_by_text("ARMED", exact=False).first.wait_for(timeout=20000)
                page.screenshot(path=str(SHOTS / "armed-1440.png"), full_page=True)
                note("armed via the real [Record this] tap")

                # 5. Wait for the conductor to fire; then PLAY the recording.
                fired = False
                deadline = time.time() + 240
                while time.time() < deadline:
                    scheds = api(page, "GET", "/api/scheduled-recordings")
                    items = scheds.get("schedules") or scheds.get("items") or scheds
                    blob = json.dumps(items)
                    if '"recording"' in blob:
                        fired = True
                        break
                    time.sleep(3)
                if not fired:
                    failures.append("the conductor never fired the recording")
                    raise RuntimeError("no fire")
                note("recording FIRED — pressing play on the owner's 1:1")
                player = subprocess.Popen(["afplay", str(CLIP)])
                time.sleep(20)
                page.screenshot(path=str(SHOTS / "recording-live-1440.png"), full_page=True)

                # 6. Let the clip play out; the deadline auto-stop owns the end.
                player.wait(timeout=260)
                note("clip finished; waiting for the auto-stop + finalize")
                meeting_id = None
                deadline = time.time() + 300
                while time.time() < deadline:
                    meetings = api(page, "GET", "/api/meetings?limit=5")
                    items = meetings.get("meetings") or meetings.get("items") or []
                    for meeting in items:
                        if meeting.get("ended_at") or meeting.get("capture_status") == "finalized":
                            meeting_id = meeting.get("id")
                            break
                    if meeting_id:
                        break
                    time.sleep(5)
                if not meeting_id:
                    # Honest fallback: one real stop gesture.
                    api(page, "POST", "/api/meeting/stop")
                    note("deadline stop not observed in the poll window; sent the real stop verb")
                    time.sleep(10)
                    meetings = api(page, "GET", "/api/meetings?limit=5")
                    items = meetings.get("meetings") or meetings.get("items") or []
                    meeting_id = items[0].get("id") if items else None
                if not meeting_id:
                    failures.append("no finalized meeting appeared")
                    raise RuntimeError("no meeting")
                note(f"meeting finalized: {meeting_id}")

                # 7. REAL intel: drive the production queue (same pattern as
                #    story-03-rig.py) then wait for .43 to finish.
                from holdspeak.intel_queue import drain_intel_queue
                intel_drained = drain_intel_queue(max_jobs=10)
                note(f"drain_intel_queue: {intel_drained} jobs processed")
                intel_ready = False
                deadline = time.time() + 900
                while time.time() < deadline:
                    detail = api(page, "GET", f"/api/meetings/{meeting_id}")
                    meeting = detail.get("meeting") or detail
                    raw_status = meeting.get("intel_status")
                    status = raw_status.get("state") if isinstance(raw_status, dict) else raw_status
                    if status == "ready":
                        intel_ready = True
                        break
                    if status in ("error", "failed"):
                        failures.append(f"intel_status={status}")
                        break
                    time.sleep(10)
                record["intel_ready"] = intel_ready
                if not intel_ready:
                    failures.append("intel never reached ready")
                    raise RuntimeError("intel not ready")

                detail = api(page, "GET", f"/api/meetings/{meeting_id}")
                meeting = detail.get("meeting") or detail
                segments = meeting.get("segments") or []
                transcript = " ".join(str(s.get("text", "")) for s in segments)
                record["segment_count"] = len(segments)
                record["transcript_sample"] = transcript[:600]
                if len(transcript.strip()) < 40:
                    failures.append("transcript trivially short — the mic heard nothing")
                intel = meeting.get("intel") or {}
                actions = intel.get("action_items") or []
                record["summary"] = intel.get("summary")
                record["action_items"] = [
                    {"task": a.get("task"), "owner": a.get("owner"), "due": a.get("due")}
                    for a in actions
                ]
                note(f"intel ready: {len(actions)} action items; summary: {str(intel.get('summary'))[:160]}")
                # M5 groundedness — substring, case-insensitive; ungrounded is
                # a FINDING, never a failure.
                low = transcript.casefold()
                for a in actions:
                    owner = (a.get("owner") or "").strip()
                    if owner and owner.casefold() not in ("me", "remote") and owner.casefold() not in low:
                        note(f"FINDING (recorded, not failed): owner {owner!r} not a transcript substring")
            finally:
                ctx.close()

            # 8. Fresh context: the Door with the real items; map a named
            #    owner through the REAL gesture if one appeared.
            c2, p2 = open_desk()
            try:
                p2.wait_for_timeout(1500)
                if p2.locator(".surface-window", has_text="People").count():
                    failures.append("occlusion: a People window covers the board shot")
                p2.screenshot(path=str(SHOTS / "door-after-intel-1440.png"), full_page=True)
                named = [a["owner"] for a in record.get("action_items", [])
                         if a.get("owner") and a["owner"].casefold() not in ("me", "remote")]
                if named:
                    display = named[0]
                    rel = api(p2, "POST", "/api/people/relationships",
                              {"display_name": display, "relationship_kind": "direct_report"})
                    rel_id = rel.get("relationship", rel).get("id")
                    api(p2, "POST", f"/api/people/relationships/{rel_id}/owner-aliases",
                        {"alias": display})
                    record["mapped_owner"] = display
                    p2.reload(wait_until="load")
                    p2.locator(".chair:not(.chair-first-value)").wait_for()
                    p2.locator('[data-testid="door-card-person-chip"]').first.wait_for(timeout=20000)
                    p2.screenshot(path=str(SHOTS / "door-mapped-1440.png"), full_page=True)
                    note(f"mapped {display!r} through the real gesture; chip on glass")
                else:
                    note("FINDING: no named (non-reserved) owner emitted this run — recorded honestly")
            finally:
                c2.close()
            browser.close()
    finally:
        if player and player.poll() is None:
            player.terminate()
        if prev_vol.isdigit():
            subprocess.run(["osascript", "-e", f"set volume output volume {prev_vol}"], check=False)
        hub.terminate()
        try:
            hub.wait(timeout=15)
        except Exception:
            hub.kill()

    record["failures"] = failures
    RECORD.write_text(json.dumps(record, indent=1))
    print(f"HONESTY: {HEADER}")
    for f in failures:
        print("FAILURE", f)
    print(f"record={RECORD}\nshots={SHOTS}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
