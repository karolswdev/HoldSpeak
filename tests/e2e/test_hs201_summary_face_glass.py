"""HS-201-04 — ask for the summary and find it again, on the glass.

One walk through the real hub with a real browser, an isolated HOME, a
controlled engine stub and a fixture WAV (never the microphone):

  record  ->  the saved meeting's FIRST summary from its verb
          ->  the disclosure BEFORE the click, the attempts AFTER
          ->  a stale selection refused as a REFUSAL with its plain reason
          ->  a FAILED row's Retry POSTs the disclosed hash
          ->  the Meetings footer chip is not a constant
          ->  a hub restart on the same HOME, the summary in <= 2 moves.

HS-201-10 adds the same walk entered through IMPORT — the only door a
stranger without a microphone can use — where the summary used to run by
itself with no route, no hash and no receipt.

Every run assertion reads the REQUEST the browser issued (its path and its
body), never the click.
"""
from datetime import datetime, timedelta
from pathlib import Path
import json
import os
import time
import wave

import pytest

from holdspeak.intel_queue import process_next_intel_job
from holdspeak.kernel.runtime import _configure
from holdspeak.meeting_session import MeetingSession
from holdspeak.principals import Principal, PrincipalKind
from tests.unit.test_hs201_record_speech_only import (
    _FixtureJournal,
    _FixtureRecorder,
    _FixtureTranscriber,
)
from tests.unit.test_meeting_deferred_admission import FakeHost, FakeIntel, _Route
from .glass_infra import (
    _api,
    _assert_clean,
    _boot,
    _ensure_build,
    _normal_chair,
    _settle,
    assign_engine,
    engine_profile,
    seed_meeting_engines,
    SUMMARY_CAPABILITY,
)

pytestmark = pytest.mark.timeout(600, method="thread")

SHOTS = Path(__file__).resolve().parents[2] / (
    "pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-04-shots"
)
TOKEN = "hs201-04-face"
OWNER = Principal(PrincipalKind.OWNER, "hs201-owner")
WIDTHS = (1440, 393)


def _shot(page, name: str) -> None:
    SHOTS.mkdir(parents=True, exist_ok=True)
    for width in WIDTHS:
        page.set_viewport_size({"width": width, "height": 900 if width == 1440 else 852})
        _settle(page)
        path = SHOTS / f"{name}-{width}.png"
        page.screenshot(path=str(path))
        assert path.stat().st_size > 2000, path
        print(f"SHOT {path}")
    page.set_viewport_size({"width": 1440, "height": 900})


def _chip_label(host: str) -> str:
    """The label the ONE canonical mapper draws for a host.

    Mirrors `web/src/desk/surface/egress.ts::egressFor` for the hosts this
    rig can produce, so the rig asserts the DISPLAYED truth: the face must
    never print the wire word `same_device` at a person.
    """
    if host in ("local", "LOCAL", "this_device", "same_device", "this machine"):
        return "THIS DEVICE"
    return host


def _record_fixture_meeting(monkeypatch: pytest.MonkeyPatch) -> str:
    """Record and stop one meeting from the fixture WAV, no summary run.

    The product's own MeetingSession with a fixture recorder and a fixture
    transcriber: the real save path, no audio device, no microphone.
    """
    monkeypatch.setattr(
        "holdspeak.meeting_session.session.MeetingRecorder", _FixtureRecorder
    )
    monkeypatch.setattr(
        "holdspeak.meeting_capture_journal.MeetingCaptureJournal", _FixtureJournal
    )
    session = MeetingSession(
        _FixtureTranscriber(),  # type: ignore[arg-type]
        principal=OWNER,
        intel_enabled=False,
        intel_deferred_enabled=False,
    )
    session.start()
    return session.stop().id


def _run_posts(requests: list[dict]) -> list[dict]:
    return [r for r in requests if r["path"].endswith("/intelligence/run")]


def _recovery_posts(requests: list[dict]) -> list[dict]:
    return [r for r in requests if r["path"].endswith("/intel-recovery/retry")]


