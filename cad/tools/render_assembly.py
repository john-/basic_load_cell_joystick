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

    color_map = {
        "BaseDisk": (0.75, 0.76, 0.78),           # Brushed aluminum base plate
        "TopPlate": (0.75, 0.76, 0.78),           # Brushed aluminum top plate
        "Standoff": (0.85, 0.72, 0.35),           # Brass / hex standoffs
        "LoadCell": (0.58, 0.62, 0.66),           # Anodized aluminum load cells
        "GripHybrid_Half_A": (0.34, 0.35, 0.37),  # Medium charcoal gray PLA (shows contours & seam)
        "GripHybrid_Half_B": (0.38, 0.39, 0.41),  # Slightly lighter contrasting half
        "ThumbPlate_Joystick": (0.52, 0.54, 0.56),# Neutral slate gray PLA thumbplate
        "Mini_Joystick": (0.12, 0.42, 0.82),      # Blue breakout PCB
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

        color = (0.7, 0.7, 0.7)
        for key, c in color_map.items():
            if key in basename:
                color = c
                break

        actor.GetProperty().SetColor(*color)
        actor.GetProperty().SetAmbient(0.25)
        actor.GetProperty().SetDiffuse(0.75)
        actor.GetProperty().SetSpecular(0.25)
        actor.GetProperty().SetSpecularPower(25.0)
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
