# Directional_eNose

## Description

The Directional eNose is an electronic nose system designed to detect and identify the direction of odors and chemical substances in the environment. The system uses multiple SGP30 air quality sensors arranged in a circular pattern to detect CO2 and TVOC (Total Volatile Organic Compounds) concentrations from different directions. It has the functionality of being able to detect where a smell is coming from and display the direction using an LED ring as indicator. In addition to that it has a BME680 and 6 functionalised gas sensors used for detecting the type of odor.

The main program (`eNose_Program.py`) continuously monitors all sensors and environmental conditions, providing real-time data on air quality measurements and environmental parameters. In addition to directional detection, the program can identify specific smells using a machine learning model generated with Edge Impulse. By loading a `.eim` model file, the system classifies odors in real time based on sensor data and displays the detected smell on the GUI. The program also features a graphical interface for live feedback and supports safe shutdown and control via the hardware buttons on the display.

## Hardware Components

- **10x SGP30 Air Quality Sensors** - CO2 and TVOC detection
- **1x BME680 Environmental Sensor** - Temperature, humidity, pressure, and gas resistance
- **2x TCA9548A I2C Multiplexers** - Managing multiple sensors with same I2C address
- **1x WS2813 RGB LED Ring (20 LEDs)** - Directional indication display
- **Raspberry Pi with Grove Base Hat** - Main processing unit
- **Adafruit PiTFT Plus 320x240 2.8" TFT** - Display for the GUI + 2 buttons

## Device I2C Addresses

| Device | Address | Notes |
|--------|---------|-------|
| SGP30 | 0x58 | All sensors (managed via multiplexers) |
| BME680 | 0x76 | Default address |
| TCA9548A | 0x70 | Primary multiplexer |
| TCA9548A | 0x71 | Secondary multiplexer (A0 shorted) |

## Hardware Setup Instructions

1. **Initial Positioning**: First make sure the top cover is positioned in such way that the BME680 port points towards you. Do not screw the top cover in place yet.

2. **Outer SGP30 Sensors**: Connect the 4 outer SGP30 sensors starting from bottom left, going clockwise to IC0-IC3 of the MUX with a default address 0x70.

3. **Inner SGP30 Sensors**: Connect the inner 6 SGP30 sensors starting from bottom left, going clockwise to IC4-IC7 on the MUX with the default address and the rest to IC0-IC1 on the MUX with address 0x71 respectively.

4. **BME680 and LED Ring**: Connect the BME680 to any open I2C port on the eNose. Connect the RGB ring GND to any ground pin on the base hat Raspberry Pi extension board, power to the 5V power supply pin and the SIG pin to GPIO 12 (pin 32 on the Raspberry Pi header).

5. **Display**: The display uses the hardware SPI pins (SCK, MOSI, MISO, CE0, CE1) as well as GPIO
#25 and #24. GPIO #17 and #27 are used for two of the 4 buttons on the display, one of which serves as a button to turn off the Raspberry Pi. All pins can be connected using female-to-female jumper cables from the display directly to the pins of the base hat apart from the power input, which is taken directly from the 5V power supply.

6. **Final Assembly**: You can now screw the top cover in place.

## Data Collection Setup

### CSV Data Collection Order

The `csv_data_collecting.py` script collects sensor data in the following specific order:

**BME680 Environmental Data (4 readings):**
1. Temperature (°C)
2. Pressure (hPa)  
3. Humidity (%RH)
4. Gas Resistance (Ohms)

**SGP30 Gas Sensor Data (12 readings from sensors 5-10):**
5. SGP30_5_CO2 (ppm)
6. SGP30_5_TVOC (ppb)
7. SGP30_6_CO2 (ppm)
8. SGP30_6_TVOC (ppb)
9. SGP30_7_CO2 (ppm)
10. SGP30_7_TVOC (ppb)
11. SGP30_8_CO2 (ppm)
12. SGP30_8_TVOC (ppb)
13. SGP30_9_CO2 (ppm)
14. SGP30_9_TVOC (ppb)
15. SGP30_10_CO2 (ppm)
16. SGP30_10_TVOC (ppb)

This order ensures consistent data formatting for machine learning model training and inference.

## Machine Learning Model Deployment

### Deploying Edge Impulse Model

To deploy your trained machine learning model from Edge Impulse:

1. **Select Deployment Target**: 
   - Go to **Deployment** options in your Edge Impulse project
   - Choose **"Linux (ARMv7)"** as the deployment target
   - Ensure the target device is set to **Raspberry Pi 4**

2. **Build and Download**:
   - Click **Build** to generate the model
   - Download the generated `.eim` file

3. **Install Model**:
   - Place the downloaded `.eim` file in the same directory as `eNose_Program.py`
   - The program will automatically load and use the model for real-time odor classification

