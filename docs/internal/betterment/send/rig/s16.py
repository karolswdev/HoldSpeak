import time
if vp==1440: page.keyboard.press("Meta+k")
else: page.get_by_role("button", name="Search").first.click()
wait(1); page.keyboard.type("Friday team update"); wait(2); text("body",200); page.keyboard.press("Enter"); wait(4)
shot("16-automation-result")
text("body", 2500)
row = page.get_by_text("DONE").first
try:
    page.get_by_text("Draft my Friday").first.click(); wait(2)
except Exception as e: print("no row", e)
shot("16-automation-result-open")
oa = page.get_by_role("button", name="Open artifact")
print("open artifact", oa.count())
if oa.count():
    oa.first.click(); wait(4)
    shot("16-artifact-window")
    text("body", 4000)
    w = page.locator("[data-seat=artifact]")
    print("artifact well", w.count())
    if w.count():
        w.first.scroll_into_view_if_needed(); wait(1); shot("16-artifact-send-well")
