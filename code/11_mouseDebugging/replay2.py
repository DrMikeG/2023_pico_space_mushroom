import time
import board
from digitalio import DigitalInOut, Direction, Pull
import analogio
import math
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keycode import Keycode
from adafruit_hid.mouse import Mouse
import pwmio
import sys


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

ledG = pwmio.PWMOut(board.GP13, frequency=1000)
ledR = pwmio.PWMOut(board.GP14, frequency=1000)
ledB = pwmio.PWMOut(board.GP12, frequency=1000)
ledR.duty_cycle = 0
ledG.duty_cycle = 0
ledB.duty_cycle = 32000

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
    [-2.0, -2.0, -2.0,  00.0,  00.0, 00.0], # TZ (zoom)
    [-6.0,  6.0, 00.0,  00.0,  00.0, 00.0], # RY
    [ 3.0,  3.0, -6.0,  00.0,  00.0, 00.0], # RX
    [00.0, 00.0, 00.0,  03.0,  03.0, 03.0]  # RZ (not used)
]

origin = []

activeMode = 0

# The analog reading on the pin. Although it is limited to the resolution of the analog to digital converter (0-1023 for 10 bits or 0-4095 for 12 bits). Data type: int.
# 9 channels of 10-bit ADC

def blink(times):
    for _ in range(times):
        led.value = False
        time.sleep(0.1)
        led.value = True
        time.sleep(0.1)

def setColour(r,g,b):
    ledR.duty_cycle = r
    ledG.duty_cycle = g
    ledB.duty_cycle = b


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

def isSwitch():
    return isSwitch0() or isSwitch1() or isSwitch2()

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

def mapValueScaled(val,midVal):
    # assuming max of 65536
    # assuming min of 0
    # midVal is given
    if val < midVal:
        return -3.0 * (1.0-(val / midVal))
    else:
        return 3.0 * (val - midVal) / (65536-midVal)


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
DEAD_THRESH = 2    # original value was 1
SPEED_PARAM = 5 # original value was 600



def move(x, y, w, sx, sy, sw):
    factor = 1
    int_x = int(math.trunc(factor*x))
    int_y = int(math.trunc(factor*y))
    int_w = int(math.trunc(factor*w))
    print("Moving {},{},{}".format(int_x,int_y,int_w))
    sx = sx + int_x
    sy = sy + int_y
    sw = sw + int_w
    mouse.move(int_x, int_y, int_w)
    print("Cumulative Move {},{},{}".format(sx,sy,sw))
    return sx, sy, sw

def resetMove(sx,sy,sw):
    print("Reset by moving {},{},{}".format(-sx,-sy,0))
    mouse.move(-sx, -sy, 0)
    return 0,0,0

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


