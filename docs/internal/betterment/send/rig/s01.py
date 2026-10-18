import time
t=time.time()
page.mouse.dblclick(505, 80); wait(3)
print("open meeting", round(time.time()-t,1))
shot("01-meeting-open")
text("body", 6000)
