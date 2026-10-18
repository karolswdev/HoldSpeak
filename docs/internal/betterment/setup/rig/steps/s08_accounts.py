import time
page.get_by_role("button", name="HoldSpeak").first.click(); wait(1)
page.get_by_role("menuitem", name="Accounts").first.click(); wait(3)
shot("14-accounts-from-menu"); text("body", n=200)
# GitHub recheck
t=time.time(); page.get_by_role("button", name="Recheck").first.click(); wait(4)
shot("15-accounts-github-recheck"); 
import re
body = page.locator("body").inner_text()
i = body.find("GitHub"); print("AFTER RECHECK:", body[i:i+300].replace("\n"," | "))
# Jira add account
page.get_by_role("button", name="Add account").first.click(); wait(2)
shot("16-accounts-jira-add"); body = page.locator("body").inner_text(); i=body.find("Jira"); print("JIRA ADD:", body[i:i+500].replace("\n"," | "))
