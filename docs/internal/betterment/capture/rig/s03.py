import time
SEED="/Users/karol/dev/tools/HoldSpeak/docs/internal/betterment/capture/rig/seed/"
w = page.locator("[data-window-id], .desk-window").filter(has_text="No meetings yet").last
t=time.time()
try:
    with page.expect_file_chooser(timeout=5000) as fc:
        page.get_by_role("button", name="Import").last.click()
    fc.value.set_files(SEED+"payments-platform-sync.txt")
    print("chooser opened directly")
except Exception as e:
    print("no direct chooser", e); wait(1.5); shot("21-import-press"); text("body", 3000)
for i in range(8):
    wait(1.5); shot(f"21-import-t{int(time.time()-t):02d}s") if i in (0,2,7) else None
text("body", 3000)
