import time, os
if vp==1440:
    page.keyboard.press("Meta+k")
else:
    page.get_by_role("button", name="Search").first.click()
wait(1); page.keyboard.type("Cutover risks"); wait(2); page.keyboard.press("Enter"); wait(4)
shot("12-thought-window")
t=time.time()
page.get_by_role("button", name="Send", exact=True).last.click()
page.locator("[data-testid=prepared-row]").first.wait_for(timeout=15000)
print("prepared visible", round(time.time()-t,1)); wait(1)
shot("12-note-send-prepared")
text("[data-testid=send-well]", 1500)
if os.environ.get("PRESS")=="1":
    o = page.locator("[data-testid=prepared-send]").first
    o.scroll_into_view_if_needed(); shot("12-note-prepared-open")
    t=time.time(); o.click(); wait(3)
    print("prepared send", round(time.time()-t,1))
    page.locator("[data-testid=prepared-result]").first.scroll_into_view_if_needed()
    shot("12-note-prepared-sent")
    text("[data-testid=send-well]", 1500)
