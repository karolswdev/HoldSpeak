import time
if vp == 1440: page.keyboard.press("Meta+k")
else: page.get_by_role("button", name="Search").first.click()
wait(1.5); page.keyboard.type("commands"); wait(2)
shot("60-search-voice-commands"); text("body", 1500)
page.keyboard.press("Enter"); wait(3)
shot("61-voice-commands"); text("body", 3000)
print("BUTTONS", [b for b in page.get_by_role("button").all_inner_texts() if b.strip()][-30:])
