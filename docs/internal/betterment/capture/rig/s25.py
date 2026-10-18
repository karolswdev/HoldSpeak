if vp == 393:
    page.get_by_role("button", name="Go").first.click(); wait(1)
    shot("02-phone-go-launcher")
    page.keyboard.press("Escape"); wait(0.5)
orb = page.locator(".record-orb, [class*=RecordOrb], [class*=record-orb], button[aria-label*=ecord]")
print("orb candidates", [(o.get_attribute("aria-label"), o.get_attribute("title")) for o in orb.all()][:6])
