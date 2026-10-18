import time
page.get_by_text("Today", exact=True).last.click(); wait(3)
page.get_by_text("Decisions", exact=True).last.click(); wait(3)
shot("22-today-decisions")
text("body", 1200)
page.get_by_text("Freeze schema changes", exact=False).first.click(); wait(3)
shot("22-decision-open")
text("body", 2000)
st = page.get_by_text("Send", exact=True)
print("send", st.count())
st.first.click(); wait(4)
shot("22-decision-send-well")
text("[data-seat=decision-record]", 1500)
w = page.locator("[data-seat=decision-record]").first
dest = "#payments-leads"
op = w.locator(f'[data-testid=send-open][data-destination="{dest}"]')
if op.count()==0:
    w.locator(f'[data-testid=destination-row] [data-destination="{dest}"]').first.click(); wait(3)
op.first.scroll_into_view_if_needed(); shot("22-decision-slack-preview")
text(f'[data-testid=send-open][data-destination="{dest}"]', 800)
v = op.locator("[data-testid=send-verb]").first; v.scroll_into_view_if_needed()
t=time.time(); v.click(); wait(4); print("send", round(time.time()-t,1))
shot("22-decision-slack-sent")
text(f'[data-testid=send-open][data-destination="{dest}"] [data-testid=send-verbs]', 400)
