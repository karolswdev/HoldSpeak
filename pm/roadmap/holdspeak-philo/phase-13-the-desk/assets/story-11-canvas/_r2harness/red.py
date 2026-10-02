"""Round-two boards (commit 1467d9173's harness, unchanged) measured by round three's R8 fences.
Writes ../shots/red-before-r2.json. Each fence must be RED here and GREEN on round three."""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rig  # the round-two rig
sys.path.insert(0, str(HERE.parent / "harness"))
import importlib.util
spec = importlib.util.spec_from_file_location("shoot3", HERE.parent / "harness" / "shoot.py")
s3 = importlib.util.module_from_spec(spec); spec.loader.exec_module(s3)
from playwright.sync_api import sync_playwright

out = {}
def measure(pg, key, phone, front):
    f = {"own": pg.evaluate(s3.OWN), "front_state": pg.evaluate(s3.FRONT), "low_contrast": pg.evaluate(s3.CONTRAST_ALL), "dockfacts": pg.evaluate(s3.DOCKFACTS)}
    if phone:
        f["targets_under_44"] = pg.evaluate(s3.TARGETS44); f["content_px"] = pg.evaluate(s3.CONTENT)
    fs = f["front_state"]
    f["red"] = {
        "ownership (all nine points)": [o for o in f["own"] if o["lost"]][:6],
        "visible state": None if (front is None or (fs["front"] == front and fs["on_glass"])) else {"intended": front, "recorded": fs["front"], "on_glass": fs["on_glass"]},
        "one blue bar": None if len(fs["blue"]) == 1 else fs["blue"],
        "in-place contrast": f["low_contrast"][:6],
        "zero badge": f["dockfacts"]["zeros"] or None,
        "project missing from the Dock": f["dockfacts"]["missing"] or None,
    }
    if phone:
        f["red"]["393 content ≥ 700"] = None if (f["content_px"] or 0) >= 700 else f["content_px"]
        f["red"]["393 targets ≥ 44"] = f["targets_under_44"][:6]
    out[key] = f["red"]
    print(key, json.dumps(f["red"])[:900], flush=True)

for width, height in [(1440, 900), (393, 852)]:
    phone = width < 500
    with rig.Stack("proposal") as st, sync_playwright() as p:
        b = p.chromium.launch(); ctx = b.new_context(viewport={"width": width, "height": height}, has_touch=phone)
        pg = ctx.new_page()
        for attempt in range(3):
            pg.goto(st.url); pg.locator(".chair").wait_for(timeout=120000)
            for _ in range(30):
                cl = pg.get_by_role("button", name="Continue later", exact=True)
                if not cl.count(): break
                try: cl.first.click(timeout=2000)
                except Exception: pass
                pg.wait_for_timeout(500)
            try:
                pg.locator("[data-testid=p13-chairdesk]").wait_for(timeout=30000); break
            except Exception:
                pg.wait_for_timeout(3000)
        pg.wait_for_timeout(3000)
        pg.evaluate("() => window.__p13.live({rec: '12:04', oneOnOne: '14:30', projects: {'p-ledger': 3, 'p-obs': 1}})")
        pg.evaluate("() => window.__p13.chairFront('needs')"); pg.wait_for_timeout(800)
        measure(pg, f"C1-1-{width}", phone, "Needs you")
        pg.evaluate("() => window.__p13Open.surface('review-meetings')"); pg.wait_for_timeout(2500)
        pg.evaluate("() => window.__p13Open.room('p-ledger')"); pg.wait_for_timeout(3000)
        measure(pg, f"C1-2a-{width}", phone, "Payments ledger cutover")
        pg.evaluate("() => window.__p13Open.closeAll()"); pg.wait_for_timeout(800)
        pg.evaluate("() => window.__p13.sheet(true)"); pg.wait_for_timeout(900)
        measure(pg, f"C1-3-{width}", phone, "Material")
        pg.evaluate("() => window.__p13.sheet(false)"); pg.wait_for_timeout(500)
        if phone:
            pg.evaluate(f"() => window.__p13Open.open('workbench:{st.seed['workbench']}')"); pg.wait_for_timeout(2500)
            pg.evaluate("() => window.__p13Open.closeAll()"); pg.wait_for_timeout(800)
            pg.evaluate("() => { window.__p13.phoneOpen('needs'); window.__p13.chairFront('needs'); }"); pg.wait_for_timeout(800)
            measure(pg, f"C1-6a-{width}", phone, "Needs you")
            pg.evaluate("() => window.__p13Open.surface('open-people')"); pg.wait_for_timeout(2500)
            measure(pg, f"C1-6b-{width}", phone, "People")
        b.close()
(HERE.parent / "shots" / "red-before-r2.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
