# Custom Circular Carrier PCB (Phase 2 Roadmap)

This directory is reserved for the custom circular printed circuit board design replacing the Phase 1 SB300 solderable breadboard.

## Architectural Objectives
- **Form Factor:** Circular PCB sized to nest concentrically inside the load cell mounting pattern above or below the base plate.
- **Perimeter Sensor Interconnects:** 3× (or 4×) keyed Molex KK 254 (or JST-XH) 4-pin male headers located radially along the board edge, matching the angular positions of the load cells (0°, 120°, 240°).
- **Central Vertical Grip Header:** Vertical keyed multi-pin shrouded header located near the board center pointing upward for clean, strain-relieved routing of the grip switch and mini-joystick harness.
- **Onboard Microcontroller:** Surface-mount ATmega32U4 MCU (or RP2040 / SAMD21) soldered directly onto the PCB with native USB Type-C connector, ESD protection, and 3.3V LDO regulator.
- **Integrated ADC Circuits:** Dual ADS122C04 24-bit ADCs placed with dedicated analog ground planes and ratiometric reference routing.
- **Ambient Lighting:** Bottom-facing addressable RGB LED ring / underglow providing status indication and ground illumination.
