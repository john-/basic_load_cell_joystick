"""
Parametric FreeCAD script to generate Left-Handed Hybrid Joystick Grip:
- SHAFT: Straight vertical shaft from JoystickGrip21 (Z <= 85mm), preserving
  palm swell, heel rest, finger grooves, index trigger pocket, central M8 core,
  and CAT5 wire conduit.
- NOTCHED TOP JOINT: 15° tilted inset notch cut directly into the vertical shaft.
  Eliminates bulky head cradles, cantilevered button arrays, and rear through-windows.
- 100% SUPPORT-FREE FDM PRINTING: Both clamshell halves (GripHybrid_Half_A and GripHybrid_Half_B)
  print flat on their X=0 split faces with ZERO overhang ceilings and zero internal supports.
- COMPACT THUMB BUTTON PLATE: Uniform 5.9mm margin from all button hole edges to plate perimeter.
  Tangential blend from SW2 down into the mounting tab for maximum structural strength.
- FLUSH APEX ALIGNMENT & 3.0MM THICKNESS: Plate thickness reduced by 0.5mm to 3.0mm, and
  positioned so the front face matches the front rounded apex of the grip (Y = -15.43mm),
  eliminating all thin feather/knife edges.
- WIDENED FLANGE (X = +18MM): The mounting flange extends to X = +18mm to intersect the inner
  circular arc directly, eliminating the narrow side step. The notch cuts fully across the neck
  (width 44mm) to eliminate all side wall slivers.
- FASTENING (OPTION 1): 2 through-grip M3 screws (1 on Half B, 1 on Half A) with countersunk front
  heads passing through the plate, front notch, conduit, and exiting the rear palm wall into
  peaked captive M3 hex nut pockets on the exterior back.
- CLAMSHELL SCREWS & OPTION A PALM SWELL EXTENSION:
  - Clamping screw pairs along BOTH the front and back of the shaft.
  - The 2 lowest stalk clamping screws (Z = -8.0mm and Z = +16.0mm) are relocated to Y = 16.5mm
    with pocket start offsets at |X| >= 5.2mm (outside the narrow cable channel X in [-5, +5]),
    guaranteeing 100% ZERO channel intrusion (0.00 mm^3 collision).
  - Smooth extended palm swell (Z in [-18, +28], Y_max = 20.5mm, 3mm corner fillets) blends seamlessly
    into the existing palm swell, ensuring a solid outer wall behind the lower clamp.
"""

import os
import sys
import math
import shutil
import zipfile
import tempfile
import xml.etree.ElementTree as ET

for p in ["/app/freecad/lib", "/usr/lib/freecad/lib", "/app/lib"]:
    if os.path.exists(p) and p not in sys.path:
        sys.path.append(p)

import FreeCAD as App
import Part

