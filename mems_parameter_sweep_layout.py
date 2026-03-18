from phidl import Device
import phidl.geometry as pg


##########################################
# Layers:
# 1 = structural/device geometry
# 2 = contact geometry
# 3 = text labels
# 11 = visualization outlines
##########################################


class EmptyClass:
    pass


def outline(width, height, layer=11):
    frame = Device("outline")
    frame << pg.rectangle(size=(width, height), layer=layer)
    return frame


def make_contact_block(size, layer=2):
    block = Device("contact_block")
    block << pg.rectangle(size=size, layer=layer)
    return block


def cantilever_total_width(mc, beam_length):
    right_extension = mc.cant_electrode_tip_overhang + (
        mc.cant_contact_width - mc.cant_stem_width
    ) / 2
    return mc.cant_anchor_width + beam_length + right_extension


def cantilever_reference_beam_xmax(mc, beam_length):
    anchor_x = (mc.cant_unit_width - cantilever_total_width(mc, beam_length)) / 2
    return anchor_x + mc.cant_anchor_width + beam_length


def make_cantilever_electrode(mc, beam_ref, gap, is_top):
    electrode = Device("cantilever_electrode")
    beam_xmin = beam_ref.xmin
    beam_xmax = beam_ref.xmax
    beam_ymin = beam_ref.ymin
    beam_ymax = beam_ref.ymax

    finger_left = beam_xmin + mc.cant_electrode_start_offset
    finger_right = beam_xmax + mc.cant_electrode_tip_overhang
    stem_x = finger_right - mc.cant_stem_width
    contact_x = stem_x + mc.cant_stem_width / 2 - mc.cant_contact_width / 2
    contact_x = min(
        max(contact_x, mc.cant_edge_margin),
        mc.cant_unit_width - mc.cant_edge_margin - mc.cant_contact_width,
    )

    if is_top:
        finger_y = beam_ymax + gap
        stem_y = finger_y + mc.cant_electrode_height
        contact_y = stem_y + mc.cant_stem_length
    else:
        finger_y = beam_ymin - gap - mc.cant_electrode_height
        contact_y = finger_y - mc.cant_stem_length - mc.cant_contact_height
        stem_y = contact_y + mc.cant_contact_height

    electrode << make_contact_block(
        (mc.cant_contact_width, mc.cant_contact_height), layer=2
    ).move((contact_x, contact_y))
    electrode << pg.rectangle(
        size=(mc.cant_stem_width, mc.cant_stem_length), layer=1
    ).move((stem_x, stem_y))
    electrode << pg.rectangle(
        size=(finger_right - finger_left, mc.cant_electrode_height), layer=1
    ).move((finger_left, finger_y))
    return electrode


def cantilever_cell(mc, L, W, gap):
    cell = Device(f"cant_L{L}_W{W}_G{gap}")
    cell << outline(mc.cant_unit_width, mc.cant_unit_height)

    anchor_x = mc.cant_fixed_beam_xmax - L - mc.cant_anchor_width
    anchor_y = mc.cant_unit_height / 2 - mc.cant_anchor_height / 2
    beam_y = mc.cant_unit_height / 2 - W / 2

    cell << pg.rectangle(
        size=(mc.cant_anchor_width, mc.cant_anchor_height), layer=1
    ).move((anchor_x, anchor_y))

    beam = cell << pg.rectangle(size=(L, W), layer=1)
    beam.move((anchor_x + mc.cant_anchor_width, beam_y))

    cell << make_cantilever_electrode(mc, beam, gap=gap, is_top=True)
    cell << make_cantilever_electrode(mc, beam, gap=gap, is_top=False)

    label = cell << pg.text(
        text=f"CANT L={L} W={W} G={gap}",
        size=mc.cell_label_size,
        layer=3,
        font="Arial",
    )
    label.move((mc.cell_label_x, mc.cell_label_y))
    return cell


