page.get_by_text("Chat engines").first.click(); wait(2)
shot("01-chat-engines-open"); text()
page.get_by_text("Optional setup").first.click(); wait(3)
shot("02-optional-open"); shot("02-optional-open-full", full=True); text(n=5000)
