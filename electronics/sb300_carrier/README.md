# Electronics Carrier: BusBoard Systems SB300 (As-Built Prototype)

This directory documents the physical carrier board currently fabricated and wired for the Phase 1 load-cell flight stick prototype.

## Hardware Summary
- **Base Board:** BusBoard Systems SB300 (solderable breadboard, 30 columns × 12 rows, 0.1" DIP pitch).
- **MCU Host:** SparkFun Pro Micro (3.3V / 8 MHz, ATmega32U4) in Swiss machined low-profile sockets.
- **ADC Converters:** 2× Adafruit #6432 (ADS122C04 24-bit ΔΣ ADCs), I2C addresses `0x40` and `0x41`.
- **Sensor Headers:** 4× Molex KK 254 4-pin keyed headers (3 populated for 120° triad + 1 spare for 90° rebuild).
- **Grip Interface:** SparkFun BOB-00716 RJ45 breakout with 8P8C jack.
- **Reset Interface:** 2-pin Molex KK 254 keyed header on Pro Micro `RST`/`GND`.

## Mandatory Track Cuts (SB300)
1. **RJ45 Ground Isolation (Rows 1-5, Columns 25-26):**
   Sever track between Row 2 and Row 4 on Cols 25 & 26 to isolate switch return grounds from I2C SCL/SDA lines. (Leave cols 19-24 intact for direct connection to Pro Micro D9-D4).
2. **Load Cell Analog Isolation (Rows 8-12, Columns 1-16):**
   Sever track between Row 9 and Row 10 on Cols 1-16 to isolate load cell header tie-points from ADC analog inputs.

*See [`docs/SPECIFICATION.md`](../../docs/SPECIFICATION.md#33-sb300-board-layout--component-placement) for the full micro coordinate placement matrix and jumper schedule.*
