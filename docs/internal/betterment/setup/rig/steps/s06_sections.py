import time
names = ["Voice","Meetings","Rhythm","Engines","Accounts","Sounds & Presence","Wallpaper","People","System"]
page.get_by_role("button", name="HoldSpeak").first.click(); wait(1)
page.get_by_role("menuitem", name="Settings").first.click(); wait(3)
if False:
    # make the window big so sections show
    pass
for i, n in enumerate(names):
    b = page.get_by_role("button", name=f"Open {n}")
    if not b.count():
        print("NO BUTTON", n); continue
    t = time.time(); b.first.click(); wait(2.5)
    slug = n.lower().replace(" & ","-").replace(" ","-")
    shot(f"11-{i}-settings-{slug}"); text("[data-window-kind], .desk-window, body", n=2500)
    print("elapsed", round(time.time()-t,1))
    # go back
    back = page.locator("button", has_text="«")
    if not back.count(): back = page.get_by_role("button", name="Back")
    if back.count(): back.first.click(); wait(1.5)
    else: print("no way back after", n)
