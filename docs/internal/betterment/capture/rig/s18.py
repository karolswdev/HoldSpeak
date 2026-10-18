if page.get_by_role("menuitem", name="Meetings").count()==0: page.get_by_role("button", name="Go").first.click(); wait(1)
page.get_by_role("menuitem", name="Meetings").first.click(); wait(2.5)
shot("40-meetings-list")
page.get_by_text("Architecture review: idempotent retries").first.click(); wait(3)
shot("41-meeting-outcomes"); shot("41-meeting-outcomes-full", full=True)
page.get_by_role("tab", name="ARTIFACTS").first.click() if page.get_by_role("tab", name="ARTIFACTS").count() else None
wait(2); shot("42-meeting-artifacts"); text("body", 1500)
