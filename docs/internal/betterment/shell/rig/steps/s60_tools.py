exec(open("steps/lib.py").read())
for q, tag in [("Activity","activity"),("Processes","processes"),("Components","components"),("Context","context"),("Commands","commands"),("Rhythm","rhythm"),("Memory","memory"),("Workbenches","workbenches"),("Setup","setup"),("Delivery","delivery"),("Terminals","terminals"),("Calendar snapshot","calendar-snapshot")]:
    close_all(page, wait)
    page.keyboard.press("Meta+k"); wait(0.8); page.keyboard.type(q); wait(1)
    page.keyboard.press("Enter"); t=__import__('time').time(); wait(3)
    shot(f"60-tool-{tag}"); print(tag, boxes(page))
    try:
        print("  ", page.locator('[role="region"][data-layer="window"]').last.inner_text(timeout=2000)[:300].replace("\n"," | "))
    except Exception as e: print("  no window")
