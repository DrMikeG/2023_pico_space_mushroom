# 2023_pico_space_mushroom

https://www.thingiverse.com/thing:5739462


I've started printing the parts - beginning with the big knob.

I've ordered:

```WMYCONGCONG 5 PCS Joystick Breakout Module Game Controller for Arduino PS2 + 120 PCS Multicolored Breadboard Jumper Wires Ribbon Cables Kit```

Because I think they match the dimensions used by the OP.

```BGTXINGI 800PCS 8 Kinds M2 Nickel-Plate Flat Head Self Tapping Screw Stainless Sheet Wood Screw Assortment Kit Collected in A Convenient Case```

For assembly

And because I plan to use a pico, which only has 3 ADCs (and I need 6 inputs) - 

```SparkFun Analog/Digital MUX Breakout - CD74HC4067```

> This is a breakout board for the very handy 16-Channel Analog/Digital Multiplexer/Demultiplexer CD74HC4067. This chip is like a rotary switch - it internally routes the common pin (COM in the schematic, SIG on the board) to one of 16 channel pins (CHANxx).
>
> It works with both digital and analog signals (the voltage can’t be higher than VCC), and the connections function in either direction. To control it, connect 4 digital outputs to the chip’s address select pins (S0-S3), and send it the binary address of the channel you want (see the datasheet for details). This allows you to connect up to 16 sensors to your system using only 5 pins!
>
> Since the mux/demux also works with digital signals, you can use it to pipe TTL-level serial data to or from multiple devices. For example, you could use it to connect the TX pins of 16 devices to one RX pin on your microcontroller. You can then select any one of those 16 devices to listen to. If you want two-way communications, you can add a second board to route your microcontroller’s TX line to 16 device’s RX lines. By using multiple boards, you can create similar arrangements for I2C, SPI, etc.
>
> The internal switches are bidirectional, support voltages between ground and VCC, have low “on” resistance and low “off” leakage, and to prevent crosstalk, perform “break-before-make” switching. The board also breaks out the chip’s “enable” pin, which when driven high, will completely disconnect the common pin (all switches “off”).
>
> Features:
> 2V to 6V operation
> “On” resistance: 70 Ohms @ 4.5V
> 6ns break-before-make @ 4.5V
> Wide operating temperature range: -55C to 125C
> Documents:
> - https://www.sparkfun.com/datasheets/IC/cd74hc4067.pdf
> - https://github.com/sparkfun/Analog_Digital_MUX_Breakout

> Do note that the enable pin, EN, is active low. The description says this but I don't read...
> Use this to read sixteen inputs or to control sixteen outputs (or any combination thereof) using only six pins from you micro (five pins if you hold EN low via hardwire).


Let's go study the example code.


It acts as both a mouse and keyboard. Can the pico do this?


https://learn.adafruit.com/circuitpython-essentials/circuitpython-hid-keyboard-and-mouse


I wired up the joystick modules to the pico, and read the dx and dy values.

They seem are sensitive enough for left vs right, but the granularity seems very low, especially for higher values.
Also, pushing fully up seems to register as full up and full right. I've ordered some more.

Going to check one I've not soldered - perhaps the heat damaged the pots?
- No, warehouse soldered ones are just as crappy.

Wait for new supplies.

5 New, equally crappy looking joystick modules arrived. Same B103 pots. New boards don't even have the corners rounded off.
Got exactly the same behaviour when plugged in - considered that it could be because I was supplying 5V and then reading it with a 3V ADC.

Swapped power to joystick to 3V and they behave much more predictably. Hopefully my ADC is not damaged.


Pan in our app is
left-shift + middle mouse button press + mouse move up/down left/right