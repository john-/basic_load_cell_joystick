#!/usr/bin/env python3
"""
cad/grips/hybrid/generators/build_assemblies_linked.py

Builds true linked FreeCAD assemblies for the Left-Handed Hybrid Joystick Grip:
1. cad/grips/hybrid/assemblies/assembly_grip_hybrid_minijoy.FCStd
   - Complete mechanical assembly including:
     - cad/base_frame/frame_base_disk.FCStd (BaseDisk)
     - 6x cad/base_frame/hardware_standoff_hex.FCStd (Standoffs for 3x load cell fixed ends)
     - 3x cad/base_frame/sensor_load_cell_tal220.FCStd (TAL220 10kg load cells in 120-degree triad)
     - cad/base_frame/frame_top_plate.FCStd (TopPlate)
     - cad/grips/hybrid/models/grip_hybrid_body_half_a.FCStd (GripHybrid_Half_A)
     - cad/grips/hybrid/models/grip_hybrid_body_half_b.FCStd (GripHybrid_Half_B)
     - cad/grips/hybrid/models/thumbplate_minijoy.FCStd (ThumbPlate_Joystick)
     - cad/base_frame/sensor_mini_joystick_breakout.FCStd (Analog_2_axis_Joystick_512_v5)

Uses FreeCAD 1.0 native Assembly::AssemblyObject containers populated with App::Link
objects, fully compliant with the FreeCAD 1.0 / 1.1 C++ serialization schema.
"""

import sys
import os
import copy
import math
import uuid
import zipfile
import xml.etree.ElementTree as ET


