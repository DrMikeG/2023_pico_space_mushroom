import time
import board
from digitalio import DigitalInOut, Direction, Pull
import analogio
import math
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keycode import Keycode

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
PORTS = [1,5,3,0,4,2]

coeff = [
    [00.0, 00.0, 00.0, -10.0, -10.0, 20.0], # TX
    [00.0, 00.0, 00.0, -17.0,  17.0, 00.0], # TY
    [-4.0, -4.0, -4.0,  00.0,  00.0, 00.0], # TZ (zoom)
    [-6.0,  6.0, 00.0,  00.0,  00.0, 00.0], # RY
    [ 3.0,  3.0, -6.0,  00.0,  00.0, 00.0], # RX
    [00.0, 00.0, 00.0,  03.0,  03.0, 03.0]  # RZ (not used)
]

origin = []
sx = 0
sy = 0
sw = 0

# The analog reading on the pin. Although it is limited to the resolution of the analog to digital converter (0-1023 for 10 bits or 0-4095 for 12 bits). Data type: int.
# 9 channels of 10-bit ADC

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
    elif cValue == 1:
        # 0001
        s3.value = False
        s2.value = False
        s1.value = False
        s0.value = True
    elif cValue == 2:
        # 0010
        s3.value = False
        s2.value = False
        s1.value = True
        s0.value = False
    elif cValue == 3:
        # 0011
        s3.value = False
        s2.value = False
        s1.value = True
        s0.value = True
    elif cValue == 4:
        # 0100
        s3.value = False
        s2.value = True
        s1.value = False
        s0.value = False
    elif cValue == 5:
        # 0101
        s3.value = False
        s2.value = True
        s1.value = False
        s0.value = True
    elif cValue == 6:
        # 0110
        s3.value = False
        s2.value = True
        s1.value = True
        s0.value = False
    elif cValue == 7:
        # 0111
        s3.value = False
        s2.value = True
        s1.value = True
        s0.value = True
    elif cValue == 8:
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

def mapValue(val,midVal):
    # assuming max of 64000
    # assuming min of 0
    # midVal is given
    # return values are -3, -2, -1, 0, 1, 2 or 3
    lowBox = (midVal / 10.0)
    if val < 3*lowBox:
        return -3
    if val < 6*lowBox:
        return -2
    if val < 9*lowBox:
        return -1
    if val < 10*lowBox:
        return 0
    highBox = (65536-midVal) / 10.0
    if val < midVal + (1 * highBox):
        return 0
    if val < midVal + (4 * highBox):
        return 1
    if val < midVal + (7 * highBox):
        return 2
    return 3

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

# I though the original values were -128 - 127 (256) and mine were -32000 - +32000
# The original values were -512 - + 512
DEAD_THRESH = 1    # original value was 1
SPEED_PARAM = 5 # original value was 600

setup()

def isRotate(mv):
    return abs(mv[RX]) > DEAD_THRESH or abs(mv[RY]) > DEAD_THRESH 


def isTranslate(mv):
    return abs(mv[TX]) > DEAD_THRESH or abs(mv[TY]) > DEAD_THRESH 

def isZoom(mv):
    return abs(mv[TZ]) > DEAD_THRESH

def printSV(sv):
    #print("RX/RY : {},{}".format(mv[RX],mv[RY]))
    print("sv: {}".format(sv))

def printMV(mv):
    print("TX/TY : {},{}".format(mv[TX],mv[TY]))
    print("TZ : {}".format(mv[TZ]))
    #print("RX/RY : {},{}".format(mv[RX],mv[RY]))

while True:

    keyboard.release_all()

    sv = [] # sensor values
    mv = [] # motion vector

    for p in range(DOF):
        #sv.append(readMux(PORTS[p])-origin[p])
        sv.append(mapValue(readMux(PORTS[p]),origin[p]))

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
        mv[i] = clamp(mv[i])

    #printSV(sv)
    #printMV(mv)
    #time.sleep(1.25)
    
    if isRotate(mv):
        #print("Rotate RX/RY : {},{}".format(mv[RX],mv[RY]))
        # App key press to rotate is arrow keys
        if mv[RX] > 0:
             keyboard.send(Keycode.RIGHT_ARROW)
        elif mv[RX] < 0:             
            keyboard.send(Keycode.LEFT_ARROW)
        if mv[RY] > 0:
             keyboard.send(Keycode.DOWN_ARROW)
        elif mv[RY] < 0:             
            keyboard.send(Keycode.UP_ARROW)
        
    if isTranslate(mv):
        print("Translating TX/TY : {},{}".format(mv[TX],mv[TY]))
        if mv[TX] > 0:
             keyboard.press(Keycode.LEFT_SHIFT, Keycode.RIGHT_ARROW)
        elif mv[TX] < 0:             
            keyboard.press(Keycode.LEFT_SHIFT, Keycode.LEFT_ARROW)
        if mv[TY] > 0:
             keyboard.press(Keycode.LEFT_SHIFT, Keycode.DOWN_ARROW)
        elif mv[TY] < 0:             
            keyboard.press(Keycode.LEFT_SHIFT, Keycode.UP_ARROW)

    if isZoom(mv):
        print("Zoom TZ: {}".format(mv[TZ]))
        if mv[TZ] > 0:
             keyboard.press(Keycode.PAGE_UP)
        elif mv[TZ] < 0:             
            keyboard.press(Keycode.PAGE_DOWN)
    
    
