shot("00-first-open")
text("body", 1500)
b = page.get_by_role("button", name="Continue later")
if b.count():
    b.first.click(); wait(2)
shot("01-desk-empty")
text("body", 2000)
# icons on the floor
icons = page.locator("[data-object-ref], .desk-icon, [data-icon-ref]")
print("ICONS", icons.count())
print("ICON LABELS", page.locator(".desk-icon-label, [data-object-ref] .label").all_inner_texts()[:40])
print("DOCK", page.locator(".desk-dock").first.inner_text().replace("\n"," | ") if page.locator(".desk-dock").count() else "none")
