page.get_by_role("button", name="Search").first.click(); wait(1); page.keyboard.type("Payments platform sync"); wait(2); page.keyboard.press("Enter"); wait(4)
page.get_by_text("Send", exact=True).last.click(); wait(4)
w = page.locator("[data-testid=meeting-send-well]").first
w.locator('[data-testid=destination-row] [data-destination="Payments issue 42"]').first.scroll_into_view_if_needed(); wait(1)
shot("24-failed-states")
w.locator("text=SENDS").first.scroll_into_view_if_needed(); wait(1)
shot("24-failed-history")