def make_cc_anchor(mc):
    anchor = Device("cc_anchor")
    anchor << pg.rectangle(size=(mc.cc_anchor_width, mc.cc_anchor_height), layer=1)
    return anchor


def make_cc_electrode_contact(mc):
    contact = Device("cc_contact")
    contact << pg.rectangle(size=(mc.cc_contact_width, mc.cc_contact_height), layer=2)
    return contact


def make_cc_electrode(mc, beam_ref, gap, is_top):
    electrode = Device("cc_electrode")
    max_active_length = beam_ref.xsize - 2 * mc.cc_anchor_clearance
    if max_active_length <= 0:
        raise ValueError("Beam is too short for the requested anchor clearance")

    target_active_length = min(
        mc.cc_electrode_coverage_fraction * beam_ref.xsize,
        beam_ref.xsize + mc.cc_electrode_tip_overhang,
    )
    active_length = min(target_active_length, max_active_length)

    active_x = beam_ref.center[0] - active_length / 2
    stem_x = beam_ref.center[0] - mc.cc_stem_width / 2
    contact_x = beam_ref.center[0] - mc.cc_contact_width / 2

    if is_top:
        active_y = beam_ref.ymax + gap
        stem_y = active_y + mc.cc_electrode_height
        contact_y = stem_y + mc.cc_stem_length
    else:
        active_y = beam_ref.ymin - gap - mc.cc_electrode_height
        contact_y = active_y - mc.cc_stem_length - mc.cc_contact_height
        stem_y = contact_y + mc.cc_contact_height

    electrode << pg.rectangle(
        size=(active_length, mc.cc_electrode_height), layer=1
    ).move((active_x, active_y))
    electrode << pg.rectangle(
        size=(mc.cc_stem_width, mc.cc_stem_length), layer=1
    ).move((stem_x, stem_y))
    electrode << make_cc_electrode_contact(mc).move((contact_x, contact_y))
    return electrode


def clamped_clamped_cell(mc, L, W, gap):
    cell = Device(f"cc_L{L}_W{W}_G{gap}")
    cell << outline(mc.cc_unit_width, mc.cc_unit_height)

    beam_y = mc.cc_unit_height / 2 - W / 2
    anchor_y = mc.cc_unit_height / 2 - mc.cc_anchor_height / 2
    left_anchor_x = mc.cc_center_x - (L / 2 + mc.cc_anchor_width)
    right_anchor_x = mc.cc_center_x + L / 2

    cell << make_cc_anchor(mc).move((left_anchor_x, anchor_y))
    beam = cell << pg.rectangle(size=(L, W), layer=1)
    beam.move((left_anchor_x + mc.cc_anchor_width, beam_y))
    cell << make_cc_anchor(mc).move((right_anchor_x, anchor_y))

    cell << make_cc_electrode(mc, beam, gap=gap, is_top=True)
    cell << make_cc_electrode(mc, beam, gap=gap, is_top=False)

    label = cell << pg.text(
        text=f"CC L={L} W={W} G={gap}",
        size=mc.cell_label_size,
        layer=3,
        font="Arial",
    )
    label.move((mc.cell_label_x, mc.cell_label_y))
    return cell


def add_section_label(parent, text, position, size):
    label = parent << pg.text(text=text, size=size, layer=3, font="Arial")
    label.move(position)
    return label


def place_parameter_grid(parent, origin, lengths, widths, gaps, cell_fn, section_name, mc):
    section = Device(section_name)
    row_pairs = [(W, G) for W in widths for G in gaps]

    for col, L in enumerate(lengths):
        header = section << pg.text(
            text=f"L={L}",
            size=mc.header_text_size,
            layer=3,
            font="Arial",
        )
        header.move((col * mc.cell_pitch_x + mc.column_label_x, mc.column_label_y))

    for row, (W, G) in enumerate(row_pairs):
        row_y = mc.grid_origin_y + row * mc.cell_pitch_y

        row_label = section << pg.text(
            text=f"W={W} G={G}",
            size=mc.header_text_size,
            layer=3,
            font="Arial",
        )
        row_label.move((mc.row_label_x, row_y + mc.row_label_y_offset))

        for col, L in enumerate(lengths):
            cell = cell_fn(mc, L, W, G)
            cell_ref = section << cell
            cell_ref.move((mc.grid_origin_x + col * mc.cell_pitch_x, row_y))

    parent << section.move(origin)


