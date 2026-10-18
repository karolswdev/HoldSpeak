def menu(mid, name):
    page.locator(f'[data-menu-id="{mid}"] button').first.click(); wait(0.8)
    shot(f"02-menu-{name}")
    text('[role="menu"]', 2500)
    page.keyboard.press("Escape"); wait(0.4)
page.locator(".desk-mark").first.click(); wait(0.8)
shot("02-menu-holdspeak"); text('[role="menu"]', 2000)
page.keyboard.press("Escape"); wait(0.4)
for m in ["desk","object","go","window"]:
    menu(m, m)
# Go > Projects / Tools submenus? hover
page.locator('[data-menu-id="go"] button').first.click(); wait(0.6)
print("GO ROWS:", page.locator('[role="menuitem"]').all_inner_texts())
page.keyboard.press("Escape"); wait(0.3)
# palette
page.keyboard.press("Meta+k"); wait(1)
shot("03-palette-empty"); text('[role="dialog"], .desk-palette, [role="listbox"]', 3000)
page.keyboard.type("tools"); wait(1); shot("03-palette-tools"); text('[role="listbox"]', 1500)
for q in ["rhythm","wallpaper","places","activity","memory","automation","agents","settings"]:
    page.keyboard.press("Meta+a"); page.keyboard.type(q); wait(0.8)
    shot(f"03-palette-{q}"); text('[role="listbox"]', 600)
page.keyboard.press("Escape")
