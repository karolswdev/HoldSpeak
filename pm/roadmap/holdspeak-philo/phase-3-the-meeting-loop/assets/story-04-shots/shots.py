"""PHILO-3-04 shots: the real Thought foot in its four states, on a real hub in an isolated HOME."""
import importlib.util, json, re, shutil, sys, tempfile, time
from pathlib import Path
REPO = Path("/Users/karol/dev/tools/wt-philo-3-04")
spec = importlib.util.spec_from_file_location("gw", REPO / "scripts/graph_walk.py")
gw = importlib.util.module_from_spec(spec); sys.modules["gw"] = gw; spec.loader.exec_module(gw)
from playwright.sync_api import sync_playwright

OUT = REPO / "pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-04-shots"
WRITE = ".thought-note-foot .surface-footer-receipt-line:not([data-line])"
FILING = ".thought-note-foot .surface-footer-receipt-line[data-line=filing]"
facts = []

def foot(page):
    w = page.locator(WRITE); f = page.locator(FILING)
    return {"write": w.first.inner_text() if w.count() else None, "filing": f.first.inner_text() if f.count() else None,
            "filing_line_font_px": page.eval_on_selector(FILING, "e => getComputedStyle(e).fontSize"),
            "verbs": page.locator(".thought-note-foot .surface-footer-verbs button").all_inner_texts()}

def shot(page, width, name):
    path = OUT / f"{width}-{name}.png"
    page.locator(".thought-workspace-window").screenshot(path=str(path))
    row = {"width": width, "state": name, "shot": str(path.relative_to(REPO)), **foot(page)}
    facts.append(row); print(json.dumps(row, ensure_ascii=False))

def wait_write(page, pattern, timeout=15000):
    page.wait_for_function("([sel, re]) => { const e = document.querySelector(sel); return !!e && new RegExp(re).test(e.innerText); }",
                           arg=[WRITE, pattern], timeout=timeout)

def run(width):
    home = Path(tempfile.mkdtemp(prefix="philo304-home-")); profile = Path(tempfile.mkdtemp(prefix="philo304-prof-"))
    hub = gw.Hub(home).start()
    print("HUB", hub.url, "DB", hub.db_path)
    try:
        with sync_playwright() as play:
            ctx = play.chromium.launch_persistent_context(str(profile), viewport={"width": width, "height": 900 if width >= 1000 else 852},
                                                          device_scale_factor=2, base_url=hub.url)
            page = ctx.new_page()
            page.goto(f"{hub.url}/?token={gw.TOKEN}")
            try: page.get_by_role("button", name="Continue later").click(timeout=8000)
            except Exception: pass
            page.locator("[data-testid=arrival-develop-thought]").click()
            body = page.locator('[aria-label="Note body"]'); body.wait_for()
            # 1 KEPT — the hub's stamp on the write
            with page.expect_response(lambda r: r.request.method == "PATCH" and r.url.endswith("/working")) as resp:
                body.fill("Drain the queue before the cutover.")
            payload = resp.value.json(); stamp = payload["thought"]["working_note"]["last_modified"]
            thought_id = payload["thought"]["id"]
            wait_write(page, "^KEPT · "); page.wait_for_timeout(300)
            print("PATCH last_modified", stamp, "directory_name", payload["thought"].get("directory_name"))
            shot(page, width, "1-kept")
            facts[-1]["patch_last_modified"] = stamp
            # 2 SAVING… — the PATCH held at the browser boundary
            held = []
            page.route("**/api/thoughts/*/working", lambda route: held.append(route))
            body.fill("Drain the queue before the cutover. Ask Priya.")
            wait_write(page, "^SAVING…$"); page.wait_for_timeout(700)
            shot(page, width, "2-saving")
            for r in held: r.continue_()
            page.unroute("**/api/thoughts/*/working")
            wait_write(page, "^KEPT · ")
            # 3a DID NOT SAVE — no response (the request aborted at the browser boundary)
            page.route("**/api/thoughts/*/working", lambda route: route.abort("failed"))
            body.fill("Drain the queue before the cutover. Ask Priya which consumers.")
            wait_write(page, "^DID NOT SAVE · THE HUB DID NOT ANSWER$"); page.wait_for_timeout(200)
            shot(page, width, "3a-did-not-save-no-answer")
            page.unroute("**/api/thoughts/*/working")
            page.locator(".thought-note-foot").get_by_role("button", name="Retry").click()
            wait_write(page, "^KEPT · ")
            # 3b DID NOT SAVE — the hub answered 500 (fulfilled at the browser boundary)
            page.route("**/api/thoughts/*/working", lambda route: route.fulfill(status=500, content_type="application/json", body='{"error":"boom"}'))
            body.fill("Drain the queue before the cutover. Ask Priya which consumers read it.")
            wait_write(page, "^DID NOT SAVE · THE HUB DID NOT ACCEPT THE CHANGE$"); page.wait_for_timeout(200)
            shot(page, width, "3b-did-not-save-not-accepted")
            page.unroute("**/api/thoughts/*/working")
            page.locator(".thought-note-foot").get_by_role("button", name="Retry").click()
            wait_write(page, "^KEPT · ")
            # 4 CHANGED ELSEWHERE — a real second writer on the hub's own route
            status, current = hub.api("GET", f"/api/thoughts/{thought_id}")
            t = current.get("thought", current)
            status2, _ = hub.api("PATCH", f"/api/thoughts/{thought_id}/working", {
                "expected_aggregate_revision": t["aggregate_revision"], "expected_working_revision": t["working_revision"],
                "body_markdown": "Written elsewhere."})
            print("second writer", status, status2)
            body.fill("Drain the queue before the cutover. My edit.")
            wait_write(page, "^CHANGED ELSEWHERE$"); page.wait_for_timeout(200)
            shot(page, width, "4-changed-elsewhere")
            ctx.close()
    finally:
        hub.stop(); shutil.rmtree(profile, ignore_errors=True); shutil.rmtree(home, ignore_errors=True)

for w in (1440, 393):
    run(w)
(OUT / "shots-facts.json").write_text(json.dumps(facts, indent=2, ensure_ascii=False) + "\n")
