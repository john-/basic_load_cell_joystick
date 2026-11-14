# Shopping List: `basic_load_cell_joystick`

This shopping contains most parts required to build the **Basic Load Cell Joystick**.

---

## 1. Electronics & Sensors

|   Qty    | Item Description                              | Primary Vendor / Link | Part # / Details                                                                                  | Purpose in Build                                                                                  |
| :------: | :-------------------------------------------- | :-------------------- | :------------------------------------------------------------------------------------------------ | :------------------------------------------------------------------------------------------------ |
|  **3**   | Straight-Bar Load Cell (10 kg, TAL220)        | SparkFun              | [SEN-13329](https://www.sparkfun.com/products/13329)                                              | 3-DOF force sensing triad (0 deg, 120 deg, 240 deg). 10 kg capacity, 1.0 mV/V, M4/M5 tapped ends. |
|  **2**   | ADS122C04 24-Bit 4-Channel ADC Breakout       | Adafruit              | [PID 6432](https://www.adafruit.com/product/6432)                                                 | 24-bit delta-sigma ADCs with programmable gain amplifier. I2C addresses `0x40` & `0x41`.          |
|  **1**   | SparkFun Pro Micro 3.3V / 8 MHz               | SparkFun              | [DEV-12587](https://www.sparkfun.com/products/12587)                                              | ATmega32U4 microcontroller with native USB HID game controller support.                           |
|  **1**   | Analog 2-Axis Thumb Joystick with Select      | Adafruit              | [PID 512](https://www.adafruit.com/product/512)                                                   | Miniature Alps thumb joystick module mounted behind thumb plate.                                  |
|  **1**   | SparkFun RJ45 Breakout Board                  | SparkFun              | [BOB-00716](https://www.sparkfun.com/products/716)                                                | Straight 1:1 8P8C break-out to 0.1" header pins.                                                  |
|  **1**   | RJ45 8-Pin PCB Socket (8P8C)                  | SparkFun              | [PRT-00643](https://www.sparkfun.com/products/643)                                                | Right-angle PCB socket soldered to BOB-00716.                                                     |
| **1 pk** | 36-Pin Swiss Machined Headers (Male + Female) | Adafruit              | [PID 3646](https://www.adafruit.com/product/3646) & [3647](https://www.adafruit.com/product/3647) | Low-profile round gold socket strips for mounting the Pro Micro on the SB300.                     |
|  **1**   | STEMMA QT / Qwiic JST SH 4-Pin Cable (50mm)   | Adafruit              | [PID 4399](https://www.adafruit.com/product/4399)                                                 | High-speed I2C bus interconnection between the two ADS122C04 breakouts.                           |

---

## 2. Wiring, Switches & Prototyping Board

|    Qty    | Item Description                                            | Primary Vendor / Link       | Part # / Details                         | Purpose in Build                                                                                |
| :-------: | :---------------------------------------------------------- | :-------------------------- | :--------------------------------------- | :---------------------------------------------------------------------------------------------- |
|   **1**   | BusBoard Systems SB300 Solderable Breadboard                | Amazon / BusBoard           | SB300 (30 cols x 12 rows)                | Prototyping carrier board holding Pro Micro, ADCs, RJ45 jack, and headers.                      |
|   **3**   | 8mm Waterproof Momentary Pushbuttons (Metal)                | Amazon (Gebildet)           | 8mm Mini Micro Push Button (Golden Foot) | 2x Thumb plate flank buttons + 1x Index finger trigger button. Fits 8.5mm holes.                |
| **1 kit** | PicoBlade 1.25mm Pre-Crimped Wire Harness Kit               | Amazon (Yoeruyo)            | MX1.25-MF (28AWG, 10 Colors)             | Quick-disconnect pigtails for modular thumb plate and trigger button replacement.               |
| **1 kit** | 2:1 Heat Shrink Tubing Kit (Assorted Colors)                | Amazon (Ginsco)             | 580 pcs Assorted Polyolefin              | Insulates pushbutton solder lugs and harness branch junctions.                                  |
|   **1**   | Standard RJ45 CAT5 / CAT6 Patch Cable (3-6 ft)              | Any supplier                | Cut one end off                          | 8-conductor trunk line routed through grip internal conduit. Intact plug connects to RJ45 jack. |
|   **3**   | 4-Pin Molex KK 254 (0.1" / 2.54mm) Keyed Headers & Housings | Electronic supplier / Molex | Molex KK 254 series                      | Plug-in sensor headers on SB300 for TAL220 load cell wires (`E+`, `E-`, `S+`, `S-`).            |
|   **3**   | 0.1 uF (100 nF) Ceramic MLCC Capacitors                     | Electronic supplier         | 50V radial ceramic MLCC                  | Decoupling capacitors placed across 3.3V and GND rails near ADCs and MCU.                       |
|   **1**   | 10 uF - 47 uF Electrolytic or Tantalum Capacitor            | Electronic supplier         | 6.3V-25V bulk capacitor                  | Bulk energy reservoir across 3.3V power rails on SB300.                                         |

---

## 3. Structural Hardware & Stock Material

|    Qty     | Item Description                                        | Primary Vendor / Link        | Part # / Details                                | Purpose in Build                                                                                                                  |
| :--------: | :------------------------------------------------------ | :--------------------------- | :---------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------- |
|   **1**    | 200 mm (7.87") Aluminum Disk Blank, 4.0 mm Thick        | Amazon (PATIKIL)             | 1060 Aluminum, Dia. 200mm x 4.0mm (1/6" / 9 Ga) | Fixed Base Plate (`frame_base_disk`).                                                                                             |
|   **1**    | 80 mm (3.15") Aluminum Disk Blank, 4.0 mm Thick         | Amazon (PATIKIL)             | 1060 Aluminum, Dia. 80mm x 4.0mm (1/6" / 9 Ga)  | Moving Top Plate (`frame_top_plate`).                                                                                             |
|  **1 pk**  | M8 x 100 mm Stainless Steel Threaded Rods + Nuts        | Amazon (LWCUSNJ)             | 304 Stainless Steel, M8-1.25 pitch              | Central structural spine through joystick grip stalk and top plate. **Cut down to 75-80 mm length.** Verify length before cutting |
| **10 pk**  | M5 Aluminum Spacers (5.2mm ID x 10mm OD x 10mm L)       | Amazon (PATIKIL)             | Plain finish round metal standoffs              | Load cell elevation standoffs above brackets and plates.                                                                          |
| **Varies** | 1" (25.4mm) Perforated Steel Square Tube Stock          | Home Depot (Everbilt)        | 1" x 1" x 36", 16-Ga. Zinc Punched Steel Tube   | Parallel load cell mounting brackets (`channel_square_7hole`). Holes pre-punched on 1" centers.                                   |
| **Varies** | 1" x 1" Aluminum Angle / L-Channel (1/16" or 1/8" Wall) | Home Depot (Everbilt)        | 1" x 1" x 36" Aluminum Angle                    | Optional base bracket mounting feet / stiffeners (`bracket_lchannel`).                                                            |
| **1 roll** | Standard Vinyl Electrical Tape                          | Hardware store / Shop supply | 3M Scotch Super 33+ or similar                  | Wrap 1-2 layers around M8 rod to provide snug, zero-slip friction fit inside grip stalk bore.                                     |

---

## 4. Fasteners & Screws (Consolidated Assortment Kits)

Instead of ordering individual screw packets, standard Amazon metric hardware kits cover all required sizes:

| Kit Description                                                             | Fasteners Used from Kit                                                                                                                                         | Purpose in Build                                                                                                                                                 |
| :-------------------------------------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **M3 Socket Head Screws Assortment Kit**<br>_(e.g., Fgruh 1120 pcs M3 kit)_ | • 2x **M3 x 25 mm** Countersunk Screws + Nuts<br>• 1x **M3 x 16 mm** SHCS + Nut<br>• 4x **M3 x 12 mm** SHCS + Nuts<br>• 4x **M3 x 8 mm** Pan/Button Head Screws | • Thumb plate mounting to grip neck<br>• Lower stalk clamping screw<br>• Grip base, swell, and neck clamping<br>• Adafruit #512 mini-joystick mounting to bosses |
| **M4 Socket Head Screws Assortment Kit**<br>_(e.g., Fgruh 480 pcs M4 kit)_  | • 6x **M4 x 16 mm** (or 20 mm) SHCS + Nuts & Washers                                                                                                            | • Bolting moving top plate to M4 load cell ends (2 screws per cell x 3 cells).                                                                                   |
| **M5 Socket Head Screws Assortment Kit**<br>_(e.g., Fgruh 272 pcs M5 kit)_  | • 6x **M5 x 25 mm** (or 30 mm) SHCS + Nuts & Washers<br>• 6x **M5 x 16 mm** SHCS + Nuts                                                                         | • Bolting TAL220 load cells and 10mm spacers to support brackets.<br>• Bolting support brackets to 200mm base plate.                                             |
| **M8 Hardware**<br>_(Included with M8 threaded rods kit)_                   | • 1x M8 Threaded Rod cut to 75-80 mm (verify length before cutting)<br>• 2x M8 Standard Hex Nuts<br>• 2x M8 Flat Washers                                        | • **Two-Nut Sandwich:** Clamps 4.0 mm aluminum top plate between upper and lower M8 nuts, forming a rigid perpendicular anchor.                                  |
| **Rig / Desk Mounting Fasteners**<br>_(Application-Specific)_               | • **Varies based on use case:** e.g. M5/M6 bolts, T-nuts for 2020/4040 aluminum profile, desk clamps, or wood screws                                            | • Mounting base disk / brackets to flight sim cockpit, desk mount, or enclosure. Recommended anchor points use the M5 load cell positions.                       |

---

## 5. 3D Printing Materials

| Item                              | Material             | Quantity | Recommendation                                                           |
| :-------------------------------- | :------------------- | :------: | :----------------------------------------------------------------------- |
| **Grip Halves (Half A & Half B)** | PLA, PETG, or PLA-CF |  ~150 g  | 4-5 wall loops, 30-40% infill for stiff clamping around M8 spine rod.    |
| **Thumb Plate (Mini-Joy)**        | PLA or PETG          |  ~25 g   | Print face-down with 100% solid walls for rigid button/joystick support. |
