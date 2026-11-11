"""Local live-piece specimens on the existing seeded Components sweep rig."""
from __future__ import annotations

import json
from typing import Any

import pytest

from tests._evidence import evidence_dir
from tests.e2e.glass_infra import clear_hub_windows_http
from tests.e2e.test_desk_sweep import (
    TOKEN, T, CLIPPED_JS, _Case, _hub_open, _normal_chair, _page,
    desk, pw_browser,  # noqa: F401 -- reuse the one seeded sweep rig
)

FACTS_JS = r"""() => {
 const root = document.querySelector('[data-testid=reference-live]');
 const seen = el => {const r=el.getBoundingClientRect();return r.width && r.height && getComputedStyle(el).visibility==='visible';};
 const sizes=[...root.querySelectorAll('*')].filter(seen).filter(el=>!el.closest('[aria-hidden=true]')).filter(el=>[...el.childNodes].some(n=>n.nodeType===3 && n.textContent.trim())).map(el=>({text:el.textContent.trim(),px:parseFloat(getComputedStyle(el).fontSize)}));
 const rgb = c => (c.match(/[\d.]+/g)||[]).slice(0,3).map(Number);
 const lum=c=>{const a=rgb(c).map(x=>{x/=255;return x<=.04045?x/12.92:((x+.055)/1.055)**2.4;});return .2126*a[0]+.7152*a[1]+.0722*a[2];};
 const contrast=(a,b)=>{const x=lum(a),y=lum(b);return +((Math.max(x,y)+.05)/(Math.min(x,y)+.05)).toFixed(2);};
 const colors=[];
 for(const selected of [false,true]) {
  const row=document.createElement('div');row.className='object-list-row';row.dataset.selected=String(selected);row.style.cssText='position:absolute;left:-10000px';root.append(row);
  const bg=getComputedStyle(root).getPropertyValue(selected?'--wb-sel':'--wb-paper').trim();
  const ground=document.createElement('span');ground.style.background=bg;row.append(ground);const back=getComputedStyle(ground).backgroundColor;
  for(const state of ['working','waiting','done','tonight','off']) {
   const mark=document.createElement('span');mark.className='surface-lamp';mark.dataset.state=state;row.append(mark);
   const cs=getComputedStyle(mark); const ink=cs.backgroundColor==='rgba(0, 0, 0, 0)' ? cs.getPropertyValue('--lamp-ink').trim() : cs.backgroundColor;
   const chip=document.createElement('span');chip.style.color=ink;row.append(chip);const fg=getComputedStyle(chip).color;
   colors.push({state,selected,fill:fg,ground:back,contrast:contrast(fg,back),outline:cs.outlineColor,outlineWidth:cs.outlineWidth,outlineContrast:contrast(cs.outlineColor,back),shadow:cs.boxShadow});
  }
  row.remove();
 }
 const deck=root.querySelector('[data-testid=program-deck]');
 const box=deck?.getBoundingClientRect();
 const meterColors=[];
 for(const selected of [false,true]) {
  const row=document.createElement('div');row.dataset.selected=String(selected);row.style.cssText='position:absolute;left:-10000px';root.append(row);
  const ground=document.createElement('span');ground.style.background=getComputedStyle(root).getPropertyValue(selected?'--wb-sel':'--wb-paper');row.append(ground);
  const bg=getComputedStyle(ground).backgroundColor;
  for(const state of ['done','working','waiting','parked','planned']) {
   const meter=document.createElement('span');meter.className='surface-meter';const mark=document.createElement('i');mark.dataset.state=state;meter.append(mark);row.append(meter);
   const ink=getComputedStyle(mark).backgroundColor;meterColors.push({state,selected,fill:ink,ground:bg,contrast:contrast(ink,bg)});
  }
  row.remove();
 }
 return {sizes,colors,meterColors,deck:box?{width:box.width,height:box.height,scrollHeight:deck.scrollHeight,clientHeight:deck.clientHeight}:null};
}"""


