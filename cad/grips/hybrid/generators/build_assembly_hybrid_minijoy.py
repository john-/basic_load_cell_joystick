#!/usr/bin/env python3
"""
build_grip_joystick_assembly.py

Generates the new Grip Hybrid assembly incorporating the alternate mini-joystick
thumb button plate (ThumbPlate_Joystick) instead of the original 5-button plate:
- GripHybrid_Half_A
- GripHybrid_Half_B
- TopPlate reference
- ThumbPlate_Joystick_Mounted (with Adafruit #512 mini-joystick breakout support)
- Mini_Joystick_Breakout (3D reference model of Adafruit #512 mounted on bosses)

Outputs:
- model/grip_hybrid/GripHybrid_Joystick_Assembly.FCStd
- model/grip_hybrid/GripHybrid_Joystick_Assembly.stl
"""

import sys
import os
import math
import zipfile
import xml.etree.ElementTree as ET

try:
    import FreeCAD as App
    import Part
except ImportError:
    App = None
    Part = None

def build_grip_joystick_assembly():
    print("=" * 65)
    print("  BUILDING GRIP HYBRID JOYSTICK ASSEMBLY")
    print("=" * 65)

    script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
    project_root = os.path.abspath(os.path.join(script_dir, "../../../.."))

    sys.path.insert(0, script_dir)
    from build_assemblies_linked import build_grip_hybrid_minijoy_assembly
    build_grip_hybrid_minijoy_assembly(project_root)
    return True

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
    <Camera settings="OrthographicCamera {{   viewportMapping ADJUST_CAMERA   position 0 -50 150   orientation 0.85 0.25 0.45  1.1   aspectRatio 1   focalDistance 100   height 150 }}"/>
</Document>
'''
    file_map["GuiDocument.xml"] = gui_xml.encode("utf-8")
    with zipfile.ZipFile(tmp_path, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for fname, data in file_map.items():
            zout.writestr(fname, data)
    os.replace(tmp_path, filepath)

if __name__ == "__main__":
    build_grip_joystick_assembly()
