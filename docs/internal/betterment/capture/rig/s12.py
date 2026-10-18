b = page.get_by_role("button", name="Continue later")
if b.count(): b.first.click(); wait(1.5)
items = page.get_by_role("menuitem", name="Capture")
print("menuitems", items.count())
if items.count()==0:
    page.get_by_role("button", name="Go").first.click(); wait(1)
page.get_by_role("menuitem", name="Capture").first.click(); wait(2)
shot("31-capture-alone"); text("body", 1500)
