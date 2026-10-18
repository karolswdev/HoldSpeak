import time
def go(name):
    if vp == 1440: page.get_by_role("button", name=name).last.click()
    else:
        if page.get_by_role("menuitem", name=name).count()==0: page.get_by_role("button", name="Go").first.click(); wait(1)
        page.get_by_role("menuitem", name=name).first.click()
    wait(3)
go("Today"); shot("50-today-calendar"); text("body", 2500)
print("BUTTONS", [b for b in page.get_by_role("button").all_inner_texts() if b.strip()][-30:])
