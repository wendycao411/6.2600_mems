from phidl import Device
import phidl.geometry as pg

import mems_parameter_sweep_layout as base


def build_sweep_layout(electrode_width, suffix):
    """Build one full sweep layout with a specified electrode width."""
    mc = base.build_parameter_object()
    mc.cant_electrode_height = electrode_width
    mc.cc_electrode_height = electrode_width

    master = Device(f"mems_parameter_sweep_{suffix}")

    row_count = len(mc.widths) * len(mc.gaps)
    section_width = mc.grid_origin_x + len(mc.lengths) * mc.cell_pitch_x

    cant_origin = (mc.master_margin, mc.master_margin + 200)
    cc_origin = (
        cant_origin[0] + section_width + mc.family_gap_x,
        cant_origin[1],
    )

    base.add_section_label(
        master,
        f"Cantilever Sweep ({electrode_width} um elec.)",
        (cant_origin[0], mc.master_margin),
        mc.section_label_size,
    )
    base.add_section_label(
        master,
        f"Clamped-Clamped Sweep ({electrode_width} um elec.)",
        (cc_origin[0], mc.master_margin),
        mc.section_label_size,
    )

    base.place_parameter_grid(
        master,
        cant_origin,
        mc.lengths,
        mc.widths,
        mc.gaps,
        base.cantilever_cell,
        f"cantilever_section_{suffix}",
        mc,
    )
    base.place_section_crosses(
        master,
        cant_origin,
        len(mc.lengths),
        len(mc.widths) * len(mc.gaps),
        mc.cant_unit_width,
        mc.cant_unit_height,
        mc,
    )
    base.place_parameter_grid(
        master,
        cc_origin,
        mc.lengths,
        mc.widths,
        mc.gaps,
        base.clamped_clamped_cell,
        f"clamped_clamped_section_{suffix}",
        mc,
    )
    base.place_section_crosses(
        master,
        cc_origin,
        len(mc.lengths),
        len(mc.widths) * len(mc.gaps),
        mc.cc_unit_width,
        mc.cc_unit_height,
        mc,
    )

    tile_label = master << pg.text(
        text=f"Electrode Width = {electrode_width} um",
        size=90,
        layer=3,
        font="Arial",
    )
    tile_label.move((mc.master_margin, mc.master_margin + 80))

    return master


def make_array_4x4():
    """
    Create a 4x4 array of the full MEMS sweep layout.
    The top row uses 5 um electrode widths; the other three rows use 10 um.
    """
    default_tile = build_sweep_layout(10, "elec10")
    special_tile = build_sweep_layout(5, "elec5")
    ref_mc = base.build_parameter_object()
    reference_section = base.make_reference_section(ref_mc)

    sample_tile = default_tile
    tile_width = sample_tile.xsize
    tile_height = sample_tile.ysize
    edge_gap_x = 2000
    edge_gap_y = 2000
    pitch_x = tile_width + edge_gap_x
    pitch_y = tile_height + edge_gap_y
    gap_x = pitch_x - tile_width
    gap_y = pitch_y - tile_height

    array = Device("mems_parameter_sweep_array_4x4")
    chip_lefts = []
    chip_bottoms = []

    for row in range(4):
        for col in range(4):
            tile = special_tile if row == 3 else default_tile
            tile_ref = array << tile
            chip_x = edge_gap_x + col * pitch_x
            chip_y = edge_gap_y + row * pitch_y
            tile_ref.move((chip_x, chip_y))
            if row == 0:
                chip_lefts.append(chip_x)
            if col == 0:
                chip_bottoms.append(chip_y)

    chip_cross = base.make_alignment_cross(300, 20, layer=2)
    x_street_centers = [chip_lefts[0] / 2]
    for i in range(3):
        right_edge = chip_lefts[i] + tile_width
        left_edge_next = chip_lefts[i + 1]
        x_street_centers.append((right_edge + left_edge_next) / 2)
    x_street_centers.append(chip_lefts[-1] + tile_width + edge_gap_x / 2)

    y_street_centers = [chip_bottoms[0] / 2]
    for i in range(3):
        top_edge = chip_bottoms[i] + tile_height
        bottom_edge_next = chip_bottoms[i + 1]
        y_street_centers.append((top_edge + bottom_edge_next) / 2)
    y_street_centers.append(chip_bottoms[-1] + tile_height + edge_gap_y / 2)

    for cross_x in x_street_centers:
        for cross_y in y_street_centers:
            cross_ref = array << chip_cross
            cross_ref.move((cross_x, cross_y))

    array_width = 4 * tile_width + 5 * gap_x
    ref_x = (array_width - reference_section.xsize) / 2 - reference_section.xmin
    ref_y = edge_gap_y + 4 * pitch_y + 1000 - reference_section.ymin
    ref_ref = array << reference_section
    ref_ref.move((ref_x, ref_y))

    return array


def main():
    array = make_array_4x4()
    output_gds = "mems_parameter_sweep_array_4x4.gds"
    array.write_gds(output_gds)
    print(f"Wrote {output_gds}")


if __name__ == "__main__":
    main()
