import time
page.get_by_role("button", name="People").last.click(); wait(3)
t0=time.time()
for name in ["Theo Lindqvist","Jun Park"]:
    page.get_by_role("button", name="Add person").last.click(); wait(1)
    page.get_by_placeholder("Name").first.fill(name)
    page.locator("button", has_text="Direct report").first.click()
    page.locator("button", has_text="Add").last.click(); wait(2.5)
print("secs for two", round(time.time()-t0,1))
shot("27-people-three"); body=page.locator("body").inner_text(); print("P:", body[-500:].replace("\n"," | "))
