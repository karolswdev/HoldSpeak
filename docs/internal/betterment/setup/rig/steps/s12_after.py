import time
b=page.get_by_role("button", name="Continue later")
if b.count(): b.first.click(); wait(3)
page.get_by_role("button", name="HoldSpeak").first.click(); wait(1)
page.get_by_role("menuitem", name="Accounts").first.click(); wait(3)
shot("23-his-mac-settings-accounts"); body=page.locator("body").inner_text(); i=body.find("Accounts | "); i=body.find("Services"); print("ACCTS:", body[i:i+900].replace("\n"," | "))
page.keyboard.press("Escape")
# People app on a fresh desk
page.get_by_role("button", name="People").last.click(); wait(3)
shot("24-people-fresh"); body=page.locator("body").inner_text(); print("PEOPLE:", body[-900:].replace("\n"," | "))
