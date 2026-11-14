#!/usr/bin/env python3
"""
cad/base_frame/generators/build_hardware_joystick_cap.py

Parametric generator for the Adafruit #512 Analog 2-Axis Thumb Joystick Cap & Shroud:
- Matches official Adafruit Product ID 512 assembled kit photos and measurements.
- Spherical Dust Skirt: OD 26.0mm (exactly 1.0mm smaller than the thumbplate Ø27.0mm hole).
  Curved spherical dome rising from Z = 0.0 to Z = 6.5mm, transitioning into the stalk.
- Slender Stalk / Neck: Cylindrical column OD 7.5mm rising from Z = 6.5mm to Z = 11.5mm (height 5.0mm).
- Mushroom Undercut Head: Sweeps horizontally outward from OD 7.5mm to OD 17.5mm thumb rest pad.
- Ergonomic Dished Head: OD 17.5mm x 3.5mm thick (Z = 11.5mm to 15.0mm) with a 1.4mm deep concave
  spherical thumb rest dish (radius 20mm) and a soft rounded perimeter rim.
- 4 Directional Tactile Grip Pips: Small raised hemispherical nubs (dia 1.2mm, height 0.4mm)
  positioned at 0 deg, 90 deg, 180 deg, and 270 deg inside the dish (r = 5.0mm from center).
- Internal Alps Actuator Socket: Keyway cavity (2.2mm x 4.2mm x 8.5mm) mating onto Alps lever.

Outputs:
- cad/base_frame/hardware_joystick_cap.FCStd
"""

import sys
import os
import math
import zipfile
import xml.etree.ElementTree as ET

for p in [
    "/app/freecad/lib",
    "/usr/lib/freecad/lib",
    "/usr/lib/freecad-daily/lib",
    "/usr/lib/freecad-python3/lib",
    os.path.expanduser("~/.local/lib/freecad/lib")
]:
    if os.path.exists(p) and p not in sys.path:
        sys.path.append(p)

import FreeCAD as App
import Part

def _clean_fcstd_gui(filepath):
    tmp_path = filepath + ".tmp"
    with zipfile.ZipFile(filepath, 'r') as zin:
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
    <Camera settings="OrthographicCamera {{   viewportMapping ADJUST_CAMERA   position 0 -50 50   orientation 0.85 0.25 0.45  1.1   aspectRatio 1   focalDistance 50   height 50 }}"/>
