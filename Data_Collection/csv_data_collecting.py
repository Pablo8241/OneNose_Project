import os
import time
import csv
import sys
import board
import adafruit_tca9548a
import adafruit_sgp30
import bme680
from datetime import datetime

# Navigate to directory with this script
# run with "python csv_data_collecting.py label"

# ------------------------------
# 🏷️ Command-line label argument
# ------------------------------
if len(sys.argv) != 2:
    print("Usage: python script.py <label>")
    sys.exit(1)

label = sys.argv[1]

# ------------------------------
# 🔌 I2C and sensor initialization
# ------------------------------
i2c = board.I2C()
mux1 = adafruit_tca9548a.TCA9548A(i2c, address=0x70)
mux2 = adafruit_tca9548a.TCA9548A(i2c, address=0x71)

# SGP30 sensor list — sensors 1 to 10
sgp30_sensors = [
    adafruit_sgp30.Adafruit_SGP30(mux1[0]),  # Index 0 = SGP30_1
    adafruit_sgp30.Adafruit_SGP30(mux1[1]),  # Index 1 = SGP30_2
    adafruit_sgp30.Adafruit_SGP30(mux1[2]),
    adafruit_sgp30.Adafruit_SGP30(mux1[3]),
    adafruit_sgp30.Adafruit_SGP30(mux1[4]),  # Index 4 = SGP30_5
    adafruit_sgp30.Adafruit_SGP30(mux1[5]),
    adafruit_sgp30.Adafruit_SGP30(mux1[6]),
    adafruit_sgp30.Adafruit_SGP30(mux1[7]),
    adafruit_sgp30.Adafruit_SGP30(mux2[0]),
    adafruit_sgp30.Adafruit_SGP30(mux2[1])   # Index 9 = SGP30_10
]

# Only use sensors 5 to 10 → indexes 4 to 9
used_sgp_sensors = sgp30_sensors[4:10]  # Python slice includes start, excludes end (i.e., 4 to 9)

for sensor in used_sgp_sensors:
    sensor.iaq_init()

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

# ------------------------------
# 📁 CSV Header Setup
# ------------------------------
os.makedirs("Data", exist_ok=True)

headers = ['timestamp', 'BME680_temp', 'BME680_pressure', 'BME680_humidity', 'BME680_gas']
for i in range(5, 11):  # Sensors 5 to 10 (inclusive)
    headers.append(f'SGP30_{i}_CO2')
    headers.append(f'SGP30_{i}_TVOC')

# ------------------------------
# ⏱️ Main Data Collection Loop
# ------------------------------
print("Starting data collection... Press Ctrl+C to stop.")

try:
    while True:
        # Start time of 10-second block
        block_start = time.time()

        # Generate new CSV filename every 10 seconds
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Data/{label}_{timestamp_str}.csv"

        with open(filename, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)

            # Loop to collect 10 readings, one per second
            for _ in range(10):
                current_time = time.strftime('%Y-%m-%d %H:%M:%S')
                row = [current_time]

                # BME680 data
                if bme680_sensor.get_sensor_data():
                    temp = round(bme680_sensor.data.temperature, 2)
                    press = round(bme680_sensor.data.pressure, 2)
                    hum = round(bme680_sensor.data.humidity, 2)
                    gas = round(bme680_sensor.data.gas_resistance, 2) if bme680_sensor.data.heat_stable else None
                else:
                    temp = press = hum = gas = None

                row += [temp, press, hum, gas]

                # SGP30 readings (sensors 5 to 10)
                for sensor in used_sgp_sensors:
                    try:
                        sensor.iaq_measure()
                        row += [sensor.eCO2, sensor.TVOC]
                    except Exception:
                        row += [None, None]

                writer.writerow(row)
                time.sleep(1)  # Wait 1 second

except KeyboardInterrupt:
    print("\nInterrupted. Finishing current 10-second block before exiting.")
    # No action needed — current file finishes in inner loop
    pass

print("Data collection stopped.")
