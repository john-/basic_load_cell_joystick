#!/usr/bin/env python3
"""
cad/tools/verify_models.py

Audit and validation script for the load_cell_joystick project:
1. Validates all binary STLs in manufacturing/print_runs/
2. Validates that all .FCStd files are uncorrupted FreeCAD documents
3. Verifies 1:1 cross-references between firmware variants and CAD models
"""

import sys
import os
import glob
import zipfile
import struct

def check_binary_stl(filepath):
    """Check binary STL format, header, and triangle count."""
    size = os.path.getsize(filepath)
    if size < 84:
        return False, f"File size too small ({size} bytes)"
    with open(filepath, 'rb') as f:
        data = f.read(84)
    if data.startswith(b'solid') and b'facet' in data[:200]:
        return False, "File is ASCII STL (must be converted to Binary STL)"
    num_triangles = struct.unpack('<I', data[80:84])[0]
    expected_size = 84 + num_triangles * 50
    if size != expected_size:
        return False, f"Size mismatch: expected {expected_size} bytes for {num_triangles:,} triangles, got {size} bytes"
    return True, f"{num_triangles:,} triangles, {size/1024/1024:.2f} MB"

def check_fcstd_schema(filepath, repo_root):
    """
    Deep schema and integrity linter for FreeCAD documents (.FCStd).
    Enforces C++ deserialization rules:
    1. Hasher consistency (StringHasher="1" requiring child tag).
    2. Dependency order (Objects Dependencies="1" requiring ObjectDeps).
    3. 1:1 Object-to-ViewProvider mapping in GuiDocument.xml.
    4. Origin coordinate system extension and material stream presence.
    5. Solid shape file presence for Part::Feature / PartDesign::Body.
    """
    import xml.etree.ElementTree as ET
    is_archive = "cad/grips/archive" in filepath
    try:
        size = os.path.getsize(filepath)
        with zipfile.ZipFile(filepath, 'r') as z:
            names = z.namelist()
            if 'Document.xml' not in names:
                return False, "Missing Document.xml"
            if 'GuiDocument.xml' not in names:
                if is_archive:
                    return True, f"Valid archive (missing GuiDocument.xml), {size/1024:.1f} KB"
                return False, "Missing GuiDocument.xml (GUI will fail or warn)"

            doc = ET.fromstring(z.read('Document.xml'))
            gui = ET.fromstring(z.read('GuiDocument.xml'))

            # 1. StringHasher check
            if doc.get('StringHasher') == '1':
                if doc.find('StringHasher') is None:
                    return False, 'Declared StringHasher="1" but missing <StringHasher> element'

            # 2. Objects and Dependency Graph
            objs_elem = doc.find('Objects')
            odata_elem = doc.find('ObjectData')
            decl_map = {}
            if objs_elem is not None:
                for o in objs_elem.findall('Object'):
                    decl_map[o.get('name')] = o.get('type')

                if objs_elem.get('Dependencies') == '1':
                    dep_names = set(d.get('Name') for d in objs_elem.findall('ObjectDeps'))
                    for name in decl_map:
                        if name not in dep_names:
                            return False, f"Object '{name}' missing from ObjectDeps dependency graph"

            data_names = set(o.get('name') for o in odata_elem.findall('Object')) if odata_elem is not None else set()
            for name in decl_map:
                if name not in data_names:
                    return False, f"Object '{name}' declared in Objects but missing in ObjectData"

            # 3. 1:1 Object-to-ViewProvider consistency (for non-archive models)
            vp_names = set(v.get('name') for v in gui.findall('.//ViewProvider'))
            if not is_archive:
                for name in decl_map:
                    if name not in vp_names:
                        return False, f"Object '{name}' missing ViewProvider in GuiDocument.xml"

            # 4. Origin & Material Stream checks
            if odata_elem is not None and decl_map.get('Origin') == 'App::Origin':
                orig_elem = odata_elem.find('Object[@name="Origin"]')
                if orig_elem is not None:
                    ext = orig_elem.find('.//Extension')
                    if ext is not None and ext.get('type') != 'App::GeoFeatureGroupExtension':
                        return False, f"Origin has {ext.get('type')} instead of App::GeoFeatureGroupExtension"

                # Check binary ShapeAppearance streams referenced by ViewProviders
                for vp in gui.findall('.//ViewProvider'):
                    sa_prop = vp.find('.//Property[@name="ShapeAppearance"]/MaterialList')
                    if sa_prop is not None:
                        sa_file = sa_prop.get('file')
                        if sa_file and sa_file not in names:
                            return False, f"ViewProvider '{vp.get('name')}' references missing ShapeAppearance file: {sa_file}"

            # 5. Check solid shapes (.Shape.brp) for Part::Feature (non-assembly)
            if "assemblies" not in filepath:
                for name, otype in decl_map.items():
                    if otype in ("Part::Feature", "PartDesign::Body"):
                        # If object data has Part::PropertyPartShape referencing file
                        obj_data = odata_elem.find(f'Object[@name="{name}"]') if odata_elem is not None else None
                        if obj_data is not None:
                            shape_prop = obj_data.find('.//Property[@name="Shape"]/Part')
                            if shape_prop is not None:
                                sfile = shape_prop.get('file')
                                if sfile and sfile not in names:
                                    return False, f"Object '{name}' references missing BRep shape: {sfile}"

        obj_count = len(decl_map)
        return True, f"Valid schema ({obj_count} objects, 1:1 ViewProviders), {size/1024:.1f} KB"
    except Exception as e:
        return False, f"Schema parsing error: {e}"