def create_linked_assembly(template_path, output_path, doc_label, links):
    """
    Transforms a genuine FreeCAD Assembly document into a clean linked assembly.
    Ensures complete schema validity:
    - ObjectDeps with exact dependency mappings
    - Complete Origin coordinate system (App::Origin, X/Y/Z axes, planes, Origin001)
    - Assembly::JointGroup (Joints) container
    - App::Link objects with LinkExtension, PropertyXLink, and exact Placements
    - Matching ViewProviders for all objects in GuiDocument.xml
    - All required ShapeAppearance material binary files
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    with zipfile.ZipFile(template_path, "r") as z:
        doc_root = ET.fromstring(z.read("Document.xml"))
        gui_root = ET.fromstring(z.read("GuiDocument.xml"))
        shape_apps = {name: z.read(name) for name in z.namelist() if "ShapeAppearance" in name}
        # Find any existing App::Link object and viewprovider as template
        base_link_obj = copy.deepcopy(doc_root.find(".//ObjectData/Object[@name=\"TopPlate\"]"))
        base_link_vp  = copy.deepcopy(gui_root.find(".//ViewProviderData/ViewProvider[@name=\"TopPlate\"]"))

    base_obj_names = ["Assembly", "Origin", "X_Axis", "Y_Axis", "Z_Axis", "XY_Plane", "XZ_Plane", "YZ_Plane", "Origin001", "Joints"]
    total_count = len(base_obj_names) + len(links)

    # 1. Update Document Properties
    props = doc_root.find("Properties")
    for p in props.findall("Property"):
        pname = p.get("name")
        if pname == "Label":
            p.find("String").set("value", doc_label)
        elif pname == "Uid":
            p.find("Uuid").set("value", str(uuid.uuid4()))
        elif pname == "Tip":
            p.find("Link").set("value", "Assembly")
        elif pname == "TipName":
            p.find("String").set("value", "Assembly")

    # 2. Rebuild Objects (ObjectDeps + Object declarations)
    objects_elem = doc_root.find("Objects")
    
    new_deps = []
    for dep in objects_elem.findall("ObjectDeps"):
        dname = dep.get("Name")
        if dname == "Assembly":
            dep.clear()
            dep.attrib = {"Name": "Assembly", "Count": str(2 + len(links))}
            ET.SubElement(dep, "Dep", {"Name": "Origin"})
            ET.SubElement(dep, "Dep", {"Name": "Joints"})
            for lk in links:
                ET.SubElement(dep, "Dep", {"Name": lk["name"]})
            new_deps.append(dep)
        elif dname == "Joints":
            dep.clear()
            dep.attrib = {"Name": "Joints", "Count": "0"}
            new_deps.append(dep)
        elif dname in base_obj_names:
            new_deps.append(dep)

    for lk in links:
        new_deps.append(ET.Element("ObjectDeps", {"Name": lk["name"], "Count": "0"}))

    new_decls = []
    curr_id = 1
    for decl in objects_elem.findall("Object"):
        dname = decl.get("name")
        if dname in base_obj_names:
            decl.set("id", str(curr_id))
            curr_id += 1
            new_decls.append(decl)

    for lk in links:
        new_decls.append(ET.Element("Object", {"type": "App::Link", "name": lk["name"], "id": str(curr_id)}))
        curr_id += 1

    objects_elem.clear()
    objects_elem.attrib = {"Count": str(total_count), "Dependencies": "1"}
    for d in new_deps:
        objects_elem.append(d)
    for decl in new_decls:
        objects_elem.append(decl)

    # 3. Rebuild ObjectData
    odata_elem = doc_root.find("ObjectData")
    new_odata = []
    for obj in odata_elem.findall("Object"):
        oname = obj.get("name")
        if oname == "Assembly":
            grp = obj.find(".//Property[@name=\"Group\"]/LinkList")
            grp.clear()
            grp.attrib = {"count": str(1 + len(links))}
            ET.SubElement(grp, "Link", {"value": "Joints"})
            for lk in links:
                ET.SubElement(grp, "Link", {"value": lk["name"]})
            new_odata.append(obj)
        elif oname == "Joints":
            grp = obj.find(".//Property[@name=\"Group\"]/LinkList")
            grp.clear()
            grp.attrib = {"count": "0"}
            new_odata.append(obj)
        elif oname in base_obj_names:
            new_odata.append(obj)

    for i, lk in enumerate(links):
        lo = copy.deepcopy(base_link_obj)
        lo.set("name", lk["name"])
        lo.find(".//Property[@name=\"Label\"]/String").set("value", lk["label"])
        
        xlink = lo.find(".//Property[@name=\"LinkedObject\"]/XLink")
        xlink.attrib = {"file": lk["file"], "stamp": "", "name": lk["target_obj"]}
        
        px, py, pz, q0, q1, q2, q3 = lk["placement"]
        angle = 2.0 * math.acos(max(-1.0, min(1.0, q3)))
        s = math.sin(angle / 2.0)
        ox, oy, oz = (0.0, 0.0, 1.0) if abs(s) < 1e-9 else (q0 / s, q1 / s, q2 / s)
        
        pm = lo.find(".//Property[@name=\"Placement\"]/PropertyPlacement")
        pm.attrib = {
            "Px": f"{px:.16f}", "Py": f"{py:.16f}", "Pz": f"{pz:.16f}",
            "Q0": f"{q0:.16f}", "Q1": f"{q1:.16f}", "Q2": f"{q2:.16f}", "Q3": f"{q3:.16f}",
            "A": f"{angle:.16f}", "Ox": f"{ox:.16f}", "Oy": f"{oy:.16f}", "Oz": f"{oz:.16f}"
        }
        
        plist_file = f"PlacementList{i}" if i > 0 else "PlacementList"
        slist_file = f"ScaleList{i}" if i > 0 else "ScaleList"
        lo.find(".//Property[@name=\"PlacementList\"]/PlacementList").set("file", plist_file)
        lo.find(".//Property[@name=\"ScaleList\"]/VectorList").set("file", slist_file)
        new_odata.append(lo)

    odata_elem.clear()
    odata_elem.attrib = {"Count": str(total_count)}
    for o in new_odata:
        odata_elem.append(o)

    # 4. Rebuild GuiDocument.xml (ViewProviderData)
    vp_elem = gui_root.find("ViewProviderData")
    vp_map = {vp.get("name"): vp for vp in vp_elem.findall("ViewProvider")}
    
    new_vps = []
    # Add base ViewProviders in canonical order
    for bname in base_obj_names:
        if bname in vp_map:
            new_vps.append(vp_map[bname])

    # Add link ViewProviders
    for i, lk in enumerate(links):
        lvp = copy.deepcopy(base_link_vp)
        lvp.set("name", lk["name"])
        lvp.set("treeRank", str(curr_id + i))
        diffuse = lk.get("diffuse_color") or 1728052992
        sm = lvp.find(".//Property[@name=\"ShapeMaterial\"]/PropertyMaterial")
        if sm is not None:
            sm.set("diffuseColor", str(diffuse))
        new_vps.append(lvp)

    vp_elem.clear()
    vp_elem.attrib = {"Count": str(total_count)}
    for v in new_vps:
        vp_elem.append(v)

    # 5. Pack into .FCStd archive
    zero_list = b"\x00\x00\x00\x00"
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        zout.writestr("Document.xml", ET.tostring(doc_root, encoding="utf-8"))
        zout.writestr("GuiDocument.xml", ET.tostring(gui_root, encoding="utf-8"))
        for sname, sdata in shape_apps.items():
            zout.writestr(sname, sdata)
        for i in range(len(links)):
            plist_file = f"PlacementList{i}" if i > 0 else "PlacementList"
            slist_file = f"ScaleList{i}" if i > 0 else "ScaleList"
            zout.writestr(plist_file, zero_list)
            zout.writestr(slist_file, zero_list)

    print(f"Generated True Linked Assembly: {output_path} ({os.path.getsize(output_path)/1024:.1f} KB)")


def build_grip_hybrid_minijoy_assembly(repo_root):
    """
    Builds cad/grips/hybrid/assemblies/assembly_grip_hybrid_minijoy.FCStd.
    Incorporates full mechanical stack-up:
    - Base plate (Z = 0.0 to 4.0 mm)
    - 6x M5 hex standoffs (Z = 4.0 to 14.0 mm)
    - 3x TAL220 load cells in 120-degree triad (Z = 14.0 to 26.7 mm)
    - Top plate (Z = 26.7 to 30.7 mm)
    - Hybrid grip halves (Z = 70.7 mm)
    - Thumb plate and mini joystick breakout (Z = 181.7 mm)
    """
    out_fcstd = os.path.join(repo_root, "cad/grips/hybrid/assemblies/assembly_grip_hybrid_minijoy.FCStd")
    template_path = out_fcstd  # Use self as template

    qx = 0.6087614290087207
    qw = 0.7933533402912352

    # Color definitions (RGBA packed integer)
    COLOR_ALUMINUM = 3435973887    # Metallic aluminum silver (plates)
    COLOR_STEEL    = 2863311615    # Hex standoff steel/brass
    COLOR_LOADCELL = 1970637311    # Anodized aluminum load cell body
    COLOR_PLA_DARK = 842150655     # Dark charcoal / black PLA grip halves
    COLOR_PLA_GRAY = 2526451455    # Neutral gray PLA thumbplate
    COLOR_PCB_BLUE = 1728052992    # Blue sensor breakout PCB

    # Load cell and standoff geometric coordinates (120-degree triad)
    # Cell 0 (0 deg):
    #   Cell local center: (14.5, -6.35, 14.0)
    #   Standoffs at r=74.5 and r=89.5, Z=4.0
    # Cell 1 (120 deg):
    #   Cell local center rotated 120 deg: (-1.7507386859688108, 15.73236835487436, 14.0), Q=(0, 0, sin(60), cos(60))
    #   Standoffs at r=74.5 and r=89.5, 120 deg: (-37.25, 64.51889258194066, 4.0) and (-44.75, 77.50927363870723, 4.0)
    # Cell 2 (240 deg):
    #   Cell local center rotated 240 deg: (-12.74926131403119, -9.382368354874353, 14.0), Q=(0, 0, sin(120), -cos(120))
    #   Standoffs at r=74.5 and r=89.5, 240 deg: (-37.25, -64.51889258194066, 4.0) and (-44.75, -77.50927363870723, 4.0)

    sin60 = math.sqrt(3.0) / 2.0
    cos60 = 0.5

    links = [
        # 1. Base Disk Plate
        {
            "name": "BaseDisk",
            "label": "BaseDisk",
            "file": "../../../base_frame/frame_base_disk.FCStd",
            "target_obj": "BaseDisk",
            "placement": (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0),
            "diffuse_color": COLOR_ALUMINUM,
        },
        # 2-3. Standoffs Cell 0 (0 deg)
        {
            "name": "Standoff_Cell0_Inner",
            "label": "Standoff_Cell0_Inner",
            "file": "../../../base_frame/hardware_standoff_hex.FCStd",
            "target_obj": "Body",
            "placement": (74.5, 0.0, 4.0, 0.0, 0.0, 0.0, 1.0),
            "diffuse_color": COLOR_STEEL,
        },
        {
            "name": "Standoff_Cell0_Outer",
            "label": "Standoff_Cell0_Outer",
            "file": "../../../base_frame/hardware_standoff_hex.FCStd",
            "target_obj": "Body",
            "placement": (89.5, 0.0, 4.0, 0.0, 0.0, 0.0, 1.0),
            "diffuse_color": COLOR_STEEL,
        },
        # 4-5. Standoffs Cell 1 (120 deg)
        {
            "name": "Standoff_Cell1_Inner",
            "label": "Standoff_Cell1_Inner",
            "file": "../../../base_frame/hardware_standoff_hex.FCStd",
            "target_obj": "Body",
            "placement": (-37.25, 64.51889258194066, 4.0, 0.0, 0.0, 0.0, 1.0),
            "diffuse_color": COLOR_STEEL,
        },
        {
            "name": "Standoff_Cell1_Outer",
            "label": "Standoff_Cell1_Outer",
            "file": "../../../base_frame/hardware_standoff_hex.FCStd",
            "target_obj": "Body",
            "placement": (-44.75, 77.50927363870723, 4.0, 0.0, 0.0, 0.0, 1.0),
            "diffuse_color": COLOR_STEEL,
        },
        # 6-7. Standoffs Cell 2 (240 deg)
        {
            "name": "Standoff_Cell2_Inner",
            "label": "Standoff_Cell2_Inner",
            "file": "../../../base_frame/hardware_standoff_hex.FCStd",
            "target_obj": "Body",
            "placement": (-37.25, -64.51889258194066, 4.0, 0.0, 0.0, 0.0, 1.0),
            "diffuse_color": COLOR_STEEL,
        },
        {
            "name": "Standoff_Cell2_Outer",
            "label": "Standoff_Cell2_Outer",
            "file": "../../../base_frame/hardware_standoff_hex.FCStd",
            "target_obj": "Body",
            "placement": (-44.75, -77.50927363870723, 4.0, 0.0, 0.0, 0.0, 1.0),
            "diffuse_color": COLOR_STEEL,
        },
        # 8-10. TAL220 Load Cells (120 deg triad)
        {
            "name": "LoadCell_0",
            "label": "LoadCell_0",
            "file": "../../../base_frame/sensor_load_cell_tal220.FCStd",
            "target_obj": "Part__Feature",
            "placement": (14.5, -6.35, 14.0, 0.0, 0.0, 0.0, 1.0),
            "diffuse_color": COLOR_LOADCELL,
        },
        {
            "name": "LoadCell_1",
            "label": "LoadCell_1",
            "file": "../../../base_frame/sensor_load_cell_tal220.FCStd",
            "target_obj": "Part__Feature",
            "placement": (-1.7507386859688108, 15.73236835487436, 14.0, 0.0, 0.0, sin60, cos60),
            "diffuse_color": COLOR_LOADCELL,
        },
        {
            "name": "LoadCell_2",
            "label": "LoadCell_2",
            "file": "../../../base_frame/sensor_load_cell_tal220.FCStd",
            "target_obj": "Part__Feature",
            "placement": (-12.74926131403119, -9.382368354874353, 14.0, 0.0, 0.0, sin60, -cos60),
            "diffuse_color": COLOR_LOADCELL,
        },
        # 11. Top Plate (rests on top of load cells at Z = 26.7 mm)
        {
            "name": "TopPlate",
            "label": "TopPlate",
            "file": "../../../base_frame/frame_top_plate.FCStd",
            "target_obj": "TopPlate",
            "placement": (0.0, 0.0, 26.7, 0.0, 0.0, 0.0, 1.0),
            "diffuse_color": COLOR_ALUMINUM,
        },
        # 12-13. Grip Body Halves (44 mm above top plate bottom -> Z = 70.7 mm)
        {
            "name": "GripHybrid_Half_A",
            "label": "GripHybrid_Half_A",
            "file": "../models/grip_hybrid_body_half_a.FCStd",
            "target_obj": "GripHybrid_Half_A",
            "placement": (0.0, 0.0, 70.7, 0.0, 0.0, 0.0, 1.0),
            "diffuse_color": COLOR_PLA_DARK,
        },
        {
            "name": "GripHybrid_Half_B",
            "label": "GripHybrid_Half_B",
            "file": "../models/grip_hybrid_body_half_b.FCStd",
            "target_obj": "GripHybrid_Half_B",
            "placement": (0.0, 0.0, 70.7, 0.0, 0.0, 0.0, 1.0),
            "diffuse_color": COLOR_PLA_DARK,
        },
        # 14. Thumb Plate Joystick
        {
            "name": "ThumbPlate_Joystick",
            "label": "ThumbPlate_Joystick",
            "file": "../models/thumbplate_minijoy.FCStd",
            "target_obj": "ThumbPlate_Joystick",
            "placement": (0.0, -9.30, 181.7, qx, 0.0, 0.0, qw),
            "diffuse_color": COLOR_PLA_GRAY,
        },
        # 15. Mini Joystick Breakout PCB
        {
            "name": "Mini_Joystick_Breakout",
            "label": "Mini_Joystick_Breakout",
            "file": "../../../base_frame/sensor_mini_joystick_breakout.FCStd",
            "target_obj": "Analog_2_axis_Joystick_512_v5",
            "placement": (-15.98, 3.8495321897864549, 178.2283572779201506, qx, 0.0, 0.0, qw),
            "diffuse_color": COLOR_PCB_BLUE,
        },
    ]

    create_linked_assembly(template_path, out_fcstd, "assembly_grip_hybrid_minijoy", links)


def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
    print("=" * 65)
    print("  BUILDING COMPLETE LINKED HYBRID GRIP ASSEMBLY (FreeCAD 1.0 App::Link)")
    print("=" * 65)
    build_grip_hybrid_minijoy_assembly(repo_root)
    print("Done!")

if __name__ == "__main__":
    main()
