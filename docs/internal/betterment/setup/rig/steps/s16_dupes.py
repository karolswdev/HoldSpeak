page.keyboard.press("Meta+k"); wait(1); page.keyboard.type("Rhythm"); wait(1.5)
shot("30-search-rhythm"); 
page.keyboard.press("Enter"); wait(3)
shot("31-rhythm-window"); body=page.locator("body").inner_text(); i=body.find("TALK"); print("RHYTHM:", body[i:i+1500].replace("\n"," | "))
page.keyboard.press("Meta+Shift+p"); wait(3)
shot("32-change-places"); body=page.locator("body").inner_text(); i=body.find("TALK"); print("PLACES:", body[i:i+800].replace("\n"," | "))
