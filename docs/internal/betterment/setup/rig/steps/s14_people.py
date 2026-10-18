import time
page.get_by_role("button", name="People").last.click(); wait(3)
t=time.time(); page.locator("button", has_text="Set up People").first.click(); wait(3)
shot("26-people-setup-pressed"); body=page.locator("body").inner_text(); print("P:", body[-1200:].replace("\n"," | ")); print(round(time.time()-t,1))
