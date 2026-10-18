import time
if vp==1440: page.keyboard.press("Meta+k")
else: page.get_by_role("button", name="Search").first.click()
wait(1); page.keyboard.type("Friday team update"); wait(2); page.keyboard.press("Enter"); wait(4)
page.get_by_text("Draft my Friday").first.click(); wait(2)
page.get_by_role("button", name="Open artifact").first.click(); wait(4)
w = page.locator("[data-seat=artifact]").first
dest="Mira, Theo, Jun (email)"
op = w.locator(f'[data-testid=send-open][data-destination="{dest}"]')
if op.count()==0:
    w.locator(f'[data-testid=destination-row] [data-destination="{dest}"]').first.click(); wait(3)
op.first.scroll_into_view_if_needed(); shot("17-artifact-email-preview")
text(f'[data-testid=send-open][data-destination="{dest}"]', 700)
import os
if os.environ.get("PRESS")=="1":
    v = op.locator("[data-testid=send-verb]").first; v.scroll_into_view_if_needed()
    t=time.time(); v.click(); wait(4); print("send", round(time.time()-t,1))
    shot("17-artifact-email-sent")
    text(f'[data-testid=send-open][data-destination="{dest}"] [data-testid=send-verbs]', 600)
