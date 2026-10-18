import time
page.get_by_role("button", name="Today").last.click(); wait(3)
t=time.time(); page.get_by_role("button", name="Record when it starts").first.click(); wait(2.5)
shot("51-today-record-armed"); text("body", 2500)
