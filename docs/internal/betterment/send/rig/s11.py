import time
page.mouse.dblclick(625, 80); wait(3)
page.get_by_role("button", name="Object", exact=True).or_(page.get_by_text("Object", exact=True)).first.click(); wait(1.5)
shot("11-note-object-menu")
text("[role=menu]", 1500)
s = page.get_by_role("menuitem", name="Send to")
print("sendto", s.count())
if s.count():
    s.first.hover(); wait(1.5); shot("11-note-object-send-to"); text("[role=menu]", 2000)
page.keyboard.press("Escape"); wait(0.5)
d = page.get_by_role("button", name="Develop this thought")
d.first.click(); wait(4)
shot("11-thought-window")
text("body", 3000)
