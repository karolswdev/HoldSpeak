page.get_by_role("button", name="Meetings").last.click(); wait(2.5)
page.get_by_text("Payments platform sync").first.click(); wait(3)
shot("45-sync-summary-cites-later"); text("body", 2500)
