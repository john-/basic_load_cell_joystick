# Project Roadmap & Subsystem TODO List: `basic_load_cell_joystick`

This document tracks active development items, known mechanical considerations, and upcoming initiatives directly related to building the **Basic Load Cell Joystick**.

---

## 1. Mechanical Clamping & M8 Spine Assembly

### [ ] M8 Spine Rod Fit: Parametric Model Tightening vs. Vinyl Electrical Tape Shim

- **Background / Current Behavior:**
  - In commit `ef1eb8e` / `hw-v1.2-minijoy`, the grip stalk bore was updated to a continuous dia. 8.2 mm cylinder over 70 mm depth (`cad/grips/hybrid/generators/build_grip_hybrid.py`).
  - Standard M8 threaded rods have thread crest diameters that vary between ~7.75 mm and 7.95 mm depending on manufacturer and zinc/cadmium plating thickness.
  - On some 3D printers, this results in minor radial play inside the grip halves before the clamshell clamping screws are torqued down.
- **Workshop Resolution (As-Built):**
  - Wrap **1 to 2 layers of standard vinyl electrical tape** around the 55 mm - 60 mm portion of the M8 rod that inserts into the stalk bore. When the M3 clamping screws on the clamshell are torqued down, the plastic embeds into the tape, yielding a rock-solid, wobble-free lock with high torsional friction.
- **Potential Model Adjustment:**
  - If a tighter press/interference fit directly off the print bed is preferred without tape, edit `cad/grips/hybrid/generators/build_grip_hybrid.py`:
    ```python
    # Change:
    new_m8_bore = Part.makeCylinder(8.2 / 2.0, 75.0, App.Vector(0, 0, -45.0), App.Vector(0, 0, 1))
    # To:
    new_m8_bore = Part.makeCylinder(8.0 / 2.0, 75.0, App.Vector(0, 0, -45.0), App.Vector(0, 0, 1)) # or 7.9mm
    ```
  - Regenerate STLs and check fit with your specific 3D printer calibration and M8 rod stock.

### [ ] Top-Plate Inner M4 Screw Access Blocked by Grip Base

- **Issue:**
  - The inner set of M4 screws on the top plate (cell-to-plate, r = 19.5 mm, i.e. 39 mm diameter centerline circle) cannot be easily reached with a straight screwdriver while the grip is installed.
  - The grip's lower body flares to approx. r = 22.5 mm (45 mm diameter) right above the plate, overhanging the inner screw circle by approx. 3 mm.
- **Assembly Service Order Workaround:**
  1. Bolt the 3x TAL220 load cells to the 80 mm top plate using the 6x M4 screws and torque them down **before** attaching the grip.
  2. Bolt the M8 threaded rod into the center hole using the two-nut sandwich (lower M8 nut below plate, upper M8 nut above plate).
  3. Slide the grip clamshells onto the M8 rod and torque the M3 clamshell clamping screws.
- **Design Options to Address Vertical Access:**
  - **Option 1: Grip Driver-Access Scallops (Recommended):** Cut driver-access scallops or notches into the lower grip body skirt at 0 deg, 120 deg, and 240 deg. This preserves the existing cell geometry, moment arm radius (`r_ref = 27 mm`), and firmware scaling without widening the top plate.
  - **Option 2: Enlarge Top Plate Diameter / Cell Radius:** Shift the cell mounting positions radially outward so the inner M4 hole clears the grip skirt (inner radius `r1 > 23 mm`). _Tradeoff:_ Increasing the top plate diameter changes the cell moment arm leverage and requires recalibrating firmware scaling constants.
  - **Option 3: Slim Grip Lower Flare:** Taper or slim the grip lower stalk to stay at or below r = 17 mm over the bottom 25 mm above the plate.

### [ ] Mechanical Upgrade: Transition from Circular Aluminum Disks to Lobed 304 Stainless Steel Plates

- **Background:**
  - The initial _basic_ prototype employs simple circular aluminum blanks (diameter 200 mm base disk, diameter 80 mm top plate) paired with commercial aluminum L-channel brackets for ease of DIY sourcing, manual cutting, and manual drill working.
