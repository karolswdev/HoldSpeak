if vp == 1440: page.get_by_role("button", name="Meetings").last.click()
else:
    if page.get_by_role("menuitem", name="Meetings").count()==0: page.get_by_role("button", name="Go").first.click(); wait(1)
    page.get_by_role("menuitem", name="Meetings").first.click()
wait(2.5)
page.get_by_role("tab", name="RECORD").first.click(); wait(2.5)
shot("52-meetings-record-wing"); shot("52-meetings-record-wing-full", full=True); text("body", 3500)
print("BUTTONS", [b for b in page.get_by_role("button").all_inner_texts() if b.strip()][-30:])
