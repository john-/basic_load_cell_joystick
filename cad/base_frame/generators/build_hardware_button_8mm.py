#!/usr/bin/env python3
"""
cad/base_frame/generators/build_hardware_button_8mm.py

Parametric generator for the Gebildet / Daier GQ-8H-10M 8mm Momentary Metal Pushbutton:
- Blueprint & Photos: Yueqing Daier / Yijia GQ-8H-10M Series & Gebildet Amazon photo
- Bushing / Body: M8 x 0.5mm threaded barrel (OD 8.0mm, Length 18.35mm, Z = -18.35 to 0.0)
- O-Ring Seal: OD 9.2mm x 1.0mm black silicone/nitrile seal seated directly beneath collar (Z = -1.0 to 0.0)
- Bezel / Collar: OD 10.4mm, Height 1.8mm (Z = 0.0 to 1.8mm) with hex collar and front conical bevel
- Annular Clearance Gap: 0.5mm wide x 1.0mm deep recess separating collar from plunger (OD 7.3mm)
- High-Round Actuator Plunger: OD 6.3mm domed "High Head" (Z = 1.8mm to 3.8mm, 2.0mm protrusion)
- Rear Hex Nut & Washer: 10.0mm across flats hex nut and washer on body (Z = -5.3 to -2.8mm)
- Solder Lugs ("Golden Foot"): 2x brass gold-plated solder terminals with stamped wire eyelets (Z = -18.35 to -21.7mm)

Outputs:
- cad/base_frame/hardware_button_8mm.FCStd
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

def build_hardware_button_8mm():
    print("=" * 65)
    print("  BUILDING PHOTOREALISTIC GEBILDET / DAIER GQ-8H-10M PUSHBUTTON")
    print("=" * 65)

    repo_root = "/net/penter/library/pub/dev/basic_load_cell_joystick"
    if not os.path.exists(repo_root):
        repo_root = os.getcwd()
    out_path = os.path.join(repo_root, "cad/base_frame/hardware_button_8mm.FCStd")

    # Dimensions
    bushing_dia = 8.0        # mm M8 threaded body
    body_len = 18.35         # mm body length under collar
    collar_dia = 10.4        # mm outer diameter of bezel
    collar_h = 1.8           # mm height of collar above panel
    button_dia = 6.3         # mm high-head button diameter
    protrusion = 2.0         # mm button height above collar (total Z = collar_h + 2.0 = 3.8mm)
    terminal_len = 3.35      # mm solder lug length below body (total depth = 18.35 + 3.35 = 21.7mm)
    terminal_w = 1.8         # mm lug width
    terminal_th = 0.5        # mm lug thickness
    eyelet_dia = 1.0         # mm wire hole in terminal

    # 1. Threaded Body Barrel (Z = -body_len to 0.0)
    barrel = Part.makeCylinder(bushing_dia / 2.0, body_len, App.Vector(0, 0, -body_len), App.Vector(0, 0, 1))

    # 2. O-Ring Seal (Z = -0.9 to 0.0)
    oring = Part.makeCylinder(9.2 / 2.0, 0.9, App.Vector(0, 0, -0.9), App.Vector(0, 0, 1))

    # 3. Outer Bezel / Collar with Annular Clearance Gap (Z = 0.0 to collar_h)
    collar_cyl = Part.makeCylinder(collar_dia / 2.0, collar_h, App.Vector(0, 0, 0), App.Vector(0, 0, 1))
    chamfer_cone = Part.makeCone(collar_dia / 2.0 - 0.6, collar_dia / 2.0 + 1.0, 0.8, App.Vector(0, 0, collar_h - 0.6), App.Vector(0, 0, 1))
    collar_body = collar_cyl.cut(chamfer_cone)

    # Annular gap between collar and button plunger:
    # Plunger OD is 6.3mm. Inner bezel bore is 7.2mm (leaving a 0.45mm crisp visual gap).
    annular_groove = Part.makeCylinder(7.2 / 2.0, 1.2, App.Vector(0, 0, collar_h - 1.2), App.Vector(0, 0, 1))
    collar = collar_body.cut(annular_groove)

    # 4. High-Round Domed Actuator Button (Z = collar_h - 0.8 to collar_h + protrusion)
    # Rises from inside the annular groove up to +3.8mm
    plunger_cyl = Part.makeCylinder(button_dia / 2.0, protrusion + 0.8, App.Vector(0, 0, collar_h - 0.8), App.Vector(0, 0, 1))
    dome_r = 4.8 # mm radius for smooth spherical dome crown
    dome_sphere = Part.makeSphere(dome_r, App.Vector(0, 0, collar_h + protrusion - dome_r))
    crown_bound = Part.makeCylinder(button_dia / 2.0, protrusion + 0.8, App.Vector(0, 0, collar_h - 0.8), App.Vector(0, 0, 1))
    plunger_crown = dome_sphere.common(crown_bound)
    button_actuator = plunger_cyl.fuse(plunger_crown)

    # 5. Hex Mounting Nut & Washer on Threaded Barrel (Z = -5.3 to -2.8)
    washer = Part.makeCylinder(11.0 / 2.0, 0.8, App.Vector(0, 0, -2.8), App.Vector(0, 0, 1))
    nut_r = 10.0 / math.sqrt(3.0)
    hex_pts = [
        App.Vector(nut_r * math.cos(i * math.pi / 3.0), nut_r * math.sin(i * math.pi / 3.0), 0)
        for i in range(6)
    ]
    hex_pts.append(hex_pts[0])
    nut_wire = Part.makePolygon(hex_pts)
    nut_face = Part.Face(nut_wire)
    nut = nut_face.extrude(App.Vector(0, 0, 2.5))
    nut.translate(App.Vector(0, 0, -5.3))
    nut_hardware = washer.fuse(nut)

    # 6. Golden Foot Solder Terminals (Z = -body_len - terminal_len to -body_len)
    term1 = Part.makeBox(terminal_w, terminal_th, terminal_len, App.Vector(-terminal_w / 2.0, 1.8, -body_len - terminal_len))
    eyelet1 = Part.makeCylinder(eyelet_dia / 2.0, 2.0, App.Vector(0, 1.0, -body_len - terminal_len + 1.2), App.Vector(0, 1, 0))
    lug1 = term1.cut(eyelet1)

    term2 = Part.makeBox(terminal_w, terminal_th, terminal_len, App.Vector(-terminal_w / 2.0, -1.8 - terminal_th, -body_len - terminal_len))
    eyelet2 = Part.makeCylinder(eyelet_dia / 2.0, 2.0, App.Vector(0, -3.0, -body_len - terminal_len + 1.2), App.Vector(0, 1, 0))
    lug2 = term2.cut(eyelet2)

    # Fuse all parts
    button_solid = barrel.fuse(oring).fuse(collar).fuse(button_actuator).fuse(nut_hardware).fuse(lug1).fuse(lug2)
    button_solid = button_solid.removeSplitter()

    print(f"GQ-8H-10M Solid Valid: {button_solid.isValid()}, Volume: {button_solid.Volume:.1f} mm^3")

    doc = App.newDocument("hardware_button_8mm")
    obj = doc.addObject("Part::Feature", "Button_8mm")
    obj.Label = "Button_8mm"
    obj.Shape = button_solid

    doc.recompute()
    doc.saveAs(out_path)
    App.closeDocument(doc.Name)

    _clean_fcstd_gui(out_path)
    print(f"Generated: {out_path} ({os.path.getsize(out_path)/1024:.1f} KB)")
    return True

if __name__ == "__main__":
    build_hardware_button_8mm()
