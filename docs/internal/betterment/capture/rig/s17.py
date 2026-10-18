import time
page.get_by_role("tab", name="ARTIFACTS").first.click(); wait(2.5)
shot("42-meeting-artifacts"); text("body", 3000)
page.get_by_role("tab", name="OUTCOMES").first.click(); wait(1.5)
page.get_by_role("button", name="More").last.click(); wait(1)
shot("43-meeting-more"); 
print("MENU", page.get_by_role("menuitem").all_inner_texts())
page.keyboard.press("Escape"); wait(0.5)
page.get_by_text("TRANSCRIPT · 12").first.click(); wait(1.5)
shot("44-meeting-transcript")
