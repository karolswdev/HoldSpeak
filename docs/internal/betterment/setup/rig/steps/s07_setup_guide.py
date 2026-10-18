import time
page.get_by_role("button", name="HoldSpeak").first.click(); wait(1)
page.get_by_role("menuitem", name="Setup").first.click(); wait(3)
shot("12-setup-menu-item"); text(n=3000)
page.keyboard.press("Escape"); wait(1)
page.get_by_role("button", name="HoldSpeak").first.click(); wait(1)
page.get_by_role("menuitem", name="Settings").first.click(); wait(3)
page.get_by_role("button", name="GUIDE").first.click(); wait(2)
shot("13-settings-guide"); text("body", n=3000)
