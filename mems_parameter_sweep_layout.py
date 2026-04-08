from phidl import Device
import phidl.geometry as pg
import numpy as np
import csv


##########################################
# Layers:
# 1 = structural/device geometry
# 2 = contact geometry
# 3 = text labels
# 11 = visualization outlines
##########################################
density = 2329 #kg/m^3 (SOI wafer)
youngs_modulus = 169*10**9 #Pa (SOI, 110 plane because shearing motion...)

class EmptyClass:

    pass

def capacitance(beam_length, beam_width, distance, permittivity=8.854e-12):
    """Calculate the capacitance of a parallel plate capacitor."""
    area = beam_length * beam_width
    return permittivity * area / distance

def force_at_DC_voltage(beam_length, beam_width, distance, voltage, permittivity=8.854e-12):
    """Calculate the electrostatic force at a given DC voltage."""
    C = capacitance(beam_length, beam_width, distance, permittivity)
    return 0.5 * C * voltage**2 / distance
def maximum_cantilever_deflection(beam_length, beam_width, beam_thickness, applied_force, youngs_modulus):
    """Calculate the maximum deflection of a cantilever beam under an applied force."""
    I = (beam_width * beam_thickness**3) / 12
    return (applied_force * beam_length**3) / (3 * youngs_modulus * I)
def clamped_resonant_frequency(beam_length, beam_width, beam_thickness, material_density, youngs_modulus):
    """Calculate the fundamental resonant frequency of a clamped-clamped beam."""
    # For a clamped-clamped beam, the first mode shape has a frequency given by:
    # f = (1/2L) * sqrt((E * I) / (rho * A))
    # where:
    # L = beam length
    # E = Young's modulus
    # I = moment of inertia of the cross-section
    # rho = material density
    # A = cross-sectional area

    A = beam_width * beam_thickness
    I = (beam_width * beam_thickness**3) / 12

    frequency = 1 / (2 * np.pi) * 3.5156 / beam_length**2 * np.sqrt(
        (youngs_modulus * I) / (material_density * A)
    )
    return frequency

def clamped_clamped_resonant_frequency(beam_length, beam_width, beam_thickness, material_density, youngs_modulus):
    """Calculate the fundamental resonant frequency of a clamped-clamped beam."""
    # For a clamped-clamped beam, the first mode shape has a frequency given by:
    # f = (1/2L) * sqrt((E * I) / (rho * A))
    # where:
    # L = beam length
    # E = Young's modulus
    # I = moment of inertia of the cross-section
    # rho = material density
    # A = cross-sectional area

    A = beam_width * beam_thickness
    I = (beam_width * beam_thickness**3) / 12

    frequency = 1 / (2 * np.pi) * 22.373 / beam_length**2 * np.sqrt(
        (youngs_modulus * I) / (material_density * A)
    )
    return frequency
def outline(width, height, layer=11):
    frame = Device("outline")
    frame << pg.rectangle(size=(width, height), layer=layer)
    return frame


def make_contact_block(size, layer=2):
    block = Device("contact_block")
    block << pg.rectangle(size=size, layer=layer)
    return block


def make_alignment_cross(arm_length, arm_width, layer=2):
    cross = Device("alignment_cross")
    cross << pg.rectangle(size=(arm_length, arm_width), layer=layer).move(
        (-arm_length / 2, -arm_width / 2)
    )
    cross << pg.rectangle(size=(arm_width, arm_length), layer=layer).move(
        (-arm_width / 2, -arm_length / 2)
    )
    return cross


