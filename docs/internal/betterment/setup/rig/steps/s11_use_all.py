import time
page.get_by_text("Optional setup").first.click(); wait(2)
n=0
for k in range(6):
    b = page.locator("button", has_text="Use it")
    if not b.count(): break
    t=time.time(); b.first.click(); n+=1; wait(4); print("use it", n, round(time.time()-t,1))
shot("21-his-mac-connections-used"); 
body=page.locator("body").inner_text(); i=body.find("Connections"); print("CONN:", body[i:i+900].replace("\n"," | "))
pass
shot("22-his-mac-hooks-installed")
body=page.locator("body").inner_text(); i=body.find("Agents"); print("AGENTS:", body[i:i+700].replace("\n"," | "))
shot("22-his-mac-after-full", full=True)
