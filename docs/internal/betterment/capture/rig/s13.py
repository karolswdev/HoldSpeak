import time, sys
which = sys.argv[-1] if False else None
def open_capture():
    if vp == 393:
        if page.get_by_role("menuitem", name="Capture").count()==0:
            page.get_by_role("button", name="Go").first.click(); wait(1)
        page.get_by_role("menuitem", name="Capture").first.click(); wait(2)
    else:
        page.get_by_role("button", name="Window").first.click(); wait(0.5)
        page.get_by_text("Desk", exact=True).last.hover(); wait(0.5)
        page.get_by_text("Capture", exact=True).last.click(); wait(2)
open_capture()
name, tag = STEP
t=time.time(); page.get_by_role("button", name=name).last.click(); wait(3)
shot(tag); text("body", 3000)
print("BUTTONS", [b for b in page.get_by_role("button").all_inner_texts() if b.strip()][-30:])