def _drain(db, meeting_id: str, tries: int = 120) -> None:
    for _ in range(tries):
        if db.meetings.get_meeting(meeting_id).intel is not None:
            return
        job = db.intel.get_latest_intel_job(meeting_id)
        if job is not None and job.status == "failed":
            return
        process_next_intel_job()
        time.sleep(0.05)


def test_the_summary_is_asked_for_disclosed_and_found_again(tmp_path, monkeypatch):
    from holdspeak.db import get_database
    from playwright.sync_api import sync_playwright

    monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(tmp_path / "people-keys.json"))
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    db = get_database()
    _configure(db)
    engine = FakeIntel()
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **kw: engine)
    monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: engine)
    monkeypatch.setattr("holdspeak.intel_queue.get_database", lambda: db)
    monkeypatch.setattr("holdspeak.db.get_database", lambda *a, **k: db)
    monkeypatch.setattr(
        "holdspeak.meeting_plugins.build_bound_meeting_plugin_host", lambda: FakeHost(())
    )
    monkeypatch.setattr(
        "holdspeak.plugins.router.preview_route_from_transcript", lambda **kw: _Route(())
    )
    # Both halves of the meeting path on one local profile: speech becomes
    # text, and text becomes a summary (glass_infra.seed_meeting_engines).
    seed_meeting_engines()

    # Astra's counsel round 2: TWO summary-ready meetings, so the canon
    # probe measures a rail that can draw more than one run verb. Only the
    # lead row may wear the filled species.
    spare_id = _record_fixture_meeting(monkeypatch)
    first_id = _record_fixture_meeting(monkeypatch)
    saved = db.meetings.get_meeting(first_id)
    assert saved is not None and saved.segments, "the fixture WAV produced no transcript"
    assert saved.intel is None, "recording must not run a summary"
    print(f"RECORDED meeting={first_id} spare={spare_id} segments={len(saved.segments)}")

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            errors: list[str] = []
            requests: list[dict] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on(
                "request",
                lambda request: requests.append(
                    {
                        "path": request.url.split("?")[0].replace(url, ""),
                        "body": request.post_data or "",
                    }
                )
                if request.method == "POST"
                else None,
            )

            def open_meetings(meeting_id: str | None = None) -> None:
                """The Meetings window, with one record open when asked."""
                page.evaluate(
                    """() => {
                        localStorage.removeItem('hs.desk.workspace.v1');
                        sessionStorage.setItem('hs.desk.staged-surface-open',
                            JSON.stringify({key:'review-meetings'}));
                    }"""
                )
                page.reload(wait_until="load")
                _normal_chair(page)
                if meeting_id is None:
                    page.locator(".meetings-stream-rows").wait_for(timeout=15_000)
                    return
                row = page.get_by_test_id(f"meeting-row-{meeting_id}")
                row.wait_for(timeout=15_000)
                print(f"ROW {meeting_id} {row.text_content()}")
                row.locator(".meetings-stream-row-body").click()
                page.locator(".meetings-detail-head").wait_for(timeout=15_000)

            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)

            # ── the disclosed route, read before any click ──
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _normal_chair(page)
            detail = _api(page, "GET", f"/api/meetings/{first_id}", token=TOKEN)
            planned = detail["planned_route"]
            assert planned["status"] == "ready", planned
            assert planned["legs"], planned
            host = planned["legs"][0]["host"]
            print(f"PLANNED host={host} hash={planned['selection_hash']}")

            # ── station 1: the record BEFORE the run ──
            open_meetings(first_id)
            route_chip = page.get_by_test_id("detail-route")
            route_chip.wait_for(timeout=15_000)
            assert _chip_label(host) in (route_chip.text_content() or ""), (
                route_chip.text_content()
            )
            page.get_by_test_id("detail-run-intelligence-btn").wait_for()
            _assert_canon(page)
            _shot(page, "record-before-run")

            # ── station 2: the first summary, from the verb, with the hash ──
            requests.clear()
            page.get_by_test_id("detail-run-intelligence-btn").click()
            page.wait_for_timeout(600)
            run_post = _run_posts(requests)[-1]
            assert run_post["path"] == f"/api/meetings/{first_id}/intelligence/run"
            assert json.loads(run_post["body"])["expected_selection_hash"] == (
                planned["selection_hash"]
            ), run_post
            print(f"RUN POST {run_post}")

            _drain(db, first_id)
            produced = db.meetings.get_meeting(first_id)
            assert produced.intel is not None, "no summary was produced"
            assert produced.intel.summary == engine.result.summary
            receipt = _api(
                page, "GET", f"/api/meetings/{first_id}/intel-recovery", token=TOKEN
            )["run_receipt"]
            assert receipt["outcome"] == "succeeded", receipt
            assert receipt["attempts"], receipt
            assert receipt["selection_hash"] == planned["selection_hash"], receipt
            print(f"RECEIPT {receipt}")

            # ── station 3: the record AFTER the run: the text and the hosts ──
            open_meetings(first_id)
            summary_text = page.get_by_test_id("meeting-summary-text")
            summary_text.wait_for(timeout=15_000)
            assert (summary_text.text_content() or "").strip() == engine.result.summary
            attempts = page.get_by_test_id("summary-record-attempts")
            attempts.wait_for()
            for attempt in receipt["attempts"]:
                assert _chip_label(attempt["host"]) in (attempts.text_content() or "")
            # The parked proposal chain never says a counter of zero.
            body = page.locator(".desk-surface-window").first.text_content() or ""
            assert "0 PROPOSALS" not in body.upper(), body
            _shot(page, "record-after-run")

            # ── the Review wing after a real run (Astra's counsel finding 3) ──
            # A disclosed summary request runs ANALYSIS only. Review must say
            # the proposal chain did NOT run — never `EXTRACTED <time>`, whose
            # stamp is the summary's own completion, and never the bare
            # "Nothing to review" that claims it looked.
            page.get_by_role("tab", name="Review").click()
            not_run = page.get_by_test_id("review-not-run")
            not_run.wait_for(timeout=15_000)
            assert (not_run.text_content() or "").strip() == "PROPOSALS · NOT RUN"
            review_words = (page.locator(".desk-surface-window").first.text_content() or "")
            assert "EXTRACTED" not in review_words.upper(), review_words
            assert "Nothing to review" not in review_words, review_words
            print(f"REVIEW {not_run.text_content()!r}")
            _shot(page, "review-not-run")
            page.get_by_role("tab", name="Outcomes").click()
            page.get_by_test_id("meeting-summary-text").wait_for(timeout=15_000)

            # ── station 4: a FAILED record, its slab, and a STALE refusal ──
            # The producer refuses once, with retries exhausted, so the
            # record carries a real FAILED summary and its recovery slab.
            second_id = _record_fixture_meeting(monkeypatch)
            second_route = _api(page, "GET", f"/api/meetings/{second_id}", token=TOKEN)[
                "planned_route"
            ]
            engine.error = "the producer refused"
            queued = _api(
                page,
                "POST",
                f"/api/meetings/{second_id}/intelligence/run",
                {"expected_selection_hash": second_route["selection_hash"]},
                token=TOKEN,
            )
            assert queued["state"] == "queued", queued
            for _ in range(60):
                job = db.intel.get_latest_intel_job(second_id)
                if job is not None and job.status == "failed":
                    break
                process_next_intel_job(retry_max_attempts=1)
                time.sleep(0.05)
            engine.error = None
            failed_job = db.intel.get_latest_intel_job(second_id)
            assert failed_job is not None and failed_job.status == "failed", failed_job
            print(f"FAILED job attempts={failed_job.attempts} state={failed_job.status}")

            open_meetings(second_id)
            slab = page.locator(".meeting-intel-recovery")
            slab.wait_for(timeout=15_000)
            slab_retry = slab.get_by_role("button", name="Retry", exact=True)
            slab_retry.wait_for(timeout=15_000)
            assert _chip_label(host) in (
                page.get_by_test_id("recovery-route").text_content() or ""
            )
            assert _chip_label(host) in (
                page.get_by_test_id("recovery-attempts").text_content() or ""
            )
            # Audit defect 6: the facts span the row, never a 7-character column.
            _assert_facts_span_the_row(page)

            # The face holds the hash it disclosed; the assignment moves
            # under it, so the hub refuses BEFORE any provider is contacted.
            stale = _api(page, "GET", f"/api/meetings/{second_id}", token=TOKEN)[
                "planned_route"
            ]["selection_hash"]
            engine_profile("hs201-second-engine")
            assign_engine(SUMMARY_CAPABILITY, 3, profile_id="hs201-second-engine")
            moved = _api(page, "GET", f"/api/meetings/{second_id}", token=TOKEN)[
                "planned_route"
            ]["selection_hash"]
            assert moved != stale, (stale, moved)
            requests.clear()
            slab_retry.click()
            refusal = page.get_by_test_id("recovery-refusal")
            refusal.wait_for(timeout=15_000)
            refusal_words = refusal.text_content() or ""
            assert "REFUSED" in refusal_words, refusal_words
            print(f"REFUSAL {refusal_words}")
            stale_post = _recovery_posts(requests)[-1]
            assert stale_post["path"] == (
                f"/api/meetings/{second_id}/intel-recovery/retry"
            )
            assert json.loads(stale_post["body"])["expected_selection_hash"] == stale
            assert db.meetings.get_meeting(second_id).intel is None, (
                "a refused run must publish no summary"
            )
            # The first meeting's receipt is untouched by the refusal, and
            # the failed run's own attempts are still on the record.
            assert _api(
                page, "GET", f"/api/meetings/{first_id}/intel-recovery", token=TOKEN
            )["run_receipt"] == receipt
            # Lane A's follow-up (`a07d4bb5`): a refusal no longer replaces
            # the receipt of the run that really happened. `run_receipt` is
            # the last EXECUTED receipt and the no-call refusal is served
            # beside it as `last_refusal` (holdspeak/db/intel.py:2352, :2363).
            after_refusal = _api(
                page, "GET", f"/api/meetings/{second_id}/intel-recovery", token=TOKEN
            )
            print(f"AFTER REFUSAL run_receipt={after_refusal.get('run_receipt')}")
            print(f"AFTER REFUSAL last_refusal={after_refusal.get('last_refusal')}")
            executed = after_refusal["run_receipt"]
            durable = after_refusal["last_refusal"]
            # The executed receipt is the FAILED run of station 4 — the
            # producer refused, so the host was contacted and the attempt
            # stands. A route refusal does not erase it any more.
            assert executed["outcome"] == "failed", executed
            assert executed["attempts"], executed
            assert executed["attempts"][0]["host"] == host, executed
            # …and the no-call refusal is beside it, with no attempt at all.
            assert durable is not None, after_refusal
            assert durable["outcome"] == "refused", durable
            assert durable["attempts"] == [], durable
            assert durable["receipt_id"] != executed["receipt_id"], (durable, executed)
            # The face shows the executed destinations from the HUB now, not
            # from anything this client remembered.
            assert _chip_label(host) in (
                page.get_by_test_id("recovery-attempts").text_content() or ""
            )
            # The route the NEXT run will use is still disclosed beside the verb.
            assert _chip_label(host) in (
                page.get_by_test_id("recovery-route").text_content() or ""
            )
            # Audit defect 7: no refusal surface overlaps a verb or the footer.
            _assert_no_overlap(page)
            _shot(page, "refusal-stale-hash")

            # ── station 5: the ledger's Retry POSTs the disclosed hash ──
            open_meetings()
            row = page.get_by_test_id(f"meeting-row-{second_id}")
            row.wait_for(timeout=15_000)
            retry = row.get_by_test_id("retry-intelligence-btn")
            retry.wait_for(timeout=15_000)
            row_route = row.get_by_test_id("row-route")
            assert _chip_label(host) in (row_route.text_content() or ""), (
                row_route.text_content()
            )
            _assert_canon(page)
            _shot(page, "ledger-retry")
            requests.clear()
            retry.click()
            page.wait_for_timeout(600)
            retry_post = _run_posts(requests)[-1]
            assert retry_post["path"] == f"/api/meetings/{second_id}/intelligence/run"
            assert json.loads(retry_post["body"])["expected_selection_hash"] == moved, (
                retry_post
            )
            print(f"RETRY POST {retry_post}")

            # ── station 6: the Meetings footer chip is not a constant ──
            chip = page.locator(".surface-footer .gadget-chip-egress").first
            chip.wait_for()
            chip_words = chip.text_content() or ""
            assert _chip_label(host) in chip_words, chip_words
            assert chip_words.strip() != "⌂ This device", chip_words
            print(f"FOOTER CHIP {chip_words!r}")
            _shot(page, "meetings-chip")
            _assert_no_overlap(page)
            _assert_clean(page, errors)

            # ── station 7: restart, then the summary in <= 2 moves ──
            server.stop()
            restarted = server.start()
            page.goto(f"{restarted}/?token={TOKEN}", wait_until="load")
            page.evaluate(
                "() => { localStorage.removeItem('hs.desk.workspace.v1');"
                " sessionStorage.removeItem('hs.desk.staged-surface-open'); }"
            )
            page.reload(wait_until="load")
            _normal_chair(page)
            rows = page.get_by_test_id("arrival-meeting-row")
            rows.first.wait_for(timeout=15_000)
            moves = 0
            opened = False
            for index in range(rows.count()):
                verb = rows.nth(index).get_by_role("button", name="Open", exact=True)
                if verb.count() > 0:
                    verb.first.click()
                    opened = True
                    break
            assert opened, "no Open verb on the Chair after the restart"
            moves += 1
            found = page.get_by_test_id("meeting-summary-text")
            try:
                found.wait_for(timeout=10_000)
            except Exception:
                page.get_by_test_id(f"meeting-row-{first_id}").locator(
                    ".meetings-stream-row-body"
                ).click()
                moves += 1
                found.wait_for(timeout=10_000)
            assert moves <= 2, moves
            assert (found.text_content() or "").strip() == engine.result.summary
            print(f"FOUND AFTER RESTART moves={moves}")
            _shot(page, "after-restart")
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


