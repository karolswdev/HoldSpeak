"""Send's bounded form, owner press and in-window discard at both sizes.

The note, preview, prepared rows, refusals and receipts come from the isolated
hub. Only FileChannel.dispatch is held or failed; nothing leaves the rig.
"""
from __future__ import annotations

import os
import json
import re
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .glass_infra import press_verb, choose_toolbar

import pytest

from .send_face_facts import send_face_facts
from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle, park_builtin_folder

TOKEN = "send-grammar"


@pytest.mark.parametrize("width", [1440, 393])
@pytest.mark.timeout(180)
def test_send_form_states(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    from playwright.sync_api import sync_playwright, expect
    from holdspeak.services.channel_contract import FileChannel, Outcome

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    phase = os.environ.get("SEND_GRAMMAR_PHASE", "after")
    shots = Path(__file__).resolve().parents[2] / ".tmp/evidence-shots/send-engines-r2-debug"
    shots.mkdir(parents=True, exist_ok=True)
    release = threading.Event()
    mode = "failed"
    real_dispatch = FileChannel.dispatch

    def dispatch(channel: Any, *args: Any, **kwargs: Any) -> Any:
        if mode == "held":
            assert release.wait(30)
        if mode == "failed":
            return Outcome("failed", "permission_denied")
        if mode == "unknown":
            return Outcome("unknown", "no_answer")
        return real_dispatch(channel, *args, **kwargs)

    monkeypatch.setattr(FileChannel, "dispatch", dispatch)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852}, reduced_motion="reduce")
            page.set_default_timeout(20000)
            page.goto(f"{base}/?token={TOKEN}")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            _api(page, "GET", "/api/channels/destinations", token=TOKEN)
            # Six destinations are made by the actual destination producers.
            # Remote credentials stay in the isolated memory store; dispatch is file-only.
            from holdspeak.services import channel_slack, channel_email
            email_keys = channel_email.MemoryEmailKeyStore()
            monkeypatch.setattr(channel_email, "KEY_STORE", lambda: email_keys)
            key_store = channel_slack.MemorySlackKeyStore()
            monkeypatch.setattr(channel_slack, "KEY_STORE", lambda: key_store)
            folder = Path.home() / "Documents" / "Architecture reports"
            folder.mkdir(parents=True)
            _api(page, "POST", "/api/channels/destinations", {"name": "Architecture review and migration reports", "channel": "file", "folder": str(folder)}, token=TOKEN)
            for index in range(2):
                _api(page, "POST", "/api/channels/destinations", {"name": f"Architecture review group {index + 1}", "channel": "email", "provider": "resend", "from_email": "owner@example.test", "key_ref": f"rig-email-{index}", "to": [f"review-{index}@example.test"]}, token=TOKEN)
                key_ref = _api(page, "POST", "/api/channels/slack-webhooks", {"webhook_url": f"https://hooks.slack.com/services/T00000000/B00000000/rigWebhookOnly{index:024d}"}, token=TOKEN)["key_ref"]
                _api(page, "POST", "/api/channels/destinations", {"name": f"Architecture migration channel {index + 1}", "channel": "slack", "key_ref": key_ref, "channel_label": f"#architecture-review-{index}"}, token=TOKEN)
            destinations = _api(page, "GET", "/api/channels/destinations", token=TOKEN)["destinations"]
            assert len(destinations) == 6 and len({row["channel"] for row in destinations}) == 3
            long_title = "Review the architecture migration and keep the current rollback plan, its decisions and the report for the steering group in view while the next delivery waits for its destination."
            assert len(long_title) == 180
            path_title = "/Users/karol/dev/tools/HoldSpeak/web/src/desk/surface/send/SendWell.tsx — Keep the frozen report and its delivery time visible for the architecture steering group"
            made = _api(page, "POST", "/api/thoughts", {
                "request_id": str(uuid.uuid4()), "raw_text": "The weekly report is ready.", "source": {"kind": "typed"},
                "initial_note": {"title": long_title, "body_markdown": f"# {long_title}\n\n## Weekly report · 2026-11-12\n\nThe weekly report is ready. " + "The migration plan keeps the rollback path ready. " * 12 + "\n" + "\nNext step: review the plan.\n" * 35, "tags": []},
            }, token=TOKEN)
            note_id = made['thought']['working_note']['id']
            ref = f"note:{note_id}"
            mode = "sent"
            from holdspeak.db import get_database
            seed_destination = next(row["id"] for row in destinations if row["channel"] == "file" and not row.get("builtin"))
            revision = dict(made["thought"])
            def write_note(fields: dict[str, Any]) -> None:
                written = _api(page, "PUT", f"/api/notes/{note_id}", {**fields, "expected_aggregate_revision": revision["aggregate_revision"], "expected_working_revision": revision["working_revision"]}, token=TOKEN)["note"]
                revision.update(written)
            for index in range(40):
                title = path_title if index % 2 else long_title
                write_note({"title": title, "body_markdown": f"# {title}\n\n## Weekly report · 2026-11-12\n\nThe weekly report is ready. " + "The migration plan keeps the rollback path ready. " * 12 + "\n" + "\nNext step: review the plan.\n" * 35})
                preview = _api(page, "POST", "/api/channels/preview", {"document_ref": ref, "destination_id": seed_destination}, token=TOKEN)
                sent = _api(page, "POST", "/api/channels/send", {"command_id": str(uuid.uuid4()), "document_ref": ref, "destination_id": seed_destination, "preview_digest": preview["payload_digest"]}, token=TOKEN)["send"]
                at = (datetime.now(timezone.utc) - timedelta(hours=40 - index)).isoformat()
                with get_database()._connection() as conn:
                    conn.execute("UPDATE channel_sends SET created_at=?, dispatch_started_at=?, settled_at=? WHERE id=?", (at, at, at, sent["id"]))
            assert len(_api(page, "GET", f"/api/channels/sends?document_ref={ref}", token=TOKEN)["sends"]) == 40
            def save_body(title: str) -> None:
                write_note({"title": title, "body_markdown": f"# {title}\n\n## Weekly report · 2026-11-12\n\nThe weekly report is ready. " + "The migration plan keeps the rollback path ready. " * 12 + "\n" + "\nNext step: review the plan.\n" * 35})
            save_body(long_title)
            mode = "failed"
            page.goto(f"{base}/?open={ref}")
            _normal_chair(page)
            win = page.locator(".thought-workspace-window").first
            win.wait_for()
            page.wait_for_function("""async ({token,id}) => {
              const response=await fetch('/api/desk/windows',{headers:{Authorization:'Bearer '+token}});
              const body=await response.json(); return body.windows?.some(row=>row.id===id);
            }""", arg={"token":TOKEN,"id":f"pullout:{ref}"}, polling=100)
            if width == 1440:
                _api(page, "POST", f"/api/desk/windows/pullout:{ref}/set_geometry", {"rect": {"x": "-1/2 + 100", "y": "-1/2 + 80", "w": "900px", "h": "600px"}}, token=TOKEN)

            def open_send(wait_preview: bool = True) -> Any:
                press_verb(win.locator(".thought-note-toolbar"), 'Send…')
                well = win.get_by_test_id("send-well")
                choice = well.get_by_role("combobox", name="Destination", exact=True)
                expect(choice.get_by_role("option", name="HoldSpeak folder", exact=True)).to_have_count(1)
                if not choice.input_value():
                    choose_toolbar(well, "Destination", "holdspeak-folder")
                if wait_preview:
                    well.get_by_test_id("send-preview-body").first.wait_for()
                return well

            def shot(state: str) -> None:
                # Every state starts at its choices; only the payload itself
                # needs scrolling. Completion remains outside both wells.
                win.locator(".surface-inspector-fields, .surface-well-body").evaluate_all("els => els.forEach(el => { el.scrollTop = 0; el.scrollLeft = 0; })")
                page.evaluate("() => document.fonts.ready.then(() => undefined)")
                _settle(page)
                expected = {"preparing":"New", "ready":"New", "failed":"Failed", "unknown":"Result unknown", "sending":"Sending…", "sent":"Sent at", "refused":"Refused", "first-sending":"Sending…", "prepared":"Prepared", "discard-question":"Prepared", "discarded":"Discarded", "no-destination":"New"}
                expect(win.get_by_test_id("send-status")).to_contain_text(expected[state])
                if state in {"ready", "prepared"}:
                    text = win.get_by_test_id("send-preview-body").first
                    expect(text).to_contain_text("Weekly report")
                    fit = text.locator(".reading-document").evaluate("el => ({reading:el.clientWidth,well:el.parentElement.clientWidth})")
                    assert fit["reading"] >= fit["well"] - 1, fit
                    if phase == "after" and width == 393:
                        reading=text.evaluate("""el=>{const well=el.closest('.surface-well-body'),p=el.querySelector('.reading-document > p');return {height:well.getBoundingClientRect().bottom-p.getBoundingClientRect().top,line:parseFloat(getComputedStyle(p).lineHeight)};}""")
                        assert reading["height"] >= 4*reading["line"]-1,reading
                if phase == "after" and state in {"ready", "prepared"}:
                    expect(win.get_by_test_id("send-add-destination")).to_be_attached()
                    assert win.get_by_test_id("send-add-destination").locator('xpath=ancestor::*[contains(@class,"surface-inspector-actions")]').count()==1
                    fit = win.get_by_role("combobox", name="Destination", exact=True).evaluate("""el => {
                        const style=getComputedStyle(el), canvas=document.createElement('canvas'), ctx=canvas.getContext('2d');
                        ctx.font=`${style.fontWeight} ${style.fontSize} ${style.fontFamily}`;
                        return {needed:ctx.measureText(el.options[el.selectedIndex].label).width + parseFloat(style.paddingLeft) + parseFloat(style.paddingRight), available:el.clientWidth};
                    }""")
                    assert fit["needed"] <= fit["available"] + 1, fit
                if phase == "after" and state == "first-sending":
                    expect(win.get_by_test_id("send-verb")).to_have_text("Sending…")
                if state == "sent":
                    proof=win.get_by_test_id("proof").first
                    path=proof.get_attribute("title")
                    assert path and proof.get_attribute("aria-label"), (path, proof.inner_text())
                    assert not proof.get_attribute("data-multiline")
                    assert proof.inner_text().endswith(".md"), proof.inner_text()
                    assert proof.get_attribute("aria-label").endswith(Path(path).name), (path, proof.inner_text())
                    assert proof.evaluate("el=>el.clientHeight <= parseFloat(getComputedStyle(el).lineHeight) * (el.hasAttribute('data-multiline') ? 2 : 1)+1")
                if state == "discard-question":
                    expect(win.get_by_test_id("prepared-preview")).to_be_visible()
                    question = win.locator("[data-question]")
                    buttons = question.get_by_role("button").all()
                    assert [button.inner_text() for button in buttons] == ["Cancel", "Discard"]
                    cancel, discard = [button.bounding_box() for button in buttons]
                    assert abs(cancel["y"] - discard["y"]) <= 1 and cancel["x"] < discard["x"], (cancel, discard)
                    assert win.get_by_test_id("send-preview-body").bounding_box()["height"] >= 60
                if phase == "after":
                    facts = send_face_facts(win, six_lines=width == 1440 and state in {"ready", "prepared"})
                    (shots / f"send-{state}-{width}-facts.json").write_text(json.dumps(facts, indent=2))
                (shots / f"send-{state}-{width}-{phase}.json").write_text(json.dumps(win.evaluate("""el => [...el.querySelectorAll(".thought-send-scroll,.thought-send-well,[data-seat],.send-sheet,[data-testid=send-well],.surface-tab-panel,.surface-inspector-form,.surface-inspector-fields,.surface-inspector-actions,.surface-well-body,.send-preview-body,.reading-heading")].map(e => ({cls:e.className,rect:e.getBoundingClientRect().toJSON(),display:getComputedStyle(e).display,flex:getComputedStyle(e).flex,overflow:getComputedStyle(e).overflow,clip:getComputedStyle(e).clipPath,visibility:getComputedStyle(e).visibility,opacity:getComputedStyle(e).opacity,color:getComputedStyle(e).color,scrollTop:e.scrollTop,font:getComputedStyle(e).font,fontReady:document.fonts.status,html:e.matches(".reading-heading") ? e.outerHTML : undefined}))"""),indent=2))
                polish = shots.parent / "send-engines14r3"
                polish.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(polish / f"send-{state}-{900 if width == 1440 else 393}-{phase}.png"))
                page.screenshot(path=str(shots / f"1-7-send-{state}-{900 if width == 1440 else 393}.png"))
                page.screenshot(path=str(shots / f"send-{state}-{'900x600' if width == 1440 else '393'}-{phase}.png"))

            if phase in {"before", "after"}:
                held_preview: list[Any] = []
                page.route("**/api/channels/preview", lambda route: held_preview.append((route, route.fetch())))
                well = open_send(False)
                expect(well.get_by_test_id("send-destination-word")).to_contain_text("HoldSpeak folder")
                expect(well.get_by_test_id("send-verb")).to_be_disabled()
                assert len(_api(page, "GET", f"/api/channels/sends?document_ref={ref}", token=TOKEN)["sends"]) == 40
                shot("preparing")
                if phase == "after":
                    expect(well.get_by_test_id("send-preview-loading")).to_have_text("Preparing preview…")
                route, response = held_preview.pop()
                route.fulfill(response=response)
                page.unroute("**/api/channels/preview")
                well.get_by_test_id("send-preview-body").wait_for()
            else:
                well = open_send()
            shot("ready")
            for tab_name, channel in (("Folder", "file"), ("Email", "email"), ("Slack", "slack")):
                well.get_by_role("tab", name=tab_name, exact=True).click()
                choices = [row for row in destinations if row["channel"] == channel]
                if phase == "before" and width == 1440 and channel in {"email", "slack"}:
                    wire = _api(page, "POST", "/api/channels/preview", {"document_ref":ref,"destination_id":choices[-1]["id"]}, token=TOKEN)
                    (shots.parents[1] / f"r3-{channel}-preview.json").write_text(json.dumps({"destination":choices[-1],"reply":wire},indent=2))
                choose_toolbar(well, "Destination", choices[-1]["id"])
                well.get_by_test_id("send-preview-body").first.wait_for()
                _settle(page)
                page.screenshot(path=str(shots.parent / "send-engines14r3" / f"send-{channel}-destination-{900 if width == 1440 else 393}-{phase}.png"))
                if phase == "after" and channel in {"email", "slack"}:
                    body = well.get_by_test_id("send-preview-body").first
                    expect(body).to_contain_text("Nov 12")
                    expect(body).not_to_contain_text("2026-11-12")
                    reading = body.locator("..").evaluate("el => ({height:el.clientHeight,line:parseFloat(getComputedStyle(el).lineHeight)})")
                    assert reading["height"] >= 6 * reading["line"] - 1, reading
                    if channel == "email":
                        expect(well.get_by_test_id("send-preview").get_by_text("Subject", exact=True)).to_be_in_viewport(ratio=1)
                if phase == "after" and channel == "file":
                    fit = well.get_by_role("combobox", name="Destination", exact=True).evaluate("""el => {
                        const s=getComputedStyle(el), c=document.createElement('canvas'),ctx=c.getContext('2d'); ctx.font=`${s.fontWeight} ${s.fontSize} ${s.fontFamily}`;
                        return {needed:ctx.measureText(el.options[el.selectedIndex].label).width+parseFloat(s.paddingLeft)+parseFloat(s.paddingRight),available:el.clientWidth};
                    }""")
                    assert fit["needed"] <= fit["available"] + 1, fit
            well.get_by_role("tab", name="Folder", exact=True).click()
            choose_toolbar(well, "Destination", "holdspeak-folder")
            well.get_by_test_id("send-preview-body").first.wait_for()
            # The second shape is a real saved source title too.
            well.get_by_test_id("send-back").click()
            save_body(path_title)
            page.reload()
            _normal_chair(page)
            well = open_send()
            _settle(page)
            page.screenshot(path=str(shots.parent / "send-engines14r3" / f"send-ready-path-title-{900 if width == 1440 else 393}-{phase}.png"))
            well.get_by_test_id("send-back").click()
            save_body(long_title)
            page.reload()
            _normal_chair(page)
            well = open_send()
            press_verb(well, "Add destination")
            expect(well.get_by_test_id("dest-form")).to_be_visible()
            page.screenshot(path=str(shots / f"6-send-add-destination-{900 if width == 1440 else 393}.png"))
            page.screenshot(path=str(shots.parent / "send-engines14r3" / f"send-add-destination-{900 if width == 1440 else 393}-{phase}.png"))
            well.get_by_test_id("dest-cancel").click()
            well.get_by_test_id("send-preview-body").wait_for()
            if phase == "after":
                completion = well.locator(".surface-inspector-actions").first
                expect(completion.get_by_role("button",name="Cancel",exact=True)).to_be_in_viewport(ratio=1)
                expect(completion.get_by_test_id("send-verb")).to_be_in_viewport(ratio=1)
                expect(completion.get_by_test_id("send-add-destination")).to_be_attached()
                assert well.locator(".send-sheet-header").count() == 0
                box = completion.bounding_box()
                assert box and box["y"] + box["height"] <= page.viewport_size["height"]
                well.locator(".surface-inspector-fields").first.evaluate("el => el.scrollTop = el.scrollHeight")
                assert completion.bounding_box() == box
                assert well.locator("[data-feedback-redact=true]").count()
            mode = "held"
            well.get_by_test_id("send-verb").click()
            well.get_by_test_id("send-running").wait_for()
            shot("first-sending")
            release.set()
            well.get_by_test_id("send-sent").wait_for()
            release.clear()
            mode = "failed"
            well.get_by_test_id("send-verb").click()
            well.get_by_test_id("send-failed").wait_for()
            shot("failed")
            mode = "unknown"
            well.get_by_test_id("send-verb").click()
            well.get_by_test_id("send-unknown").wait_for()
            shot("unknown")
            expect(win.get_by_test_id("send-status").get_by_role("status")).to_have_text("Result unknown")
            assert well.get_by_role("button", name="Try again", exact=True).count() == 1
            mode = "held"
            well.get_by_test_id("send-verb").click()
            well.get_by_test_id("send-running").wait_for()
            shot("sending")
            release.set()
            well.get_by_test_id("send-sent").wait_for()
            shot("sent")
            well.get_by_role("tab", name="Sent", exact=True).click()
            if phase == "after":
                assert well.get_by_test_id("history-row").count() >= 40
                if width == 393:
                    expect(well.get_by_test_id("history-row").first.locator('[data-folded-col="when"]')).to_be_visible()
            page.screenshot(path=str(shots / f"1-3-send-history-{900 if width == 1440 else 393}.png"))
            page.screenshot(path=str(shots.parent / "send-engines14r3" / f"send-history-{900 if width == 1440 else 393}-{phase}.png"))
            saved = well.get_by_test_id("history-row").filter(has=page.get_by_test_id("history-word").filter(has_text=re.compile("^Saved$"))).first
            saved.click()
            _settle(page)
            proof = well.get_by_test_id("proof").first
            expect(proof).to_have_attribute("title", re.compile(r"\.md$"))
            if phase == "after" and "…" in proof.inner_text():
                head, tail = proof.inner_text().split("…", 1)
                full = proof.get_attribute("aria-label")
                assert full and full.startswith(head) and full.endswith(tail), (full, head, tail)
                assert head[-1] in "/:_-. " and full[len(full)-len(tail)-1] in "/:_-. ", (full, head, tail)
            page.screenshot(path=str(shots / f"1-3-send-receipt-{900 if width == 1440 else 393}.png"))
            page.screenshot(path=str(shots.parent / "send-engines14r3" / f"send-receipt-{900 if width == 1440 else 393}-{phase}.png"))
            well.get_by_role("tab", name="Folder", exact=True).click()
            # A stale press crosses the real hub boundary and is refused;
            # the transport itself is never called for this request.
            def stale(route: Any) -> None:
                payload = route.request.post_data_json
                route.continue_(post_data=json.dumps({**payload, "preview_digest": "0" * 64}))
            page.route("**/api/channels/send", stale)
            well.get_by_test_id("send-verb").click()
            well.get_by_test_id("send-refused").wait_for()
            shot("refused")
            expect(well.get_by_test_id("send-preview-body")).to_contain_text("The weekly report is ready.")
            expect(well.get_by_test_id("send-verb")).to_be_enabled()
            page.unroute("**/api/channels/send", stale)
            well.get_by_test_id("send-back").click()
            dests = _api(page, "GET", "/api/channels/destinations", token=TOKEN)["destinations"]
            prepared = _api(page, "POST", "/api/channels/sends", {"document_ref": ref, "destination_id": dests[0]["id"]}, token=TOKEN)["send"]
            page.reload()
            _normal_chair(page)
            well = open_send()
            well.get_by_test_id("prepared-preview").wait_for()
            well.get_by_test_id("prepared-preview").scroll_into_view_if_needed()
            shot("prepared")
            if phase == "after":
                body_box = well.get_by_test_id("prepared-preview").get_by_test_id("send-preview-body").bounding_box()
                assert body_box and body_box["width"] >= well.bounding_box()["width"] * .8
            well.get_by_test_id("prepared-discard").click()
            shot("discard-question")
            question = well.locator("[data-question]")
            if phase == "after":
                expect(question).to_be_visible()
                expect(question.get_by_role("button", name="Cancel", exact=True)).to_be_focused()
            stored_prepared = next(s for s in _api(page, "GET", f"/api/channels/sends?document_ref={ref}", token=TOKEN)["sends"] if s["id"] == prepared["id"])
            assert stored_prepared["state"] == "prepared", "opening Discard must not write"
            question.get_by_role("button", name="Discard", exact=True).click()
            expect(well.get_by_test_id("prepared-result")).to_be_visible()
            if phase == "before":
                well.get_by_test_id("prepared-result").scroll_into_view_if_needed()
            shot("discarded")
            park_builtin_folder()
            with get_database()._connection() as conn:
                conn.execute("UPDATE channel_destinations SET state='parked'")
            page.reload()
            _normal_chair(page)
            press_verb(win.locator(".thought-note-toolbar"), 'Send…')
            well.get_by_test_id("send-none").wait_for()
            shot("no-destination")
            browser.close()
    finally:
        release.set()
        server.stop()


