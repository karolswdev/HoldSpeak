exec(open("steps/lib.py").read())
import time
def choose(name, tag):
    close_all(page, wait)
    page.keyboard.press("Meta+Shift+p"); wait(2)
    c = page.locator('[role="region"][aria-label="Change places"] button', has_text=name).first
    c.scroll_into_view_if_needed(); c.click(); wait(6)
    shot(f"51-scene-{tag}-with-window")
    close_all(page, wait); wait(3)
    shot(f"52-scene-{tag}-desk")
    page.locator('.desk-dock [aria-label^="Meetings"]').first.click(); wait(3)
    shot(f"53-scene-{tag}-meetings")
    fr = page.evaluate("""() => new Promise(r => {let n=0; const t0=performance.now(); function f(){n++; if(performance.now()-t0<2000) requestAnimationFrame(f); else r(n/2)} requestAnimationFrame(f)})""")
    print(tag, "fps(headless)", fr)
for name, tag in [("NIGHT TRAIN","night-train"), ("JUPITER","jupiter"), ("RAINY CITY","rainy-city")]:
    choose(name, tag)
# back to default
close_all(page, wait)
page.keyboard.press("Meta+Shift+p"); wait(2)
c = page.locator('[role="region"][aria-label="Change places"] button', has_text="QUIET DESK").first
c.scroll_into_view_if_needed(); c.click(); wait(3)
close_all(page, wait)