def _assert_canon(page) -> None:
    """UX-CANON: one filled primary per face, and no counter of zero."""
    found = page.evaluate(
        """() => {
            const out = {primaries: [], zeros: [], runVerbs: []};
            for (const win of document.querySelectorAll('.desk-surface-window')) {
              for (const b of win.querySelectorAll('.btn--primary'))
                out.primaries.push(b.textContent || '');
              // How many run verbs the face offers at all: the probe must
              // be measuring a rail that COULD draw more than one primary.
              for (const b of win.querySelectorAll('.meetings-stream button')) {
                const label = (b.textContent || '').trim();
                if (label === 'Run summary' || label === 'Retry')
                  out.runVerbs.push(label);
              }
            }
            const body = document.body.innerText || '';
            for (const m of body.matchAll(/\b0 [A-Z]+\b/g)) out.zeros.push(m[0]);
            return out;
        }"""
    )
    print(
        f"CANON primaries={found['primaries']} zeros={found['zeros']} "
        f"run_verbs_in_rail={found['runVerbs']}"
    )
    assert len(found["primaries"]) <= 1, found["primaries"]
    assert found["zeros"] == [], found["zeros"]
    # The rail really does offer more than one run verb here, so the single
    # primary above is the RULE working, not an empty face.
    assert len(found["runVerbs"]) >= 2, found["runVerbs"]