def make_fillet_pieces(f_r, layer=1):
    """Create the four inside-corner fillet pieces from the provided template."""
    D1 = pg.circle(radius=f_r, layer=layer).move([f_r, f_r])

    D2 = pg.rectangle(size=[f_r, f_r], layer=layer)
    F_tr = pg.boolean(
        A=D2, B=D1, operation="not", precision=1e-6, num_divisions=[1, 1], layer=layer
    )

    D2 = pg.rectangle(size=[f_r, f_r], layer=layer).move([f_r, 0])
    F_tl = pg.boolean(
        A=D2, B=D1, operation="not", precision=1e-6, num_divisions=[1, 1], layer=layer
    )
    F_tl.move([-2 * f_r, 0])

    D2 = pg.rectangle(size=[f_r, f_r], layer=layer).move([f_r, f_r])
    F_bl = pg.boolean(
        A=D2, B=D1, operation="not", precision=1e-6, num_divisions=[1, 1], layer=layer
    )
    F_bl.move([-2 * f_r, -2 * f_r])

    D2 = pg.rectangle(size=[f_r, f_r], layer=layer).move([0, f_r])
    F_br = pg.boolean(
        A=D2, B=D1, operation="not", precision=1e-6, num_divisions=[1, 1], layer=layer
    )
    F_br.move([0, -2 * f_r])

    return {"tr": F_tr, "tl": F_tl, "bl": F_bl, "br": F_br}


def cantilever_total_width(mc, beam_length):
    right_extension = mc.cant_electrode_tip_overhang + (
        mc.cant_contact_width - mc.cant_stem_width_max
    ) / 2
    return mc.cant_anchor_width + beam_length + right_extension


def cantilever_reference_beam_xmax(mc, beam_length):
    anchor_x = (mc.cant_unit_width - cantilever_total_width(mc, beam_length)) / 2
    return anchor_x + mc.cant_anchor_width + beam_length


def cantilever_reference_anchor_x(mc, beam_length):
    return cantilever_reference_beam_xmax(mc, beam_length) - beam_length - mc.cant_anchor_width


def cantilever_beam_center_x(mc, anchor_x, beam_length):
    return anchor_x + mc.cant_anchor_width + beam_length / 2


def cantilever_reference_finger_width(mc, beam_length):
    return beam_length - mc.cant_electrode_start_offset + mc.cant_electrode_tip_overhang


def make_cantilever_electrode(mc, beam_ref, gap, is_top):
    electrode = Device("cantilever_electrode")
    beam_xmin = beam_ref.xmin
    beam_xmax = beam_ref.xmax
    beam_ymin = beam_ref.ymin
    beam_ymax = beam_ref.ymax

    finger_left = beam_xmin + mc.cant_electrode_start_offset
    finger_right = beam_xmax + mc.cant_electrode_tip_overhang
    finger_width = finger_right - finger_left
    contact_x = mc.cant_fixed_contact_x
    stem_width = mc.cant_fixed_stem_width
    stem_x = finger_left

    if is_top:
        finger_y = beam_ymax + gap
        contact_y = finger_y + mc.cant_electrode_height + mc.cant_stem_length
        stem_y = finger_y + mc.cant_electrode_height
    else:
        finger_y = beam_ymin - gap - mc.cant_electrode_height
        contact_y = finger_y - mc.cant_stem_length - mc.cant_contact_height
        stem_y = contact_y + mc.cant_contact_height

    electrode << make_contact_block(
        (mc.cant_contact_width, mc.cant_contact_height), layer=2
    ).move((contact_x, contact_y))
    electrode << pg.rectangle(
        size=(stem_width, mc.cant_stem_length), layer=1
    ).move((stem_x, stem_y))
    electrode << pg.rectangle(
        size=(finger_width, mc.cant_electrode_height), layer=1
    ).move((finger_left, finger_y))
    return electrode


def cantilever_cell(mc, L, W, gap):
    cell = Device(f"cant_L{L}_W{W}_G{gap}")
    cell << outline(mc.cant_unit_width, mc.cant_unit_height)

    anchor_x = mc.cant_fixed_anchor_x
    anchor_y = mc.cant_unit_height / 2 - mc.cant_anchor_height / 2
    beam_y = mc.cant_unit_height / 2 - W / 2

    cell << pg.rectangle(
        size=(mc.cant_anchor_width, mc.cant_anchor_height), layer=1
    ).move((anchor_x, anchor_y))

    beam = cell << pg.rectangle(size=(L, W), layer=1)
    beam.move((anchor_x + mc.cant_anchor_width, beam_y))

    junction_x = anchor_x + mc.cant_anchor_width
    fillets = make_fillet_pieces(mc.cant_fillet_radius, layer=1)
    cell << fillets["tr"].move((junction_x, beam_y + W))
    cell << fillets["br"].move((junction_x, beam_y))

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


