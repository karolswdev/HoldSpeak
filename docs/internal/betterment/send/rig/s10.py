import time
if vp==1440:
    page.mouse.dblclick(625, 80); wait(3)
else:
    page.get_by_role("button", name="Search").first.click(); wait(1); page.keyboard.type("Cutover risks"); wait(1.5); page.keyboard.press("Enter"); wait(3)
shot("10-note-open")
text("body", 2500)