def mode0Loop():
    global activeMode
    sx = 0
    sy = 0
    sw = 0

    activeMode = 0
    # Have we started a movement?
    isMouseMoving = False
    # This will cause the mouse position to reset
    shouldEndMove = False
    print("Mode: VTK/NX/SE")
    RED = [32000,0,0]
    
    setColour(RED[0],RED[1],RED[2])

    allMVs = [
    [1.18329, 2.01284, -0.000308048, -0.00147518, 0.00128862, -0.354987],
    [1.72408, 2.98185, -0.00150685, -0.00689852, 0.000450795, -0.517223],
    [1.72408, 2.98185, -0.000295392, 0.000320148, -0.0013664, -0.517223],
    [1.73285, 2.96695, -0.000308048, -0.00147518, 0.00128862, -0.519854],
    [1.73574, 2.97187, 0.000290394, 0.000320148, 0.000390959, -0.520721],
    [1.71814, 2.96203, 0.00030199, -0.001472, -0.00226247, -0.520757],
    [2.43795, 4.31836, 1.19405, 1.68161, -0.918565, -0.0511544],
    [2.6172, 3.65468, 1.61643, 3.32454, -0.831009, 0.161931],
    [1.87662, 2.41545, 1.84586, 3.54316, 0.185204, 0.378875],
    [1.27783, 1.39756, 2.4675, 2.92665, 1.12026, 0.561128],
    [1.35725, 2.97243, 2.64964, 0.257304, 0.913091, 0.989918],
    [2.17407, 7.38314, 1.71247, -3.55309, -0.193189, 2.31202],
    [2.81434, 4.88669, 0.914859, -4.36462, -1.3741, 3.21354],
    [2.84343, 4.80698, 0.888843, -4.43908, -1.33507, 3.20482],
    [5.42151, 3.81203, 0.788195, -3.5513, -2.96332, 1.8218],
    [5.87072, 3.31522, 1.17496, 0.00408936, -7.13611, 1.75768],
    [5.53414, 3.06669, 1.1738, 0.00229645, -7.14227, 1.64673],
    [5.5847, 2.7439, 1.17555, 0.00220947, -7.14227, 1.56354],
    [5.33642, 2.16755, 1.17619, -0.0048706, -7.14585, 1.3764],
    [0.00600672, 0.00147128, 2.52179, 1.34983, -1.07699, -0.00180202],
    [1.03101, -1.77095, 2.18508, 3.55743, 1.22428, -0.31462],
    [5.40143, -1.94571, 2.09526, 3.55571, 0.952221, 0.294686],
    [8.90131, -1.92574, 1.7272, 3.55741, -0.154527, 0.824954],
    [9.18332, -1.93073, 1.35457, 2.76175, -0.0842697, 0.865933],
    [9.54663, -1.9159, 0.960629, 1.82827, 0.139484, 0.919148],
    [9.66002, -1.92082, 0.893876, 1.65964, 0.197351, 0.937458],
    [9.71521, -1.91575, 0.806232, 1.4108, 0.297118, 0.949681],
    [9.72389, -1.91076, 0.79479, 1.38346, 0.298433, 0.952306],
    [9.71514, -1.90576, 0.754144, 1.29334, 0.32242, 0.952315],
    [9.68583, -1.86582, 0.000290394, 0.000320148, 0.000390959, 0.958492],
    [-6.92112, -0.018613, 0.000887775, -0.001472, -0.000505114, -1.03291],
    [-7.39953, -0.0387929, -0.000893833, -0.00147518, -0.000468735, -1.09933],
    [-7.3995, -0.0287029, -0.000308048, -0.00147518, 0.00128862, -1.102],
    [-7.41134, -0.0387929, -0.000295392, 0.000320148, -0.0013664, -1.1011],
    [-7.40838, -0.033694, -0.000295392, 0.000320148, -0.0013664, -1.10465],
    [-7.41722, -0.0287029, -0.000295392, 0.000320148, -0.0013664, -1.10466],
    [-7.42019, -0.0337479, -0.000308048, -0.00147518, 0.00128862, -1.10377],
    [-7.53834, -0.0540047, 0.000289334, -0.00326732, 0.000392549, -1.1135],
    [-10.7368, -7.2885, 0.000289334, -0.00326732, 0.000392549, 0.321742],
    [-4.00294, -13.5143, -0.000295392, 0.000320148, -0.0013664, 1.20088],
    [-3.87664, -13.729, 0.000289334, -0.00326732, 0.000392549, 1.16299],
    [-3.88255, -13.729, -0.000893833, -0.00147518, -0.000468735, 1.16211],
    [-3.87364, -13.7139, -0.000296452, -0.00326732, -0.00136481, 1.16209],
    [-4.5052, -12.6705, 0.000290394, 0.000320148, 0.000390959, 1.3489],
    [-5.61432, 9.75274, -0.000295392, 0.000320148, -0.0013664, 1.6843],
    [-5.77261, 10.1792, 0.00147457, -0.001472, 0.00125527, 1.7344],
    [-5.79891, 10.2239, 0.000290394, 0.000320148, 0.000390959, 1.74229],
    [-5.83392, 10.2638, -0.00206322, 0.000159147, 0.00392139, 1.75541],
    [-5.85429, 10.2689, -0.000315867, -0.00508292, 0.00130035, 1.75629],
    [-5.87763, 10.2987, 0.000290394, 0.000320148, 0.000390959, 1.76329],
    [-5.86594, 10.2788, 0.000876129, -0.00326732, 0.00215294, 1.75978],
    [-5.87471, 10.2937, 0.000289334, -0.00326732, 0.000392549, 1.76241],
    [-4.66915, 9.67045, -0.000893833, -0.00147518, -0.000468735, 1.40336],
    [1.12095, 7.28227, -0.5648, 3.28674, 0.848027, -0.336286],
    [3.67969, 6.25671, -0.0105667, 7.1419, 0.0140403, -1.10391],
    [3.83871, 6.52711, -0.0099741, 7.13847, 0.0157877, -1.15427],
    [3.54373, 6.02559, -0.00998096, 7.1419, 0.0157976, -1.06312],
    [2.51972, 4.28476, -0.011142, 7.14363, 0.0149031, -0.755915],
    [0.0262122, 0.0458027, -0.009417, 7.13845, 0.012316, -0.00786365],
    [0.0291481, 0.0408116, -0.00653095, 7.13155, 0.0106226, -0.00874443],
    [0.00892817, -0.00344596, -0.00998096, 7.1419, 0.0157976, -6.21743e-05],
    [0.00599225, 0.00154511, 0.548907, 5.46524, -0.822534, 0.000818603],
    [0.00599225, 0.00154511, 0.548907, 5.46524, -0.822534, 0.000818603],
    [0.000178298, 0.00154511, 0.547753, 5.46353, -0.823439, -5.34893e-05],
    [0.000178298, 0.00154511, 1.18827, 3.56243, -1.78421, -5.34893e-05]
    ]
    testDataRowCounter = 0
    nTestDataRows = 50

    for i in range(0,nTestDataRows):
        sv = [] # sensor values
        mv = [0,0,0,0,0,0] # motion vector
        
        mv = allMVs[i]
        print(i)

        print(mv)
        if isTranslate(mv):
            print("Translating TX/TY : {},{}".format(mv[TX],mv[TY]))
            sx,sy,sw = move(mv[TX],mv[TY],0,sx,sy,sw)
            time.sleep(0.3)

    walkBack = False
    if walkBack:
        for j in range(nTestDataRows-1,-1,-1):
            sv = [] # sensor values
            mv = [0,0,0,0,0,0] # motion vector
            
            mv = allMVs[j]
            mv[TX] = -mv[TX]
            mv[TY] = -mv[TY]
            print(j)

            print(mv)
            if isTranslate(mv):
                print("Translating TX/TY : {},{}".format(mv[TX],mv[TY]))
                sx,sy,sw = move(mv[TX],mv[TY],0,sx,sy,sw)
                time.sleep(0.1)
    else:
        sx,sy,sw = resetMove(sx,sy,sw)
        sx = 0
        sy = 0
        sw = 0