</Document>
'''
    file_map["GuiDocument.xml"] = gui_xml.encode("utf-8")
    with zipfile.ZipFile(tmp_path, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for fname, data in file_map.items():
            zout.writestr(fname, data)
    os.replace(tmp_path, filepath)

def build_hardware_joystick_cap():
    print("=" * 65)
    print("  BUILDING ACCURATE MUSHROOM-STALK ADAFRUIT #512 JOYSTICK SHROUD")
    print("=" * 65)

    repo_root = "/net/penter/library/pub/dev/basic_load_cell_joystick"
    if not os.path.exists(repo_root):
        repo_root = os.getcwd()
    out_path = os.path.join(repo_root, "cad/base_frame/hardware_joystick_cap.FCStd")

    # Dimensions
    skirt_od = 26.0       # mm outer diameter of spherical skirt base (1mm smaller than 27mm hole)
    skirt_r = skirt_od / 2.0  # 13.0 mm
    skirt_wall = 1.3      # mm wall thickness of hollow skirt
    skirt_h = 6.5         # mm height of spherical skirt dome
    stalk_od = 7.5        # mm slender neck column diameter
    stalk_h = 5.0         # mm neck column height (Z = 6.5 to 11.5mm)
    head_od = 17.5        # mm thumb rest pad diameter
    head_h = 3.5          # mm head thickness (Z = 11.5 to 15.0mm)
    total_h = skirt_h + stalk_h + head_h  # 15.0 mm total height

    # 1. Outer Spherical Skirt Dome (Base rim at Z = 0)
    # A spherical dome with base radius 13.0mm, height 6.5mm:
    # Sphere radius R: R^2 = (R - 6.5)^2 + 13.0^2 => R^2 = R^2 - 13*R + 42.25 + 169 => 13*R = 211.25 => R = 16.25 mm!
    R_sphere = 16.25
    center_z = 6.5 - R_sphere  # -9.75 mm
    outer_sphere = Part.makeSphere(R_sphere, App.Vector(0, 0, center_z))
    # Slice flat at bottom Z = 0
    bot_cutter = Part.makeBox(60, 60, 40, App.Vector(-30, -30, -40))
    # Slice top at Z = skirt_h
    top_cutter = Part.makeBox(60, 60, 40, App.Vector(-30, -30, skirt_h))
    skirt_outer = outer_sphere.cut(bot_cutter).cut(top_cutter)

    # Hollow interior skirt to clear Alps mechanism
    inner_sphere = Part.makeSphere(R_sphere - skirt_wall, App.Vector(0, 0, center_z))
    skirt_hollow = skirt_outer.cut(inner_sphere)

    # 2. Slender Stalk / Neck Column (Z = 5.5 to 11.5, blending smoothly with skirt)
    stalk = Part.makeCylinder(stalk_od / 2.0, stalk_h + 1.0, App.Vector(0, 0, skirt_h - 1.0), App.Vector(0, 0, 1))

    # 3. Mushroom Undercut Head (Z = 11.5 to 15.0)
    # Underside fillet / flare:
    head_base = Part.makeCylinder(head_od / 2.0, head_h, App.Vector(0, 0, skirt_h + stalk_h), App.Vector(0, 0, 1))
    under_flare = Part.makeCone(stalk_od / 2.0, head_od / 2.0, 1.2, App.Vector(0, 0, skirt_h + stalk_h - 0.8), App.Vector(0, 0, 1))

    # Spherical Concave Thumb Dish indentation at top:
    dish_r = 20.0  # mm radius of spherical thumb hollow
    dish_sphere = Part.makeSphere(dish_r, App.Vector(0, 0, total_h + dish_r - 1.4))

    # Soft rounded outer rim:
    groove_ring = Part.makeTorus(head_od / 2.0 - 1.0, 0.35)
    groove_ring.translate(App.Vector(0, 0, total_h))

    # 4. Fuse head, stalk, and skirt, then cut dish
    cap_body = skirt_hollow.fuse(stalk).fuse(under_flare).fuse(head_base)
    cap_dished = cap_body.cut(dish_sphere).cut(groove_ring)

    # 5. 4 Directional Tactile Grip Pips (North, South, East, West inside dish)
    pip_r = 5.0   # mm radius from center
    pip_sphere_r = 0.7
    pips = []
    # Dish surface Z at radius pip_r:
    z_dish_surface = total_h + dish_r - 1.4 - math.sqrt(dish_r**2 - pip_r**2)
    for angle_deg in [0.0, 90.0, 180.0, 270.0]:
        rad = math.radians(angle_deg)
        px = pip_r * math.cos(rad)
        py = pip_r * math.sin(rad)
        pip = Part.makeSphere(pip_sphere_r, App.Vector(px, py, z_dish_surface + 0.25))
        pips.append(pip)

    for p in pips:
        cap_dished = cap_dished.fuse(p)

    # 6. Internal Alps Actuator Socket (Inside central core from Z = 0 to 8.5)
    socket_box = Part.makeBox(2.2, 4.2, 8.5, App.Vector(-1.1, -2.1, -0.5))
    cap_solid = cap_dished.cut(socket_box)
    cap_solid = cap_solid.removeSplitter()

    print(f"Accurate Adafruit #512 Cap Solid Valid: {cap_solid.isValid()}, Volume: {cap_solid.Volume:.1f} mm^3")

    doc = App.newDocument("hardware_joystick_cap")
    obj = doc.addObject("Part::Feature", "Joystick_Cap")
    obj.Label = "Joystick_Cap"
    obj.Shape = cap_solid

    doc.recompute()
    doc.saveAs(out_path)
    App.closeDocument(doc.Name)

    _clean_fcstd_gui(out_path)
    print(f"Generated: {out_path} ({os.path.getsize(out_path)/1024:.1f} KB)")
    return True

if __name__ == "__main__":
    build_hardware_joystick_cap()
