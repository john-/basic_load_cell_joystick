#!/usr/bin/env python3
"""
cad/tools/render_assembly.py

Headless 3D rendering pipeline for the complete joystick assembly:
1. Opens cad/grips/hybrid/assemblies/assembly_grip_hybrid_minijoy.FCStd
2. Converts linked part shapes into positioned triangle meshes
3. Uses VTK to render a high-resolution anti-aliased upright isometric view
4. Exports single hero image to docs/images/assembly_isometric.png
"""

import os
import sys
import tempfile
import subprocess
import glob

def export_part_meshes(repo_root, tmp_dir):
    """Uses FreeCAD to extract individual positioned meshes for all assembly links."""
    fc_script = f"""
import FreeCAD as App
import MeshPart

doc = App.openDocument('{repo_root}/cad/grips/hybrid/assemblies/assembly_grip_hybrid_minijoy.FCStd')
links = [o for o in doc.Objects if o.TypeId == 'App::Link']

for lk in links:
    if hasattr(lk, 'Shape') and lk.Shape:
        sh = lk.Shape.copy()
        sh.Placement = lk.Placement
        mesh = MeshPart.meshFromShape(Shape=sh, LinearDeflection=0.08, AngularDeflection=0.15)
        out_path = '{tmp_dir}/part_' + lk.Name + '.stl'
        mesh.write(out_path)
"""
    cmd = [
        "flatpak", "run",
        "--filesystem=/net/penter",
        "--filesystem=/tmp",
        "--command=freecadcmd",
        "org.freecad.FreeCAD",
        "-c", fc_script
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print("FreeCAD export failed:", res.stderr)
        sys.exit(1)


def render_upright_isometric(tmp_dir, output_dir):
    """Uses VTK to render a strictly upright isometric perspective."""
    import vtk

    # Material and color properties for high visual fidelity
    material_map = {
        "BaseDisk": {
            "color": (0.75, 0.76, 0.78),
            "ambient": 0.25, "diffuse": 0.75, "specular": 0.35, "specular_power": 30.0
        },
        "TopPlate": {
            "color": (0.75, 0.76, 0.78),
            "ambient": 0.25, "diffuse": 0.75, "specular": 0.35, "specular_power": 30.0
        },
        "Standoff": {
            "color": (0.85, 0.72, 0.35),
            "ambient": 0.30, "diffuse": 0.70, "specular": 0.60, "specular_power": 45.0
        },
        "LoadCell": {
            "color": (0.58, 0.62, 0.66),
            "ambient": 0.25, "diffuse": 0.75, "specular": 0.30, "specular_power": 25.0
        },
        "GripHybrid_Half_A": {
            "color": (0.32, 0.33, 0.35),
            "ambient": 0.25, "diffuse": 0.75, "specular": 0.15, "specular_power": 15.0
        },
        "GripHybrid_Half_B": {
            "color": (0.36, 0.37, 0.39),
            "ambient": 0.25, "diffuse": 0.75, "specular": 0.15, "specular_power": 15.0
        },
        "ThumbPlate_Joystick": {
            "color": (0.50, 0.52, 0.54),
            "ambient": 0.25, "diffuse": 0.75, "specular": 0.20, "specular_power": 20.0
        },
        "Mini_Joystick_Cap": {
            # Soft-touch matte black / charcoal silicone thumbstick cap with low specular
            "color": (0.16, 0.16, 0.17),
            "ambient": 0.20, "diffuse": 0.80, "specular": 0.10, "specular_power": 10.0
        },
        "Mini_Joystick_Breakout": {
            # Adafruit STEMMA blue PCB
            "color": (0.10, 0.45, 0.85),
            "ambient": 0.25, "diffuse": 0.75, "specular": 0.25, "specular_power": 25.0
        },
        "Button_": {
            # Polished chrome / stainless steel metal pushbutton with high specular reflection
            "color": (0.88, 0.89, 0.92),
            "ambient": 0.20, "diffuse": 0.65, "specular": 0.85, "specular_power": 75.0
        },
    }

    stl_files = sorted(glob.glob(os.path.join(tmp_dir, "part_*.stl")))
    if not stl_files:
        print("No part meshes found to render!")
        sys.exit(1)

    renderer = vtk.vtkRenderer()
    renderer.SetBackground(0.96, 0.96, 0.98) # Clean high-contrast soft gray

    for stl in stl_files:
        basename = os.path.basename(stl)[5:-4]
        reader = vtk.vtkSTLReader()
        reader.SetFileName(stl)

        normals = vtk.vtkPolyDataNormals()
        normals.SetInputConnection(reader.GetOutputPort())
        normals.ComputePointNormalsOn()
        normals.ComputeCellNormalsOff()
        normals.SetFeatureAngle(60.0)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(normals.GetOutputPort())

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)

        # Match exact material entry
        mat = {
            "color": (0.7, 0.7, 0.7),
            "ambient": 0.25, "diffuse": 0.75, "specular": 0.25, "specular_power": 25.0
        }
        for key, m in material_map.items():
            if key in basename:
                mat = m
                break

        actor.GetProperty().SetColor(*mat["color"])
        actor.GetProperty().SetAmbient(mat["ambient"])
        actor.GetProperty().SetDiffuse(mat["diffuse"])
        actor.GetProperty().SetSpecular(mat["specular"])
        actor.GetProperty().SetSpecularPower(mat["specular_power"])
        renderer.AddActor(actor)

    renderWindow = vtk.vtkRenderWindow()
    renderWindow.SetOffScreenRendering(1)
    renderWindow.AddRenderer(renderer)
    renderWindow.SetSize(1600, 1200)

    # Set up camera strictly upright with FreeCAD Z as vertical UP
    camera = renderer.GetActiveCamera()
    camera.SetFocalPoint(0.0, 0.0, 88.0)
    camera.SetPosition(390.0, -390.0, 275.0)
    camera.SetViewUp(0.0, 0.0, 1.0) # Strictly upright
    renderer.ResetCameraClippingRange()

    renderWindow.Render()

    windowToImageFilter = vtk.vtkWindowToImageFilter()
    windowToImageFilter.SetInput(renderWindow)
    windowToImageFilter.Update()

    out_path = os.path.join(output_dir, "assembly_isometric.png")
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(out_path)
    writer.SetInputConnection(windowToImageFilter.GetOutputPort())
    writer.Write()
    print(f"  Rendered upright isometric view: {out_path} ({os.path.getsize(out_path)/1024:.1f} KB)")

    # 3. Close-up view of Grip Head & Thumbplate Controls
    camera.SetFocalPoint(3.0, 10.0, 195.0)
    camera.SetPosition(90.0, -90.0, 270.0)
    camera.SetViewUp(0.0, 0.0, 1.0)
    renderer.ResetCameraClippingRange()

    renderWindow.Render()

    windowToImageFilter2 = vtk.vtkWindowToImageFilter()
    windowToImageFilter2.SetInput(renderWindow)
    windowToImageFilter2.Update()

    detail_path = os.path.join(output_dir, "assembly_head_detail.png")
    writer.SetFileName(detail_path)
    writer.SetInputConnection(windowToImageFilter2.GetOutputPort())
    writer.Write()
    print(f"  Rendered head controls detail view: {detail_path} ({os.path.getsize(detail_path)/1024:.1f} KB)")

    # 4. Rear-quarter isometric view highlighting trigger button on Half A
    # Trigger is at X=12.58, Y=8.82, Z=146.7 pointing radially outward toward (+X, +Y).
    # Viewing from rear quarter (+X, +Y, +Z)
    camera.SetFocalPoint(0.0, 0.0, 110.0)
    camera.SetPosition(380.0, 360.0, 240.0)
    camera.SetViewUp(0.0, 0.0, 1.0)
    renderer.ResetCameraClippingRange()

    renderWindow.Render()

    windowToImageFilter3 = vtk.vtkWindowToImageFilter()
    windowToImageFilter3.SetInput(renderWindow)
    windowToImageFilter3.Update()

    rear_path = os.path.join(output_dir, "assembly_rear_isometric.png")
    writer.SetFileName(rear_path)
    writer.SetInputConnection(windowToImageFilter3.GetOutputPort())
    writer.Write()
    print(f"  Rendered rear-quarter isometric view: {rear_path} ({os.path.getsize(rear_path)/1024:.1f} KB)")


def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    output_dir = os.path.join(repo_root, "docs/images")
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 65)
    print("  RENDERING UPRIGHT ISOMETRIC ASSEMBLY VIEW (FreeCAD + VTK)")
    print("=" * 65)

    with tempfile.TemporaryDirectory() as tmp_dir:
        print("1. Extracting positioned component meshes from FreeCAD assembly...")
        export_part_meshes(repo_root, tmp_dir)
        print("2. Rendering upright isometric perspective via VTK...")
        render_upright_isometric(tmp_dir, output_dir)

    print("Rendering complete!")

if __name__ == "__main__":
    main()
