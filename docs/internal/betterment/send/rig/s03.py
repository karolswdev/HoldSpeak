import time
page.mouse.dblclick(505, 80); wait(3)
page.get_by_role("button", name="Send", exact=True).last.click(); wait(2)
t=time.time()
page.get_by_role("button", name="Add destination").first.click(); wait(3)
print("add dest", round(time.time()-t,1))
shot("03-add-destination-settings")
text("body", 6000)