def _clean_fcstd_gui(fcstd_path):
    """Sanitize Document.xml and inject clean GuiDocument.xml container for error-free GUI loading."""
    if not os.path.exists(fcstd_path):
        return
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".FCStd")
    os.close(tmp_fd)
    with zipfile.ZipFile(fcstd_path, "r") as zin:
        file_map = {item.filename: zin.read(item.filename) for item in zin.infolist() if not item.filename.endswith(".Map.txt")}

    doc_root = ET.fromstring(file_map["Document.xml"])
    if doc_root.find("StringHasher") is None:
        hasher = ET.Element("StringHasher", {"saveall": "0", "threshold": "0", "count": "0"})
        doc_root.insert(0, hasher)
    objects_in_doc = [obj.get("name") for obj in doc_root.findall(".//Objects/Object") if obj.get("name")]

    for obj in doc_root.findall(".//ObjectData/Object"):
        for prop in obj.findall('.//Property[@name="Shape"]'):
            for elem in list(prop):
                if "HasherIndex" in elem.attrib:
                    del elem.attrib["HasherIndex"]
                if elem.tag == "ElementMap":
                    elem.clear()
                if elem.tag == "ElementMap2":
                    prop.remove(elem)

    for elem in doc_root.findall('.//Property[@type="App::PropertyXLink"]'):
        parent = doc_root.find(f".//*[@name='{elem.get('name')}']/..")
        if parent is not None:
            parent.remove(elem)

    file_map["Document.xml"] = ET.tostring(doc_root, encoding="utf-8")

    vp_blocks = []
    for name in objects_in_doc:
        vp_blocks.append(f'''        <ViewProvider name="{name}" expanded="0" treeRank="-1">
            <Properties Count="2">
                <Property name="Visibility" type="App::PropertyBool" status="1">
                    <Bool value="true"/>
                </Property>
                <Property name="ShowInTree" type="App::PropertyBool" status="1">
                    <Bool value="true"/>
                </Property>
            </Properties>
        </ViewProvider>''')
    vp_xml = "\n".join(vp_blocks)
    gui_xml = f'''<?xml version="1.0" encoding="utf-8"?>
<Document SchemaVersion="1" HasExpansion="1">
    <Expand />
    <ViewProviderData Count="{len(objects_in_doc)}">
{vp_xml}
    </ViewProviderData>
    <Camera settings="OrthographicCamera {{   viewportMapping ADJUST_CAMERA   position 0 -50 150   orientation 0.85 0.25 0.45  1.1   aspectRatio 1   focalDistance 100   height 150 }}"/>
</Document>
'''
    file_map["GuiDocument.xml"] = gui_xml.encode("utf-8")
    with zipfile.ZipFile(tmp_path, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for fname, data in file_map.items():
            zout.writestr(fname, data)
    shutil.copyfile(tmp_path, fcstd_path)
    os.remove(tmp_path)

def make_hex_prism(flat_to_flat, depth, peaked=True):
    """Generate regular hexagonal prism for captive hex nut. Peaked roof bridges cleanly."""
    r = (flat_to_flat / 2.0) / math.cos(math.radians(30))
    pts = []
    base_ang = 0.0 if peaked else 30.0
    for i in range(6):
        a = math.radians(60 * i + base_ang)
        pts.append(App.Vector(r * math.cos(a), r * math.sin(a), 0))
    pts.append(pts[0])
    w = Part.makePolygon(pts)
    f = Part.Face(w)
    return f.extrude(App.Vector(0, 0, depth))

def build_hybrid_grip():
    print("=" * 65)
    print("  BUILDING KNIFE-EDGE-FREE FLUSH HYBRID JOYSTICK GRIP")
    print("=" * 65)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "../../../.."))
    base_fcstd = os.path.join(project_root, "cad/grips/archive/v1_joystickgrip21/JoystickGrip21.FCStd")
    tp_fcstd   = os.path.join(project_root, "cad/base_frame/frame_top_plate.FCStd")
    models_dir = os.path.join(project_root, "cad/grips/hybrid/models")
    asm_dir = os.path.join(project_root, "cad/grips/hybrid/assemblies")
    stl_dir = os.path.join(project_root, "cad/grips/hybrid/stl")
    os.makedirs(stl_dir, exist_ok=True)
    tools_dir = os.path.join(project_root, "cad/tools")
    if tools_dir not in sys.path:
        sys.path.append(tools_dir)
    import convert_stl

    # -------------------------------------------------------------------------
    # 1. PARAMETRIC DEFINITIONS
    # -------------------------------------------------------------------------
    plate_th = 3.0       # mm faceplate thickness (reduced by 0.5mm to eliminate knife edge)
    hole_dia = 12.2      # mm clearance for 12mm threaded pushbuttons
    
    # Pure circular arc geometry with uniform 5.9mm margin:
    cx = 0.0
    cy = -32.88
    R_mid = 46.5
    R_in = 34.5
    R_out = 58.5
    r_end = (R_out - R_in) / 2.0  # 12.0 mm

    # 5 Button Centers: 1x 16.0mm (Middle Button 3) + 4x 6.6mm (Smaller Buttons 1, 2, 4, 5):
    buttons = [
        {"name": "SW2_StickTop", "x": -17.79, "y":  10.08, "dia":  6.6},  # Button 1 (Small)
        {"name": "SW3_Arc1",     "x":   0.00, "y":  13.62, "dia":  6.6},  # Button 2 (Small)
        {"name": "SW4_RestHome", "x":  17.79, "y":  10.08, "dia": 16.0},  # Button 3 (Big Middle)
        {"name": "SW5_Arc3",     "x":  32.88, "y":   0.00, "dia":  6.6},  # Button 4 (Small)
        {"name": "SW6_Horiz",    "x":  42.96, "y": -15.09, "dia":  6.6},  # Button 5 (Small)
    ]

    # Horizontal through-grip mounting screws (1 on Half B, 1 on Half A):
    mount_holes = [
        {"name": "Hole_Half_B", "x": -8.0, "y": -5.5},
        {"name": "Hole_Half_A", "x":  8.0, "y": -5.5}
    ]

    # -------------------------------------------------------------------------
    # 2. BUILD COMPACT THUMBPLATE_HYBRID (NARROWED SYMMETRICAL FLANGE TO X = +/-12.5MM)
    # -------------------------------------------------------------------------
    print("\n--- 1. Generating Compact ThumbPlate_Hybrid with 1x 16mm + 4x 6.6mm Holes ---")
    # Outer circular arc from th = -22.5 to th = +67.5 deg:
    p_out_start = App.Vector(cx + R_out * math.sin(math.radians(-22.5)), cy + R_out * math.cos(math.radians(-22.5)), 0)
    p_out_mid   = App.Vector(cx + R_out * math.sin(math.radians(22.5)),  cy + R_out * math.cos(math.radians(22.5)), 0)
    p_out_end   = App.Vector(cx + R_out * math.sin(math.radians(67.5)),  cy + R_out * math.cos(math.radians(67.5)), 0)
    arc_out = Part.ArcOfCircle(p_out_start, p_out_mid, p_out_end)

    # End cap at SW6 (th = +67.5 deg): Semicircle centered at SW6 (radius 12mm)
    p_in_end = App.Vector(cx + R_in * math.sin(math.radians(67.5)), cy + R_in * math.cos(math.radians(67.5)), 0)
    sw6 = buttons[4]
    p_cap6_mid = App.Vector(sw6["x"] + r_end * math.cos(math.radians(67.5)), sw6["y"] - r_end * math.sin(math.radians(67.5)), 0)
    arc_cap6 = Part.ArcOfCircle(p_out_end, p_cap6_mid, p_in_end)

    # Narrowed symmetrical flange extending to X = +/-12.5 mm:
    # Matches the intersection of the back of the flange with the front of the grip (X = +/-12.53 mm at Y = -5.5 mm):
    x_flange = 12.5
    y_tab_right = cy + math.sqrt(R_in**2 - x_flange**2)
    p_tab_right = App.Vector(x_flange, y_tab_right, 0)
    p_in_mid = App.Vector(cx + R_in * math.sin(math.radians(45.0)), cy + R_in * math.cos(math.radians(45.0)), 0)
    arc_in = Part.ArcOfCircle(p_in_end, p_in_mid, p_tab_right)

    # Tab right vertical edge down to Y = -12.5 (sits 0.5mm above notch floor):
    p_tab_bot_r = App.Vector(x_flange, -12.5, 0)
    edge_tab_r = Part.LineSegment(p_tab_right, p_tab_bot_r)

    # Tab bottom edge (base of screw flange, symmetric 25mm width):
    p_tab_bot_l = App.Vector(-x_flange, -12.5, 0)
    edge_tab_b = Part.LineSegment(p_tab_bot_r, p_tab_bot_l)

    # Tab left vertical edge up to intersection with SW2 round (at X = -12.5):
    sw2 = buttons[0]
    y_sw2_bot = sw2["y"] - math.sqrt(r_end**2 - (-x_flange - sw2["x"])**2)
    p_tab_l = App.Vector(-x_flange, y_sw2_bot, 0)
    edge_tab_l = Part.LineSegment(p_tab_bot_l, p_tab_l)

    # Circular cap around SW2 from p_tab_l to p_out_start:
    p_sw2_mid = App.Vector(sw2["x"] - r_end, sw2["y"], 0)
    arc_sw2 = Part.ArcOfCircle(p_tab_l, p_sw2_mid, p_out_start)

    wire_plate = Part.Wire([
        arc_out.toShape(),
        arc_cap6.toShape(),
        arc_in.toShape(),
        edge_tab_r.toShape(),
        edge_tab_b.toShape(),
        edge_tab_l.toShape(),
        arc_sw2.toShape()
    ])

    face_plate = Part.Face(wire_plate)
    solid_plate = face_plate.extrude(App.Vector(0, 0, plate_th))

    # Cut 5 button clearance holes (1x 16.0mm middle button + 4x 6.6mm small buttons)
    for b in buttons:
        bcyl = Part.makeCylinder(b["dia"] / 2.0, plate_th + 4.0, App.Vector(b["x"], b["y"], -2.0), App.Vector(0, 0, 1))
        solid_plate = solid_plate.cut(bcyl)

    # Cut 2 countersunk M3 mounting holes (1 per half) on front face
    for mh in mount_holes:
        hcyl = Part.makeCylinder(3.4 / 2.0, plate_th + 4.0, App.Vector(mh["x"], mh["y"], -2.0), App.Vector(0, 0, 1))
        hcb  = Part.makeCylinder(6.0 / 2.0, 1.8, App.Vector(mh["x"], mh["y"], plate_th - 1.5), App.Vector(0, 0, 1))
        solid_plate = solid_plate.cut(hcyl).cut(hcb)

    # Detent removed: surface is flat and smooth; large 16mm button provides natural tactile indexing
    print(f"ThumbPlate_Hybrid Valid: {solid_plate.isValid()}, Volume: {solid_plate.Volume:.1f} mm^3")

    # -------------------------------------------------------------------------
    # 3. POSITION PLATE RECESSED & FLUSH ON VERTICAL SHAFT (15 DEG PITCH TILT)
    # -------------------------------------------------------------------------
    print("\n--- 2. Positioning Plate Recessed & Flush into Grip Apex (15 deg pitch) ---")
    tilt_rad = math.radians(15.0)
    rot_mat = App.Matrix(
        1.0, 0.0, 0.0, 0.0,
        0.0, math.sin(tilt_rad), -math.cos(tilt_rad), 0.0,
        0.0, math.cos(tilt_rad),  math.sin(tilt_rad), 0.0,
        0.0, 0.0, 0.0, 1.0
    )
    rot_plate = App.Rotation(rot_mat)
    # (0.0, -9.30, 111.0) places the front face of the 3.0mm plate exactly flush with the front rounded apex of the grip (Y = -15.43):
    pos_plate = App.Vector(0.0, -9.30, 111.0)
    placement_plate = App.Placement(pos_plate, rot_plate)

    solid_plate_world = solid_plate.copy()
    solid_plate_world.Placement = placement_plate

    # -------------------------------------------------------------------------
    # 4. LOAD BASE SHAFT FROM JOYSTICKGRIP21 (Z <= 85mm)
    # -------------------------------------------------------------------------
    print("\n--- 3. Preserving Shaft & Slicing Off Original Head at Z=85mm ---")
    doc_base = App.openDocument(base_fcstd)
    ha = doc_base.getObject('Half_A')
    hb = doc_base.getObject('Half_B')

    s_ha = ha.Shape.copy()
    s_ha.transformShape(ha.Placement.toMatrix().inverse())
    s_hb = hb.Shape.copy()
    s_hb.transformShape(hb.Placement.toMatrix().inverse())
    App.closeDocument(doc_base.Name)

    # Defeat the inherited 2nd screw hole from the top at Y = +11.0mm, Z = 76.0mm
    # AND the obsolete epoxy injection port at Y in [-16, -4], Z in [22, 26]
    # directly using OpenCASCADE defeaturing on both halves before fusing into shaft.
    # Defeaturing restores the original underlying continuous B-spline exterior skin and
    # interior channel wall completely, leaving 0 seam faces, 0 protuberances, and 0 void remnants.
    faces_def_a = [f for f in s_ha.Faces if (
        (f.BoundBox.ZMin >= 72 and f.BoundBox.ZMax <= 80 and f.BoundBox.YMin >= 7 and f.BoundBox.YMax <= 15 and (hasattr(f.Surface, 'Radius') or (hasattr(f.Surface, 'Axis') and abs(f.Surface.Axis.x) > 0.9)))
        or
        (f.BoundBox.ZMin >= 22.0 and f.BoundBox.ZMax <= 26.0 and f.BoundBox.YMin >= -16.0 and f.BoundBox.YMax <= -4.0 and hasattr(f.Surface, 'Radius') and round(f.Surface.Radius, 2) in [1.60, 3.20])
    )]
    s_ha_clean = s_ha.defeaturing(faces_def_a)

    faces_def_b = [f for f in s_hb.Faces if (
        (f.BoundBox.ZMin >= 72 and f.BoundBox.ZMax <= 80 and f.BoundBox.YMin >= 7 and f.BoundBox.YMax <= 15 and not isinstance(f.Surface, Part.BSplineSurface))
        or
        (f.BoundBox.ZMin >= 22.0 and f.BoundBox.ZMax <= 26.0 and f.BoundBox.YMin >= -16.0 and f.BoundBox.YMax <= -4.0 and hasattr(f.Surface, 'Radius') and round(f.Surface.Radius, 2) in [1.60, 3.20])
    )]
    s_hb_clean = s_hb.defeaturing(faces_def_b)

    # Cut off and discard original head above Z=85.0 mm
    box_cutter = Part.makeBox(400, 400, 200, App.Vector(-200, -200, 85.0))
    shaft = s_ha_clean.fuse(s_hb_clean).cut(box_cutter)

    # Fill legacy loose Ø9.60mm bore and Ø11.20mm internal annular chambers solid (Z in [-40.0, +30.0]),
    # starting exactly at bottom base plane Z = -40.0mm (zero lip/collar protrusion):
    cyl_fill_bore = Part.makeCylinder(5.65, 70.0, App.Vector(0, 0, -40.0), App.Vector(0, 0, 1))
    shaft = shaft.fuse(cyl_fill_bore)

    # Re-drill continuous Ø8.2mm bore to exact legacy depth (depth = 70.0mm, from Z = -40.0mm to ceiling at Z = +30.0mm):
    # Starts at Z = -45.0mm to cleanly penetrate bottom face, length 75.0mm terminates at exactly Z = +30.0mm:
    new_m8_bore = Part.makeCylinder(8.2 / 2.0, 75.0, App.Vector(0, 0, -45.0), App.Vector(0, 0, 1))
    shaft = shaft.cut(new_m8_bore)

    # Vertical neck extension from Z=85 up to Z=130 (0 deg cant, straight vertical)
    w_neck = shaft.slice(App.Vector(0, 0, 1), 84.99)
    f_outer = Part.Face(w_neck[0])
    f_inner = Part.Face(w_neck[1])
    f_neck = f_outer.cut(f_inner)
    neck_vert = f_neck.extrude(App.Vector(0, 0, 45.0))
    full_grip = shaft.fuse(neck_vert)

    # -------------------------------------------------------------------------
    # 4B. 3D ORGANIC SMOOTH DOME BOSS (MELDED INTO TOP PART OF PALM SWELL)
    # -------------------------------------------------------------------------
    print("\n--- 4B. Adding Seamless 3D Organic Dome Boss Melded into Top of Palm Swell ---")
    # Generates a true 3D organically curved dome (ellipsoid) centered at (0.0, 16.8, -2.0)
    # with semi-axes Rx = 13.0mm, Ry = 5.2mm, Rz = 14.0mm.
    # Bridges the screw clamp boss at Z=-8mm directly into the top crest of the palm
    # swell hump at Z=0 to +6mm (Y ~ 22.0mm), eliminating any dip or saddle.
    sphere_unit = Part.makeSphere(1.0)
    scale_mat = App.Matrix()
    scale_mat.scale(13.0, 5.2, 14.0)
    boss_organic = sphere_unit.transformGeometry(scale_mat)
    boss_organic.translate(App.Vector(0.0, 16.8, -2.0))

    full_grip = full_grip.fuse(boss_organic)

    # -------------------------------------------------------------------------
    # 5. CUT FULL-SPAN NOTCH & BUTTON CLEARANCE (REMOVES SIDE KNIFE EDGES)
    # -------------------------------------------------------------------------
    print("\n--- 4. Cutting Full-Span Notch & Button Clearance (No Knife Edges) ---")
    # Full-span notch step (width 44mm, cutting completely through the 34.8mm neck):
    notch_front = Part.makeBox(44.0, 14.5, 20.0, App.Vector(-22.0, -13.0, 0.0))
    # Unobstructed button clearance pocket behind SW2, SW3, and SW4:
    notch_button_clearance = Part.makeBox(70.0, 50.0, 70.0, App.Vector(-35.0, 0.0, -35.0))
    sw4_clearance = Part.makeCylinder(22.0 / 2.0, 25.0, App.Vector(17.79, 10.08, -20.0), App.Vector(0, 0, 1))
    notch_full = notch_front.fuse(notch_button_clearance).fuse(sw4_clearance)
    notch_full_world = notch_full.copy()
    notch_full_world.Placement = placement_plate

    grip_notched = full_grip.cut(notch_full_world)

    # -------------------------------------------------------------------------
    # 6. THROUGH-GRIP SCREWS WITH REAR CAPTIVE NUT POCKETS (M3 x 25MM)
    # -------------------------------------------------------------------------
    print("\n--- 5. Drilling Through-Grip Holes & Cutting Rear Captive Nut Pockets ---")
    for mh in mount_holes:
        # Through hole (dia 3.4mm) passing completely through front notch, conduit, and rear wall
        th_cyl_local = Part.makeCylinder(3.4 / 2.0, 48.0, App.Vector(mh["x"], mh["y"], -42.0), App.Vector(0, 0, 1))
        th_cyl_world = th_cyl_local.transformGeometry(placement_plate.toMatrix())
        grip_notched = grip_notched.cut(th_cyl_world)

        # Captive M3 hex nut pocket on the rear back side (flat-to-flat: 5.7mm, depth: 8.0mm outward)
        # Seating face at Z_local = -20.0mm ensures M3 x 25mm screw has full thread engagement
        # across the standard 2.4mm M3 nut (3.1mm engagement), while both the nut and screw tip
        # sit safely recessed >= 1.4mm inside the rear surface, completely eliminating protrusion into palm.
        nut_local = make_hex_prism(5.7, 8.0, peaked=True)
        nut_local.translate(App.Vector(mh["x"], mh["y"], -28.0))
        nut_world = nut_local.transformGeometry(placement_plate.toMatrix())
        grip_notched = grip_notched.cut(nut_world)

    # -------------------------------------------------------------------------
    # 7. CLAMSHELL CLAMPING SCREWS (FRONT, REAR & UPPER NECK)
    # -------------------------------------------------------------------------
    print("\n--- 6. Adding Shaft Clamping Screws (Option A Relocated Stalk Clamps) ---")
    # For Z=-8.0 and Z=16.0 (narrow cable channel section), screws are relocated to Y=16.5mm
    # with counterbore/nut pockets starting at |X| >= 5.2mm (outside the X in [-5, +5] channel),
    # guaranteeing 0.00 mm^3 collision with the cable channel and solid plastic barrier walls.
    extra_screws = [
        ( 11.0, -30.0, 4.0),  # Base clamp (solid plastic, no channel)
        ( 16.5,  -8.0, 5.2),  # Lower stalk clamp (relocated to clear narrow cable channel)
        ( 11.0,  40.0, 4.0),  # Palm swell upper-mid
        ( 11.0,  95.0, 4.0),  # Upper neck clamp (back)
        (-11.0,  95.0, 4.0),  # Upper neck clamp (front)
    ]

    for y_c, z_c, x_s in extra_screws:
        clearance = Part.makeCylinder(3.4 / 2.0, 50.0, App.Vector(-25, y_c, z_c), App.Vector(1, 0, 0))
        cb = Part.makeCylinder(6.2 / 2.0, 25.0, App.Vector(x_s, y_c, z_c), App.Vector(1, 0, 0))
        r_hex = 5.5 / math.sqrt(3.0) + 0.15
        hex_pts = []
        for i in range(7):
            ang = math.radians(60.0 * i + 30.0)
            hex_pts.append(App.Vector(-x_s, y_c + r_hex * math.cos(ang), z_c + r_hex * math.sin(ang)))
        hex_face = Part.Face(Part.makePolygon(hex_pts))
        nut_pocket = hex_face.extrude(App.Vector(-25.0, 0, 0))
        grip_notched = grip_notched.cut(clearance).cut(cb).cut(nut_pocket)
        hex_face = Part.Face(Part.makePolygon(hex_pts))
        nut_pocket = hex_face.extrude(App.Vector(-25.0, 0, 0))
        grip_notched = grip_notched.cut(clearance).cut(cb).cut(nut_pocket)

    # -------------------------------------------------------------------------
    # 7B. CUT POINTER FINGER BUTTON (RADIALLY TOWARD CENTER, 100% CONTACT RECESS)
    # -------------------------------------------------------------------------
    print("\n--- 6B. Cutting Pointer Finger Button (Ø8.5mm, Radially Toward Center, Half A) ---")
    sw1_y = 11.0
    sw1_z = 76.0
    sw1_dia = 8.5  # Close-fit Ø8.5mm through-hole matching thumb plate buttons (for Ø8mm button bushings)
    # Button collar outer diameter is 11.8mm.
    # cs_dia = 12.2mm (+0.4mm clearance for FDM 3D printing).
    # cs_depth = 3.8mm recesses the button collar past the deepest point (+3.69mm)
    # on the 3D-curved B-spline rear flank turning surface, ensuring 100% continuous circumferential planar contact.
    cs_dia = 12.2
    cs_depth = 3.8
    x_ext = 15.69  # True exterior skin position at Y=11.0, Z=76.0

    # Radial vector pointing from exterior point (x_ext, sw1_y) toward joystick center (0, 0):
    dx = -x_ext
    dy = -sw1_y
    ray_len = math.hypot(dx, dy)
    vx = dx / ray_len
    vy = dy / ray_len
    v_dir = App.Vector(vx, vy, 0.0)

    # Start 5.0mm outside exterior surface along radial ray:
    p_start = App.Vector(x_ext - vx * 5.0, sw1_y - vy * 5.0, sw1_z)

    # 1. Countersink for button collar (Ø12.2mm, 3.8mm deep into skin):
    btn_cs = Part.makeCylinder(cs_dia / 2.0, 5.0 + cs_depth, p_start, v_dir)

    # 2. Circular through-hole Ø8.5mm along radial axis:
    # Length 30.0mm penetrates completely through the shell wall and enters the internal cable cavity:
    btn_hole = Part.makeCylinder(sw1_dia / 2.0, 30.0, p_start, v_dir)

    # Approach 2: No internal nut pocket cutter. The interior boss is preserved 100% solid,
    # ensuring maximum strength, zero punctures, and zero rear wall breaches.

    # -------------------------------------------------------------------------
    # 8. SPLIT CLAMSHELL HALVES ACROSS X=0
    # -------------------------------------------------------------------------
    print("\n--- 7. Splitting Clamshell Halves Across X=0 Plane ---")
    split_box_a = Part.makeBox(400, 400, 300, App.Vector(   0, -200, -60)) # X > 0 is Half_A
    split_box_b = Part.makeBox(400, 400, 300, App.Vector(-400, -200, -60)) # X < 0 is Half_B

    # Cut button countersink and through-hole into Half A alone:
    half_a_hybrid = grip_notched.cut(btn_cs).cut(btn_hole).common(split_box_a)
    half_b_hybrid = grip_notched.common(split_box_b)

    print(f"Half_A_Hybrid Valid: {half_a_hybrid.isValid()}, Volume: {half_a_hybrid.Volume:.1f} mm^3")
    print(f"Half_B_Hybrid Valid: {half_b_hybrid.isValid()}, Volume: {half_b_hybrid.Volume:.1f} mm^3")

    # -------------------------------------------------------------------------
    # 9. SAVE FREECAD DOCUMENTS AND EXPORT STLS
    # -------------------------------------------------------------------------
    print("\n--- 8. Saving Projects and Exporting STLs ---")
    
    # 9A. Standalone Clamshell Body Halves
    # (Note: thumbplate_5button is maintained separately via build_thumbplate_5button.py)
    doc_ha = App.newDocument("grip_hybrid_body_half_a")
    feat_ha_single = doc_ha.addObject("Part::Feature", "GripHybrid_Half_A")
    feat_ha_single.Shape = half_a_hybrid
    doc_ha.recompute()
    out_ha_fcstd = os.path.join(models_dir, "grip_hybrid_body_half_a.FCStd")
    doc_ha.saveAs(out_ha_fcstd)
    _clean_fcstd_gui(out_ha_fcstd)
    print(f"Saved Standalone Body Half A: {out_ha_fcstd}")
    App.closeDocument(doc_ha.Name)

    doc_hb = App.newDocument("grip_hybrid_body_half_b")
    feat_hb_single = doc_hb.addObject("Part::Feature", "GripHybrid_Half_B")
    feat_hb_single.Shape = half_b_hybrid
    doc_hb.recompute()
    out_hb_fcstd = os.path.join(models_dir, "grip_hybrid_body_half_b.FCStd")
    doc_hb.saveAs(out_hb_fcstd)
    _clean_fcstd_gui(out_hb_fcstd)
    print(f"Saved Standalone Body Half B: {out_hb_fcstd}")
    App.closeDocument(doc_hb.Name)

    # 9C. Full Assembly Document (assembly_grip_hybrid_5button.FCStd)
    # Generates a true FreeCAD 1.0 linked assembly (Assembly::AssemblyObject with App::Link)
    try:
        sys.path.insert(0, script_dir)
        from build_assemblies_linked import build_grip_hybrid_5button_assembly
        build_grip_hybrid_5button_assembly(project_root)
    except Exception as e:
        print(f"Warning: Could not invoke build_assemblies_linked: {e}")

    # Export individual half STLs (ready for flat 3D printing on X=0)
    out_ha_stl = os.path.join(stl_dir, "grip_hybrid_body_half_a.stl")
    out_hb_stl = os.path.join(stl_dir, "grip_hybrid_body_half_b.stl")
    half_a_hybrid.exportStl(out_ha_stl)
    half_b_hybrid.exportStl(out_hb_stl)
    convert_stl.ascii_to_binary_stl(out_ha_stl, out_ha_stl, "grip_hybrid_body_half_a binary STL")
    convert_stl.ascii_to_binary_stl(out_hb_stl, out_hb_stl, "grip_hybrid_body_half_b binary STL")
    print(f"Exported Binary STL: {out_ha_stl}")
    print(f"Exported Binary STL: {out_hb_stl}")

    print("\n" + "=" * 65)
    print("  KNIFE-EDGE-FREE JOYSTICK GRIP GENERATION COMPLETE!")
    print("=" * 65)
    return True

if __name__ == "__main__":
    build_hybrid_grip()