def cc_reference_left_anchor_x(mc, beam_length):
    return mc.cc_center_x - (beam_length / 2 + mc.cc_anchor_width)


def cc_beam_center_x(mc, left_anchor_x, beam_length):
    return left_anchor_x + mc.cc_anchor_width + beam_length / 2


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

    active_center_x = beam_ref.center[0]
    active_x = active_center_x - active_length / 2
    contact_x = mc.cc_fixed_contact_x
    contact_center_x = contact_x + mc.cc_contact_width / 2
    stem_core_width = min(mc.cc_stem_width_max, mc.cc_contact_width, active_length)
    stem_x = active_x
    stem_right = max(contact_center_x + stem_core_width / 2, active_x + stem_core_width)
    stem_width = stem_right - stem_x

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
        size=(stem_width, mc.cc_stem_length), layer=1
    ).move((stem_x, stem_y))
    electrode << make_cc_electrode_contact(mc).move((contact_x, contact_y))
    return electrode


def clamped_clamped_cell(mc, L, W, gap):
    cell = Device(f"cc_L{L}_W{W}_G{gap}")
    cell << outline(mc.cc_unit_width, mc.cc_unit_height)

    beam_y = mc.cc_unit_height / 2 - W / 2
    anchor_y = mc.cc_unit_height / 2 - mc.cc_anchor_height / 2
    left_anchor_x = mc.cc_fixed_left_anchor_x
    right_anchor_x = left_anchor_x + mc.cc_anchor_width + L

    cell << make_cc_anchor(mc).move((left_anchor_x, anchor_y))
    beam = cell << pg.rectangle(size=(L, W), layer=1)
    beam.move((left_anchor_x + mc.cc_anchor_width, beam_y))
    fillets = make_fillet_pieces(mc.cc_fillet_radius, layer=1)
    left_jx = left_anchor_x + mc.cc_anchor_width
    right_jx = right_anchor_x
    cell << fillets["tr"].move((left_jx, beam_y + W))
    cell << fillets["br"].move((left_jx, beam_y))
    cell << fillets["tl"].move((right_jx, beam_y + W))
    cell << fillets["bl"].move((right_jx, beam_y))
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


def place_section_crosses(parent, origin, ncols, nrows, unit_width, unit_height, mc):
    gap_x = mc.cell_pitch_x - unit_width
    gap_y = mc.cell_pitch_y - unit_height

    cross = make_alignment_cross(mc.cross_arm_length, mc.cross_arm_width, layer=mc.cross_layer)

    # Starting point of the first cell's bottom-left corner
    base_x = origin[0] + mc.grid_origin_x
    base_y = origin[1] + mc.grid_origin_y

    for col in range(ncols - 1):
        # Center of gap = (Right edge of cell) + (Half of gap)
        cross_x = base_x + (col * mc.cell_pitch_x) + unit_width + (gap_x / 2)

        for row in range(nrows - 1):
            # Center of gap = (Top edge of cell) + (Half of gap)
            cross_y = base_y + (row * mc.cell_pitch_y) + unit_height + (gap_y / 2)

            cross_ref = parent << cross
            cross_ref.move((cross_x, cross_y))


