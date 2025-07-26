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

