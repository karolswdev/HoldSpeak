import time
b=page.get_by_role("button", name="TALK").first
print("press", time.strftime("%H:%M:%S")); b.click(); wait(3)
names=[(x.get_attribute("aria-label"), x.inner_text()) for x in page.locator("button").all() if "TALK" in (x.inner_text() or "")]
print("held names", names)
print("exit with mic held", time.strftime("%H:%M:%S"))
