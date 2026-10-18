import time
page.get_by_role("button", name="Search").first.click(); wait(1); page.keyboard.type("Payments platform sync"); wait(2)
text("body", 100)
page.keyboard.press("Enter"); wait(4)
shot("21-meeting-open")
text("body", 600)
b = page.get_by_text("Send", exact=True)
print("send texts", b.count())
b.last.click(); wait(4)
shot("21-meeting-send-well")
w = page.locator("[data-testid=meeting-send-well]").first
w.locator("text=SENDS").first.scroll_into_view_if_needed(); wait(1)
shot("21-meeting-sends-history")