def build_parameter_object():
    mc = EmptyClass()

    mc.lengths = [100, 200, 300, 400, 500]
    mc.widths = [10, 15, 20]
    mc.gaps = [2, 3, 5]

    mc.cell_label_size = 42
    mc.cell_label_x = 80
    mc.cell_label_y = 80
    mc.header_text_size = 70
    mc.section_label_size = 110

    mc.cell_pitch_x = 1800
    mc.cell_pitch_y = 1700
    mc.grid_origin_x = 220
    mc.grid_origin_y = 220
    mc.column_label_x = 520
    mc.column_label_y = 40
    mc.row_label_x = 20
    mc.row_label_y_offset = 620

    mc.family_gap_x = 1200
    mc.master_margin = 200

    mc.cant_unit_width = 1500
    mc.cant_unit_height = 1500
    mc.cant_edge_margin = 150
    mc.cant_anchor_width = 250
    mc.cant_anchor_height = 250
    mc.cant_contact_width = 250
    mc.cant_contact_height = 250
    mc.cant_stem_width = 20
    mc.cant_stem_length = 180
    mc.cant_electrode_height = 90
    mc.cant_electrode_start_offset = 30
    mc.cant_electrode_tip_overhang = 15
    mc.cant_reference_beam_length = 500
    mc.cant_fixed_beam_xmax = cantilever_reference_beam_xmax(
        mc, mc.cant_reference_beam_length
    )

    mc.cc_unit_width = 1500
    mc.cc_unit_height = 1500
    mc.cc_center_x = mc.cc_unit_width / 2
    mc.cc_anchor_width = 250
    mc.cc_anchor_height = 250
    mc.cc_contact_width = 250
    mc.cc_contact_height = 250
    mc.cc_stem_width = 20
    mc.cc_stem_length = 140
    mc.cc_electrode_height = 80
    mc.cc_electrode_coverage_fraction = 0.9
    mc.cc_electrode_tip_overhang = 15
    mc.cc_anchor_clearance = 25

    mc.output_gds = "mems_parameter_sweep_layout.gds"
    return mc


def main():
    mc = build_parameter_object()
    master = Device("mems_parameter_sweep_layout")

    row_count = len(mc.widths) * len(mc.gaps)
    section_width = mc.grid_origin_x + len(mc.lengths) * mc.cell_pitch_x
    section_height = mc.grid_origin_y + row_count * mc.cell_pitch_y

    cant_origin = (mc.master_margin, mc.master_margin + 200)
    cc_origin = (
        cant_origin[0] + section_width + mc.family_gap_x,
        cant_origin[1],
    )

    add_section_label(
        master,
        "Cantilever Sweep",
        (cant_origin[0], mc.master_margin),
        mc.section_label_size,
    )
    add_section_label(
        master,
        "Clamped-Clamped Sweep",
        (cc_origin[0], mc.master_margin),
        mc.section_label_size,
    )

    place_parameter_grid(
        master,
        cant_origin,
        mc.lengths,
        mc.widths,
        mc.gaps,
        cantilever_cell,
        "cantilever_section",
        mc,
    )
    place_parameter_grid(
        master,
        cc_origin,
        mc.lengths,
        mc.widths,
        mc.gaps,
        clamped_clamped_cell,
        "clamped_clamped_section",
        mc,
    )

    master.write_gds(mc.output_gds)
    print(f"Wrote {mc.output_gds}")


if __name__ == "__main__":
    main()
