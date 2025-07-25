# Directional_eNose

## Description

The Directional eNose is an electronic nose system designed to detect and identify the direction of odors and chemical substances in the environment. The system uses multiple SGP30 air quality sensors arranged in a circular pattern to detect CO2 and TVOC (Total Volatile Organic Compounds) concentrations from different directions. It has the functionality of being able to detect where a smell is coming from and display the direction using an LED ring as indicator. In addition to that it has a BME680 and 6 functionalised gas sensors used for detecting the type of odor.

The main program (`eNose_Program.py`) continuously monitors all sensors and environmental conditions, providing real-time data on air quality measurements and environmental parameters.

## Hardware Components

- **10x SGP30 Air Quality Sensors** - CO2 and TVOC detection
- **1x BME680 Environmental Sensor** - Temperature, humidity, pressure, and gas resistance
- **2x TCA9548A I2C Multiplexers** - Managing multiple sensors with same I2C address
- **1x WS2813 RGB LED Ring (20 LEDs)** - Directional indication display
- **Raspberry Pi with Grove Base Hat** - Main processing unit
- **Adafruit PiTFT Plus 320x240 2.8" TFT** - Display for the GUI

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
#25 and #24. GPIO #17 and #27 are used for two of the 4 buttons on the display and serve as buttons to turn off the Raspberry Pi or close the GUI. All pins are connected using female-to-female jumper cables from the display directly to the pins of the base hat.

5. **Final Assembly**: You can now screw the top cover in place.