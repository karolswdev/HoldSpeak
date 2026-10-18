shot("15-desk-after-summaries")
labels = page.locator(".desk-icon-name, [class*='icon'] [class*='label'], [class*='IconLabel']").all_inner_texts()
print("LABELS", labels[:60])
print("BELL", page.locator('.desk-chrome [aria-label*="eed"], [class*="bell"]').all_inner_texts()[:4])
