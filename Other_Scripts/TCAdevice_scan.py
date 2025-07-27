# This example shows using two TCA9548A multiplexers to scan for connected devices
import board
import busio
import adafruit_tca9548a

# Create I2C bus as normal
i2c = busio.I2C(board.SCL, board.SDA)

# Create TCA9548A objects for both multiplexers at 0x70 and 0x71
tca_0 = adafruit_tca9548a.TCA9548A(i2c, address=0x70)
tca_1 = adafruit_tca9548a.TCA9548A(i2c, address=0x71)

# List of (multiplexer object, name) for easier looping
multiplexers = [
    (tca_0, "0x70"),
    (tca_1, "0x71"),
]

for tca, name in multiplexers:
    print(f"Scanning multiplexer at address {name}:")
    for channel in range(8):
        if tca[channel].try_lock():
            print(f"  Channel {channel}:", end=" ")
            addresses = tca[channel].scan()
            # Filter out multiplexer addresses to avoid listing itself
            filtered = [hex(addr) for addr in addresses if addr not in (0x70, 0x71)]
            print(filtered)
            tca[channel].unlock()
        else:
            print(f"  Channel {channel}: Could not lock I2C")