@pytest.mark.parametrize("width", [1440, 393])
@pytest.mark.timeout(180)
def test_review_9c_masked_send_and_fast_activation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    """Real hub/file effect: no masked press, multi-click or held-key dispatch."""
    from playwright.sync_api import sync_playwright, expect
    from .glass_infra import clear_hub_windows

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    shots = Path(__file__).resolve().parents[2] / ".tmp/evidence-shots/send-engines-r2-debug"
    shots.mkdir(parents=True, exist_ok=True)
    size = "900x600" if width == 1440 else "393"
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852}, reduced_motion="reduce")
            page.set_default_timeout(20000)
            page.goto(f"{base}/?token={TOKEN}")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)

            def note(text: str) -> str:
                made = _api(page, "POST", "/api/notes", {"title": "Review draft", "body_markdown": text, "tags": []}, token=TOKEN)
                return f"note:{made['note']['id']}"

            def seat(ref: str) -> Any:
                clear_hub_windows(page, token=TOKEN)
                page.goto(f"{base}/?open={ref}")
                _normal_chair(page)
                win = page.locator(f"[id='pullout:{ref}']")
                if width == 1440:
                    _api(page, "POST", f"/api/desk/windows/pullout:{ref}/set_geometry", {"rect": {"x": "-1/2 + 100", "y": "-1/2 + 80", "w": "900px", "h": "600px"}}, token=TOKEN)
                press_verb(win.locator(".thought-note-toolbar"), 'Send…')
                win.get_by_test_id("send-preview-body").wait_for()
                return win

            requests: list[Any] = []
            page.on("request", lambda request: requests.append(request) if request.url.endswith("/api/channels/send") else None)
            secret_ref = note("Token: github_pat_hiddenValue123\n\nRead the report before you send.")
            win = seat(secret_ref)
            expect(win.get_by_test_id("send-verb")).to_be_disabled()
            expect(win.locator(".surface-completion-state").get_by_text("This text holds a credential. Edit it before you send.", exact=True)).to_be_visible()
            expect(win.get_by_test_id("send-edit")).to_be_enabled()
            send_face_facts(win)
            page.screenshot(path=str(shots / f"send-credential-{size}-after.png"))
            dest = _api(page, "GET", "/api/channels/destinations", token=TOKEN)["destinations"][0]["id"]
            _api(page, "POST", "/api/channels/sends", {"document_ref": secret_ref, "destination_id": dest}, token=TOKEN)
            win = seat(secret_ref)
            expect(win.get_by_test_id("prepared-send")).to_be_disabled()
            expect(win.get_by_test_id("send-edit")).to_be_enabled()
            send_face_facts(win)
            page.screenshot(path=str(shots / f"send-prepared-credential-{size}-after.png"))
            assert not requests

            with page.expect_response(lambda response: response.request.method == "POST" and response.url.endswith("/api/notes")) as edited:
                win.get_by_test_id("send-edit").click()
            edited_id = edited.value.json()["note"]["id"]
            editor = page.locator(f"[id='pullout:note:{edited_id}'] .thought-note-body .cm-content")
            expect(editor).to_be_visible()
            expect(editor).to_contain_text("github_pat_hiddenValue123")
            editor.click()
            page.keyboard.press("ControlOrMeta+A")
            page.keyboard.type("The report is ready.\n" * 20)
            page.wait_for_function("""async id => {const r=await fetch('/api/notes/'+id,{headers:{Authorization:'Bearer send-grammar'}});const n=(await r.json()).note;return n.body_markdown.startsWith('The report is ready.') && !n.body_markdown.includes('github_pat_');}""",arg=edited_id)
            clean_ref = f"note:{edited_id}"
            win = page.locator(f"[id='pullout:{clean_ref}']")
            if width == 1440:
                _api(page,"POST",f"/api/desk/windows/pullout:{clean_ref}/set_geometry",{"rect":{"x":"-1/2 + 100","y":"-1/2 + 80","w":"900px","h":"600px"}},token=TOKEN)
            press_verb(win.locator(".thought-note-toolbar"), 'Send…')
            win.get_by_test_id("send-preview-body").wait_for()
            verb = win.get_by_test_id("send-verb")
            try:
                expect(verb).to_be_enabled()
            except AssertionError as exc:
                page.screenshot(path=str(shots / f"send-clean-diagnostic-{size}.png"))
                raise AssertionError({"face":win.inner_text(),"note":_api(page,"GET",f"/api/notes/{edited_id}",token=TOKEN),
                    "preview":_api(page,"POST","/api/channels/preview",{"document_ref":clean_ref,"destination_id":dest},token=TOKEN)}) from exc
            verb.click(click_count=1)
            expect(win.get_by_test_id("send-sent")).to_be_visible()
            expect(verb).to_be_enabled()
            box = verb.bounding_box()
            assert box
            page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            page.mouse.down(click_count=2)
            page.mouse.up(click_count=2)
            _settle(page)
            assert len(requests) == 1, "a double-click's second event dispatched after the first receipt"
            verb.focus()
            with page.expect_response(lambda response: response.url.endswith("/api/channels/send")):
                page.keyboard.down("Enter")
            expect(verb).to_be_enabled()
            assert len([s for s in _api(page,"GET",f"/api/channels/sends?document_ref={clean_ref}",token=TOKEN)["sends"] if s["state"] == "sent"]) == 2
            verb.focus()  # loading disabled the button and can move focus
            page.keyboard.down("Enter")
            _settle(page)
            assert len(requests) == 2, "held Return dispatched again after a fast receipt"
            page.keyboard.up("Enter")
            verb.focus()
            with page.expect_response(lambda response: response.url.endswith("/api/channels/send")):
                page.keyboard.press("Enter")
            expect(verb).to_be_enabled()
            assert len(requests) == 3
            assert len([s for s in _api(page,"GET",f"/api/channels/sends?document_ref={clean_ref}",token=TOKEN)["sends"] if s["state"] == "sent"]) == 3
            page.screenshot(path=str(shots / f"send-gesture-receipt-{size}-after.png"))
            browser.close()
    finally:
        server.stop()


