import time
t=time.time()
page.get_by_role("button", name="Find on LAN").last.click()
for i in range(12):
    wait(1)
    if page.get_by_role("button", name="Use it").count(): break
print("found after", round(time.time()-t,1)); shot("25-lan-found")
page.get_by_role("button", name="Use it").last.click(); wait(3)
shot("25-lan-used"); text("body", 5000)
print("BUTTONS", [b for b in page.get_by_role("button").all_inner_texts() if b.strip()][-40:])
