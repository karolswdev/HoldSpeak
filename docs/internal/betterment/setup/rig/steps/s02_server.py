import time
page.get_by_text("Chat engines").first.click(); wait(1)
page.get_by_role("button", name="Use a server").first.click(); wait(2)
shot("03-use-a-server"); text(n=4000)
b = page.get_by_role("button", name="Find on LAN")
if b.count():
    t=time.time(); b.first.click(); wait(6); print("find took", time.time()-t)
    shot("04-find-on-lan"); text(n=4000)
