import time
if vp == 1440:
    page.get_by_role("button", name="Window").first.click(); wait(1)
    shot("30-window-menu")
    page.get_by_text("Desk", exact=True).last.hover(); wait(1)
    shot("30-window-desk-sub")
    page.get_by_text("Capture", exact=True).last.click(); wait(2)
else:
    page.get_by_text("Capture", exact=True).first.click(); wait(2)
shot("31-capture-window"); text("body", 4000)
print("BUTTONS", [b for b in page.get_by_role("button").all_inner_texts() if b.strip()][-30:])
