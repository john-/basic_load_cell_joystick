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
- **Potential Model Adjustment:**
  - Cut driver-access scallops or notches into the lower grip body skirt at 0 deg, 120 deg, and 240 deg so a hex driver can pass vertically without removing the grip.

---

## 2. Wiring & Electrical Serviceability

### [ ] Modular Button Harness & In-Cavity Quick-Disconnects

- **Current As-Built Setup:**
  - Fully documented in [`docs/wiring.md`](wiring.md), utilizing a 2-pin / 5-pin Molex PicoBlade 1.25mm harness topology.
  - Allows each panel-mount pushbutton to unplug and pass its rear retaining nut over the micro-connector without desoldering.
- **Todo / Enhancements:**
  - Verify wire bundle stowage clearance inside the upper neck cavity so wires and disconnects do not pinch when tightening clamshell screws.
  - Provide a dedicated strain-relief clip for the CAT5 cable exit loop above the top plate.

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

### [ ] User Feel Calibration Extent Tuning (`c` Command)

- **Background:**
  - The default full-scale deflection constants (`axis_scale = {144000, 144000, 54000}`) correspond to nominal ~400 g Pitch/Roll and ~500 g Z pull forces.
- **Todo:**
  - Connect via Serial monitor (115200 baud) and send the `c` command to run the interactive calibration wizard.
  - Push the stick to your natural physical comfort extents in Pitch, Roll, and Z to tune individual control feel and save the values directly to onboard EEPROM.
