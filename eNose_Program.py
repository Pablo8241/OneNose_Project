import os
import sys
import subprocess
import time
import adafruit_sgp30
import bme680
import board
import adafruit_tca9548a
import tkinter as tk
import threading
import RPi.GPIO as GPIO # For GPIO control
from PIL import Image, ImageTk # For GUI image handling
from grove.i2c import Bus # For Grove I2C communication
from rpi_ws281x import PixelStrip, Color # For WS2813 RGB LED Strip control
from grove_ws2813_rgb_led_strip import GroveWS2813RgbStrip # For Grove WS2813 RGB LED Strip control
from edge_impulse_linux.runner import ImpulseRunner # Imports Edge Impulse's C++ model runner (runs the .eim model file)

from enose_functions import normalize, colorWipe # Import utility functions (moved them to make the code cleaner)

# Define a bias to rotate LED direction to match sensor layout
PIN   = 12  # connect Grove WS2813 RGB LED Strip SIG to pin 12(slot PWM)
COUNT = 20  # For Grove - WS2813 RGB LED Ring - 20 LED total

args = sys.argv[1:] # a list that contains the command-line arguments passed to the script (e.g. model.eim)

stop_event = threading.Event() # thread-safe flag

shutdown = False  # Global shutdown flag

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

bme680_sensor = None # later initialized in program_init()

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
        print(f"Sensor with highest readings (outer 4 only): SGP30_{highest_index + 1}")

        label3.after(0, lambda: label3.config(
            text=f"Highest: SGP30_{highest_index + 1}",
            foreground="red"
        ))

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

        # Read BME680 sensor data and collect features
        features = []  # List to store all sensor readings as floats
        
        if bme680_sensor.get_sensor_data():
            # Add BME680 readings to features list
            features.append(float(bme680_sensor.data.temperature))
            features.append(float(bme680_sensor.data.pressure))
            features.append(float(bme680_sensor.data.humidity))
            
            if bme680_sensor.data.heat_stable:
                features.append(float(bme680_sensor.data.gas_resistance))
                output = '{0:.2f} C,{1:.2f} hPa,{2:.2f} %RH'.format(
                    bme680_sensor.data.temperature,
                    bme680_sensor.data.pressure,
                    bme680_sensor.data.humidity)
                print('{0},{1} Ohms'.format(
                    output,
                    bme680_sensor.data.gas_resistance))
            else:
                features.append(0.0)  # Add 0.0 if gas reading not stable
                output = '{0:.2f} C,{1:.2f} hPa,{2:.2f} %RH'.format(
                    bme680_sensor.data.temperature,
                    bme680_sensor.data.pressure,
                    bme680_sensor.data.humidity)
                print(output)
        else:
            # Add zeros if BME680 reading fails
            features.extend([0.0, 0.0, 0.0, 0.0])
        
        # Add SGP30 sensor readings (indexes 4-9) to features list
        for i in range(4, 10):  # SGP30_5 to SGP30_10 (indexes 4-9)
            if i < len(co2_readings) and co2_readings[i] is not None and tvoc_readings[i] is not None:
                features.append(float(co2_readings[i]))
                features.append(float(tvoc_readings[i]))
            else:
                # Add zeros if sensor reading fails
                features.extend([0.0, 0.0])
        
        # Print features array for debugging
        print(f"Features array: {features}")
        print(f"Features count: {len(features)}")


        if runner is not None:
            try:
                res = runner.classify(features)
                print("Raw model output:", res)

                if 'result' in res and 'classification' in res['result']:
                    classifications = res['result']['classification']
                    top_class = max(classifications, key=classifications.get)
                    label4.after(0, lambda: label4.config(
                        text=f"Smell: {top_class}",
                        foreground="black"
                    ))
                else:
                    label4.after(0, lambda: label4.config(
                        text="Invalid model output.",
                        foreground="red"
                    ))
            except Exception as e:
                print(f"Classification error: {e}")
                label4.after(0, lambda: label4.config(
                    text="Classification failed.",
                    foreground="red"
                ))
        else:
            label4.after(0, lambda: label4.config(
                text="No model loaded.",
                foreground="gray"
            ))

        time.sleep(1) # Wait for 1 second before the next reading (this is the minimum required for SGP30)

