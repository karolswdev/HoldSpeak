page.keyboard.press("Meta+k"); wait(1); page.keyboard.type("Engines"); wait(1.5); page.keyboard.press("Enter"); wait(3)
d = page.get_by_text("Default engine", exact=True)
print("def", d.count()); d.first.click(); wait(2)
text("body", 3000)
r = page.get_by_text("Qwen3.8 27B")
print("rows", r.count())
for i in range(r.count()):
    try: print(i, r.nth(i).inner_text()[:100])
    except Exception: pass
r.first.click(); wait(3)
text("body", 3000)