- **Pros of the Lobed Steel Approach:**
  - **Significantly Higher Rigidity & Zero Parasitic Flex:** 304 stainless steel has roughly triple the elastic modulus of aluminum (~193–200 GPa vs. ~69 GPa). Under aggressive stick inputs (up to 12 kg overload limit), the base ring remains effectively rigid so all displacement occurs across the TAL220 cantilever flexures rather than deflecting the plates.
  - **Eliminates Intermediate Brackets (Direct Mounting):** The TAL220 cells bolt directly to the 4.0 mm lobed base (M5 countersunk screws from below) and top plate arms (M4 countersunk screws from above), eliminating the aluminum L-brackets, hex standoffs, and multiple joint interfaces that introduce play or creep.
  - **Natural Desktop Ballast & Stability:** The dense steel base ring concentrates mass low on the desk, lowering the center of gravity and reducing the need for suction cups, clamps, or heavy secondary ballast bases.
  - **Open Load Paths & Wiring Clearance:** Trimming away unused circular disk material outside the 120° load paths opens unobstructed pass-through windows between the lobes for wire routing and visual inspection. _(Note: The inner M4 screws on the top plate remain at r = 19.5 mm under the grip flare, so screw driver access still requires either grip scallops or enlarging the top plate diameter as described above)._
- **Todo:**
  - Update mechanical specifications, screw length schedules, and assembly instructions when ready to cut or order steel parts.

---

## 2. Wiring & Electrical Serviceability

### [ ] Modular Button Harness & In-Cavity Quick-Disconnects

- **Current As-Built Setup:**
  - Fully documented in [`docs/wiring.md`](wiring.md), utilizing a 2-pin / 5-pin Molex PicoBlade 1.25mm harness topology.
  - Allows each panel-mount pushbutton to unplug and pass its rear retaining nut over the micro-connector without desoldering.

### [ ] Future Enhancement: Custom Base Carrier PCB (SB300 Replacement)

- **Background:**
  - The current hardware prototype uses a BusBoard Systems SB300 solderable breadboard with point-to-point jumpers and hand-cut traces to interconnect the Pro Micro MCU, dual ADS122C04 ADCs, load cell headers, and RJ45 breakout.
- **Goal:**
  - Design a dedicated 2-layer PCB to replace the SB300 carrier board.
  - Integrate clean SMD/through-hole footprints for MCU, ADCs, ratiometric reference filtering, bulk caps, RJ45 receptacle, and keyed Molex KK 254 load cell headers.

### [ ] Future Enhancement: Grip Head / Button Consolidation PCB

- **Background:**
  - Routing individual Molex PicoBlade pigtails and mini-joystick wires down the neck cavity is labor-intensive and crowded.
- **Goal:**
  - Design a small custom PCB for the upper grip cavity that directly mounts or headers the pushbuttons and mini-joystick potentiometer/switch.
  - Consolidate all grip signals into a single compact ribbon/header interface down to the base cable, drastically minimizing internal grip wiring.

### [ ] Pushbutton Ergonomics: Sourcing Better Grip Buttons

- **Background / Issue:**
  - The current panel-mount pushbuttons have hard metal outer bezels/edges and button actuator surfaces that are too recessed.
  - During extended use, this feels sharp and makes activation uncomfortable or inconsistent.
- **Todo:**
  - Research and source improved tactile panel-mount switches (e.g. domed, convex, soft-touch, or flush/raised actuator profiles with contoured/beveled bezels).
  - Check hole cutout dimensions and rear clearance against the grip clamshell and thumbplate CAD models.

---

## 3. Sensor Protection & Shrouds

### [ ] 3D Printed Protective Load Cell Shrouds

- **Background:**
  - The TAL220 load cells have exposed silicone encapsulation covering the delicate strain gauge bridge wiring.
  - While operating or handling the base, fingers or loose tools can press against the strain gauge silicone or snag the fine lead wires.
- **Todo:**
  - Design simple 3D-printable slip-on protective end-shrouds that snap or fasten over the cantilever beam without contacting the moving top plate or restricting cell deflection.

---

## 4. Firmware & Calibration Tuning

### [ ] Tare In-Progress and Completion LED Visual Signaling

- **Issue:**
  - When the user presses the buttons on the stick to tare, it is not clear what is happening.
- **Todo:**
  - Add LED flashing to acknowledge the start of the tare process (providing a clear signal to remove hands from the stick).
  - Indicate the end of the tare process with a confirmation LED signal.
