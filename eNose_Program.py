
import time
import seeed_sgp30
import bme680
import board
import adafruit_tca9548a
from grove.i2c import Bus
from rpi_ws281x import PixelStrip, Color

# Define LED animation function
def colorWipe(strip, color, wait_ms=50):
    """Wipe color across display a pixel at a time."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms/1000.0)

# Address notes for each device:
# SGP30: 0x58
# BME680: 0x76 (Default)
# TCA9548A: 0x70 (primary), 0x71 (secondary, if A0 is shorted)

# BME680 setup === start ===
# Initialize the BME680 sensor
try:
    sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
except (RuntimeError, IOError): # If the primary address fails, try the secondary address
    sensor = bme680.BME680(bme680.I2C_ADDR_SECONDARY)

# Oversampling & Filter Settings... for improved accuracy and noise reduction
sensor.set_humidity_oversample(bme680.OS_2X)
sensor.set_pressure_oversample(bme680.OS_4X)
sensor.set_temperature_oversample(bme680.OS_8X)
sensor.set_filter(bme680.FILTER_SIZE_3)
sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)

# Print all available sensor data fields immediately after startup, even if they’re uninitialized.
print('\n\nInitial reading:')
for name in dir(sensor.data):
    value = getattr(sensor.data, name)
    if not name.startswith('_'):
        print('{}: {}'.format(name, value))

# Set up the gas sensor heater
# The heater profile is a list of tuples (temperature, duration)
sensor.set_gas_heater_temperature(320)
sensor.set_gas_heater_duration(150)
sensor.select_gas_heater_profile(0)
# BME680 setup === end ===

# Grove WS2813 RGB LED Strip setup === start ===
# connect to pin 12(slot PWM)
PIN   = 12
# For Grove - WS2813 RGB LED Ring - 20 LED/m
# there are 20 RGB LEDs.
COUNT = 20
strip = GroveWS2813RgbStrip(PIN, COUNT)
# Grove WS2813 RGB LED Strip setup === end ===


# Create I2C bus as normal
i2c = board.I2C()  # uses board.SCL and board.SDA

# Create the PCA9546A object and give it the I2C bus
mux1 = adafruit_tca9548a.PCA9546A(i2c, address=0x70)
mux2 = adafruit_tca9548a.PCA9546A(i2c, address=0x71) # Note: remember to change address by shorting the A0 pad on the module

# For each sensor, create it using the PCA9546A channel instead of the I2C object
sgp30_1 = seeed_sgp30.grove_sgp30(mux1[0])
sgp30_2 = seeed_sgp30.grove_sgp30(mux1[1])
sgp30_3 = seeed_sgp30.grove_sgp30(mux1[2])
sgp30_4 = seeed_sgp30.grove_sgp30(mux1[3])
sgp30_5 = seeed_sgp30.grove_sgp30(mux1[4])
sgp30_6 = seeed_sgp30.grove_sgp30(mux1[5])
sgp30_7 = seeed_sgp30.grove_sgp30(mux1[6])
sgp30_8 = seeed_sgp30.grove_sgp30(mux1[7])
sgp30_9 = seeed_sgp30.grove_sgp30(mux2[0])
sgp30_10 = seeed_sgp30.grove_sgp30(mux2[1])

print ('Testing LED ring functionality with a color wipe animation.')
colorWipe(strip, Color(255, 0, 0))  # Red wipe
colorWipe(strip, Color(0, 255, 0))  # Blue wipe
colorWipe(strip, Color(0, 0, 255))  # Green wipe

# After initial setup, can just use sensors as normal.
while True:
    # Read SGP30 sensor data
    print(f"SGP30_1: CO2={sgp30_1.getCO2_ppm()}ppm, TVOC={sgp30_1.getTVOC_ppb()}ppb")
    print(f"SGP30_2: CO2={sgp30_2.getCO2_ppm()}ppm, TVOC={sgp30_2.getTVOC_ppb()}ppb")
    print(f"SGP30_3: CO2={sgp30_3.getCO2_ppm()}ppm, TVOC={sgp30_3.getTVOC_ppb()}ppb")
    print(f"SGP30_4: CO2={sgp30_4.getCO2_ppm()}ppm, TVOC={sgp30_4.getTVOC_ppb()}ppb")
    print(f"SGP30_5: CO2={sgp30_5.getCO2_ppm()}ppm, TVOC={sgp30_5.getTVOC_ppb()}ppb")
    print(f"SGP30_6: CO2={sgp30_6.getCO2_ppm()}ppm, TVOC={sgp30_6.getTVOC_ppb()}ppb")
    print(f"SGP30_7: CO2={sgp30_7.getCO2_ppm()}ppm, TVOC={sgp30_7.getTVOC_ppb()}ppb")
    print(f"SGP30_8: CO2={sgp30_8.getCO2_ppm()}ppm, TVOC={sgp30_8.getTVOC_ppb()}ppb")
    print(f"SGP30_9: CO2={sgp30_9.getCO2_ppm()}ppm, TVOC={sgp30_9.getTVOC_ppb()}ppb")
    print(f"SGP30_10: CO2={sgp30_10.getCO2_ppm()}ppm, TVOC={sgp30_10.getTVOC_ppb()}ppb")
    print("-" * 50)

    # Read BME680 sensor data
    if sensor.get_sensor_data():
        output = '{0:.2f} C,{1:.2f} hPa,{2:.2f} %RH'.format(
            sensor.data.temperature,
            sensor.data.pressure,
            sensor.data.humidity)

        if sensor.data.heat_stable:
            print('{0},{1} Ohms'.format(
                output,
                sensor.data.gas_resistance))
        else:
            print(output)

    

    time.sleep(1)