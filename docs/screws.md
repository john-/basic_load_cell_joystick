# Fastener Specifications & BOM (`docs/screws.md`)

This document specifies the exact screw lengths, nut specifications, and clamped thicknesses for the Basic Load Cell Joystick. Fastener selections are optimized for standard **M3 Fastener Assortment Kits** containing:
**M3 x 6 mm, 8 mm, 10 mm, 12 mm, 16 mm, 20 mm, 25 mm, 30 mm**

Each screw length is chosen to guarantee **100% full thread engagement** through standard M3 nuts (or printed plastic standoffs) while providing the **minimum possible protrusion**, ensuring all screw tips sit safely recessed below exterior grip surfaces and clear of internal wiring.

---

## 1. Production Hybrid Grip (`cad/grips/hybrid/`)

### Summary BOM Table

| Fastener Location                | Qty | Optimal Kit Size            | Head Type          | Nut / Thread                    | Clamped Span | Thread Engagement  | Tip Protrusion Past Nut |    Safety Margin to Outer Skin    |
| :------------------------------- | :-: | :-------------------------- | :----------------- | :------------------------------ | :----------: | :----------------: | :---------------------: | :-------------------------------: |
| **Thumb Plate to Neck**          |  2  | **M3 x 25 mm**              | Flat / Countersunk | M3 Hex Nut                      |   21.9 mm    | 3.1 mm (Full 100%) |         +0.7 mm         |  **Recessed 1.4 mm** inside palm  |
| **Clamshell: Lower Stalk**       |  1  | **M3 x 16 mm**              | Socket / Pan Head  | M3 Hex Nut                      |   10.4 mm    | 2.4 mm (Full 100%) |         +3.2 mm         | **Recessed 4.3 mm** inside pocket |
| **Clamshell: Base, Swell, Neck** |  4  | **M3 x 12 mm** _(or 16 mm)_ | Socket / Pan Head  | M3 Hex Nut                      |    8.0 mm    | 2.4 mm (Full 100%) |         +1.6 mm         | **Recessed 5.8 mm** inside pocket |
| **Mini-Joystick PCB Standoffs**  |  4  | **M3 x 8 mm** _(or 6 mm)_   | Pan / Button Head  | Self-tap into dia. 2.6 mm pilot | 1.6 mm (PCB) |  6.4 mm (in boss)  |    N/A (blind hole)     | **3.1 mm margin** to pilot bottom |

> [!TIP]
> **Consolidated Kit Selection:**
> If you wish to minimize distinct lengths from your hardware kit, you can assemble the entire grip using just **three kit sizes**:
>
> 1. **M3 x 25 mm Countersunk** (Qty: 2) - Thumb Plate Mounting
> 2. **M3 x 16 mm Socket/Pan Head** (Qty: 5) - Clamshell Halves Clamping (fits all 5 clamp positions with zero outer protrusion)
> 3. **M3 x 8 mm Pan Head** (Qty: 4) - Mini-Joystick PCB Standoffs

---

## 2. Central M8 Spine Rod & Top Plate Sandwich

The central M8 threaded steel rod provides the primary mechanical connection between the moving top plate and the joystick grip.

### A. Cut-Down Length (100 mm -> 75 mm to 80 mm)

- **Raw Stock:** The standard rods supplied in hardware assortment kits (e.g. LWCUSNJ kit) are 100 mm long.
- **The Fit Issue:** The grip internal stalk bore is 70 mm deep (running from the grip base at Z = -40 mm up to the ceiling at Z = +30 mm). If a full 100 mm rod is used, the rod bottoms out against the ceiling of the internal bore before the grip can seat down onto the top plate mounting hardware.
- **Specification:** Cut the M8 threaded rod down with a metal hacksaw to **75 mm - 80 mm** total length (trimming off 20 mm - 25 mm). Chamfer or file the cut end to allow easy nut threading.

### B. M8 Two-Nut Sandwich Clamping Stack

The 4.0 mm aluminum top plate has a dia. 9.0 mm clearance through-hole (not tapped). The M8 rod is securely anchored by **sandwiching the plate between two M8 hex nuts**:

1. Thread the **lower M8 hex nut** (6.5 mm thickness) onto the bottom end of the rod, followed by an M8 flat washer.
2. Pass the rod upward through the dia. 9.0 mm hole in the 4.0 mm aluminum top plate.
3. Install an upper M8 flat washer and thread the **upper M8 hex nut** down onto the top surface of the plate.
4. Torque the upper and lower nuts firmly against one another. This locks the threaded rod rigidly perpendicular to the plate with zero wobble and zero reliance on weak aluminum threads.
5. The lower nut sits in the open central zone between the three 120-degree load cells (r < 14.5 mm), fully clear of all cell bodies.

### C. Grip Bore Fit: Electrical Tape Wrap vs. Parametric Model Adjustment

- **Thread Crest Play:** Standard M8 threaded rods vary in outer diameter (~7.75 mm to 7.95 mm across thread crests). In some 3D prints, the grip's dia. 8.2 mm continuous bore can feel slightly loose before the clamshell screws are torqued down.
- **Workshop Friction Shim (Recommended):** Wrap **1 to 2 layers of standard vinyl electrical tape** around the upper 55 mm - 60 mm portion of the rod that slides inside the grip stalk. When the clamshell halves are bolted together with the M3 screws, the plastic bites into the tape, providing a rock-solid, wobble-free lock with high torsional friction.
- **Parametric CAD Option:** Builders who prefer an interference fit directly off the print bed can edit `cad/grips/hybrid/generators/build_grip_hybrid.py` to tighten `new_m8_bore` from `8.2 / 2.0` down to `8.0 / 2.0` or `7.9 / 2.0`.

