exec(open("steps/lib.py").read())
b = page.get_by_role("button", name="Continue later")
if b.count(): b.first.click(); wait(2)
close_all(page, wait); wait(1)
shot("40-phone-home"); text("body", 1500)
shot("40-phone-home-full", full=True)
# dock
print("DOCK", page.evaluate("""() => [...document.querySelectorAll('.desk-dock button')].map(b => b.getAttribute('aria-label'))"""))
# tap Meetings row in the home list
page.get_by_text("Meetings", exact=True).first.tap(); wait(2.5)
shot("41-phone-meetings"); print("BOX", boxes(page))
page.get_by_text("Platform sync").first.tap(); wait(2.5)
shot("42-phone-meeting"); text("header.desk-pullout-head", 300)
bb = page.locator('button[aria-label^="Back from"]')
print("BACK", bb.count()); 
if bb.count(): bb.first.tap(); wait(1.5)
shot("43-phone-after-back"); print("BOX", boxes(page))
page.locator('[data-menu-id="go"] button').first.tap(); wait(1); shot("44-phone-go"); text('[role="menu"]', 1500)
page.keyboard.press("Escape"); wait(0.5)
# search
s = page.locator('button[aria-label*="Search"]')
print("search", s.count())
if s.count(): s.first.tap(); wait(1.2); shot("45-phone-search"); page.keyboard.type("mira"); wait(1.2); shot("45-phone-search-mira"); text('[role="listbox"]', 800)
