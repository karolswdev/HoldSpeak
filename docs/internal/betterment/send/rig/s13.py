import time
page.mouse.dblclick(75, 655); wait(4)
shot("13-room-open")
t=time.time()
page.get_by_role("button", name="Draft update").first.click()
for i in range(60):
    wait(3)
    b = page.locator("body").inner_text()
    if "Publish" in b or "REV" in b or "failed" in b.lower(): break
print("draft", round(time.time()-t,1))
shot("13-draft-update")
text("body", 4000)
