# Test script for Thumbstick
# V2 renumbered to use pin 22 on the pico frame in the scanner (not the test pico on the breadboard)

import time
import board
import digitalio
from digitalio import DigitalInOut, Direction, Pull
import analogio




thumbSwitch = digitalio.DigitalInOut(board.GP22)
thumbSwitch.switch_to_input(pull=digitalio.Pull.UP)

thumbLeftRight = analogio.AnalogIn(board.GP26)
thumbUpDown = analogio.AnalogIn(board.GP27)

led = DigitalInOut(board.LED)
led.direction = Direction.OUTPUT
led.value = True

def blink(times):
    for _ in range(times):
        led.value = False
        time.sleep(0.1)
        led.value = True
        time.sleep(0.1)


def isLeft():
    # 0 or 65535
    return thumbLeftRight.value < 16383

def isRight():
    # 0 or 65535
    return thumbLeftRight.value > 49149

def isUp():
    # 0 or 65535
    return thumbUpDown.value > 49149
        
def isDown():
    # 0 or 65535
    return thumbUpDown.value < 16383




while True:

    if thumbSwitch.value == False:
        print("Thumb switch is pressed")
        time.sleep(0.5)

    if isLeft():
        print("Left")
    if isRight():
        print("Right")
    if isUp():
        print("Up")
    if isDown():
        print("Down")
    time.sleep(0.25)