def make_reference_section(mc):
    """Create PHIDL lithography reference structures matching the older solar workflow."""
    section = Device("reference_section")

    title = section << pg.text(
        text="Lithography References",
        size=mc.section_label_size,
        layer=3,
        font="Arial",
    )
    title.move((0, mc.ref_title_y))

    steps_l1 = section << pg.litho_steps(
        line_widths=mc.ref_line_widths,
        line_spacing=mc.ref_line_spacing,
        height=mc.ref_steps_height,
        layer=1,
    )
    steps_l1.move((mc.ref_struct_x, mc.ref_steps_y1))

    steps_l2 = section << pg.litho_steps(
        line_widths=mc.ref_line_widths,
        line_spacing=mc.ref_line_spacing,
        height=mc.ref_steps_height,
        layer=2,
    )
    steps_l2.move((mc.ref_struct_x, mc.ref_steps_y2))

    cal_h = section << pg.litho_calipers(
        notch_size=mc.ref_caliper_notch_size,
        notch_spacing=mc.ref_caliper_notch_spacing,
        num_notches=mc.ref_caliper_num_notches,
        offset_per_notch=mc.ref_caliper_offset_per_notch,
        row_spacing=0,
        layer1=1,
        layer2=2,
    )
    cal_h.move((mc.ref_struct_x, mc.ref_caliper_y1))

    cal_v = section << pg.litho_calipers(
        notch_size=mc.ref_caliper_notch_size,
        notch_spacing=mc.ref_caliper_notch_spacing,
        num_notches=mc.ref_caliper_num_notches,
        offset_per_notch=mc.ref_caliper_offset_per_notch,
        row_spacing=0,
        layer1=1,
        layer2=2,
    )
    cal_v.rotate(90).move((mc.ref_struct_x, mc.ref_caliper_y2))
    return section


def place_reference_section(parent, origin, mc):
    """Place PHIDL lithography reference structures matching the older solar workflow."""
    parent << make_reference_section(mc).move(origin)


