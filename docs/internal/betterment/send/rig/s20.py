import time
# the meeting window should still be open (hub keeps windows)
wait(3)
text("body", 300)
well = page.locator("[data-testid=meeting-send-well]")
if well.count()==0:
    page.mouse.dblclick(505, 80); wait(3)
    page.get_by_role("button", name="Send", exact=True).last.click(); wait(4)
well = page.locator("[data-testid=meeting-send-well]").first
well.scroll_into_view_if_needed()
op = well.locator('[data-testid=send-open][data-destination="PAY-12 ticket"]')
if op.count(): op.locator("[data-testid=send-verbs]").first.scroll_into_view_if_needed()
shot("20-after-reload-jira-sending")
text("[data-testid=meeting-send-well]", 3000)
v = op.locator("[data-testid=send-verb]")
if v.count(): print("send-again disabled?", v.first.is_disabled())