def _assert_facts_span_the_row(page) -> None:
    """Audit defect 6: the NOT DONE facts are not a seven-character column."""
    facts = page.locator(".meeting-intel-recovery-facts").first
    assert facts.count() > 0, "the summary slab did not render on a refused record"
    box = facts.bounding_box()
    row = page.locator(".meeting-intel-recovery .gadget-row").first.bounding_box()
    assert box and row, (box, row)
    assert box["width"] > row["width"] * 0.5, (box, row)
    print(f"FACTS width={box['width']:.0f} of row={row['width']:.0f}")


def _assert_no_overlap(page) -> None:
    """Standing rule: no surface overlaps a verb or the window footer.

    Covers the refusal token, any error surface, and the summary slab's
    fact line (audit defect 7; the first 201-04 shot caught the fact line
    running under Retry/Skip).
    """
    overlap = page.evaluate(
        """() => {
            const footer = document.querySelector('.surface-footer');
            const bad = [];
            const hits = (a, b) =>
              a.bottom > b.top && a.top < b.bottom && a.right > b.left && a.left < b.right;
            for (const surface of document.querySelectorAll(
                '.surface-state-error, [data-testid$="-refusal"],' +
                ' .meeting-intel-recovery-facts')) {
              const a = surface.getBoundingClientRect();
              if (a.width === 0) continue;
              if (footer && hits(a, footer.getBoundingClientRect())) bad.push('footer');
              // …and nothing may run out of its own window's right edge
              // (UX-CANON A.6: a window's wings never leave the window).
              const win = surface.closest('.desk-surface-window');
              if (win) {
                const w = win.getBoundingClientRect();
                if (a.right > w.right + 1) bad.push('out of window: ' + (surface.textContent || ''));
              }
              for (const verb of document.querySelectorAll('button')) {
                const b = verb.getBoundingClientRect();
                if (b.width === 0) continue;
                if (hits(a, b)) bad.push(verb.textContent || 'verb');
              }
            }
            return bad;
        }"""
    )
    assert overlap == [], overlap


