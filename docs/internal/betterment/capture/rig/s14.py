import time
b=page.get_by_role("button", name="TALK").first; print("count", page.get_by_role("button", name="TALK").count(), b.get_attribute("aria-label"))
print("T0 press", time.strftime("%H:%M:%S"))
b.click(); wait(3); shot("32-talk-held-3s")
print("T1 release", time.strftime("%H:%M:%S"))
b.click()
for i in range(12):
    wait(1)
    if i in (0,4,11): shot(f"32-talk-after-stop-t{i+1:02d}s"); text("body", 900)
