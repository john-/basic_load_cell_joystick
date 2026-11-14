# Tooling & Drill Bit Inventory: `basic_load_cell_joystick`

This inventory specifies the exact drill bit sizes, nominal metric hole diameters, and closest available Imperial fractional, wire-gauge, and letter drill bits required to machine and assemble the **basic load cell joystick** from raw aluminum stock.

---

## 1. Quick Master Drill Bit Chart

| Feature / Location | Metric Size (Nominal) | Hole Purpose | Closest Imperial Size | Imperial Type | Decimal (Inch) | Decimal (mm) | Fit Delta & Workshop Notes |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| **Top Plate Cell Mount** | **dia. 4.5mm** | M4 screw through-clearance (6 holes, 3 pairs) | **#15**<br>**#16**<br>**3/16"** | Wire<br>Wire<br>Fractional | 0.1800"<br>0.1770"<br>0.1875" | 4.572mm<br>4.496mm<br>4.763mm | **#15** is +0.07mm (ideal close clearance).<br>#16 is -0.004mm (very snug).<br>3/16" is +0.26mm (free clearance). |
| **Base Plate Cell Mount** | **dia. 5.5mm** | M5 screw through-clearance (6 holes, 3 pairs) | **7/32"**<br>**#3** | Fractional<br>Wire | 0.2188"<br>0.2130" | 5.556mm<br>5.410mm | **7/32"** is +0.056mm (near perfect match).<br>#3 is -0.09mm (too tight for M5). |
| **Top Plate Center Spine** | **dia. 9.0mm** | M8 spine rod pass-through | **Letter T**<br>**23/64"** | Letter<br>Fractional | 0.3580"<br>0.3594" | 9.093mm<br>9.128mm | **Letter T** is +0.09mm (clean pass).<br>**23/64"** is +0.13mm (excellent clearance). |
| **Grip Clamshell Screws** | **dia. 3.4mm** | M3 screw through-clearance | **#29**<br>**9/64"** | Wire<br>Fractional | 0.1360"<br>0.1406" | 3.454mm<br>3.572mm | **#29** is +0.054mm (standard M3 clearance).<br>9/64" is +0.17mm (free fit). |
| **Thumb Plate PCB Bosses** | **dia. 2.6mm** | M3 self-tap pilot hole | **#37**<br>**7/64"** | Wire<br>Fractional | 0.1040"<br>0.1094" | 2.642mm<br>2.778mm | **#37** is +0.042mm (firm thread forming in PLA/PETG).<br>7/64" is +0.18mm (loose thread engagement). |
| **Pushbuttons (Flank & Trigger)** | **dia. 8.5mm** | 8mm bushing panel mount | **Letter R**<br>**11/32"** | Letter<br>Fractional | 0.3390"<br>0.3438" | 8.611mm<br>8.731mm | **Letter R** is +0.11mm (close fit for 8mm switch).<br>**11/32"** is +0.23mm (easy installation fit). |
| **Trigger Spotface (Grip Shell)** | **dia. 12.2mm** | 8mm button collar counterbore | **31/64"**<br>**1/2"** | Fractional<br>Fractional | 0.4844"<br>0.5000" | 12.303mm<br>12.700mm | **31/64"** is +0.10mm (counterbore or spotface bit).<br>1/2" (12.7mm) provides +0.5mm room. |
| **Square Tube Brackets** | **dia. 8.75mm** | M8 bracket through-holes (if using unpunched tube) | **23/64"**<br>**Letter W** | Fractional<br>Letter | 0.3594"<br>0.3860" | 9.128mm<br>9.804mm | **Note:** Home Depot 16-Ga. perforated steel tube stock comes pre-punched with holes on 1" centers, eliminating layout drilling. If drilling custom holes, **23/64"** (9.13mm) passes M8 bolt with +0.38mm margin. |

---

## 2. Recommended Minimal Drill Bit Set for North American Makers

If you do not own a metric drill index, you can complete all machining operations using **four common imperial drill bits**:

1. **7/32"** (0.2188" / 5.56mm) - Base plate M5 through-holes.
2. **3/16"** (0.1875" / 4.76mm) - Top plate M4 through-holes.
3. **23/64"** (0.3594" / 9.13mm) - Top plate M8 center spine & square tube bracket holes.
4. **11/32"** (0.3438" / 8.73mm) - Thumb plate pushbuttons & trigger button panel through-holes.

*(For 3D printed parts, screw clearance holes are pre-formed during slicing and only need deburring or light clean-out with a standard 1/8" or 9/64" drill bit).*

---

## 3. Drilling & Machining Guidelines

### A. Template Affixing & Punching
1. Print the templates in `templates/` on paper at **100% scale** (verify the printed ruler using a physical caliper).
2. Cut around the perimeter and spray the back with a light mist of temporary repositionable spray adhesive (e.g., 3M 77 or Elmer's spray adhesive).
3. Smooth the template down onto the aluminum blank, aligning the circular perimeter or bracket edges.
4. Use an **automatic center punch** or sharp prick punch directly at every crosshair intersection. A crisp punch mark prevents the drill bit from wandering off center.

### B. Pilot Drilling Technique
- Aluminum plate stock (4.0mm / 9Ga) grabs easily: always clamp the blank to your drill press table or backer board.
- For holes >= 5.5mm, drill a small pilot hole first with a **1/16" or 3/32"** bit.
- Use a drop of cutting fluid or WD-40 to keep cuts cool and prevent aluminum galling on drill flutes.
- Deburr both sides of all drilled holes with a 90° countersink bit or larger twist drill rotated lightly by hand.
