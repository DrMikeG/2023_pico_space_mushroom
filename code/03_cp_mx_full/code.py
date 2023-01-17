# Test script for Thumbstick
# V2 renumbered to use pin 22 on the pico frame in the scanner (not the test pico on the breadboard)

import time
import board
from digitalio import DigitalInOut, Direction, Pull
import analogio

import usb_hid
from adafruit_hid.mouse import Mouse
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keycode import Keycode

mouse = Mouse(usb_hid.devices)
keyboard = Keyboard(usb_hid.devices)
keyboard_layout = KeyboardLayoutUS(keyboard)  # We're in the US :)

adc = analogio.AnalogIn(board.GP27)

s0 = DigitalInOut(board.GP2)
s1 = DigitalInOut(board.GP3)
s2 = DigitalInOut(board.GP4)
s3 = DigitalInOut(board.GP5)
s0.direction = Direction.OUTPUT
s1.direction = Direction.OUTPUT
s2.direction = Direction.OUTPUT
s3.direction = Direction.OUTPUT

led = DigitalInOut(board.LED)
led.direction = Direction.OUTPUT
led.value = True

DOF = 6
TX = 0 # translation X -> pan X
TY = 1 # translation Y -> pan Y
TZ = 2 # translation Z -> zoom
RX = 3 # rotation X
RY = 4 # rotation Y
RZ = 5 # rotation Z

# [2,3]       [0,1]
#      \     /
#       \   /
#         |
#         |
#       [4,5]
# 2   0
#   *    left/right
#   4
#
# 3   1
#   *   up/down
#   5
# Reading the above number anti-clockwise 2 o'clock, 10 o'clock, 6 o'clock
PORTS = [1,3,5,0,2,4]

coeff = [
    [00.0, 00.0, 00.0, -10.0, -10.0, 20.0], # TX
    [00.0, 00.0, 00.0, -17.0,  17.0, 00.0], # TY
    [-3.0, -3.0, -3.0,  00.0,  00.0, 00.0], # TZ (zoom)
    [-6.0,  6.0, 00.0,  00.0,  00.0, 00.0], # RY
    [ 3.0,  3.0, -6.0,  00.0,  00.0, 00.0], # RX
    [00.0, 00.0, 00.0,  03.0,  03.0, 03.0]  # RZ (not used)
]

origin = []
sx = 0
sy = 0
sw = 0




def move(x, y, w):
    x = deaden(x)
    y = deaden(y)
    w = deaden(w)
    mouse.move(x, y, w)
    sx = sx + x
    sy = sy + y
    sw = sw + w

def resetMove():
    mouse.move(-sx, -sy, -sw)
    sx=0
    sy=0
    sw=0

def blink(times):
    for _ in range(times):
        led.value = False
        time.sleep(0.1)
        led.value = True
        time.sleep(0.1)

def switchMX(cValue):
    if cValue == 0:
        # 0000
        s3.value = False
        s2.value = False
        s1.value = False
        s0.value = False
    if cValue == 1:
        # 0001
        s3.value = False
        s2.value = False
        s1.value = False
        s0.value = True
    if cValue == 2:
        # 0010
        s3.value = False
        s2.value = False
        s1.value = True
        s0.value = False
    if cValue == 3:
        # 0011
        s3.value = False
        s2.value = False
        s1.value = True
        s0.value = True
    if cValue == 4:
        # 0100
        s3.value = False
        s2.value = True
        s1.value = False
        s0.value = False
    if cValue == 5:
        # 0101
        s3.value = False
        s2.value = True
        s1.value = False
        s0.value = True
    if cValue == 6:
        # 0110
        s3.value = False
        s2.value = True
        s1.value = True
        s0.value = False
    if cValue == 7:
        # 0111
        s3.value = False
        s2.value = True
        s1.value = True
        s0.value = True
    if cValue == 8:
        # 1000
        s3.value = True
        s2.value = False
        s1.value = False
        s0.value = False
    #print(adc.value)

def isSwitch0():
    # enable checking of C6
    switchMX(6)
    return adc.value < 500

def isSwitch1():
    # enable checking of C7
    switchMX(7)
    return adc.value < 500

def isSwitch2():
    # enable checking of C8
    switchMX(8)
    return adc.value < 500

def readMux(cValue):
    switchMX(cValue)
    return adc.value


def deaden(val):
    if val > DEAD_THRESH:
        val = val - DEAD_THRESH
    elif val < DEAD_THRESH:
        val = val + DEAD_THRESH
    else:
        val = 0
    return val

def clamp(val):
    if val > 127:
        return 127
    elif val < -128:
        return -128
    return val

def setup():
    for p in range(DOF):
        port = PORTS[p]
        vals = []
        nSamples = 10
        for _ in range(nSamples):
            vals.append(readMux(port))
        origin.append(round(sum(vals)/nSamples))
        print("port {}: {} samples as vals {} averaged to {}".format(p,nSamples,vals,origin[p]))


DEAD_THRESH = 50    # original value was 1
SPEED_PARAM = 30000 # original value was 600

setup()

def isTranslate(mv):
    return abs(mv[RX]) > DEAD_THRESH or abs(mv[RY]) > DEAD_THRESH 

def printSV(sv):
    #print("RX/RY : {},{}".format(mv[RX],mv[RY]))
    print("sv: {}".format(sv))


def printMV(mv):
    print("TX/TY : {},{}".format(mv[TX],mv[TY]))
    print("TZ : {}".format(mv[TZ]))
    print("RX/RY : {},{}".format(mv[RX],mv[RY]))

while True:

    sv = [] # sensor values
    mv = [] # motion vector

    for p in range(DOF):
        sv.append(readMux(PORTS[p])-origin[p])

    # origins are around 30,000
    #printSV(sv)
    # SVs are +/-1500
    
    # The max difference for zoom is 3x the difference from average
    # 32000 * 3 * 3 = 288,000
    # / 600 = 160

    for i in range(DOF):
        mv.append(0.0)
        for j in range(DOF):
            mv[i] = mv[i] + (coeff[i][j] * sv[j])
        mv[i] = mv[i] / SPEED_PARAM
        #mv[i] = clamp(mv[i])

    #printSV(sv)
    printMV(mv)
    time.sleep(1.25)
    #if isTranslate(mv):
    #    print("Translate....")

    #print("d0x:{:06} d0y:{:06} d1x:{:06} d1y:{:06} d2x:{:06} d2y:{:06}".format(readMux(0),readMux(1),readMux(2),readMux(3),readMux(4),readMux(5)))

    if isSwitch0():
        print("Switch 0 pressed")
        #https://docs.circuitpython.org/projects/hid/en/latest/api.html
        keyboard.press(Keycode.LEFT_SHIFT)
        mouse.press(Mouse.MIDDLE_BUTTON)
        mouse.move(-100, 0, 0)
        time.sleep(.09)
        mouse.release(Mouse.MIDDLE_BUTTON)
        keyboard.release(Keycode.LEFT_SHIFT)
        mouse.move(100, 0, 0)
        time.sleep(0.25)
