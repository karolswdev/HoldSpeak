"""Declared library direction only; run through .tmp/entry/locked.py."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

out = Path(__file__).resolve().parents[4] / ".tmp" / "entry" / "canvas-presence-shots"
out.mkdir(parents=True, exist_ok=True)
facts = []
with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    for width, height in ((1440, 900), (393, 852)):
        page = browser.new_page(viewport={"width": width, "height": height}, has_touch=width == 393, reduced_motion="reduce")
        for face in ("ready", "long", "connecting", "error"):
            page.goto(f"http://127.0.0.1:4499/?face={face}&context=declared-sample")
            page.locator(".presence-activity .gadget-lamp.is-block").wait_for()
            page.wait_for_function("document.getAnimations().every(a => a.playState !== 'running' || a.effect.getTiming().iterations === Infinity)")
            page.screenshot(path=str(out / f"presence-{face}-{width}.png"))
            fact = page.evaluate("""() => {
              const card=document.querySelector('.presence-card'), lamp=document.querySelector('.gadget-lamp'), button=document.querySelector('.presence-back');
              const rect=el=>{const r=el.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height,scrollWidth:el.scrollWidth,clientWidth:el.clientWidth};};
              return {face:new URLSearchParams(location.search).get('face'),width:innerWidth,height:innerHeight,documentWidth:document.documentElement.scrollWidth,
                card:rect(card),lamp:{...rect(lamp),label:lamp.textContent,on:lamp.dataset.on,tone:lamp.dataset.tone},button:rect(button)};
            }""")
            button = page.get_by_role("button", name="Desk", exact=True)
            target = button.evaluate("""el => {
              const r=el.getBoundingClientRect(),after=getComputedStyle(el,'::after');
              const halo=el.matches('.btn')&&after.content!=='none'?parseFloat(after.height)||0:0;
              const height=Math.max(r.height,halo);
              return {x:r.x,y:r.y+(r.height-height)/2,width:r.width,height};
            }""")
            points = []
            for fx, fy in ((.5,.5),(.5/target["width"],.5),(1-.5/target["width"],.5),(.5,.5/target["height"]),(.5,1-.5/target["height"]),(.5/target["width"],.5/target["height"]),(1-.5/target["width"],.5/target["height"]),(.5/target["width"],1-.5/target["height"]),(1-.5/target["width"],1-.5/target["height"])):
                point = {"x": target["x"] + target["width"]*fx, "y": target["y"] + target["height"]*fy}
                page.mouse.move(point["x"], point["y"])
                points.append(button.evaluate("""(el,p) => {const hit=document.elementFromPoint(p.x,p.y);return {...p,owned:hit===el||el.contains(hit)};}""", point))
            assert all(point["owned"] for point in points), (face, width, target, points)
            if width == 393:
                assert target["width"] >= 44 and target["height"] >= 44, target
            fact["return_target"] = {**target, "points": points}
            facts.append(fact)
            print(f"presence-{face}-{width}.png")
        page.close()
    browser.close()
(out / "facts.json").write_text(json.dumps(facts, indent=2))