# ──────────────────────────────────────────────────────────────────────
# HS-201-10 — the same walk, entered through IMPORT.
#
# Import is the only door a stranger without a microphone can use, and the
# 2026-09-20 rehearsal watched it run the summary by itself: contact with
# 192.168.1.43 before any gesture, `run_receipt: null`, and no "Run summary"
# verb ever drawn (audits/rehearsal-07-opus.md, steps 3-5 and defect 2).
# This is the same rig, on that door: import the fixture WAV through the
# real face, prove NOTHING ran, then ask, and read the receipt.
# ──────────────────────────────────────────────────────────────────────

IMPORT_TOKEN = "hs201-10-import"
FIXTURE_WAV = Path(__file__).resolve().parents[1] / "fixtures" / "core_path_smoke_16k.wav"
SHOTS_10 = Path(__file__).resolve().parents[2] / (
    "pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-10-shots"
)


class _FixtureImportTranscriber:
    """Stands in for Whisper on the import path. Never loads a model."""

    def transcribe(self, audio, **_admission):
        return "The quick brown fox jumps over the lazy dog."


def _shot_10(page, name: str) -> None:
    SHOTS_10.mkdir(parents=True, exist_ok=True)
    for width in WIDTHS:
        page.set_viewport_size({"width": width, "height": 900 if width == 1440 else 852})
        _settle(page)
        path = SHOTS_10 / f"{name}-{width}.png"
        page.screenshot(path=str(path))
        assert path.stat().st_size > 2000, path
        print(f"SHOT {path}")
    page.set_viewport_size({"width": 1440, "height": 900})


