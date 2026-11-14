# 3D Print Run Manifest: Hybrid Grip & Mini-Joystick Plate (v1.2)

- **Date Sent to Manufacturing:** 2026-11-08
- **Git Milestone Tag:** [`hw-v1.2-minijoy-printed`](https://git)
- **Status:** Submitted to 3D Printing / In Fabrication

---

## Included Models

| File | Triangles | Size (Binary) | Description |
| :--- | :--- | :--- | :--- |
| `thumbplate_minijoy.stl` | 21,066 | 1.00 MB | Mini-joystick plate with controls shifted -6mm, dia. 8.5mm button holes, dia. 27.0mm aperture with 1.5mm x 45 deg conical chamfer, and smooth concave flange arcs. |
| `grip_hybrid_body_half_a.stl` | 100,963 | 4.81 MB | Right clamshell half (+X flank) with snug dia. 8.2mm continuous M8 rod bore (exact 70.0mm depth, Z = -40mm to +30mm), flush base (zero lip), eliminated epoxy port, relocated Switch 1 (dia. 8.5mm through-hole + dia. 12.2mm spotface), and captive M3 nut pocket. |
| `grip_hybrid_body_half_b.stl` | 83,877 | 4.00 MB | Left clamshell half (-X flank) with matching snug dia. 8.2mm continuous M8 rod bore (exact 70.0mm depth), flush base, eliminated epoxy port, captive M3 nut pocket, and cable routing conduit. |
| `v1.2_complete.stl` | 205,906 | 9.82 MB | Consolidated single-plate print bed layout containing all 3 components oriented for simultaneous 3D printing. |

---

## Key Hardware & Geometric Updates in v1.2

1. **Thumb Plate Control Shift & Sizing:**
 - Mini-joystick shifted left by -6.0mm (X = 3.07mm) to provide ample thumb clearance from stick deflection.
 - Flanking buttons shifted left by -6.0mm (`SW_Left` at X = -23.79mm, `SW_Right` at X = 29.00mm), creating an expansive thumb leverage shelf on the right.
 - Button through-holes updated to **dia. 8.5mm** for close-fit mounting of standard dia. 8mm threaded bushings.
 - Button caps maintain true concentric circular perimeter arcs (R = 9.0mm, 4.75mm solid wall margin).
 - Joystick aperture updated to **dia. 27.0mm** with a **1.5mm x 45 deg conical front chamfer** (expanding the front mouth to dia. 30.0mm), accommodating the physical 26.0mm skirt during full 23 deg stick deflection.
 - Symmetrical 25mm flange transitions updated with smooth tangent-constrained concave arcs on both left and right returns.

2. **Grip Clamshell Ergonomics & Structural Clamping:**
 - **Continuous Snug M8 Shaft Bore (dia. 8.2mm):** The central rod bore has been tightened from the legacy dia. 9.60mm down to a continuous dia. 8.2mm across the entire clamping stalk (Z in [-40mm, +30mm]). All 4 internal annular relief chambers (dia. 11.2mm) have been filled solid to provide 100% continuous contact clamping around standard M8 threaded rods with zero radial play (eliminating the need for shimming or electrical tape).
 - **Epoxy Injection Hole Removed:** The obsolete dia. 3.2mm epoxy port has been defeatured, leaving a seamless 3D B-spline exterior shell.
 - Pointer finger trigger button relocated to rear-upper position with a standardized close-fit **dia. 8.5mm through-hole** (matching thumb plate pushbuttons for dia. 8mm bushings) and a 100\% contact planar spotface (dia. 12.2mm x 3.8mm deep).
 - Captive M3 hex nut pockets on the rear exterior skin allow drop-in nut installation on the bench and standard M3 x 25mm countersunk screws that remain safely recessed >= 1.4mm below the outer palm skin.
 - Stalk rear bulbous swell trimmed at Z = +4mm, recovering finger wrap clearance while securely enclosing the stalk clamping hardware.

---

## Recommended Print Settings

- **Process:** FDM (e.g. Bambu Lab X1C / P1S, Prusa MK4/XL) or SLA/Resin
- **Material:** PETG, PLA-CF, or Tough PLA
- **Layer Height:** 0.16 mm - 0.20 mm
- **Infill:** 30% - 50% Gyroid or Adaptive Cubic
- **Wall Loops:** 4 - 5 perimeters (ensures solid mounting bosses and screw clamping zones)
- **Top / Bottom Shells:** 5 layers

### Print Orientations
- **`thumbplate_minijoy.stl`:**
 - Place **front face flat down** on the build plate.
 - The 1.0mm x 45 deg outer perimeter chamfer prints cleanly without elephant's foot or brim cleanup.
 - Printed standoff bosses extend vertically upward (+Z).
 - **Zero supports required.**
- **`grip_hybrid_body_half_a.stl` & `grip_hybrid_body_half_b.stl`:**
 - Place flat parting split face (X = 0) directly down on the build plate.
 - Internal cavity and captive nut pockets (with 45 deg peaked ceilings) print **completely support-free**.

---

## Hardware & Electronics BOM Checklist

- **Thumb Joystick:** 1× Adafruit #512 (Analog 2-axis Thumb Joystick with select switch, Alps RKJXV mechanism, 26.0mm skirt).
- **PCB Standoff Screws:** 4× M2.5 or M3 self-tapping screws (6mm - 8mm thread length into 9.5mm deep pilot holes).
- **Flanking Pushbuttons:** 2× dia. 8mm panel-mount momentary pushbuttons (Left and Right).
- **Pointer Finger Button (Switch 1):** 1× dia. 8mm panel-mount pushbutton (seated in Half A spotface with dia. 8.5mm through-hole).
- **Plate-to-Grip Fasteners:** 2× M3 x 25mm countersunk screws + 2× standard M3 hex nuts.
- **Clamshell Clamping:** 1× M3 x 20mm socket head cap screw + 1× M3 hex nut (lower stalk swell).
