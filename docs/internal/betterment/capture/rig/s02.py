import time
b = page.get_by_role("button", name="Continue later")
if b.count(): b.first.click(); wait(1.5)
if vp == 1440:
    page.locator(".dock, footer, nav").get_by_text("Meetings", exact=True).last.click() if False else page.get_by_role("button", name="Meetings").last.click()
else:
    page.get_by_text("Meetings", exact=True).first.click()
wait(3); shot("20-meetings-empty"); text("body", 2500)
btns = page.get_by_role("button").all_inner_texts()
print("BUTTONS", [b for b in btns if b.strip()][:80])
