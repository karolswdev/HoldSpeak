import time
b = page.get_by_role("button", name="Continue later")
if b.count(): b.first.click(); wait(1.5)
t=time.time()
if vp == 1440:
    page.locator("text=Speak").last.click()
else:
    page.get_by_text("Speak", exact=True).first.click() if page.get_by_text("Speak", exact=True).count() else None
wait(3); print("open", round(time.time()-t,1))
shot("10-speak-open"); text("body", 3000)
for w in ["Journal", "Blocks", "Learned"]:
    loc = page.get_by_role("tab", name=w)
    if not loc.count(): loc = page.get_by_role("button", name=w)
    if loc.count():
        loc.first.click(); wait(2); shot(f"11-speak-{w.lower()}"); text("body", 2500)
    else: print("no wing", w)
