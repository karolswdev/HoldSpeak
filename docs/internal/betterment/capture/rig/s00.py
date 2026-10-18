shot("00-first-open")
text("body", 1500)
b = page.get_by_role("button", name="Continue later")
if b.count():
    b.first.click(); wait(2)
shot("01-desk-empty")
text("body", 1500)
