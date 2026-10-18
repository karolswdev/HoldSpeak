page.get_by_role("button", name="Continue later").first.click(); wait(3)
shot("07-desk-after-continue"); text(n=2000)
# HoldSpeak menu
m = page.get_by_role("button", name="HoldSpeak")
print("hs menu count", m.count())
if m.count():
    m.first.click(); wait(1); shot("08-holdspeak-menu"); text("[role=menu]", n=2000)
