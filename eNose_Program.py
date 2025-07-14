import time
import adafruit_sgp30
import bme680
import board
import adafruit_tca9548a
import tkinter as tk
import threading
from grove.i2c import Bus
from rpi_ws281x import PixelStrip, Color
from grove_ws2813_rgb_led_strip import GroveWS2813RgbStrip

# Define a bias to rotate LED direction to match sensor layout
PIN   = 12  # connect Grove WS2813 RGB LED Strip SIG to pin 12(slot PWM)
COUNT = 20  # For Grove - WS2813 RGB LED Ring - 20 LED total

stop_event = threading.Event()

co2_readings = []
tvoc_readings = []
combined_scores = []

# Grove WS2813 RGB LED Strip setup
strip = GroveWS2813RgbStrip(PIN, COUNT)

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

sensor_to_led_map = {
    0: 1,    # Sensor 0 → LED 1
    1: 5,    # Sensor 1 → LED 5
    2: 11,   # Sensor 2 → LED 11
    3: 15,   # Sensor 3 → LED 15
}

bme680_sensor = None # later initialized in sensor_init()

def normalize(value, min_val, max_val):
    return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))

# Define LED animation function
def colorWipe(strip, color, wait_ms=50):
    """Wipe color across display a pixel at a time."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms/1000.0)

# Reading sensor data and adjusting LED colors
def sensor_loop():
    while not stop_event.is_set():
        co2_readings.clear()
        tvoc_readings.clear()
        combined_scores.clear()

        # Read SGP30 sensor data
        for i, sensor in enumerate(sgp30_sensors):
            try:
                sensor.iaq_measure()  # Must call this every second

                co2 = sensor.eCO2
                tvoc = sensor.TVOC

                co2_readings.append(co2)
                tvoc_readings.append(tvoc)

                # Normalize (you can adjust these min/max bounds based on your expected range)
                norm_co2 = normalize(co2, 400, 60000)  # Normalizing CO2 from 400ppm to 60000ppm
                norm_tvoc = normalize(tvoc, 0, 60000)  # Normalizing TVOC from 0ppb to 60000ppb
                score = norm_co2 + norm_tvoc  # Simple combined score

                combined_scores.append(score)
            except Exception as e:
                print(f"Error reading SGP30_{i+1}: {e}")

                co2_readings.append(None)
                tvoc_readings.append(None)
                combined_scores.append(-1)  # Force it to be lowest

        # Now find which sensor has the highest readings for determining the direction of the smell
        # --- Only use outer 4 sensors (0 to 3) for scoring and LED ---
        outer_scores = combined_scores[:4]  # only use first 4 sensor scores

        # Find index of max score in outer sensors
        highest_index = outer_scores.index(max(outer_scores))
        print(f"Sensor with highest pollution (outer 4 only): SGP30_{highest_index + 1}")

        highlight_led = sensor_to_led_map.get(highest_index)

        # Turn off all LEDs
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, Color(0, 0, 0))
        strip.show()

        # Highlight LED if it's valid
        if highlight_led is not None:
            strip.setPixelColor(highlight_led, Color(255, 0, 0))  # red highlight
            strip.show()

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

        time.sleep(1) # Wait for 1 second before the next reading (this is the minimum required for SGP30)

def start_gui():
    global window
    window = tk.Tk()
    window.title("Directional eNose GUI")
    window.protocol("WM_DELETE_WINDOW", on_closing)
    window.attributes('-fullscreen', True)
    
    # GUI widgets
    window.label = tk.Label(
        text="==OneNose==",
        foreground="black",  # Set the text color
        background="white"  # Set the background color
    )
    window.label.pack()


    window.mainloop()  # Start the Tkinter main loop

def on_closing():
    print("Closing app...")
    stop_event.set()       # Stop sensor thread
    window.destroy()       # Close GUI

def sensor_init():
    global bme680_sensor
    # Sensor initialization
    # BME680 setup
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

    print('Initializing SGP30 sensors...')
    for sensor in sgp30_sensors:
        sensor.iaq_init()

    print ('Testing LED ring functionality with a color wipe animation.')
    colorWipe(strip, Color(255, 0, 0))  # Red wipe
    colorWipe(strip, Color(0, 255, 0))  # Blue wipe
    colorWipe(strip, Color(0, 0, 255))  # Green wipe

## MAIN == start ==

# Initialize sensors
sensor_init()

# Start the sensor loop in a separate thread
sensor_thread = threading.Thread(target=sensor_loop, daemon=True)
sensor_thread.start()

# Start the GUI (main thread)
start_gui()

# Wait for the sensor thread to finish after GUI closes
sensor_thread.join()
print("Sensor thread stopped. Exiting cleanly.")

## MAIN == end ==