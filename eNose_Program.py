import time
import adafruit_sgp30
import bme680
import board
import adafruit_tca9548a
from grove.i2c import Bus
from rpi_ws281x import PixelStrip, Color
from grove_ws2813_rgb_led_strip import GroveWS2813RgbStrip

# Define LED animation function
def colorWipe(strip, color, wait_ms=50):
    """Wipe color across display a pixel at a time."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms/1000.0)

# BME680 setup === start ===
# Initialize the BME680 sensor
try:
    bme680_sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
except (RuntimeError, IOError): # If the primary address fails, try the secondary address
    bme680_sensor = bme680.BME680(bme680.I2C_ADDR_SECONDARY)

# Oversampling & Filter Settings... for improved accuracy and noise reduction
bme680_sensor.set_humidity_oversample(bme680.OS_2X)
bme680_sensor.set_pressure_oversample(bme680.OS_4X)
bme680_sensor.set_temperature_oversample(bme680.OS_8X)
bme680_sensor.set_filter(bme680.FILTER_SIZE_3)
bme680_sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)

# Print all available sensor data fields immediately after startup, even if they’re uninitialized.
print('\n\nInitial reading:')
for name in dir(bme680_sensor.data):
    value = getattr(bme680_sensor.data, name)
    if not name.startswith('_'):
        print('{}: {}'.format(name, value))

# Set up the gas sensor heater
# The heater profile is a list of tuples (temperature, duration)
bme680_sensor.set_gas_heater_temperature(320)
bme680_sensor.set_gas_heater_duration(150)
bme680_sensor.select_gas_heater_profile(0)
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

# Create the TCA9548A object and give it the I2C bus
mux1 = adafruit_tca9548a.TCA9548A(i2c, address=0x70)
mux2 = adafruit_tca9548a.TCA9548A(i2c, address=0x71) # Note: remember to change address by shorting the two A0 pads on the module

# For each sensor, create it using the TCA9548A channel instead of the I2C object
sgp30_sensors = [
    adafruit_sgp30.Adafruit_SGP30(mux1[0]),  # SGP30_1
    adafruit_sgp30.Adafruit_SGP30(mux1[1]),  # SGP30_2
    adafruit_sgp30.Adafruit_SGP30(mux1[2]),  # SGP30_3
    adafruit_sgp30.Adafruit_SGP30(mux1[3]),  # SGP30_4
    adafruit_sgp30.Adafruit_SGP30(mux1[4]),  # SGP30_5
    adafruit_sgp30.Adafruit_SGP30(mux1[5]),  # SGP30_6
    adafruit_sgp30.Adafruit_SGP30(mux1[6]),  # SGP30_7
    adafruit_sgp30.Adafruit_SGP30(mux1[7]),  # SGP30_8
    adafruit_sgp30.Adafruit_SGP30(mux2[0]),  # SGP30_9
    adafruit_sgp30.Adafruit_SGP30(mux2[1])   # SGP30_10
]

print('Initializing SGP30 sensors...')
for sensor in sgp30_sensors:
    sensor.iaq_init()

print ('Testing LED ring functionality with a color wipe animation.')
colorWipe(strip, Color(255, 0, 0))  # Red wipe
colorWipe(strip, Color(0, 255, 0))  # Blue wipe
colorWipe(strip, Color(0, 0, 255))  # Green wipe

# After initial setup, can just use sensors as normal.
while True:
    co2_readings = []
    tvoc_readings = []

    # Read SGP30 sensor data
    for i, sensor in enumerate(sgp30_sensors):
        try:
            sensor.iaq_measure()  # Must call this every second
            co2_readings.append(sensor.eCO2)
            tvoc_readings.append(sensor.TVOC)
        except Exception as e:
            print(f"Error reading SGP30_{i+1}: {e}")
            co2_readings.append(None)
            tvoc_readings.append(None)
    
    # Print SGP30 sensor data
    print("-" * 50)
    for i, (co2, tvoc) in enumerate(zip(co2_readings, tvoc_readings)):
        if co2 is not None and tvoc is not None:
            print(f"SGP30_{i+1}: CO2={co2}ppm, TVOC={tvoc}ppb")
        else:
            print(f"SGP30_{i+1}: Error reading sensor")
    print("-" * 50)

    # Read BME680 sensor data
    if bme680_sensor.get_sensor_data():
        output = '{0:.2f} C,{1:.2f} hPa,{2:.2f} %RH'.format(
            bme680_sensor.data.temperature,
            bme680_sensor.data.pressure,
            bme680_sensor.data.humidity)

        if bme680_sensor.data.heat_stable:
            print('{0},{1} Ohms'.format(
                output,
                bme680_sensor.data.gas_resistance))
        else:
            print(output)

    

    

    time.sleep(1)