exec(open("steps/lib.py").read())
for q in ["Context","Terminals","Delivery"]:
    close_all(page, wait)
    page.keyboard.press("Meta+k"); wait(0.8); page.keyboard.type(q); wait(1.2)
    print(q, "ROWS:", page.locator('[role="option"]').all_inner_texts()[:5])
    page.keyboard.press("Enter"); wait(3); print("  after:", boxes(page)); shot(f"61-enter-{q.lower()}")
    page.keyboard.press("Escape")
