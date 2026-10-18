page.get_by_role("button", name="HoldSpeak").first.click(); wait(1)
page.get_by_role("menuitem", name="Settings").first.click(); wait(3)
shot("10-settings-open"); text(n=6000)
shot("10-settings-open-full", full=True)
