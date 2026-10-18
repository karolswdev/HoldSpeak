import time
if vp == 1440: page.get_by_role("button", name="Meetings").last.click()
else:
    if page.get_by_role("menuitem", name="Meetings").count()==0: page.get_by_role("button", name="Go").first.click(); wait(1)
    page.get_by_role("menuitem", name="Meetings").first.click()
wait(2.5); shot("40-meetings-list"); text("body", 1500)
t=time.time()
page.get_by_text("Architecture review: idempotent retries").first.click(); wait(3)
print("open", round(time.time()-t,1))
shot("41-meeting-outcomes"); text("body", 5000)
print("BUTTONS", [x for x in page.get_by_role("button").all_inner_texts() if x.strip()][-60:])
print("TABS", page.get_by_role("tab").all_inner_texts())
