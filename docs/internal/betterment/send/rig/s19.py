import time
page.mouse.dblclick(505, 80); wait(3)
page.get_by_role("button", name="Send", exact=True).last.click(); wait(3)
well = page.locator("[data-testid=meeting-send-well]").first
def go(dest, name, wait_s=5):
    op = well.locator(f'[data-testid=send-open][data-destination="{dest}"]')
    if op.count() == 0:
        well.locator(f'[data-testid=destination-row] [data-destination="{dest}"]').first.click(); wait(3)
    v = op.locator("[data-testid=send-verb], [data-testid=send-retry]").first
    v.scroll_into_view_if_needed()
    t=time.time(); v.click(); wait(wait_s)
    print(name, "after", round(time.time()-t,1))
    op.locator("[data-testid=send-verbs]").first.scroll_into_view_if_needed()
    shot(f"19-{name}")
    text(f'[data-testid=send-open][data-destination="{dest}"] [data-testid=send-verbs]', 800)
go("Payments issue 42", "github-failed")
go("#payments-leads", "slack-failed")
go("PAY-12 ticket", "jira-held", 20)
text("[data-testid=meeting-send-well]", 4000)
