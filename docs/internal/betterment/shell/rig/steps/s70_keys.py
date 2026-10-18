exec(open("steps/lib.py").read())
import time
close_all(page, wait); wait(0.5)
page.locator("body").click(position={"x":700,"y":500}); wait(0.3)
for chord, tag in [("Control+1","speak"),("Control+2","meetings"),("Control+3","conductor"),("Control+4","settings"),("Meta+i","ask")]:
    n0 = page.locator('header.desk-pullout-head').count()
    t = time.time(); page.keyboard.press(chord)
    try:
        page.wait_for_function(f"document.querySelectorAll('header.desk-pullout-head').length > {n0}", timeout=6000)
        print(chord, tag, "opened in", round(time.time()-t,2), "s", boxes(page)[-1] if boxes(page) else None)
    except Exception: print(chord, tag, "no new window", boxes(page))
    wait(0.8)
shot("70-keys-five-windows")
page.keyboard.press("Meta+/"); wait(1); shot("71-shortcut-sheet"); text(".desk-shortcut-sheet, [role='dialog']", 2000)
page.keyboard.press("Escape"); wait(0.4)
for i in range(3): page.keyboard.press("Meta+`"); wait(0.4)
print("front after cycles:", page.locator(".desk-verbbar ~ *").count())
