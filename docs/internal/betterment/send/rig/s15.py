import time
if vp==1440:
    page.mouse.dblclick(75, 655); wait(4)
else:
    page.get_by_role("button", name="Search").first.click(); wait(1); page.keyboard.type("Payments ledger"); wait(2); page.keyboard.press("Enter"); wait(4)
w = page.locator("[data-testid=send-well]").first
w.scroll_into_view_if_needed(); shot("15-update-send-well")
for dest, nm in (("Team reports folder","folder"),("Mira, Theo, Jun (email)","email")):
    op = w.locator(f'[data-testid=send-open][data-destination="{dest}"]')
    if op.count()==0:
        w.locator(f'[data-testid=destination-row] [data-destination="{dest}"]').first.click(); wait(3)
    op.first.scroll_into_view_if_needed(); shot(f"15-update-{nm}-refused")
    text(f'[data-testid=send-open][data-destination="{dest}"]', 600)
