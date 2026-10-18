import time
SEED="/Users/karol/dev/tools/HoldSpeak/docs/internal/betterment/capture/rig/seed/"
if not page.get_by_text("Drop it here").count() and not page.get_by_text("one-on-one-theo.txt").count():
    page.get_by_role("button", name="Import").last.click(); wait(1.5)
if not page.get_by_text("one-on-one-theo.txt").count():
    with page.expect_file_chooser(timeout=6000) as fc:
        page.get_by_text("browse").last.click()
    fc.value.set_files(SEED+"one-on-one-theo.txt"); wait(1)
shot("22-import-form")
inputs = page.locator("input:visible")
print("inputs", [ (inputs.nth(i).get_attribute("aria-label"), inputs.nth(i).get_attribute("placeholder")) for i in range(inputs.count())])
page.locator("input[aria-label=Title]").last.fill("1:1 with Theo")
shot("22-import-form-filled")
t=time.time()
page.get_by_role("button", name="Import", exact=True).last.click()
for i in range(25):
    wait(1)
    if i in (0,2,5,10,24): shot(f"23-imported-t{int(time.time()-t):02d}s"); text("body",2500)