def test_import_transcribes_and_stops_then_the_summary_is_asked_for(
    tmp_path, monkeypatch
):
    from holdspeak.db import get_database
    from holdspeak.web.routes import meeting_import as import_route
    from playwright.sync_api import sync_playwright

    monkeypatch.setenv(
        "HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(tmp_path / "people-keys.json")
    )
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=IMPORT_TOKEN)
    db = get_database()
    _configure(db)
    engine = FakeIntel()
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **kw: engine)
    monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: engine)
    monkeypatch.setattr("holdspeak.intel_queue.get_database", lambda: db)
    monkeypatch.setattr("holdspeak.db.get_database", lambda *a, **k: db)
    monkeypatch.setattr(
        "holdspeak.meeting_plugins.build_bound_meeting_plugin_host", lambda: FakeHost(())
    )
    monkeypatch.setattr(
        "holdspeak.plugins.router.preview_route_from_transcript", lambda **kw: _Route(())
    )
    # No Whisper on this walk: the subject is what the import DOES, not what
    # it hears. The engine that would write the summary is the real seam and
    # it is watched (`engine.analyzed`).
    monkeypatch.setattr(
        import_route, "_transcriber_factory", lambda cfg: _FixtureImportTranscriber()
    )
    seed_meeting_engines()

    # The file the rehearsal imported, with a mtime months in the past —
    # the exact shape that dated the meeting JUN 03 (defect 10).
    source = tmp_path / "core_path_smoke_16k.wav"
    source.write_bytes(FIXTURE_WAV.read_bytes())
    old = (datetime.now() - timedelta(days=108)).timestamp()
    os.utime(source, (old, old))
    with wave.open(str(source), "rb") as wav_file:
        seconds = wav_file.getnframes() / float(wav_file.getframerate())
    assert 2.0 < seconds < 3.0, seconds
    print(f"FIXTURE {source.name} {seconds:.2f}s mtime={datetime.fromtimestamp(old)}")

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            errors: list[str] = []
            requests: list[dict] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on(
                "request",
                lambda request: requests.append(
                    {
                        "path": request.url.split("?")[0].replace(url, ""),
                        "body": request.post_data or "",
                    }
                )
                if request.method == "POST"
                else None,
            )

            def open_meetings(expect_rows: bool = True) -> None:
                page.evaluate(
                    """() => {
                        localStorage.removeItem('hs.desk.workspace.v1');
                        sessionStorage.setItem('hs.desk.staged-surface-open',
                            JSON.stringify({key:'review-meetings'}));
                    }"""
                )
                page.reload(wait_until="load")
                _normal_chair(page)
                # A cold desk draws the Meetings face with no stream at all,
                # so the face's own head verbs are what a first visit waits
                # for (the headline span is empty while the list loads).
                page.locator(".meetings-head-verbs").wait_for(timeout=15_000)
                if expect_rows:
                    page.locator(".meetings-stream-rows").wait_for(timeout=15_000)

            page.goto(f"{url}/?token={IMPORT_TOKEN}", wait_until="load")
            _api(
                page, "PUT", "/api/setup/onboarding", {"disposition": "completed"},
                token=IMPORT_TOKEN,
            )
            open_meetings(expect_rows=False)

            # ── station 1: the Import door, and the real gesture ──
            page.locator(".meetings-head-verbs").get_by_role(
                "button", name="Import", exact=True
            ).click()
            file_input = page.locator(".surface-dropwell input[type=file]")
            # The dropwell hides its input behind the label's own species.
            file_input.wait_for(timeout=15_000, state="attached")
            file_input.set_input_files(str(source))
            page.get_by_role("textbox", name="Title").fill("Imported standup")
            requests.clear()
            page.locator(".surface-actions").get_by_role(
                "button", name="Import", exact=True
            ).click()

            import_post = None
            for _ in range(120):
                posts = [r for r in requests if r["path"] == "/api/meetings/import"]
                if posts:
                    import_post = posts[-1]
                    break
                page.wait_for_timeout(100)
            assert import_post is not None, requests
            # Defect 10 at its source: the gesture sends no file mtime.
            assert "started_at_ms" not in import_post["body"], import_post
            print(f"IMPORT POST {import_post['path']} (no started_at_ms)")

            imported = None
            for _ in range(150):
                rows = db.meetings.list_meetings()
                done = [
                    row for row in rows
                    if row.id and db.meetings.get_meeting(row.id).segments
                ]
                if done:
                    imported = db.meetings.get_meeting(done[0].id)
                    break
                page.wait_for_timeout(100)
            assert imported is not None, "the import never produced a transcript"
            print(f"IMPORTED {imported.id} segments={len(imported.segments)}")

            # ── the fence: it transcribed, and it stopped ──
            assert db.intel.list_intel_jobs() == [], db.intel.list_intel_jobs()
            assert db.intel.get_latest_intel_job(imported.id) is None
            assert engine.analyzed == [], engine.analyzed
            assert imported.intel is None
            assert imported.intel_status == "disabled", imported.intel_status
            # Defects 10 and 11: dated the import moment, transcript final.
            assert imported.started_at > datetime.now() - timedelta(minutes=10)
            assert imported.transcription_status == "complete", (
                imported.transcription_status
            )
            print(
                f"AFTER IMPORT jobs={db.intel.list_intel_jobs()} "
                f"analyzed={engine.analyzed} intel_status={imported.intel_status} "
                f"started_at={imported.started_at} "
                f"transcription_status={imported.transcription_status}"
            )

            # ── station 2: the row tells the truth about its length ──
            open_meetings()
            row = page.get_by_test_id(f"meeting-row-{imported.id}")
            row.wait_for(timeout=15_000)
            row_words = row.text_content() or ""
            print(f"ROW {row_words}")
            assert "3 S" in row_words, row_words
            assert "1 MIN" not in row_words, row_words
            today = _ledger_date(datetime.now())
            assert today in row_words, (today, row_words)
            run_verb = row.get_by_test_id("run-intelligence-btn")
            run_verb.wait_for(timeout=15_000)
            detail = _api(
                page, "GET", f"/api/meetings/{imported.id}", token=IMPORT_TOKEN
            )
            planned = detail["planned_route"]
            assert planned["status"] == "ready", planned
            host = planned["legs"][0]["host"]
            assert _chip_label(host) in (
                row.get_by_test_id("row-route").text_content() or ""
            )
            assert detail.get("run_receipt") is None, detail.get("run_receipt")
            print(f"PLANNED host={host} hash={planned['selection_hash']}")
            _shot_10(page, "import-row-length")

            # ── station 3: the record, with the verb and the planned host ──
            row.locator(".meetings-stream-row-body").click()
            page.locator(".meetings-detail-head").wait_for(timeout=15_000)
            route_chip = page.get_by_test_id("detail-route")
            route_chip.wait_for(timeout=15_000)
            assert _chip_label(host) in (route_chip.text_content() or "")
            page.get_by_test_id("detail-run-intelligence-btn").wait_for(timeout=15_000)
            head = page.locator(".meetings-detail-head").text_content() or ""
            print(f"DETAIL HEAD {head}")
            assert "3 S" in head, head
            assert "1 MIN" not in head, head
            _shot_10(page, "import-done")

            # ── station 4: ask for it, and read the receipt ──
            requests.clear()
            page.get_by_test_id("detail-run-intelligence-btn").click()
            page.wait_for_timeout(600)
            run_post = [r for r in requests if r["path"].endswith("/intelligence/run")][-1]
            assert run_post["path"] == f"/api/meetings/{imported.id}/intelligence/run"
            assert json.loads(run_post["body"])["expected_selection_hash"] == (
                planned["selection_hash"]
            ), run_post
            print(f"RUN POST {run_post}")

            _drain(db, imported.id)
            produced = db.meetings.get_meeting(imported.id)
            assert produced.intel is not None, "no summary was produced"
            assert produced.intel.summary == engine.result.summary
            assert engine.analyzed, "the provider was never contacted by the gesture"
            receipt = _api(
                page, "GET", f"/api/meetings/{imported.id}/intel-recovery",
                token=IMPORT_TOKEN,
            )["run_receipt"]
            assert receipt["outcome"] == "succeeded", receipt
            assert receipt["attempts"], receipt
            assert receipt["selection_hash"] == planned["selection_hash"], receipt
            assert receipt["attempts"][0]["host"] == host, receipt
            print(f"RECEIPT {receipt}")

            open_meetings()
            page.get_by_test_id(f"meeting-row-{imported.id}").locator(
                ".meetings-stream-row-body"
            ).click()
            summary_text = page.get_by_test_id("meeting-summary-text")
            summary_text.wait_for(timeout=15_000)
            assert (summary_text.text_content() or "").strip() == engine.result.summary
            attempts = page.get_by_test_id("summary-record-attempts")
            attempts.wait_for(timeout=15_000)
            for attempt in receipt["attempts"]:
                assert _chip_label(attempt["host"]) in (attempts.text_content() or "")
            _shot_10(page, "import-after-run")
            _assert_no_overlap(page)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


def _ledger_date(when: datetime) -> str:
    """The catalog's date column, as `helpers.ts::ledgerDate` draws it."""
    months = (
        "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
        "JUL", "AUG", "SEP", "OCT", "NOV", "DEC",
    )
    return f"{months[when.month - 1]} {when.day:02d}"
