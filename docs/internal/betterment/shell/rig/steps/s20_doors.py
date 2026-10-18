import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath("steps/lib.py"))); 
exec(open("steps/lib.py").read())
close_all(page, wait); wait(1)
shot("20-desk-clean"); print("BOXES0", boxes(page))
t0=__import__('time').time()
page.locator('.desk-dock [aria-label^="Today"]').first.click(); wait(2.5)
shot("21-door-today"); print("BOXES today", boxes(page))
page.locator('.desk-dock [aria-label^="Meetings"]').first.click(); wait(2.5)
shot("22-door-meetings"); print("BOXES meetings", boxes(page))
# open a meeting from the Meetings list
row = page.get_by_text("Platform sync").first
row.click(); wait(2.5)
shot("23-meeting-from-list"); print("BOXES meeting", boxes(page))
# open meeting via desk icon double click
page.keyboard.press("Meta+Shift+e"); wait(1.5); shot("24-overview"); page.keyboard.press("Escape"); wait(1)
page.locator('[data-menu-id="go"] button').first.click(); wait(0.5)
page.get_by_role("menuitem", name="Ask AI").first.click(); wait(2.5)
shot("25-door-ask"); print("BOXES ask", boxes(page))
page.locator(".desk-mark").first.click(); wait(0.5)
page.get_by_role("menuitem", name="Settings").first.click(); wait(2.5)
shot("26-door-settings"); print("BOXES settings", boxes(page))
