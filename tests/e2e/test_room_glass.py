"""Real Room update, delivery and read custody on the selection grammar."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair
from .test_room_os_grammar_glass import _verb

TOKEN = "room-update-grammar10"
OUT = Path(__file__).resolve().parents[2] / ".tmp/evidence-shots/room11"

SEAM = r"""(() => {
 const real=window.fetch.bind(window); window.__deliveryCalls=[];window.__dropDelivery=false;
 window.fetch=async(input,init)=>{
  const url=typeof input==='string'?input:input.url;
  if(!/\/api\/updates\/[^/]+\/delivered$/.test(url))return real(input,init);
  window.__deliveryCalls.push({url,body:JSON.parse(init.body)});
  const drop=window.__dropDelivery;window.__dropDelivery=false;
  const answer=await real(input,init);
  if(drop){await answer.text();throw new TypeError('Injected lost reply');}
  return answer;
 };
})()"""


def _open(page: Any, base: str, pid: str, width: int) -> Any:
    _api(page, "POST", "/api/desk/windows/surface-project-memory/open", {"object_ref": f"project:{pid}"}, token=TOKEN)
    if width == 1440:
        _api(page, "POST", "/api/desk/windows/surface-project-memory/set_geometry", {"rect": {"x": "-1/2 + 100", "y": "-1/2 + 80", "w": "900px", "h": "600px"}}, token=TOKEN)
    page.reload(wait_until="load")
    _normal_chair(page)
    return page.locator("#surface-project-memory")


@pytest.mark.parametrize("width", [1440, 393])
def test_update_wrap_save_publish_and_delivery_custody(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    from playwright.sync_api import sync_playwright, expect

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852}, reduced_motion="reduce")
            page.set_default_timeout(15000)
            page.add_init_script(SEAM)
            page.goto(f"{base}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            pid = _api(page, "POST", "/api/projects", {"name": "Ledger cutover"}, token=TOKEN)["project"]["id"]
            earlier = _api(page, "POST", f"/api/projects/{pid}/updates/draft", {"generator": "deterministic"}, token=TOKEN)["update"]
            _api(page, "POST", f"/api/updates/{earlier['id']}/publish", {}, token=TOKEN)
            update = _api(page, "POST", f"/api/projects/{pid}/updates/draft", {"generator": "deterministic"}, token=TOKEN)["update"]
            text = "The ledger cutover is ready for the controlled migration window. " * 8
            saved = _api(page, "PUT", f"/api/updates/{update['id']}", {"body_md": text}, token=TOKEN)["update"]
            win = _open(page, base, pid, width)
            win.get_by_role("tab", name="Updates", exact=True).click()
            row = win.locator(f"[data-object-id='{update['id']}']")
            row.click()
            _verb(page, win, "Edit")
            editor = win.get_by_role("textbox", name="Update body", exact=True)
            assert "controlled migration window" in editor.input_value()
            bounds = editor.evaluate("e=>({scroll:e.scrollWidth,client:e.clientWidth,whiteSpace:getComputedStyle(e).whiteSpace})")
            assert bounds["scroll"] <= bounds["client"] + 1, bounds
            assert bounds["whiteSpace"] in ("pre-wrap", "normal", "pre-line", "break-spaces"), bounds
            editor.fill(text + "The rollback path stays ready.")
            save = win.locator(".surface-inspector-actions").get_by_role("button", name="Save", exact=True)
            save.click()
            expect(save).to_be_disabled()
            read = _api(page, "GET", f"/api/updates/{update['id']}", token=TOKEN)["update"]
            assert "The rollback path stays ready." in read["body_md"]
            _verb(page, win, "Publish")
            expect(win.get_by_role("textbox", name="Update body", exact=True)).to_have_count(0)
            _verb(page, win, "Send")
            expect(win.get_by_test_id("send-sheet")).to_be_visible()
            expect(win.get_by_role("combobox", name="Destination", exact=True)).to_be_visible()
            expect(win.get_by_test_id("send-preview-body")).to_contain_text("The rollback path stays ready.")
            expect(win.get_by_test_id("send-verb")).to_be_visible()
            from .send_face_facts import send_face_facts
            send_face_facts(win, six_lines=width == 1440)
            if width == 1440 and os.environ.get("HOLDSPEAK_WIRE_WRITE") == "1":
                destinations = _api(page, "GET", "/api/channels/destinations", token=TOKEN)
                ref = f"project_update:{update['id']}"
                tape = {
                    "provenance": "test_room_glass.py: real isolated room, two updates and local folder preview; engine none",
                    "room": _api(page, "GET", f"/api/projects/{pid}/room", token=TOKEN),
                    "updates": _api(page, "GET", f"/api/projects/{pid}/updates", token=TOKEN),
                    "destinations": destinations,
                    "preview": _api(page, "POST", "/api/channels/preview", {"document_ref": ref, "destination_id": destinations["destinations"][0]["id"]}, token=TOKEN),
                }
                target = Path(__file__).resolve().parents[2] / "web/src/features/project-room/__tests__/room-wires/send-handoff.json"
                target.write_text(json.dumps(tape, indent=2) + "\n")
            expect(win.get_by_test_id("send-well")).not_to_have_attribute("aria-busy", "true")
            suffix = "900x600" if width == 1440 else "393"
            page.screenshot(path=str(OUT / f"published-send-seat-{suffix}-after.png"))
            assert _api(page, "GET", f"/api/updates/{update['id']}", token=TOKEN)["update"]["deliveries"] == []
            win.get_by_test_id("send-back").click()
            _verb(page, win, "Mark delivered")
            to = win.get_by_role("textbox", name="Delivered to", exact=True)
            to.fill("Steering group")
            page.evaluate("window.__dropDelivery=true")
            win.locator(".surface-inspector-actions").get_by_role("button", name="Mark delivered", exact=True).click()
            unknown = win.get_by_text("Result unknown", exact=True)
            expect(unknown).to_be_visible()
            expect(win.get_by_text("No delivery result", exact=True)).to_have_count(0)
            expect(win.get_by_text("Result unknown", exact=True)).to_have_count(1)
            expect(win.locator(f"[data-object-id='{earlier['id']}']")).to_be_visible()
            expect(win.locator(f"[data-object-id='{update['id']}']")).to_be_visible()
            assert unknown.evaluate("e=>{const r=e.getBoundingClientRect(),w=e.closest('[data-layer=window]').getBoundingClientRect();return r.bottom<=w.bottom && r.top>=w.top;}")
            expect(to).to_have_count(0)
            expect(win.locator('span[data-feedback-redact="true"]', has_text="Steering group")).to_be_visible()
            page.screenshot(path=str(OUT / f"delivery-unknown-{suffix}-after.png"))
            first = page.evaluate("window.__deliveryCalls[0]")
            win.locator(".surface-inspector-actions").get_by_role("button", name="Try again", exact=True).click()
            expect(to).to_be_enabled()
            expect(to).to_have_value("")
            calls = page.evaluate("window.__deliveryCalls")
            assert len(calls) == 2 and calls[0] == calls[1], calls
            read = _api(page, "GET", f"/api/updates/{update['id']}", token=TOKEN)["update"]
            assert len(read["deliveries"]) == 1 and read["deliveries"][0]["delivered_to"] == "Steering group", read
            # A second acknowledged owner press is a second delivery, not a retry.
            to.fill("Architecture guild")
            win.locator(".surface-inspector-actions").get_by_role("button", name="Mark delivered", exact=True).click()
            expect(to).to_have_value("")
            read = _api(page, "GET", f"/api/updates/{update['id']}", token=TOKEN)["update"]
            assert [row["delivered_to"] for row in read["deliveries"]] == ["Steering group", "Architecture guild"]
            expect(win.locator(f"[data-object-id='{update['id']}']")).to_be_visible()
            if width == 1440:
                expect(win.get_by_role("grid", name="Updates")).to_contain_text("Steering group · Architecture guild")
            suffix = "900x600" if width == 1440 else "393"
            page.screenshot(path=str(OUT / f"delivery-custody-{suffix}-after.png"))
            browser.close()
    finally:
        server.stop()
