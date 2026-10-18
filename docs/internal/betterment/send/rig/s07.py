import time
page.mouse.dblclick(505, 80); wait(3)
page.get_by_role("button", name="Send", exact=True).last.click(); wait(2.5)
well = page.locator("[data-testid=meeting-send-well]").first
shot("07-meeting-well-six")
text("[data-testid=destination-list]", 1500)
t=time.time()
well.locator("[data-testid=destination-row]").filter(has_text="Team reports folder").first.locator("[data-destination]").first.click(); wait(2)
print("pick", round(time.time()-t,1))
well.locator("[data-testid=send-open]").first.scroll_into_view_if_needed()
shot("07-folder-preview")
v = well.locator("[data-testid=send-open] [data-testid=send-verb]").first
v.scroll_into_view_if_needed(); wait(0.5)
shot("07-folder-preview-send-verb")
t=time.time(); v.click(); wait(3)
print("send", round(time.time()-t,1))
shot("07-folder-sent")
text("[data-testid=send-open]", 1500)
text("[data-testid=meeting-send-well]", 2500)