def start_gui():
    global window
    window = tk.Tk()
    window.title("Directional eNose GUI")
    window.protocol("WM_DELETE_WINDOW", on_closing) # Handle window close event
    window.attributes('-fullscreen', True) # Fullscreen mode
    window.config(cursor="none") # Hide mouse cursor

    # Get screen width and height
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    # Resize image to fit screen
    bg_image = Image.open("Assets/background.jpg")
    bg_image = bg_image.resize((screen_width, screen_height), Image.LANCZOS)
    bg_photo = ImageTk.PhotoImage(bg_image)

    # Place the image as a Label behind everything
    bg_label = tk.Label(window, image=bg_photo)
    bg_label.place(x=0, y=0, relwidth=1, relheight=1)

    # GUI widgets
    # Create a label at the top center of the window
    window.label = tk.Label(
        window,
        text="OneNose",           # The text to display
        foreground="black",           # Text color
        background="#216dd8",           # Background color (matches window background)
        font=("Helvetica", 60, "bold"), # Font family, size, and style
        anchor="n",                   # Anchor text to the top center ('n' = north)
        justify="center"              # Center the text horizontally
    )
    window.label.pack(pady=(2))  # Add some padding below the first label

    # Create a second label below the first one
    window.label2 = tk.Label(
        window,
        text="Directional Electronic Nose", 
        foreground="black",                       
        background="#216dd8",                   
        font=("Helvetica", 35),               
        justify="center"                       
    )
    window.label2.pack(pady=(0, 4))  # Move expand=True to the second label -- pady(characters above, characters below)

    # Create a third label below the second one (this one will display the sensor with the highest readings)
    global label3
    
    label3 = tk.Label(
        window,
        text="Awaiting sensor data...",  # Initial text
        foreground="yellow",                      
        background="#216dd8",                      
        font=("Helvetica", 35),                 
        justify="center"                         
    )
    label3.pack(pady=(30, 0))  # Move expand=True to the second label

    # Create a fourth label below the third (this one will display the detected smell)
    global label4

    label4 = tk.Label(
        window,
        text="Bind smell to this label",
        foreground="gray",                      
        background="#216dd8",                      
        font=("Helvetica", 35, "bold"),       
        justify="center"                         
    )
    label4.pack(pady=(2, 0))  # Move expand=True to the second label

    window.mainloop()  # Start the Tkinter main loop

def on_closing():
    print("Closing app...")

    stop_event.set()       # Stop sensor thread

    # Small shutdown animation
    colorWipe(strip, Color(255, 0, 0))  # Red wipe
    # Turn off all LEDs
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

    window.destroy()       # Close GUI

def program_init():
    global bme680_sensor
    global runner

    GPIO.cleanup()
    
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

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Shutdown trigger
    GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Button action unassigned
    button_thread = threading.Thread(target=button_polling_loop, daemon=True)
    button_thread.start()

    if len(args) != 1:
        print("No model file provided. Running without Edge Impulse model.")
        runner = None
    else:
        model = args[0]
        dir_path = os.path.dirname(os.path.realpath(__file__))
        modelfile = os.path.join(dir_path, model)

        try:
            runner = ImpulseRunner(modelfile)
            model_info = runner.init()
            print("Model info:")
            print(model_info['project']['owner'] + '/' + model_info['project']['name'])
            print(model_info['model_parameters']['input_features_count'], "features expected")
        except Exception as e:
            print(f"Error loading model: {e}")
            runner = None

    print ('Testing LED ring functionality with a color wipe animation.')
    colorWipe(strip, Color(0, 255, 0))  # Green wipe

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
            window.after(1, on_closing)

        if prev_state_17 == GPIO.HIGH and curr_state_17 == GPIO.LOW:
            print("GPIO 17 pressed – button action unassigned.")

        prev_state_27 = curr_state_27
        prev_state_17 = curr_state_17

        time.sleep(0.05)  # 50ms polling delay

## MAIN == start ==
# Initialize sensors
program_init()

# Start the sensor loop in a separate thread
sensor_thread = threading.Thread(target=sensor_loop, daemon=True)
sensor_thread.start()

# Start the GUI (main thread)
start_gui()

# Wait for the sensor thread to finish after GUI closes
sensor_thread.join(timeout=3)  # Wait for up to 3 seconds for the thread to finish, if it doesn't, just go on

if sensor_thread.is_alive():
    print("Sensor thread didn't exit in time. Forcing exit.")
else:
    print("Sensor thread stopped. Exiting cleanly.")

if shutdown:
    print("Shutdown flag is set. Closing app and shutting down...")
    label3.after(0, lambda: label3.config(
            text=f"Closing app and shutting down...",
            foreground="red"
        ))
    time.sleep(1)  # Delay before shutdown
    subprocess.run(["sudo", "shutdown", "now"])
else:
    label3.after(0, lambda: label3.config(
            text=f"Closing app without shutdown...",
            foreground="red"
        ))
    print("Shutdown not triggered - on_closing() called, closing app without shutdown.")

## MAIN == end ==