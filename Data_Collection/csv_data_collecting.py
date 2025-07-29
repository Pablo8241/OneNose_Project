import os
import time
import csv
import board
import sys
import threading
from datetime import datetime
import adafruit_tca9548a
import adafruit_sgp30
import bme680

# Make sure to navigate to the correct environment with all needed packages installed.
# run script with "/home/pablo/appenv/bin/python /home/pablo/OneNose_Project/Data_Collection/csv_datacollecting.py"

# Global stop flag
stop_requested = False

def input_listener():
    global stop_requested
    while True:
        user_input = input()
        if user_input.strip().lower() == 'stop':
            print("[INFO] Stop requested. Finishing current file...")
            stop_requested = True
            break

# Start background thread to watch for 'stop'
threading.Thread(target=input_listener, daemon=True).start()

# ----------------------------
# Sensor Initialization
# ----------------------------
print("Initializing I2C and multiplexers...")
i2c = board.I2C()
mux1 = adafruit_tca9548a.TCA9548A(i2c, address=0x70)
mux2 = adafruit_tca9548a.TCA9548A(i2c, address=0x71)

print("Initializing SGP30 sensors...")
sgp30_sensors = [
    adafruit_sgp30.Adafruit_SGP30(mux1[0]),  # Index 0 = SGP30_1
    adafruit_sgp30.Adafruit_SGP30(mux1[1]),
    adafruit_sgp30.Adafruit_SGP30(mux1[2]),
    adafruit_sgp30.Adafruit_SGP30(mux1[3]),
    adafruit_sgp30.Adafruit_SGP30(mux1[4]),
    adafruit_sgp30.Adafruit_SGP30(mux1[5]),
    adafruit_sgp30.Adafruit_SGP30(mux1[6]),
    adafruit_sgp30.Adafruit_SGP30(mux1[7]),
    adafruit_sgp30.Adafruit_SGP30(mux2[0]),
    adafruit_sgp30.Adafruit_SGP30(mux2[1]),
]

# Only use SGP30 sensors 5 to 10 (index 4 to 9)
used_sgp_sensors = sgp30_sensors[4:10]
for sensor in used_sgp_sensors:
    sensor.iaq_init()

print("Initializing BME680...")
# BME680 setup
try:
    bme680_sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
except (RuntimeError, IOError):
    bme680_sensor = bme680.BME680(bme680.I2C_ADDR_SECONDARY)

bme680_sensor.set_humidity_oversample(bme680.OS_2X)
bme680_sensor.set_pressure_oversample(bme680.OS_4X)
bme680_sensor.set_temperature_oversample(bme680.OS_8X)
bme680_sensor.set_filter(bme680.FILTER_SIZE_3)
bme680_sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)
bme680_sensor.set_gas_heater_temperature(320)
bme680_sensor.set_gas_heater_duration(150)
bme680_sensor.select_gas_heater_profile(0)

# ----------------------------
# Ask user for label interactively
# ----------------------------
label = input("Enter label: ").strip()
if not label:
    print("Label cannot be empty.")
    sys.exit(1)

# ----------------------------
# CSV header
# ----------------------------
script_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(script_dir, "Data")
os.makedirs(data_dir, exist_ok=True)

headers = ['timestamp', 'BME680_temp', 'BME680_pressure', 'BME680_humidity', 'BME680_gas']
for i in range(5, 11):
    headers.append(f'SGP30_{i}_CO2')
    headers.append(f'SGP30_{i}_TVOC')

# ----------------------------
# Main Loop
# ----------------------------
print("[INFO] Starting data collection. Type 'stop' and press Enter to stop after current file.")

try:
    while not stop_requested:
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(data_dir, f"{label}_{timestamp_str}.csv")
        with open(filename, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)

            file_start_time = time.time() # Track file start time
            for _ in range(10):
                loop_start = time.time()
                elapsed_ms = round((loop_start - file_start_time) * 1000)
                row = [elapsed_ms]

                # BME680
                if bme680_sensor.get_sensor_data():
                    temp = round(bme680_sensor.data.temperature, 2)
                    press = round(bme680_sensor.data.pressure, 2)
                    hum = round(bme680_sensor.data.humidity, 2)
                    gas = round(bme680_sensor.data.gas_resistance, 2) if bme680_sensor.data.heat_stable else None
                else:
                    temp = press = hum = gas = None

                row += [temp, press, hum, gas]

                # SGP30 sensors 5 to 10
                for sensor in used_sgp_sensors:
                    try:
                        sensor.iaq_measure()
                        row += [sensor.eCO2, sensor.TVOC]
                    except Exception:
                        row += [None, None]

                writer.writerow(row)

                elapsed = time.time() - loop_start
                if elapsed < 1.0:
                    time.sleep(1.0 - elapsed)

except KeyboardInterrupt:
    print("\n[INFO] Ctrl+C detected. Finishing current file and exiting...")

print("[INFO] Data collection stopped.")
