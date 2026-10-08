#!/usr/bin/env python3
"""Parametric models of the assembly tools for BRK-100 Motor Bracket Assembly.

Tools modelled (purchased tools such as the TW-101 torque wrench are not modelled):
    FX-201  Locating Fixture        - nests bracket BRK-100 on two dowel pins
    PT-301  Bushing Press Punch     - presses bushing BU-12 into the bracket bore
    GA-401  Go/No-Go Pin Gauge      - checks the bushing bore after pressing

Change any value in the PARAMETERS section and run:
    pip install cadquery
    python tool_models.py            # writes the .step files next to this script

All dimensions are in millimetres.
"""

import os

import cadquery as cq

# ============================================================== PARAMETERS

FX201 = {
    "plate_length": 150.0,       # X
    "plate_width": 100.0,        # Y
    "plate_thickness": 20.0,     # Z
    "corner_radius": 5.0,
    "pocket_length": 62.0,       # nest for bracket BRK-100 (60 x 40 part + 1 mm clearance per side)
    "pocket_width": 42.0,
    "pocket_depth": 5.0,
    "pocket_corner_radius": 3.0,
    "dowel_diameter": 8.0,       # locating dowel pins, h6
    "dowel_height": 12.0,        # above pocket floor
    "dowel_spacing": 44.0,       # centre-to-centre along X
    "mount_hole_diameter": 6.6,  # M6 clearance
    "mount_cbore_diameter": 11.0,
    "mount_cbore_depth": 6.5,
    "mount_hole_inset": 12.0,    # from plate edges
    "relief_slot_width": 16.0,   # finger slots to lift the part out
    "relief_slot_length": 10.0,  # how far each slot reaches beyond the pocket
    "edge_chamfer": 1.0,
}

PT301 = {
    "shank_diameter": 20.0,      # fits arbor press ram
    "shank_length": 60.0,
    "shoulder_diameter": 30.0,   # pushes on bushing flange
    "shoulder_length": 10.0,
    "pilot_diameter": 10.02,     # guides bushing BU-12 (bore 10.00 +0.05)
    "pilot_length": 12.0,
    "pilot_chamfer": 1.0,
    "shank_chamfer": 1.5,
    "grip_flat_depth": 2.0,      # two flats on the shank for a spanner / anti-rotation
    "grip_flat_length": 25.0,
}

GA401 = {
    "handle_diameter": 16.0,
    "handle_length": 70.0,
    "go_diameter": 10.00,        # GO end must enter the bore
    "nogo_diameter": 10.05,      # NO-GO end must NOT enter
    "go_length": 20.0,
    "nogo_length": 10.0,         # NO-GO is shorter so the ends are told apart by eye
    "neck_diameter": 8.0,
    "neck_length": 4.0,
    "groove_depth": 0.8,         # identification groove near the NO-GO end
    "groove_width": 2.0,
    "end_chamfer": 0.5,
}

# ============================================================== MODELS


def make_fx201(p=FX201):
    L, W, T = p["plate_length"], p["plate_width"], p["plate_thickness"]
    plate = (
        cq.Workplane("XY").box(L, W, T).translate((0, 0, T / 2))
        .edges("|Z").fillet(p["corner_radius"])
    )
    # nest pocket for the bracket
    plate = (
        plate.faces(">Z").workplane()
        .rect(p["pocket_length"], p["pocket_width"]).cutBlind(-p["pocket_depth"])
    )
    plate = plate.edges("|Z").edges(cq.selectors.BoxSelector(
        (-p["pocket_length"], -p["pocket_width"], 0), (p["pocket_length"], p["pocket_width"], T))
    ).fillet(p["pocket_corner_radius"])
    # finger relief slots on both long sides of the pocket
    slot_len = p["relief_slot_length"] + 1.0  # 1 mm overlap into the pocket
    for side in (1, -1):
        slot = (
            cq.Workplane("XY")
            .box(p["relief_slot_width"], slot_len, p["pocket_depth"])
            .translate((0, side * (p["pocket_width"] / 2 + slot_len / 2 - 1.0), T - p["pocket_depth"] / 2))
        )
        plate = plate.cut(slot)
    # counterbored M6 mounting holes in the corners
    dx, dy = L / 2 - p["mount_hole_inset"], W / 2 - p["mount_hole_inset"]
    plate = (
        plate.faces(">Z").workplane(origin=(0, 0, T))
        .pushPoints([(dx, dy), (-dx, dy), (dx, -dy), (-dx, -dy)])
        .cboreHole(p["mount_hole_diameter"], p["mount_cbore_diameter"], p["mount_cbore_depth"])
    )
    plate = plate.faces(">Z or <Z").edges("not(%CIRCLE)").chamfer(p["edge_chamfer"])

    floor = T - p["pocket_depth"]
    pins = (
        cq.Workplane("XY", origin=(0, 0, floor - 8.0))  # pressed 8 mm into the plate
        .pushPoints([(-p["dowel_spacing"] / 2, 0), (p["dowel_spacing"] / 2, 0)])
        .circle(p["dowel_diameter"] / 2).extrude(8.0 + p["dowel_height"])
        .faces(">Z").edges().chamfer(0.5)
    )
    plate = plate.cut(pins)

    assy = cq.Assembly(name="FX-201 Locating Fixture")
    assy.add(plate, name="FX-201-01 Base Plate", color=cq.Color(0.55, 0.6, 0.65))
    assy.add(pins, name="FX-201-02 Dowel Pin D8 h6 (2x)", color=cq.Color(0.85, 0.75, 0.3))
    return assy