@pytest.mark.parametrize("width", [900, 393])
def test_live_program_deck(desk: dict[str, Any], pw_browser: Any, width: int) -> None:
    base = desk["base"]
    clear_hub_windows_http(base, TOKEN)
    _hub_open(base, "surface-components", None, window=width == 900)
    ctx, page, errors, requests = _page(pw_browser, width, base)
    out = evidence_dir("live1")
    try:
        page.goto(f"{base}/?token={TOKEN}", wait_until="load")
        _normal_chair(page)
        sweep = _Case(page, base, "surface-components", errors, requests)
        sweep.settle()
        win = page.locator("#surface-components")
        win.get_by_test_id("reference-group-live").click()
        win.get_by_test_id("program-deck").wait_for(timeout=T)
        facts = {}
        for state in ["waiting", "working", "done"]:
            win.get_by_role("combobox", name="Example state").select_option(state)
            page.mouse.move(2, 2)
            sweep.settle()
            # At narrow sizes the list owns the first view. Open uses the same
            # selection verb and brings the seat into this window.
            if width == 393:
                page.screenshot(path=str(out / f"program-deck-{state}-{width}-list.png"))
                win.get_by_role("button", name="Open", exact=True).click()
            sweep.settle()
            facts[state] = page.evaluate(FACTS_JS)
            facts[state]["clipped"] = page.evaluate(CLIPPED_JS, '#surface-components [data-testid=reference-live]')
            page.screenshot(path=str(out / f"program-deck-{state}-{width}.png"))
            sweep.fences(state)
            if state == "waiting":
                answer = win.get_by_role("button", name="Go on", exact=True)
                assert answer.is_visible()
                bounds = answer.bounding_box()
                seat = win.locator(".surface-pane-inspector").bounding_box()
                assert bounds["y"] + bounds["height"] <= seat["y"] + seat["height"]
                question = win.get_by_text("The check passed. Keep the changes and go on?", exact=True).bounding_box()
                assert question["y"] >= seat["y"] and question["y"] + question["height"] <= bounds["y"]
            assert not facts[state]["clipped"], facts[state]["clipped"]
            (out / f"facts-{width}.json").write_text(json.dumps({"engine":"none","width":width,"states":facts,"fences":sweep.failures}, indent=2))
            assert all(item["px"] >= 12 for item in facts[state]["sizes"]), facts[state]["sizes"]
            if state == "working":
                screen = win.get_by_role("log", name="Agent screen")
                assert screen.get_attribute("data-feedback-redact") == "true"
                first = screen.inner_text()
                page.wait_for_function("before => document.querySelector('[role=log]').innerText !== before", arg=first, timeout=10_000)
                assert screen.get_attribute("aria-live") == "off"
            for color in facts[state]["colors"]:
                if color["state"] != "off":
                    assert max(color["contrast"], color["outlineContrast"] if color["outlineWidth"] != "0px" else 0) >= 3, color
            for color in facts[state]["meterColors"]:
                if color["state"] != "planned":
                    assert color["contrast"] >= 3, color
            assert facts[state]["deck"]["scrollHeight"] <= facts[state]["deck"]["clientHeight"] + 1
        (out / f"facts-{width}.json").write_text(json.dumps({"engine":"none","width":width,"states":facts,"fences":sweep.failures}, indent=2))
        assert not sweep.failures, json.dumps(sweep.failures, indent=2)
        # Each piece alone uses the same reduced-motion and fit fences.
        for piece in ["Lamp", "Meter", "Step track", "Live well", "Elapsed", "Inspector figures"]:
            win.get_by_role("combobox", name="Live piece").select_option(piece)
            sweep.settle()
            page.screenshot(path=str(out / f"{piece.lower().replace(' ', '-')}-{width}.png"))
            sweep.fences(piece)
            if piece == "Step track":
                strip = win.get_by_role("tablist", name="Example steps")
                assert strip.evaluate("el => el.scrollWidth > el.clientWidth && el.scrollLeft > 0")
                assert strip.evaluate("el => {const b=el.getBoundingClientRect(),s=el.querySelector('[aria-current=step]').getBoundingClientRect();return s.left>=b.left && s.right<=b.right}")
        assert not sweep.failures, json.dumps(sweep.failures, indent=2)
        # Motion is also exercised with the owner's normal preference. The
        # unchanged sweep above ran under reduce; do not silence its recorder.
        win.get_by_role("combobox", name="Live piece").select_option("Program deck")
        win.get_by_role("combobox", name="Example state").select_option("working")
        if width == 393:
            win.get_by_role("button", name="Open", exact=True).click()
        page.emulate_media(reduced_motion="no-preference")
        animations = """() => document.getAnimations().filter(a => document.querySelector('[data-testid=reference-live]').contains(a.effect?.target)).map(a=>a.animationName)"""
        page.wait_for_function("""() => document.getAnimations().some(a => a.animationName === 'surface-step-travel')""")
        normal = page.evaluate(animations)
        assert "surface-lamp-breathe" in normal and "surface-step-travel" in normal
        page.emulate_media(reduced_motion="reduce")
        page.wait_for_function("""() => !document.getAnimations().some(a => document.querySelector('[data-testid=reference-live]').contains(a.effect?.target))""")
        assert page.evaluate(animations) == []
        (out / f"motion-{width}.json").write_text(json.dumps({"normal":normal,"reduced":[]}, indent=2))
    finally:
        ctx.close()
