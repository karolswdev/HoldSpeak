if vp == 1440:
    page.get_by_role("button", name="Meetings").last.click(); wait(2)
else:
    pass
shot("27-summaries-running"); text("body", 3000)