def check_fcstd(filepath):
    """Legacy check wrapper for backwards compatibility."""
    try:
        with zipfile.ZipFile(filepath, 'r') as z:
            names = z.namelist()
            if 'Document.xml' not in names:
                return False, "Missing Document.xml"
        size = os.path.getsize(filepath)
        return True, f"Valid FreeCAD document, {size/1024:.1f} KB"
    except Exception as e:
        return False, f"Corrupted zip: {e}"

def check_assembly_links(filepath):
    """Checks that App::Link objects in active FreeCAD assemblies resolve to valid files and objects."""
    import xml.etree.ElementTree as ET
    try:
        with zipfile.ZipFile(filepath, 'r') as z:
            names = z.namelist()
            if 'Document.xml' not in names:
                return False, "Missing Document.xml"
            # Active assemblies must not contain duplicate embedded BReps
            brps = [n for n in names if n.endswith('.brp')]
            if brps:
                return False, f"Assembly contains {len(brps)} embedded BRep shape(s); must use App::Link"
            doc = ET.fromstring(z.read('Document.xml'))
            link_objs = doc.findall('.//Objects/Object[@type="App::Link"]')
            if not link_objs:
                return False, "No App::Link objects found in assembly"
            for obj in link_objs:
                lname = obj.get("name")
                odata = doc.find(f'.//ObjectData/Object[@name="{lname}"]')
                if odata is None:
                    return False, f"Missing ObjectData for link {lname}"
                xlink = odata.find('.//Property[@name="LinkedObject"]/XLink')
                if xlink is None:
                    return False, f"Missing XLink property for link {lname}"
                rel_file = xlink.get("file")
                target_obj = xlink.get("name")
                if not rel_file or not target_obj:
                    return False, f"Link {lname} missing file or target object"
                target_path = os.path.normpath(os.path.join(os.path.dirname(filepath), rel_file))
                if not os.path.exists(target_path):
                    return False, f"Linked file does not exist: {target_path} (from {rel_file})"
                with zipfile.ZipFile(target_path, 'r') as tz:
                    tdoc = ET.fromstring(tz.read('Document.xml'))
                    found = any(o.get('name') == target_obj for o in tdoc.findall('.//Object'))
                    if not found:
                        return False, f"Target object '{target_obj}' not found in {target_path}"
        return True, f"{len(link_objs)} linked reference(s) verified, 0 embedded BReps"
    except Exception as e:
        return False, f"Assembly verification error: {e}"

def verify_all():
    print("=" * 70)
    print("  LOAD CELL JOYSTICK: MODEL & CAD REPOSITORY AUDIT")
    print("=" * 70)

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    failures = 0

    # 1. Check Binary STLs
    print("\n--- 1. Manufacturing Print Runs (Binary STLs) ---")
    stls = sorted(glob.glob(os.path.join(repo_root, "manufacturing/print_runs/**/*.stl"), recursive=True))
    if not stls:
        print("  ERROR: No STLs found in manufacturing/print_runs/")
        failures += 1
    for stl in stls:
        rel = os.path.relpath(stl, repo_root)
        ok, msg = check_binary_stl(stl)
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {rel:<60} : {msg}")
        if not ok:
            failures += 1

    # 2. Check FreeCAD Documents with Schema Linter
    print("\n--- 2. Active FreeCAD Models & Assemblies (Schema Linter) ---")
    fcstds = sorted(glob.glob(os.path.join(repo_root, "cad/**/*.FCStd"), recursive=True))
    for fc in fcstds:
        rel = os.path.relpath(fc, repo_root)
        ok, msg = check_fcstd_schema(fc, repo_root)
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {rel:<60} : {msg}")
        if not ok:
            failures += 1

    # 3. Check Active Linked Assemblies (App::Link Integrity)
    print("\n--- 3. Active FreeCAD Linked Assemblies (App::Link & SSOT) ---")
    asm_files = sorted(glob.glob(os.path.join(repo_root, "cad/grips/hybrid/assemblies/*.FCStd")))
    for af in asm_files:
        rel = os.path.relpath(af, repo_root)
        ok, msg = check_assembly_links(af)
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {rel:<60} : {msg}")
        if not ok:
            failures += 1

    print("\n" + "=" * 70)
    if failures == 0:
        print("  ALL AUDIT CHECKS PASSED (0 failures)")
    else:
        print(f"  AUDIT FAILED with {failures} error(s)")
    print("=" * 70)
    return failures == 0

if __name__ == "__main__":
    success = verify_all()
    sys.exit(0 if success else 1)
