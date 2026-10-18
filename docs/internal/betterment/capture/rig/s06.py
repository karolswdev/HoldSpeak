page.get_by_role("button", name="Choose engine").last.click(); wait(3)
shot("24-choose-engine"); text("body", 4000)
print("BUTTONS", [b for b in page.get_by_role("button").all_inner_texts() if b.strip()][-60:])
