import time
from rpi_ws281x import Color
from RGB_ring import GroveWS2813RgbStrip

# connect to pin 12(slot PWM)
PIN   = 12
# For Grove - WS2813 RGB LED Strip Waterproof - 30 LED/m
# there is 30 RGB LEDs.
COUNT = 20
strip = GroveWS2813RgbStrip(PIN, COUNT)

# Define functions which animate LEDs in various ways.
def colorWipe(strip, color, wait_ms=50):
    """Wipe color across display a pixel at a time."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms/1000.0)

while True:

    print ('Color wipe animations.')
    colorWipe(strip, Color(255, 0, 0))  # Red wipe
    colorWipe(strip, Color(0, 255, 0))  # Blue wipe
    colorWipe(strip, Color(0, 0, 255))  # Green wipe

# to run this on the Raspberry Pi: "sudo /home/raspberrypi/Desktop/OneNose_Scripts/Directional_eNose/Test_Scripts/RGB_ring_simple.py"
# This is because the GPIO pins need root privileges to access.