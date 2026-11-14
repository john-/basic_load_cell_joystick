# Left-Handed Hybrid Joystick Grip

This directory contains the 3D CAD models and slicer-ready STL files for the **Left-Handed Hybrid Joystick Grip**.

---

## 1. Key Design Features

1. **Straight Ergonomic Vertical Shaft (0 deg Cant / Roll):**

- Ergonomic geometry (Z <= 85mm): palm swell, heel rest, index trigger pocket (Z = 24mm), finger grooves, continuous M8 spine rod conduit, and internal CAT5 cable routing.
- Snug dia. 8.2mm continuous M8 rod bore with zero annular play.
- Support-free FDM printing on X = 0 split faces.

2. **Mini-Joystick Thumb Plate (Adafruit #512):**

- Mini-joystick shifted left by -6.0mm (X = 3.07mm) to provide thumb clearance from stick deflection.
- Flanking pushbuttons shifted left (`SW_Left` at X = -23.79mm, `SW_Right` at X = 29.00mm), creating an expansive thumb leverage shelf on the right.
- dia. 8.5mm button holes for close-fit mounting of standard dia. 8mm threaded bushings.
- dia. 27.0mm aperture with a 1.5mm x 45 deg conical front chamfer.
- Symmetrical 25mm flange transitions with smooth tangent-constrained concave arcs.

3. **Index Finger Trigger Button (Switch 1):**

- Relocated to rear-upper position with a standardized dia. 8.5mm through-hole and planar spotface (dia. 12.2mm x 3.8mm deep).
- Solid internal backing with zero outer gaps.

4. **Cable Routing & Quick-Disconnects:**

- Pre-crimped PicoBlade 1.25mm connectors allow rapid thumb plate and button servicing without desoldering.

---

## 2. File Index

### Generators (`generators/`)

- `build_grip_hybrid.py`: Master script generating clamshell body halves.
- `build_thumbplate_minijoy.py`: Dedicated generator for the Adafruit #512 mini-joystick thumb plate.
- `build_assembly_hybrid_minijoy.py`: Assembly generator for the mini-joystick variant.
- `build_assemblies_linked.py`: FreeCAD native linked assembly generator.

### Active Models & Assemblies

- `models/grip_hybrid_body_half_a.FCStd`: Clamshell Body Half A (+X).
- `models/grip_hybrid_body_half_b.FCStd`: Clamshell Body Half B (-X).
- `models/thumbplate_minijoy.FCStd`: Mini-joystick thumb plate.
- `assemblies/assembly_grip_hybrid_minijoy.FCStd`: Linked FreeCAD assembly.
