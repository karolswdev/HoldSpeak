exec(open("steps/lib.py").read())
close_all(page, wait); wait(1)
ic = page.locator('.desk-icon-name', has_text="On-call").first
ic.click(); wait(0.8)
shot("30-note-selected")
page.locator('[data-menu-id="object"] button').first.click(); wait(0.8)
shot("31-object-menu-note"); text('[role="menu"]', 1500)
# ghost state per row
print(page.evaluate("""() => [...document.querySelectorAll('[role=menu] [role=menuitem]')].map(e => [e.innerText.replace(/\\n/g,' '), e.getAttribute('aria-disabled')])"""))
page.keyboard.press("Escape"); wait(0.4)
ic.click(button="right"); wait(0.8); shot("32-note-context-menu"); text('[role="menu"]', 1500)
print(page.evaluate("""() => [...document.querySelectorAll('[role=menu] [role=menuitem]')].map(e => [e.innerText.replace(/\\n/g,' '), e.getAttribute('aria-disabled')])"""))
page.keyboard.press("Escape"); wait(0.4)
ic.dblclick(); wait(2.5); shot("33-note-opened"); print("BOX note", boxes(page))
page.locator('[data-menu-id="object"] button').first.click(); wait(0.8)
shot("34-object-menu-note-window"); 
print(page.evaluate("""() => [...document.querySelectorAll('[role=menu] [role=menuitem]')].map(e => [e.innerText.replace(/\\n/g,' '), e.getAttribute('aria-disabled')])"""))
page.keyboard.press("Escape"); wait(0.4)
close_all(page, wait)
m = page.locator('.desk-icon-name', has_text="1:1 with Mira").first
m.dblclick(); wait(2.5); shot("35-meeting-icon-opened"); print("BOX meeting icon", boxes(page))
p = page.locator('.desk-icon-name', has_text="Theo Brandt").first
p.dblclick(); wait(2.5); shot("36-person-icon-opened"); print("BOX person icon", boxes(page))
n = page.locator('.desk-icon-name', has_text="Needs you").first
n.dblclick(); wait(2.5); shot("37-needs-you-icon"); print("BOX needs", boxes(page))