@pytest.mark.parametrize("width", [1440, 393])
@pytest.mark.timeout(180)
def test_room_send_and_delivery_seats(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    """The shared Send status replaces Room state; custody keeps one retry."""
    from playwright.sync_api import sync_playwright, expect
    from .test_room_glass import SEAM
    from .test_room_os_grammar_glass import _verb

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    shots = Path(__file__).resolve().parents[2] / ".tmp/evidence-shots/send-engines-r2-debug"
    shots.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852}, reduced_motion="reduce")
            page.add_init_script(SEAM)
            page.goto(f"{base}/?token={TOKEN}")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            pid = _api(page, "POST", "/api/projects", {"name": "Ledger cutover"}, token=TOKEN)["project"]["id"]
            update = _api(page, "POST", f"/api/projects/{pid}/updates/draft", {"generator": "deterministic"}, token=TOKEN)["update"]
            _api(page, "PUT", f"/api/updates/{update['id']}", {"body_md": "The migration keeps the rollback path ready. " * 20}, token=TOKEN)
            _api(page, "POST", f"/api/updates/{update['id']}/publish", {}, token=TOKEN)
            # This rig's auth token differs from the general Room rig.
            _api(page, "POST", "/api/desk/windows/surface-project-memory/open", {"object_ref": f"project:{pid}"}, token=TOKEN)
            if width == 1440:
                _api(page, "POST", "/api/desk/windows/surface-project-memory/set_geometry", {"rect": {"x": "-1/2 + 100", "y": "-1/2 + 80", "w": "900px", "h": "600px"}}, token=TOKEN)
            page.reload()
            _normal_chair(page)
            win = page.locator("#surface-project-memory")
            win.get_by_role("tab", name="Updates", exact=True).click()
            win.locator(f"[data-object-id='{update['id']}']").click()
            _verb(page, win, "Send")
            expect(win.get_by_test_id("send-preview-body")).to_be_visible()
            expect(win.get_by_test_id("send-status").get_by_role("status")).to_have_text("New")
            expect(win.get_by_test_id("room-headline")).to_have_count(0)
            title = win.get_by_test_id("send-preview-body").get_by_role("heading").first
            assert not __import__("re").search(r"\d{4}-\d{2}-\d{2}", title.inner_text())
            send_face_facts(win, six_lines=width == 1440)
            page.screenshot(path=str(shots / f"1-5-room-send-{900 if width == 1440 else 393}.png"))
            polish = shots.parent / "send-engines14r3"
            polish.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(polish / f"1-5-room-send-{900 if width == 1440 else 393}-{os.environ.get('SEND_GRAMMAR_PHASE', 'after')}.png"))
            win.get_by_test_id("send-back").click()
            _verb(page, win, "Mark delivered")
            to = win.get_by_role("textbox", name="Delivered to", exact=True)
            expect(to).to_have_attribute("placeholder", "No recipient")
            page.screenshot(path=str(shots / f"6-room-custody-empty-{900 if width == 1440 else 393}.png"))
            polish = shots.parent / "send-engines14r3"
            polish.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(polish / f"6-room-custody-empty-{900 if width == 1440 else 393}-{os.environ.get('SEND_GRAMMAR_PHASE', 'after')}.png"))
            to.fill("Steering group")
            page.evaluate("window.__dropDelivery=true")
            win.locator(".surface-inspector-actions").get_by_role("button", name="Mark delivered", exact=True).click()
            expect(win.get_by_text("Result unknown", exact=True)).to_have_count(1)
            expect(win.get_by_test_id("delivery-status").get_by_role("status")).to_have_text("Result unknown")
            expect(win.get_by_test_id("room-headline")).to_have_count(0)
            expect(win.get_by_role("button", name="Try again", exact=True)).to_be_visible()
            expect(win.get_by_text("Result unknown · Try again", exact=True)).to_have_count(0)
            page.screenshot(path=str(shots / f"7-room-custody-unknown-{900 if width == 1440 else 393}.png"))
            polish = shots.parent / "send-engines14r3"
            polish.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(polish / f"7-room-custody-unknown-{900 if width == 1440 else 393}-{os.environ.get('SEND_GRAMMAR_PHASE', 'after')}.png"))
            win.get_by_role("button", name="Try again", exact=True).click()
            expect(to).to_have_value("")
            page.screenshot(path=str(shots / f"6-room-custody-saved-{900 if width == 1440 else 393}.png"))
            polish = shots.parent / "send-engines14r3"
            polish.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(polish / f"6-room-custody-saved-{900 if width == 1440 else 393}-{os.environ.get('SEND_GRAMMAR_PHASE', 'after')}.png"))
            browser.close()
    finally:
        server.stop()
