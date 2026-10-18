import time
t=time.time()
page.get_by_role("button", name="Record a meeting").last.click(); wait(2.5)
shot("36-record-orb-press"); text("body", 1500)