def make_pt301(p=PT301):
    shank = (
        cq.Workplane("XY").circle(p["shank_diameter"] / 2).extrude(p["shank_length"])
        .faces(">Z").edges().chamfer(p["shank_chamfer"])
    )
    # two spanner flats on the shank
    r = p["shank_diameter"] / 2
    for side in (1, -1):
        cutter = (
            cq.Workplane("XY")
            .box(p["grip_flat_depth"] * 2, p["shank_diameter"] * 2, p["grip_flat_length"])
            .translate((side * r, 0, p["shank_length"] - 10.0 - p["grip_flat_length"] / 2))
        )
        shank = shank.cut(cutter)
    shoulder = (
        cq.Workplane("XY").circle(p["shoulder_diameter"] / 2).extrude(-p["shoulder_length"])
        .faces("<Z").edges().chamfer(0.5)
    )
    pilot = (
        cq.Workplane("XY", origin=(0, 0, -p["shoulder_length"]))
        .circle(p["pilot_diameter"] / 2).extrude(-p["pilot_length"])
        .faces("<Z").edges().chamfer(p["pilot_chamfer"])
    )
    punch = shank.union(shoulder).union(pilot)
    assy = cq.Assembly(name="PT-301 Bushing Press Punch")
    assy.add(punch, name="PT-301-01 Punch Body (tool steel, hardened 58-62 HRC)",
             color=cq.Color(0.45, 0.47, 0.5))
    return assy


def make_ga401(p=GA401):
    hl = p["handle_length"]
    handle = (cq.Workplane("XY").circle(p["handle_diameter"] / 2).extrude(hl)
              .faces(">Z or <Z").edges().chamfer(0.8))
    # identification groove near the NO-GO end
    groove = (
        cq.Workplane("XY", origin=(0, 0, hl - 8.0))
        .circle(p["handle_diameter"] / 2 + 1).circle(p["handle_diameter"] / 2 - p["groove_depth"])
        .extrude(p["groove_width"])
    )
    handle = handle.cut(groove)

    def end(diameter, length, at_top):
        sign = 1 if at_top else -1
        base = hl if at_top else 0.0
        neck = (cq.Workplane("XY", origin=(0, 0, base))
                .circle(p["neck_diameter"] / 2).extrude(sign * p["neck_length"]))
        pin = (cq.Workplane("XY", origin=(0, 0, base + sign * p["neck_length"]))
               .circle(diameter / 2).extrude(sign * length))
        pin = pin.faces(">Z" if at_top else "<Z").edges().chamfer(p["end_chamfer"])
        return neck.union(pin)

    go = end(p["go_diameter"], p["go_length"], at_top=False)
    nogo = end(p["nogo_diameter"], p["nogo_length"], at_top=True)
    assy = cq.Assembly(name="GA-401 Go/No-Go Pin Gauge")
    assy.add(handle, name="GA-401-01 Handle", color=cq.Color(0.2, 0.35, 0.6))
    assy.add(go, name="GA-401-02 GO Pin D10.00", color=cq.Color(0.2, 0.6, 0.3))
    assy.add(nogo, name="GA-401-03 NO-GO Pin D10.05", color=cq.Color(0.75, 0.2, 0.2))
    return assy


TOOLS = {
    "FX-201_Locating_Fixture.step": make_fx201,
    "PT-301_Bushing_Press_Punch.step": make_pt301,
    "GA-401_Go_No-Go_Pin_Gauge.step": make_ga401,
}


def main(out_dir=None):
    out_dir = out_dir or os.path.dirname(os.path.abspath(__file__))
    for filename, build in TOOLS.items():
        path = os.path.join(out_dir, filename)
        build().export(path)
        print("wrote", path)


if __name__ == "__main__":
    main()
