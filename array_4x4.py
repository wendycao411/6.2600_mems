from phidl import Device
import phidl.geometry as pg
import mems_parameter_sweep_layout as base

def build_sweep_layout(electrode_width, suffix):
    """Build one full sweep layout with a specified electrode width."""
    mc = base.build_parameter_object()
    mc.cant_electrode_height = electrode_width
    mc.cc_electrode_height = electrode_width

    master = Device(f"mems_parameter_sweep_{suffix}")

    # Calculate internal dimensions
    row_count = len(mc.widths) * len(mc.gaps)
    section_width = mc.grid_origin_x + len(mc.lengths) * mc.cell_pitch_x

    cant_origin = (mc.master_margin, mc.master_margin + 200)
    cc_origin = (
        cant_origin[0] + section_width + mc.family_gap_x,
        cant_origin[1],
    )

    # Add section labels
    base.add_section_label(master, f"Cantilever Sweep ({electrode_width} um elec.)",
                           (cant_origin[0], mc.master_margin), mc.section_label_size)
    base.add_section_label(master, f"Clamped-Clamped Sweep ({electrode_width} um elec.)",
                           (cc_origin[0], mc.master_margin), mc.section_label_size)

    # Place grids and internal crosses
    base.place_parameter_grid(master, cant_origin, mc.lengths, mc.widths, mc.gaps,
                              base.cantilever_cell, f"cantilever_section_{suffix}", mc)
    base.place_section_crosses(master, cant_origin, len(mc.lengths), row_count,
                               mc.cant_unit_width, mc.cant_unit_height, mc)

    base.place_parameter_grid(master, cc_origin, mc.lengths, mc.widths, mc.gaps,
                              base.clamped_clamped_cell, f"clamped_clamped_section_{suffix}", mc)
    base.place_section_crosses(master, cc_origin, len(mc.lengths), row_count,
                               mc.cc_unit_width, mc.cc_unit_height, mc)

    # Footer label
    tile_label = master << pg.text(text=f"Electrode Width = {electrode_width} um",
                                   size=90, layer=3, font="Arial")
    tile_label.move((mc.master_margin, mc.master_margin + 80))
    master.move((-master.center[0], -master.center[1]))
    return master

def make_array_4x4():
    """Create a 4x4 array with alignment crosses centered in the streets."""
    # 1. Setup tiles
    default_tile = build_sweep_layout(10, "elec10")
    special_tile = build_sweep_layout(5, "elec5")
    default_tile.move((-default_tile.xmin, -default_tile.ymin))
    special_tile.move((-special_tile.xmin, -special_tile.ymin))
    mc = base.build_parameter_object()
    reference_section = base.make_reference_section(mc)

    # 2. Define geometry
    # Use xsize/ysize but we will anchor placement to a fixed pitch
    tile_w = default_tile.xsize
    tile_h = default_tile.ysize
    print(default_tile.xmin, default_tile.xmax)
    print(default_tile.ymin, default_tile.ymax)
    street_width = 2000  # The gap between chips

    pitch_x = tile_w + street_width
    pitch_y = tile_h + street_width

    array = Device("mems_parameter_sweep_array_4x4")

    # 3. Place Tiles
    for row in range(4):
        for col in range(4):
            tile = special_tile if row == 3 else default_tile
            tile_ref = array << tile
            tile_ref.move((col * pitch_x, row * pitch_y))

    # 4. Calculate Cross Centers
    # We want crosses in the centers of the streets (gaps)
    # This includes the "half-street" on the outside edges for dicing marks
    x_centers = []
    # Start with far left edge
    x_centers.append(-street_width / 2)
    # Between the 4 columns
    for i in range(4):
        x_centers.append((i * pitch_x) + tile_w + (street_width / 2))

    y_centers = []
    # Start with bottom edge
    y_centers.append(-street_width / 2)
    # Between the 4 rows
    for i in range(4):
        y_centers.append((i * pitch_y) + tile_h + (street_width / 2))

    # 5. Place Crosses
    chip_cross = base.make_alignment_cross(400, 30, layer=2)
    for cx in x_centers:
        for cy in y_centers:
            c_ref = array << chip_cross
            c_ref.center = (cx, cy)

    # 6. Add Reference Section (Centered at the top)
    ref_ref = array << reference_section
    # Center horizontally relative to the whole array, place 1000um above top row
    ref_ref.move((array.center[0] - ref_ref.center[0], array.ymax + 1000))

    return array

def main():
    array = make_array_4x4()
    output_gds = "mems_parameter_sweep_array_4x4.gds"
    array.write_gds(output_gds)
    print(f"Wrote {output_gds}")

if __name__ == "__main__":
    main()