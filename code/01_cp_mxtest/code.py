# Test script for Thumbstick
# V2 renumbered to use pin 22 on the pico frame in the scanner (not the test pico on the breadboard)

import time
import board
import digitalio
from digitalio import DigitalInOut, Direction, Pull
import analogio



thumbSwitch = digitalio.DigitalInOut(board.GP22)
thumbSwitch.switch_to_input(pull=digitalio.Pull.UP)

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


while True:
    print("d0x:{:06} d0y:{:06} d1x:{:06} d1y:{:06} d2x:{:06} d2y:{:06}".format(readMux(0),readMux(1),readMux(2),readMux(3),readMux(4),readMux(5)))
    time.sleep(0.25)
