import os
import time
import csv
import board
import adafruit_tca9548a
import adafruit_sgp30
import bme680

# Create I2C bus and multiplexers
i2c = board.I2C()
mux1 = adafruit_tca9548a.TCA9548A(i2c, address=0x70)
mux2 = adafruit_tca9548a.TCA9548A(i2c, address=0x71)

# Initialize SGP30 sensors on each mux channel
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

# Initialize each SGP30 sensor
for sensor in sgp30_sensors:
    sensor.iaq_init()

# Initialize BME680
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

# CSV setup
os.makedirs("Data", exist_ok=True)
csv_file = os.path.join("Data", "sensor_readings.csv")

headers = ['timestamp', 'BME680_temp', 'BME680_pressure', 'BME680_humidity', 'BME680_gas']
for i in range(1, 11):
    headers.append(f'SGP30_{i}_CO2')
    headers.append(f'SGP30_{i}_TVOC')

# Write headers once
if not os.path.exists(csv_file):
    with open(csv_file, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)

# Main loop
try:
    while True:
        row = [time.strftime('%Y-%m-%d %H:%M:%S')]

        # BME680 data
        if bme680_sensor.get_sensor_data():
            temp = round(bme680_sensor.data.temperature, 2)
            press = round(bme680_sensor.data.pressure, 2)
            hum = round(bme680_sensor.data.humidity, 2)
            gas = round(bme680_sensor.data.gas_resistance, 2) if bme680_sensor.data.heat_stable else None
        else:
            temp = press = hum = gas = None

        row += [temp, press, hum, gas]

        # SGP30 data
        for sensor in sgp30_sensors:
            try:
                sensor.iaq_measure()
                row += [sensor.eCO2, sensor.TVOC]
            except Exception:
                row += [None, None]

        # Append to CSV
        with open(csv_file, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row)

        time.sleep(1)  # 1 reading per second

except KeyboardInterrupt:
    print("Stopped by user.")
