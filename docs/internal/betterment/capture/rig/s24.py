if vp == 1440: page.get_by_role("button", name="Speak").last.click()
else:
    if page.get_by_role("menuitem", name="Speak").count()==0: page.get_by_role("button", name="Go").first.click(); wait(1)
    print("speak in go:", page.get_by_role("menuitem", name="Speak").count())
    page.get_by_role("button", name="TALK").first.click() if False else None
wait(2.5)
if vp==1440:
    page.get_by_text("⚙︎").first.click()
    wait(2); shot("12-speak-settings"); text("body", 3000)
    page.get_by_role("tab", name="SPEAK").first.click(); wait(1.5)
    page.locator("textarea").first.fill("Remind Theo that the reconciliation profile is due Thursday."); wait(0.5)
    page.get_by_text("DRY RUN").first.click(); wait(0.5)
    shot("13-speak-typed-dryrun")
    page.keyboard.press("Meta+Enter"); wait(15)
    shot("13-speak-dryrun-result"); text("body", 3000)
    page.get_by_text("Details").first.click(); wait(1.5); shot("14-speak-details"); text("body",3000)
