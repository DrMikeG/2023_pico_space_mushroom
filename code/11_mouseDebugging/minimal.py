import time
import math
import usb_hid
from adafruit_hid.mouse import Mouse
import sys


mouse = Mouse(usb_hid.devices)

def move(x, y, w, sx, sy, sw):
    
    
    print("Moving {},{},{}".format(x,y,w))
    sx = sx + x
    sy = sy + y
    sw = sw + w
    mouse.move(x, y,w)
    print("Cumulative Move {},{},{}".format(sx,sy,sw))
    return sx, sy, sw

def resetMove(sx,sy,sw):
    print("Reset by moving {},{},{}".format(-sx,-sy,0))
    mouse.move(-sx, -sy, 0)
    return 0,0,0

try:
    print("Position your mouse somewhere for reference... movement will start in 5 seconds...")
    time.sleep(5)
    sx = 0
    sy = 0
    sw = 0
    #Moving 2,4,0
    print("Step 1 of 5")
    sx,sy,sw = move(2,4,0,sx,sy,sw)
    time.sleep(1.5)
    #Cumulative Move 2,4,0
    #Moving 3,5,0
    print("Step 2 of 5")
    sx,sy,sw = move(3,5,0,sx,sy,sw)
    time.sleep(1.5)
    #Cumulative Move 5,9,0
    #Moving 3,5,0
    print("Step 3 of 5")
    sx,sy,sw = move(3,5,0,sx,sy,sw)
    time.sleep(1.5)
    #Cumulative Move 8,14,0
    #Moving 3,5,0
    print("Step 4 of 5")
    sx,sy,sw = move(3,5,0,sx,sy,sw)
    time.sleep(1.5)
    #Cumulative Move 11,19,0
    #Moving 3,5,0
    print("Step 5 of 5")
    sx,sy,sw = move(3,5,0,sx,sy,sw)
    time.sleep(1.5)
    #Cumulative Move 14,24,0
    #Reset by moving -14,-24,0
    print("Return to starting position?")
    sx,sy,sw = resetMove(14,24,sw)
    time.sleep(1.3)
    
except:
    mouse.release_all()
    print(sys.exc_info()[0])



121,118
-14,-24
---
107,94
