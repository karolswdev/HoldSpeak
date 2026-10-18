import time
page.mouse.dblclick(505, 80); wait(3)
page.get_by_role("button", name="Send", exact=True).last.click(); wait(2.5)
well = page.locator("[data-testid=meeting-send-well]").first
def form(label):
    well.locator("[data-testid=doc-forms] select").first.select_option(label=label); wait(2.5)
def go(dest, name, frm):
    form(frm)
    op = well.locator(f'[data-testid=send-open][data-destination="{dest}"]')
    if op.count() == 0:
        well.locator(f'[data-testid=destination-row] [data-destination="{dest}"]').first.click(); wait(3)
    op.first.scroll_into_view_if_needed()
    shot(f"08-{name}-preview")
    print(name, "PREVIEW:"); text(f'[data-testid=send-open][data-destination="{dest}"]', 1500)
    v = op.locator("[data-testid=send-verb], [data-testid=send-retry]").first
    v.scroll_into_view_if_needed()
    t=time.time(); v.click(); wait(4)
    print(name, "send", round(time.time()-t,1))
    op.locator("[data-testid=send-verbs]").first.scroll_into_view_if_needed()
    shot(f"08-{name}-sent")
    text(f'[data-testid=send-open][data-destination="{dest}"] [data-testid=send-verbs]', 1500)
go("Payments issue 42", "github", "Follow-up")
go("PAY-12 ticket", "jira", "Summary")
go("Mira, Theo, Jun (email)", "email", "Digest")
go("#payments-leads", "slack", "Digest")
well.locator("text=SENDS").first.scroll_into_view_if_needed(); wait(1)
shot("08-history")
text("[data-testid=meeting-send-well]", 6000)