def test():
    sx = 0
    sy = 0
    sw = 0

    #Moving 2,4,0
    sx,sy,sw = move(2,4,0,sx,sy,sw)
    time.sleep(0.3)
    #Cumulative Move 2,4,0
    #Moving 3,5,0
    sx,sy,sw = move(3,5,0,sx,sy,sw)
    time.sleep(0.3)
    #Cumulative Move 5,9,0
    #Moving 3,5,0
    sx,sy,sw = move(3,5,0,sx,sy,sw)
    time.sleep(0.3)
    #Cumulative Move 8,14,0
    #Moving 3,5,0
    sx,sy,sw = move(3,5,0,sx,sy,sw)
    time.sleep(0.3)
    #Cumulative Move 11,19,0
    #Moving 3,5,0
    sx,sy,sw = move(3,5,0,sx,sy,sw)
    time.sleep(0.3)
    #Cumulative Move 14,24,0
    #Reset by moving -14,-24,0
    sx,sy,sw = resetMove(14,24,sw)
    time.sleep(0.3)


def mode1Loop():
    global activeMode
    sx = 0
    sy = 0
    sw = 0
   
    activeMode = 1
    # Have we started a movement?
    isMouseMoving = False
    # This will cause the mouse position to reset
    shouldEndMove = False

    print("Mode: Visio")
    GREEN = [0,32000,0]
    
    setColour(GREEN[0],GREEN[1],GREEN[2])

    while True:

        sv = [] # sensor values
        mv = [] # motion vector

        # Values are read and simply mapped -3 to +3
        for p in range(DOF):
            sv.append(mapValueScaled(readMux(PORTS[p]),origin[p]))

        for i in range(DOF):
            mv.append(0.0)
            for j in range(DOF):
                mv[i] = mv[i] + (coeff[i][j] * sv[j])
            mv[i] = mv[i] / SPEED_PARAM
            # I doubt this is having any effect

        movementDetected = isRotate(mv) or isTranslate(mv) or isZoom(mv)
        
        if movementDetected:
            if not isMouseMoving: # if we were not moving, we now are
                isMouseMoving = True
                print("Starting movement...")
                # Start move (Init mouse? Press Key?)
                mouse.press(Mouse.MIDDLE_BUTTON)
        else:
            if isMouseMoving: # if we were moving, now we are not, and we should end
                isMouseMoving = False
                shouldEndMove = True

        if isMouseMoving:
            if isRotate(mv):
                print("Rotate RX/RY : {},{}".format(mv[RX],mv[RY]))
                # No keys pressed
                sx,sy,sw = move(mv[RX],mv[RY],0,sx,sy,sw)
                time.sleep(0.1)
                
            if isTranslate(mv):
                print("Translating TX/TY : {},{}".format(mv[TX],mv[TY]))
                keyboard.press(Keycode.LEFT_SHIFT)
                sx,sy,sw = move(mv[TX],mv[TY],0,sx,sy,sw)
                time.sleep(0.1)
                keyboard.release(Keycode.LEFT_SHIFT)

            if isZoom(mv):
                print("Zoom TZ: {}".format(mv[TZ]))
                keyboard.press(Keycode.LEFT_CONTROL)
                time.sleep(0.05)
                sx,sy,sw = move(0,mv[TZ],0,sx,sy,sw)
                time.sleep(0.05)
                keyboard.release(Keycode.LEFT_CONTROL)

        if shouldEndMove:
            print("Ending movement...")
            mouse.release(Mouse.MIDDLE_BUTTON)        
            time.sleep(0.1)
            keyboard.release_all()
            time.sleep(0.1)
            #sx,sy,sw = resetMove(sx,sy,sw)
            sx = 0
            sy = 0
            sw = 0
            shouldEndMove = False     

        if isSwitch():
            activeMode = activeMode + 1
            time.sleep(0.24)
            return

setup()



activeMode = 0

try:
    print("Press switch to start mouse movement")
    while True:
        if isSwitch():
            mode0Loop()
        
    
except:
    keyboard.release_all()
    mouse.release_all()
    print(sys.exc_info()[0])
