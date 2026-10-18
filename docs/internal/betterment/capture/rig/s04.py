import time
SEED="/Users/karol/dev/tools/HoldSpeak/docs/internal/betterment/capture/rig/seed/"
text("body", 1500)
if not page.get_by_text("Drop it here").count():
    page.get_by_role("button", name="Import").last.click(); wait(1.5)
t=time.time()
with page.expect_file_chooser(timeout=6000) as fc:
    page.get_by_text("browse").last.click()
fc.value.set_files(SEED+"one-on-one-theo.txt")
for i in range(10):
    wait(1)
    if i in (0,2,5,9): shot(f"22-import-after-t{int(time.time()-t):02d}s")
text("body", 3000)
