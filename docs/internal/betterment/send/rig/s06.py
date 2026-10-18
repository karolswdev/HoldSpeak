page.keyboard.press("Meta+k") if vp==1440 else None
if vp==1440:
    wait(1); page.keyboard.type("Accounts"); wait(1.5); page.keyboard.press("Enter"); wait(3)
else:
    page.get_by_role("button", name="Search").first.click(); wait(1); page.keyboard.type("Accounts"); wait(1.5); page.keyboard.press("Enter"); wait(3)
d = page.locator("[data-testid=destinations]").first
d.scroll_into_view_if_needed(); wait(1)
shot("06-destinations-saved")
text("[data-testid=destinations]", 2000)
page.locator("[data-testid=dest-row]").filter(has_text="Payments issue 42").first.click(); wait(1.5)
shot("06-destination-github-details")
text("[data-testid=dest-open]", 1000)
