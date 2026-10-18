page.locator('.desk-dock [aria-label^="People"]').first.click(); wait(2)
shot("11-people-open"); text("body", 1500)
for name in ["Set up People", "Set up", "Start"]:
    b = page.get_by_role("button", name=name)
    if b.count():
        print("PRESS", name); b.first.click(); wait(3); break
shot("11-people-setup"); text("body", 1500)
