import time
# close Settings by focusing Meetings via dock
page.get_by_role("button", name="Meetings").last.click(); wait(2)
row = page.get_by_role("button", name="Run summary")
print("run buttons", row.count())
t=time.time()
row.nth(1).click()
for i in range(120):
    wait(1)
    body = page.locator("body").inner_text()
    if i in (1,5,15,30,60): shot(f"27-summary-running-t{int(time.time()-t):03d}s")
    if "Architecture review: idempotent retries" in body and ("Not run" not in body.split("Architecture review: idempotent retries")[1][:200]) and ("Running" not in body.split("Architecture review: idempotent retries")[1][:200]) and ("Summar" not in body.split("Architecture review: idempotent retries")[1][:120] or i>3):
        pass
    seg = body.split("Architecture review: idempotent retries")[1][:250].replace("\n"," | ")
    if i % 10 == 0: print(int(time.time()-t), seg)
    if "decision" in seg.lower() or "action" in seg.lower():
        break
print("done after", round(time.time()-t,1)); shot("27-summary-done")
