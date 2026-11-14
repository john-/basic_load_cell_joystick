import sys, os
import FreeCAD as App, Part, math

doc_a = App.openDocument('cad/grips/hybrid/models/grip_hybrid_body_half_a.FCStd')
doc_b = App.openDocument('cad/grips/hybrid/models/grip_hybrid_body_half_b.FCStd')
sh_a = doc_a.GripHybrid_Half_A.Shape
sh_b = doc_b.GripHybrid_Half_B.Shape

# Clamshell screws
screws = [
    ('Base clamp', 11.0, -30.0, 4.0),
    ('Lower stalk clamp', 16.5, -8.0, 5.2),
    ('Palm swell upper-mid', 11.0, 40.0, 4.0),
    ('Upper neck clamp (back)', 11.0, 95.0, 4.0),
    ('Upper neck clamp (front)', -11.0, 95.0, 4.0),
]

print("=== CLAMSHELL SCREWS ===")
for name, yc, zc, xs in screws:
    # Test ray along +X for Half A:
    # Origin at X=0, Y=yc, Z=zc
    # Find outer surface of Half A:
    line_a = Part.makeLine(App.Vector(0, yc, zc), App.Vector(50, yc, zc))
    pts_a = sh_a.section(line_a).Vertexes
    x_outer_a = max([p.Point.x for p in pts_a]) if pts_a else None

    line_b = Part.makeLine(App.Vector(0, yc, zc), App.Vector(-50, yc, zc))
    pts_b = sh_b.section(line_b).Vertexes
    x_outer_b = min([p.Point.x for p in pts_b]) if pts_b else None

    cb_seat_x = xs
    nut_seat_x = -xs
    clamped_thickness = cb_seat_x - nut_seat_x # 2 * xs

    print(f"\n{name} at Y={yc:.1f}, Z={zc:.1f}:")
    print(f"  Counterbore seat on Half A: X = +{cb_seat_x:.1f} mm")
    print(f"  Captive nut seat on Half B:  X = {nut_seat_x:.1f} mm")
    print(f"  Clamped solid thickness:    {clamped_thickness:.1f} mm")
    if x_outer_a:
        cb_depth = x_outer_a - cb_seat_x
        print(f"  Half A exterior skin:       X = +{x_outer_a:.2f} mm (counterbore depth = {cb_depth:.2f} mm)")
    if x_outer_b:
        pocket_depth = abs(x_outer_b) - xs
        print(f"  Half B exterior skin:       X = {x_outer_b:.2f} mm (nut pocket depth = {pocket_depth:.2f} mm)")