---

## 3. Base Mounting & Rig Integration Fasteners (Varies)

Physical mounting of the joystick base disk is **application-specific** and therefore called out as **"Varies"** in the bill of materials:

### A. Ideal Mounting Locations: M5 Load Cell Anchors

- The base disk features 3 pairs of M5 clearance/tapped holes at 0 deg, 120 deg, and 240 deg located at radii r = 74.5 mm and r = 89.5 mm (15 mm center-to-center hole pitch).
- **Recommended Practice:** Secure your mounting brackets or cockpit plate directly through or inline with these **M5 load cell anchor positions**.
- **Structural Advantage:** Because these points sit directly beneath the rigid 10 mm standoffs supporting the fixed ends of the load cells, grounding through these points directs all pitch/roll/yaw moment reactions straight into the mounting structure. This prevents bending or flexing of the 4.0 mm aluminum base plate, preserving absolute measurement linearity and maximum calibration fidelity.

### B. Hardware Options by Rig Type

- **Aluminum Profile Rigs (2020 / 4040 / 4080 Extrusion):** M5 or M6 Socket Head Cap Screws with roll-in or drop-in spring-ball T-nuts sized for the profile slot (e.g. 6 mm or 8 mm slot).
- **Flat Cockpit / Desk Mounting Plates:** M5 SHCS bolts passing through the base disk and bracket flanges with nylon-insert locknuts (Nyloc) or threaded into drilled/tapped mounting plates.
- **Support Brackets Stock:** Off-the-shelf 1" perforated 16-gauge steel square tube and 1" x 1" aluminum angle (sourced from Home Depot) provide pre-aligned 1" hole spacing for versatile bolting.

---

## 4. Detailed Engineering Breakdown

### A. Thumb Plate Mounting Screws (`thumbplate_minijoy`)

- **Screws:** 2 x **M3 x 25 mm Flat-Head (Countersunk)** through flange (X = +/- 8.0 mm, Y = -5.5 mm).
- **Nuts:** 2 x standard M3 hex nuts (5.5 mm across flats, 2.4 mm thick) seated in rear captive nut pockets on exterior palm swell.
- **Clearance Holes:** dia. 3.4 mm.
- **Geometry & Fit:**
  - The countersunk head sits flush with the front face of the thumb plate (Z_local = 3.0 mm).
  - Grip travel from countersunk seat to rear nut seating face: **21.9 mm**.
  - Total travel through the 2.4 mm nut: **24.3 mm**.
  - M3 x 25 mm provides **3.1 mm of thread engagement** (0.7 mm tip protrusion past the nut).
  - The rear exterior palm skin is located at 26.4 mm along the screw axis; the screw tip sits safely **recessed >= 1.4 mm below the outer palm skin**, completely eliminating contact or irritation to the palm.

### B. Clamshell Shaft Clamping Screws

- **Screws:** 5 x **M3 x 12 mm to 16 mm Socket Head Cap Screws (SHCS) or Pan Head Screws**.
  - Half A provides dia. 6.2 mm counterbores (seats at X = +x_s).
  - Half B provides 5.7 mm regular hexagon captive nut pockets (seats at X = -x_s).
- **Nuts:** 5 x standard M3 hex nuts (5.5 mm across flats, 2.4 mm thick).
- **Clearance Holes:** dia. 3.4 mm (drilled along X axis).
- **Locations & Minimum Protrusion Selection:**
  1. **Base Clamp:** (Y = 11.0 mm, Z = -30.0 mm) - Clamped plastic: 8.0 mm. M3 x 12 mm protrudes 1.6 mm past nut (8.2 mm recessed inside pocket).
  2. **Lower Stalk Clamp:** (Y = 16.5 mm, Z = -8.0 mm) - Clamped plastic: 10.4 mm (widened for 0.8 mm solid wall to cable conduit). **Requires M3 x 16 mm** for 100% thread engagement (3.2 mm past nut, recessed 4.3 mm inside pocket).
  3. **Palm Swell Upper-Mid:** (Y = 11.0 mm, Z = 40.0 mm) - Clamped plastic: 8.0 mm. M3 x 12 mm protrudes 1.6 mm past nut (11.4 mm recessed inside pocket).
  4. **Upper Neck Clamp (Back):** (Y = 11.0 mm, Z = 95.0 mm) - Clamped plastic: 8.0 mm. M3 x 12 mm protrudes 1.6 mm past nut (9.2 mm recessed inside pocket).
  5. **Upper Neck Clamp (Front):** (Y = -11.0 mm, Z = 95.0 mm) - Clamped plastic: 8.0 mm. M3 x 12 mm protrudes 1.6 mm past nut (9.2 mm recessed inside pocket).

### C. Mini-Joystick Module (`thumbplate_minijoy`)

- **Screws:** 4 x **M3 x 8 mm (or M3 x 6 mm)** Pan Head / Button Head Screws.
- **Mounting:** Threaded directly into dia. 2.6 mm printed pilot holes in rear standoff bosses (dia. 6.5 mm x 12.0 mm height) to secure the Adafruit #512 PCB.
- **Engagement & Clearance:**
  - PCB thickness: 1.6 mm.
  - Boss pilot hole depth: **9.5 mm**.
  - **M3 x 8 mm:** Thread penetration into standoff is **6.4 mm** (~12.8 threads engaged in plastic), leaving **3.1 mm safety margin** before the pilot hole floor.
  - **M3 x 6 mm:** Thread penetration is **4.4 mm** (5.1 mm safety margin).
