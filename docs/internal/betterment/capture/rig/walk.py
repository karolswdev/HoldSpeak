"""Run one walk step file against a rig hub: walk.py <port> <1440|393> <step.py> [url-suffix]"""
import os, sys, time, runpy
from playwright.sync_api import sync_playwright
SCR = os.path.dirname(os.path.abspath(__file__))
SHOTS = "/Users/karol/dev/tools/HoldSpeak/docs/internal/betterment/capture/shots"
port = sys.argv[1]; vp = int(sys.argv[2]); step = sys.argv[3]
suffix = sys.argv[4] if len(sys.argv) > 4 else "/"
URL = f"http://127.0.0.1:{port}{suffix}{'&' if '?' in suffix else '?'}token=graph-walk-token"
T0 = time.time()
with sync_playwright() as p:
    kw = dict(viewport={"width": 1440, "height": 900}) if vp == 1440 else dict(
        viewport={"width": 393, "height": 852}, device_scale_factor=2, is_mobile=True, has_touch=True)
    ctx = p.chromium.launch_persistent_context(os.path.join(SCR, f"profile-{port}-{vp}"), headless=True,
        args=["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream"],
        permissions=["microphone"], **kw)
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    logs = []
    page.on("console", lambda m: logs.append(f"{m.type}: {m.text}") if m.type in ("error", "warning") else None)
    def shot(name, full=False):
        path = os.path.join(SHOTS, f"{name}-{vp}.png")
        page.screenshot(path=path, full_page=full)
        print(f"SHOT {os.path.basename(path)} t={time.time()-T0:.1f}s")
    def text(sel="body", n=3000):
        try:
            t = page.locator(sel).first.inner_text(timeout=3000)
        except Exception as e:
            t = f"<no text: {e}>"
        print(f"TEXT[{sel}]:", t[:n].replace("\n", " | "))
    def wait(s): time.sleep(s)
    page.set_default_timeout(8000); page.goto(URL); page.wait_for_load_state("load")
    time.sleep(3)
    _cl = page.get_by_role("button", name="Continue later")
    if _cl.count() and "--keep-firstrun" not in sys.argv: _cl.first.click(); time.sleep(1.5)
    runpy.run_path(step, init_globals=dict(page=page, shot=shot, text=text, wait=wait, vp=vp, T0=T0))
    if logs: print("CONSOLE:", logs[-8:])
    ctx.close()
