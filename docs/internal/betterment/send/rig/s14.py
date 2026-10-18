import time
page.mouse.dblclick(75, 655); wait(4)
text("body", 1200)
p = page.get_by_role("button", name="Publish")
print("publish", p.count())
if p.count()==0:
    page.get_by_text("REV 1").first.click(); wait(3); p = page.get_by_role("button", name="Publish")
t=time.time(); p.first.click(); wait(4)
print("publish press", round(time.time()-t,1))
shot("14-update-published")
text("body", 3500)
