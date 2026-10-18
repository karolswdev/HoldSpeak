import time
page.get_by_text("Chat engines").first.click(); wait(1)
page.get_by_role("button", name="Use a server").first.click(); wait(1)
page.get_by_placeholder("http://<host>:<port>/v1").fill("http://192.168.1.43:8080/v1")
page.get_by_role("button", name="Check").first.click(); t=time.time(); wait(4)
shot("05-server-checked"); text(n=4000)
page.get_by_role("button", name="Use this for summaries").first.click(); wait(4)
shot("06-server-used"); text(n=4000)
