page.locator(".desk-mark").first.click(); wait(0.6)
page.get_by_role("menuitem", name="Engines").first.click(); wait(3)
r = page.get_by_text("Default engine").first
r.click(); wait(2)
shot("13-default-open"); 
q = page.get_by_role("button", name="Qwen3.8 27B")
print("q", q.count())
if q.count(): q.first.click(); wait(3)
else:
    q = page.get_by_text("Qwen3.8 27B")
    print("qt", q.count()); 
    if q.count(): q.first.click(); wait(3)
shot("13-default-assigned"); text("body", 1500)
