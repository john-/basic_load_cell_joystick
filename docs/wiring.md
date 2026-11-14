# Grip Wiring & Quick-Disconnect Architecture (`docs/wiring.md`)

This document outlines the internal wiring design, quick-disconnect connector specifications, and assembly procedures for the hybrid flight stick grip. 

The primary design requirement is **modular plate iteration**: the thumb button plate profile is subject to continuous ergonomic revisions, meaning the exact same pushbuttons and mini-joystick module must transfer cleanly into newly printed plates without cutting, desoldering, or re-terminating wires.

---

## 1. Mechanical Constraints & Nut Clearance

Standard miniature panel-mount pushbuttons (e.g. M6, 1/4", or Gebildet M8 momentary switches) are secured from behind the thumb plate and grip shell using a hex nut and lock washer.

- **The Transfer Bottleneck:** To move a button from Plate A to Plate B without desoldering, the rear mounting nut and washer must be unscrewed, slid completely off the wire leads, and slipped onto the new plate.
- **Nut ID vs. Connector Size:**
 - Standard M6 button nuts have a through-clearance of ≈ 6.0 mm (minor thread diameter ≈ 5.0 mm).
 - Standard M8 button nuts have a through-clearance of ≈ 8.0 mm (minor thread diameter ≈ 6.8 mm).
 - A **2-pin Molex PicoBlade (1.25 mm pitch)** receptacle housing measures ≈ 3.2 mm x 4.2 mm x 3.5 mm (diagonal envelope ≈ 5.3 mm).
- **Rule for Transferability:** 
 - A **2-pin PicoBlade connector easily passes through an M8 nut and washer**, and can clear an M6 nut (or pass through with pins unlatched).
 - Any connector larger than 2 pins (3-pin, 4-pin, 5-pin, or 8-pin) **cannot fit through the mounting nut**.
 - Therefore, **every panel-mount pushbutton must terminate in its own dedicated 2-pin connector pigtail**.

---

## 2. Harness Architecture & Topology

The grip receives an 8-conductor trunk line cut from a standard CAT5/CAT6 cable. Inside the upper neck cavity, the trunk branches into dedicated micro-disconnects using 10-color pre-crimped wire leads (Molex PicoBlade 1.25 mm / JST style).

```
                  ┌────────────────────────────────────────────────────────────────────────┐
                  │                        THUMB PLATE ASSEMBLY                            │
                  │                                                                        │
                  │   [Left Button]  ────── [2-Pin Pigtail: Blue + Black] ───────────┐     │
                  │                                                                  │     │
                  │   [Right Button] ────── [2-Pin Pigtail: Yellow + Black] ─────────┼──┐  │
                  │                                                                  │  │  │
                  │   [Adafruit #512] ───── [5-Pin Pigtail: Red/Blk/Purp/Gry/Wht] ───┼──┼──│
                  └──────────────────────────────────────────────────────────────────┼──┼──┘
                                                                                     │  │
 ════════════════════════════════════════════════════════════════════════════════════╪══╪═══════ (Disconnect Boundary)
                                                                                     │  │
                      CAT5 Trunk in Neck (8 Conductors)                              │  │
                      ├── Conductor 6 (White-Green) + GND ──── [2-Pin: Green+Black] ─┴──┴── [Trigger Button in Half A]
                      ├── Conductor 5 (Blue)        + GND ──── [2-Pin: Blue+Black] ──────── (To Left Button)
                      ├── Conductor 4 (White-Blue)   + GND ──── [2-Pin: Yellow+Black] ────── (To Right Button)
                      └── Conductors 1, 2, 3, 7, 8  ────────── [5-Pin: Red/Blk/Purp/Gry/Wht] (To Adafruit #512)
```

### Pre-Crimped Wire Color Standardization

To ensure error-free assembly and visual traceability, the 10 available pre-crimped wire colors are allocated into dedicated roles:

| Signal Role | Assigned Color | Wire Type / Application | Function Description |
| :--- | :--- | :--- | :--- |
| **Excitation Power (`+3.3V` / VCC)** | **Red** | Power Rail | Mini-joystick potentiometer supply rail |
| **Common Ground (`GND`)** | **Black** | Common Ground Return | Shared ground return across all switches & stick |
| **Switch 1 (Index Trigger)** | **Green** | Dedicated Switch Lead | Tactical trigger button in Half A grip shell |
| **Switch 2 (Left Flank Button)** | **Blue** | Dedicated Switch Lead | Left button on thumb plate |
| **Switch 3 (Right Flank Button)** | **Yellow** | Dedicated Switch Lead | Right button on thumb plate |
| **Switch 4 (Mini-Joystick Select)** | **Purple** | Dedicated Switch Lead | Center push click switch on Adafruit #512 |
| **Mini-Joystick X-Axis (`Xout`)** | **White** | Analog Signal | Horizontal axis analog potentiometer output |
| **Mini-Joystick Y-Axis (`Yout`)** | **Grey** | Analog Signal | Vertical axis analog potentiometer output |
| *Spare / Reserved* | **Brown** | Available Line | Reserved for future expansion / sensors |
| *Spare / Reserved* | **Orange** | Available Line | Reserved for future expansion / sensors |

---

### Signal & Conductor Mapping (CAT5 Trunk to Pre-Crimped Pigtails)

| CAT5 Pin | CAT5 Trunk Wire Colour | Signal Function | Pre-Crimped Lead Colour | Target Component Pin | Connector Type |
| :---: | :--- | :--- | :---: | :--- | :---: |
| **1** | Brown | MiniJoy X-Axis (Analog) | **White** | Adafruit #512 Pin 4 (`Xout`) | 5-Pin PicoBlade |
| **2** | White-Brown | MiniJoy Y-Axis (Analog) | **Grey** | Adafruit #512 Pin 3 (`Yout`) | 5-Pin PicoBlade |
| **3** | Green | MiniJoy Push Select (Click) | **Purple** | Adafruit #512 Pin 2 (`SEL` / Switch 4) | 5-Pin PicoBlade |
| **4** | White-Blue | Switch 3 (Right Flank Button) | **Yellow** | Right Button Signal Terminal | 2-Pin PicoBlade |
| **5** | Blue | Switch 2 (Left Flank Button) | **Blue** | Left Button Signal Terminal | 2-Pin PicoBlade |
| **6** | White-Green | Switch 1 (Pointer Trigger) | **Green** | Trigger Button Signal Terminal | 2-Pin PicoBlade |
| **7** | Orange | +3.3V Excitation Power | **Red** | Adafruit #512 Pin 5 (`VCC`) | 5-Pin PicoBlade |
| **8** | White-Orange | Common Ground Return (`GND`) | **Black** | Adafruit #512 Pin 1 (`GND`) + All Switches | Shared Return Bus |

### Common Ground Return Bus
To prevent mechanical coupling between independent components:
- **Do not daisy-chain ground across the button terminals on the thumb plate.** (Doing so binds the buttons together and prevents sliding mounting nuts off).
- **Distribute ground on the CAT5 harness side:** Conductor 8 (`GND`, White-Orange) connects to a 4-way insulated junction in the grip neck cavity, sending an individual **Black** ground return wire to each connector:
  1. Trigger Button 2-pin plug (Green + **Black**)
  2. Left Button 2-pin plug (Blue + **Black**)
  3. Right Button 2-pin plug (Yellow + **Black**)
  4. Mini-Joystick 5-pin plug (Red, **Black**, Purple, Grey, White)

---

## 3. Component Transfer & Iteration Procedure

When migrating components into a newly 3D-printed thumb plate iteration:

### A. Flanking Pushbuttons (Left & Right)
1. Unplug the 2-pin PicoBlade connector from the neck harness.
2. Unscrew the rear hex nut and lock washer.
3. Slide the nut and washer off the back of the switch, passing directly over the 2-pin PicoBlade plastic shell.
4. Pull the pushbutton out through the front of the old plate.
5. Insert the switch into the new thumb plate through-hole.
6. Slide the washer and nut over the 2-pin connector, thread onto the switch body, and torque down.
7. Reconnect the 2-pin PicoBlade to the neck harness.

### B. Mini-Joystick Module (Adafruit #512)
1. Unplug the 5-pin PicoBlade connector.
2. Remove the 4× M3 (or M2.5) screws securing the PCB to the rear standoff bosses.
3. Seat the board onto the rear standoffs of the new plate and reinstall the 4 screws.
4. Plug the 5-pin PicoBlade connector back in.

### C. Trigger Button (Half A Shell)
- The pointer-finger trigger button remains inside its lateral slot on Half A.
- Its independent 2-pin PicoBlade disconnect ensures the thumb plate and Half B can be detached, serviced, or modified on the bench without pulling or stressing the trigger switch wires.

---

## 4. Strain Relief & Wire Protection

Pre-crimped PicoBlade leads (typically 28-32 AWG) have fine copper stranding that wicks solder, becoming brittle right at the transition between solder and insulation.

1. **Pushbutton Terminals:**
 - Solder pre-crimped pigtails (~30-40 mm length) directly to button solder lugs using their dedicated wire colors:
 - **Trigger (Switch 1):** **Green** (Signal) + **Black** (Ground)
 - **Left Button (Switch 2):** **Blue** (Signal) + **Black** (Ground)
 - **Right Button (Switch 3):** **Yellow** (Signal) + **Black** (Ground)
 - Apply 1.0 mm or 1.5 mm adhesive-lined polyolefin heat-shrink tubing over each lug to insulate against shorts and provide mechanical bend relief.
2. **Mini-Joystick Through-Hole Pads:**
 - **Wire Insertion & Solder Orientation:**
 - The mini-joystick module mounts to the rear printed standoffs of the thumb plate with the gimbal mechanism, potentiometers, and stick facing forward through the plate opening, leaving the **flat solder side (back of PCB)** facing rearward into the grip cavity.
 - Solder the 5 pre-crimped leads to their dedicated pads:
 - `GND` (Pin 1): **Black**
 - `SEL` (Pin 2, Switch 4): **Purple**
 - `Yout` (Pin 3, Vertical Axis): **Grey**
 - `Xout` (Pin 4, Horizontal Axis): **White**
 - `VCC` (Pin 5, +3.3V Power): **Red**
 - **Insert the stripped wire ends from the back side (solder side) into the through-holes, or lay the stripped wire leads flat onto the annular rings on the back side of the PCB.**
 - Do **not** push long wire ends from the front/top of the PCB through to the back: doing so leaves protruding wire loops or insulation on the front component side that can foul against the rear mounting bosses or thumb plate plastic.
 - Clip any excess conductor flush on the front side so nothing protrudes past the front surface of the PCB.
 - **Mechanical Relief:** Lay the insulated wire leads flat across the back fiberglass surface routed downward toward the neck cavity, and secure them with a strip of Kapton tape 5-10 mm back from the solder pads.
 - **Adhesive Dome:** Apply a bead of **neutral-cure electronic-grade silicone** (e.g. MG Chemicals 1035 / Dow 737) or **UV-curable resin** over the solder joints and taped area. This creates a flexible strain-relief boot that absorbs pulling forces, protecting the fine copper strands.