def build_parameter_object():
    mc = EmptyClass()

    mc.lengths = [100, 200, 300, 400, 500]
    mc.widths = [3, 4, 5]
    mc.gaps = [1, 2, 3]
    mc.beam_thickness = 1  # microns

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
    mc.cross_arm_length = 140
    mc.cross_arm_width = 12
    mc.cross_layer = 2

    mc.cant_unit_width = 1500
    mc.cant_unit_height = 1500
    mc.cant_edge_margin = 150
    mc.cant_anchor_width = 250
    mc.cant_anchor_height = 250
    mc.cant_contact_width = 250
    mc.cant_contact_height = 250
    mc.cant_stem_width_max = 60
    mc.cant_stem_length = 180
    mc.cant_electrode_height = 10
    mc.cant_electrode_start_offset = 30
    mc.cant_electrode_tip_overhang = 15
    mc.cant_fillet_radius = 5
    mc.cant_reference_beam_length = 500
    mc.cant_fixed_beam_xmax = cantilever_reference_beam_xmax(
        mc, mc.cant_reference_beam_length
    )
    mc.cant_fixed_anchor_x = cantilever_reference_anchor_x(
        mc, mc.cant_reference_beam_length
    )
    mc.cant_pad_reference_beam_length = 100
    mc.cant_fixed_contact_x = (
        cantilever_beam_center_x(
            mc, mc.cant_fixed_anchor_x, mc.cant_pad_reference_beam_length
        )
        - mc.cant_contact_width / 2
    )
    mc.cant_fixed_stem_width = min(
        mc.cant_stem_width_max,
        cantilever_reference_finger_width(mc, mc.cant_pad_reference_beam_length),
    )

    mc.cc_unit_width = 1500
    mc.cc_unit_height = 1500
    mc.cc_center_x = mc.cc_unit_width / 2
    mc.cc_anchor_width = 250
    mc.cc_anchor_height = 250
    mc.cc_contact_width = 250
    mc.cc_contact_height = 250
    mc.cc_stem_width_max = 60
    mc.cc_stem_length = 140
    mc.cc_electrode_height = 10
    mc.cc_electrode_coverage_fraction = 0.9
    mc.cc_electrode_tip_overhang = 15
    mc.cc_anchor_clearance = 25
    mc.cc_fillet_radius = 5
    mc.cc_reference_beam_length = 100
    mc.cc_fixed_left_anchor_x = cc_reference_left_anchor_x(
        mc, mc.cc_reference_beam_length
    )
    mc.cc_fixed_contact_x = (
        cc_beam_center_x(mc, mc.cc_fixed_left_anchor_x, mc.cc_reference_beam_length)
        - mc.cc_contact_width / 2
    )

    mc.ref_section_gap_y = 1200
    mc.ref_title_y = 1850
    mc.ref_struct_x = 900
    mc.ref_steps_y1 = 1200
    mc.ref_steps_y2 = 700
    mc.ref_caliper_y1 = 250
    mc.ref_caliper_y2 = -250
    mc.ref_label_x = 0
    mc.ref_label_dy = 120
    mc.ref_label_size = 60
    mc.ref_line_widths = [1, 1.5, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 30]
    mc.ref_line_spacing = 20
    mc.ref_steps_height = 500
    mc.ref_caliper_notch_size = [2, 10]
    mc.ref_caliper_notch_spacing = 4
    mc.ref_caliper_num_notches = 20
    mc.ref_caliper_offset_per_notch = 0.1

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
    place_section_crosses(
        master,
        cant_origin,
        len(mc.lengths),
        len(mc.widths) * len(mc.gaps),
        mc.cant_unit_width,
        mc.cant_unit_height,
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
    place_section_crosses(
        master,
        cc_origin,
        len(mc.lengths),
        len(mc.widths) * len(mc.gaps),
        mc.cc_unit_width,
        mc.cc_unit_height,
        mc,
    )

    section_height = mc.grid_origin_y + (row_count - 1) * mc.cell_pitch_y + mc.cant_unit_height
    ref_origin = (mc.master_margin, cant_origin[1] + section_height + mc.ref_section_gap_y)
    place_reference_section(master, ref_origin, mc)

    master.write_gds(mc.output_gds)
    print(f"Wrote {mc.output_gds}")

    # Calculate resonant frequencies and write to CSV
    csv_filename = "device_frequencies.csv"
    with open(csv_filename, 'w', newline='') as csvfile:
        fieldnames = ['type', 'length_um', 'width_um', 'gap_um', 'thickness_um', 'frequency_hz', 'capacitance_fF', 'force_pN', 'max_deflection_nm']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # Convert to meters for calculation
        thickness_m = mc.beam_thickness * 1e-6

    #     for L in mc.lengths:
    #         L_m = L * 1e-6
    #         for W in mc.widths:
    #             W_m = W * 1e-6
    #             for G in mc.gaps:
    #                 # Cantilever frequency
    #                 cant_freq = clamped_resonant_frequency(L_m, W_m, thickness_m, density, youngs_modulus)
    #                 cap = capacitance(L_m, W_m, G * 1e-6)
    #                 force = force_at_DC_voltage(L_m, W_m, G * 1e-6, voltage=100)
    #                 maximum_deflection = maximum_cantilever_deflection(L_m, W_m, thickness_m, force, youngs_modulus)  # Example voltage
    #                 writer.writerow({
    #                     'type': 'cantilever',
    #                     'length_um': L,
    #                     'width_um': W,
    #                     'gap_um': G,
    #                     'thickness_um': mc.beam_thickness,
    #                     'frequency_hz': cant_freq,
    #                     "capacitance_fF": cap * 1e15,
    #                     "force_pN": force * 1e12,
    #                     "max_deflection_nm": maximum_deflection * 1e9
    #                 })

    #                 # Clamped-clamped frequency
    #                 cc_freq = clamped_clamped_resonant_frequency(L_m, W_m, thickness_m, density, youngs_modulus)
    #                 maximum_deflection = maximum_cantilever_deflection(L_m, W_m, thickness_m, force, youngs_modulus)
    #                 writer.writerow({
    #                     'type': 'clamped_clamped',
    #                     'length_um': L,
    #                     'width_um': W,
    #                     'gap_um': G,
    #                     'thickness_um': mc.beam_thickness,
    #                     'frequency_hz': cc_freq,
    #                     "capacitance_fF": cap * 1e15,
    #                     "force_pN": force * 1e12,
    #                     "max_deflection_nm": maximum_deflection * 1e9

    #                 })

    # print(f"Wrote {csv_filename}")


if __name__ == "__main__":
    main()
