import time
shot("09-desk-after-agent-prepared")
# Needs you
if vp==1440:
    page.mouse.dblclick(1356, 75); wait(3)
else:
    page.get_by_text("Needs you").first.click(); wait(3)
shot("09-needs-you-no-prepared")
text("body", 1500)
