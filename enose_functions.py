import os
import subprocess
import time
import adafruit_sgp30
import bme680
import board
import adafruit_tca9548a
import tkinter as tk
import threading
import RPi.GPIO as GPIO
from grove.i2c import Bus
from rpi_ws281x import PixelStrip, Color
from grove_ws2813_rgb_led_strip import GroveWS2813RgbStrip

def normalize(value, min_val, max_val):
    return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))

# Define LED animation function
def colorWipe(strip, color, wait_ms=50):
    """Wipe color across display a pixel at a time."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms/1000.0)

def button_polling_loop():
    global shutdown

    prev_state_27 = GPIO.input(27)
    prev_state_17 = GPIO.input(17)

    while not stop_event.is_set():
        curr_state_27 = GPIO.input(27)
        curr_state_17 = GPIO.input(17)

        if prev_state_27 == GPIO.HIGH and curr_state_27 == GPIO.LOW:
            print("GPIO 27 pressed – triggering shutdown.")
            shutdown = True
            window.after(0, on_closing)

        if prev_state_17 == GPIO.HIGH and curr_state_17 == GPIO.LOW:
            print("GPIO 17 pressed – exiting app without shutdown.")
            shutdown = False
            window.after(0, on_closing)

        prev_state_27 = curr_state_27
        prev_state_17 = curr_state_17

        time.sleep(0.05)  # 50ms polling delay