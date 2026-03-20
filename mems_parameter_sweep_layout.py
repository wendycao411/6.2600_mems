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


# ---------------------------------------------------------------------------
# Fillet helpers
# ---------------------------------------------------------------------------

def make_fillet_pieces(f_r, layer=1):
    """

        'tr'  top-right air    ->  material bottom-left   (F1 from reference snippet)
        'tl'  top-left air     ->  material bottom-right
        'bl'  bottom-left air  ->  material top-right
        'br'  bottom-right air ->  material top-left      (F4 from reference snippet)

    Usage:
        fillets = make_fillet_pieces(f_r, layer=1)
        cell << fillets['tr'].move((corner_x, corner_y))
    """
    D1 = pg.circle(radius=f_r, layer=layer).move([f_r, f_r])

    D2 = pg.rectangle(size=[f_r, f_r], layer=layer)
    F_tr = pg.boolean(A=D2, B=D1, operation='not',
                      precision=1e-6, num_divisions=[1, 1], layer=layer)



    D2 = pg.rectangle(size=[f_r, f_r], layer=layer).move([f_r, 0])
    F_tl = pg.boolean(A=D2, B=D1, operation='not',
                      precision=1e-6, num_divisions=[1, 1], layer=layer)
    F_tl.move([-2 * f_r, 0])



    D2 = pg.rectangle(size=[f_r, f_r], layer=layer).move([f_r, f_r])
    F_bl = pg.boolean(A=D2, B=D1, operation='not',
                      precision=1e-6, num_divisions=[1, 1], layer=layer)
    F_bl.move([-2 * f_r, -2 * f_r])

    D2 = pg.rectangle(size=[f_r, f_r], layer=layer).move([0, f_r])
    F_br = pg.boolean(A=D2, B=D1, operation='not',
                      precision=1e-6, num_divisions=[1, 1], layer=layer)
    F_br.move([0, -2 * f_r])
    # corner at (0,0); piece extends into +x,-y  ✓

    return {'tr': F_tr, 'tl': F_tl, 'bl': F_bl, 'br': F_br}


# ---------------------------------------------------------------------------
# Cantilever geometry
# ---------------------------------------------------------------------------

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

    finger_left  = beam_xmin + mc.cant_electrode_start_offset
    finger_right = beam_xmax + mc.cant_electrode_tip_overhang
    finger_width = finger_right - finger_left
    contact_x    = mc.cant_fixed_contact_x
    stem_width   = mc.cant_fixed_stem_width
    stem_x       = finger_left

    if is_top:
        finger_y  = beam_ymax + gap
        contact_y = finger_y + mc.cant_electrode_height + mc.cant_stem_length
        stem_y    = finger_y + mc.cant_electrode_height
    else:
        finger_y  = beam_ymin - gap - mc.cant_electrode_height
        contact_y = finger_y - mc.cant_stem_length - mc.cant_contact_height
        stem_y    = contact_y + mc.cant_contact_height

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
    beam_y   = mc.cant_unit_height / 2 - W / 2

    cell << pg.rectangle(
        size=(mc.cant_anchor_width, mc.cant_anchor_height), layer=1
    ).move((anchor_x, anchor_y))

    beam = cell << pg.rectangle(size=(L, W), layer=1)
    beam.move((anchor_x + mc.cant_anchor_width, beam_y))

    # ---- fillets at the anchor-beam junction --------------------------------
    # junction_x = right face of anchor = left face of beam
    junction_x = anchor_x + mc.cant_anchor_width
    fillets = make_fillet_pieces(mc.cant_fillet_radius, layer=1)

    # Top inner corner: material is left + below  ->  air is top-right  ->  'tr'
    cell << fillets['tr'].move((junction_x, beam_y + W))

    # Bottom inner corner: material is left + above  ->  air is bottom-right  ->  'br'
    cell << fillets['br'].move((junction_x, beam_y))
    # -------------------------------------------------------------------------

    cell << make_cantilever_electrode(mc, beam, gap=gap, is_top=True)
    cell << make_cantilever_electrode(mc, beam, gap=gap, is_top=False)

    label = cell << pg.text(
        text=f"CANT L={L} W={W} G={gap}",
        size=mc.cell_label_size,
        layer=3,
        font="DejaVu Sans",
    )
    label.move((mc.cell_label_x, mc.cell_label_y))
    return cell


# ---------------------------------------------------------------------------
# Clamped-clamped geometry
# ---------------------------------------------------------------------------

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

    active_center_x  = beam_ref.center[0]
    active_x         = active_center_x - active_length / 2
    contact_x        = mc.cc_fixed_contact_x
    contact_center_x = contact_x + mc.cc_contact_width / 2
    stem_core_width  = min(mc.cc_stem_width_max, mc.cc_contact_width, active_length)
    stem_x           = active_x
    stem_right       = max(contact_center_x + stem_core_width / 2, active_x + stem_core_width)
    stem_width       = stem_right - stem_x

    if is_top:
        active_y  = beam_ref.ymax + gap
        stem_y    = active_y + mc.cc_electrode_height
        contact_y = stem_y + mc.cc_stem_length
    else:
        active_y  = beam_ref.ymin - gap - mc.cc_electrode_height
        contact_y = active_y - mc.cc_stem_length - mc.cc_contact_height
        stem_y    = contact_y + mc.cc_contact_height

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

    beam_y         = mc.cc_unit_height / 2 - W / 2
    anchor_y       = mc.cc_unit_height / 2 - mc.cc_anchor_height / 2
    left_anchor_x  = mc.cc_fixed_left_anchor_x
    right_anchor_x = left_anchor_x + mc.cc_anchor_width + L

    cell << make_cc_anchor(mc).move((left_anchor_x, anchor_y))
    beam = cell << pg.rectangle(size=(L, W), layer=1)
    beam.move((left_anchor_x + mc.cc_anchor_width, beam_y))
    cell << make_cc_anchor(mc).move((right_anchor_x, anchor_y))

    # ---- fillets at both anchor-beam junctions --------------------------------
    fillets  = make_fillet_pieces(mc.cc_fillet_radius, layer=1)
    left_jx  = left_anchor_x + mc.cc_anchor_width  # right face of left anchor
    right_jx = right_anchor_x                       # left  face of right anchor

    # Left junction: material is left+above/below  ->  air is top-right / bottom-right
    cell << fillets['tr'].move((left_jx,  beam_y + W))
    cell << fillets['br'].move((left_jx,  beam_y))

    # Right junction: material is right+above/below  ->  air is top-left / bottom-left
    cell << fillets['tl'].move((right_jx, beam_y + W))
    cell << fillets['bl'].move((right_jx, beam_y))
    # --------------------------------------------------------------------------

    cell << make_cc_electrode(mc, beam, gap=gap, is_top=True)
    cell << make_cc_electrode(mc, beam, gap=gap, is_top=False)

    label = cell << pg.text(
        text=f"CC L={L} W={W} G={gap}",
        size=mc.cell_label_size,
        layer=3,
        font="DejaVu Sans",
    )
    label.move((mc.cell_label_x, mc.cell_label_y))
    return cell


# ---------------------------------------------------------------------------
# Layout assembly
# ---------------------------------------------------------------------------

def add_section_label(parent, text, position, size):
    label = parent << pg.text(text=text, size=size, layer=3, font="DejaVu Sans")
    label.move(position)
    return label


def place_parameter_grid(parent, origin, lengths, widths, gaps, cell_fn, section_name, mc):
    section   = Device(section_name)
    row_pairs = [(W, G) for W in widths for G in gaps]

    for col, L in enumerate(lengths):
        header = section << pg.text(
            text=f"L={L}",
            size=mc.header_text_size,
            layer=3,
            font="DejaVu Sans",
        )
        header.move((col * mc.cell_pitch_x + mc.column_label_x, mc.column_label_y))

    for row, (W, G) in enumerate(row_pairs):
        row_y = mc.grid_origin_y + row * mc.cell_pitch_y

        row_label = section << pg.text(
            text=f"W={W} G={G}",
            size=mc.header_text_size,
            layer=3,
            font="DejaVu Sans",
        )
        row_label.move((mc.row_label_x, row_y + mc.row_label_y_offset))

        for col, L in enumerate(lengths):
            cell     = cell_fn(mc, L, W, G)
            cell_ref = section << cell
            cell_ref.move((mc.grid_origin_x + col * mc.cell_pitch_x, row_y))

    parent << section.move(origin)


# ---------------------------------------------------------------------------
# Grating / line-gradient test structures
# ---------------------------------------------------------------------------

def grating_cell(mc, line_w, space_w, is_vertical, layer=1):
    """
    Fixed-size cell filled with parallel lines on `layer`.

    is_vertical=True  -> stripes run top-to-bottom (pitch in x)
    is_vertical=False -> stripes run left-to-right (pitch in y)

    Lines are centred inside the cell.  The cell outline is on layer 11.
    """
    orient = "V" if is_vertical else "H"
    cell = Device(f"grating_{orient}_L{line_w}_S{space_w}")
    cell << outline(mc.grating_cell_w, mc.grating_cell_h)

    pitch = line_w + space_w

    if is_vertical:
        n      = max(1, int(mc.grating_cell_w / pitch))
        total  = n * pitch - space_w          # width occupied by n lines + (n-1) spaces
        offset = (mc.grating_cell_w - total) / 2
        for i in range(n):
            cell << pg.rectangle(
                size=(line_w, mc.grating_cell_h), layer=layer
            ).move((offset + i * pitch, 0))
    else:
        n      = max(1, int(mc.grating_cell_h / pitch))
        total  = n * pitch - space_w
        offset = (mc.grating_cell_h - total) / 2
        for i in range(n):
            cell << pg.rectangle(
                size=(mc.grating_cell_w, line_w), layer=layer
            ).move((0, offset + i * pitch))

    label = cell << pg.text(
        text=f"L{line_w} S{space_w}",
        size=mc.grating_label_size,
        layer=3,
        font="DejaVu Sans",
    )
    label.move((mc.grating_label_x, mc.grating_label_y))
    return cell


def place_grating_section(parent, origin, mc):
    """
    Place two grating sub-sections beneath the main MEMS sections:

      Sub-section 1 – CD sweep:
        line_w = space_w ∈ mc.grating_cd_widths   (1:1 duty cycle)
        Rows: Vertical then Horizontal orientation

      Sub-section 2 – Duty-cycle sweep:
        line_w fixed = mc.grating_dc_line_w
        space_w ∈ mc.grating_dc_spaces
        Rows: Vertical then Horizontal orientation

    Column headers appear above the top row of each sub-section.
    Row labels appear to the left of each row.
    A section title sits above both sub-sections.
    """
    section     = Device("grating_section")
    cell_pitch_x = mc.grating_cell_w + mc.grating_gap_x
    cell_pitch_y = mc.grating_cell_h + mc.grating_gap_y

    # Each sub-section is 2 rows (V then H)
    # Layout (y increases upward in GDS):
    #   y=0              : V row, sub-section 1
    #   y=cell_pitch_y   : H row, sub-section 1
    #   y=2*cpy + gap    : V row, sub-section 2
    #   y=3*cpy + gap    : H row, sub-section 2
    # Column headers above each sub-section's top row.
    # Section title above everything.

    subsec_gap   = mc.grating_subsection_gap
    col_offset_x = mc.grating_col_offset_x     # space for row labels

    # ---- helper: place one sub-section ----
    def _place_subsec(base_y, line_ws, space_ws, col_hdr_fn):
        orientations = [
            (True,  "Vert."),
            (False, "Horiz."),
        ]
        for row_idx, (is_vert, orient_lbl) in enumerate(orientations):
            row_y = base_y + row_idx * cell_pitch_y

            # Row label
            rl = section << pg.text(
                text=orient_lbl, size=mc.grating_header_size, layer=3, font="DejaVu Sans"
            )
            rl.move((0, row_y + mc.grating_cell_h // 2 - mc.grating_header_size // 2))

            for col_idx, (lw, sw) in enumerate(zip(line_ws, space_ws)):
                cell_x = col_offset_x + col_idx * cell_pitch_x

                # Column header above the top row only
                if row_idx == len(orientations) - 1:
                    hdr = section << pg.text(
                        text=col_hdr_fn(lw, sw),
                        size=mc.grating_header_size,
                        layer=3,
                        font="DejaVu Sans",
                    )
                    hdr.move((cell_x, row_y + mc.grating_cell_h + 20))

                gcell = grating_cell(mc, lw, sw, is_vert)
                section << gcell.move((cell_x, row_y))

    # Sub-section 1: CD sweep
    _place_subsec(
        base_y    = 0,
        line_ws   = mc.grating_cd_widths,
        space_ws  = mc.grating_cd_widths,        # 1:1 duty cycle
        col_hdr_fn = lambda lw, sw: f"L=S={lw}µm",
    )

    # Sub-section 2: duty-cycle sweep
    dc_base_y = 2 * cell_pitch_y + subsec_gap
    _place_subsec(
        base_y    = dc_base_y,
        line_ws   = [mc.grating_dc_line_w] * len(mc.grating_dc_spaces),
        space_ws  = mc.grating_dc_spaces,
        col_hdr_fn = lambda lw, sw: f"L={lw} S={sw}µm",
    )

    # Sub-section titles
    ss1_title = section << pg.text(
        text=f"CD Sweep  (1:1 duty)",
        size=mc.grating_header_size, layer=3, font="DejaVu Sans",
    )
    ss1_title.move((col_offset_x, 2 * cell_pitch_y + 20))

    ss2_title = section << pg.text(
        text=f"Duty-Cycle Sweep  (line = {mc.grating_dc_line_w} µm)",
        size=mc.grating_header_size, layer=3, font="DejaVu Sans",
    )
    ss2_title.move((col_offset_x, dc_base_y + 2 * cell_pitch_y + 20))

    # Overall section title
    sec_title = section << pg.text(
        text="Line Gradient Characterization",
        size=mc.section_label_size, layer=3, font="DejaVu Sans",
    )
    sec_title.move((0, dc_base_y + 2 * cell_pitch_y + mc.grating_header_size + 60))

    parent << section.move(origin)


# ---------------------------------------------------------------------------
# Parameter object
# ---------------------------------------------------------------------------

def build_parameter_object():
    mc = EmptyClass()

    mc.lengths = [100, 200, 300, 400, 500]
    mc.widths  = [10, 15, 20]
    mc.gaps    = [2, 3, 5]

    mc.cell_label_size    = 42
    mc.cell_label_x       = 80
    mc.cell_label_y       = 80
    mc.header_text_size   = 70
    mc.section_label_size = 110

    mc.cell_pitch_x       = 1800
    mc.cell_pitch_y       = 1700
    mc.grid_origin_x      = 220
    mc.grid_origin_y      = 220
    mc.column_label_x     = 520
    mc.column_label_y     = 40
    mc.row_label_x        = 20
    mc.row_label_y_offset = 620

    mc.family_gap_x  = 1200
    mc.master_margin = 200

    # ---- cantilever ----
    mc.cant_unit_width             = 1500
    mc.cant_unit_height            = 1500
    mc.cant_edge_margin            = 150
    mc.cant_anchor_width           = 250
    mc.cant_anchor_height          = 250
    mc.cant_contact_width          = 250
    mc.cant_contact_height         = 250
    mc.cant_stem_width_max         = 60
    mc.cant_stem_length            = 180
    mc.cant_electrode_height       = 10
    mc.cant_electrode_start_offset = 30
    mc.cant_electrode_tip_overhang = 15
    mc.cant_fillet_radius          = 3   #(micrometer)

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

    # ---- clamped-clamped ----
    mc.cc_unit_width                   = 1500
    mc.cc_unit_height                  = 1500
    mc.cc_center_x                     = mc.cc_unit_width / 2
    mc.cc_anchor_width                 = 250
    mc.cc_anchor_height                = 250
    mc.cc_contact_width                = 250
    mc.cc_contact_height               = 250
    mc.cc_stem_width_max               = 60
    mc.cc_stem_length                  = 140
    mc.cc_electrode_height             = 10
    mc.cc_electrode_coverage_fraction  = 0.9
    mc.cc_electrode_tip_overhang       = 15
    mc.cc_anchor_clearance             = 25
    mc.cc_fillet_radius                = 3   # anchor-beam junction fillet radius (µm)

    mc.cc_reference_beam_length = 100
    mc.cc_fixed_left_anchor_x = cc_reference_left_anchor_x(
        mc, mc.cc_reference_beam_length
    )
    mc.cc_fixed_contact_x = (
        cc_beam_center_x(mc, mc.cc_fixed_left_anchor_x, mc.cc_reference_beam_length)
        - mc.cc_contact_width / 2
    )

    mc.output_gds = "mems_parameter_sweep_layout.gds"

    # ---- grating / line-gradient test structures ----
    mc.grating_cell_w         = 500    # µm, cell width
    mc.grating_cell_h         = 500    # µm, cell height
    mc.grating_gap_x          = 150    # µm, horizontal gap between cells
    mc.grating_gap_y          = 150    # µm, vertical gap between cells
    mc.grating_subsection_gap = 300    # µm, extra y-gap between CD and duty-cycle sub-sections
    mc.grating_label_size     = 28     # µm, text inside each grating cell
    mc.grating_label_x        = 10     # µm
    mc.grating_label_y        = 10     # µm
    mc.grating_header_size    = 60     # µm, column/row header text
    mc.grating_col_offset_x   = 400    # µm, x-space reserved for row labels
    mc.grating_cd_widths      = [1, 2, 3, 5, 10]   # µm, line=space CD sweep
    mc.grating_dc_line_w      = 3      # µm, fixed line width for duty-cycle sweep
    mc.grating_dc_spaces      = [1, 2, 5, 10, 20]  # µm, varying space widths

    return mc


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    mc     = build_parameter_object()
    master = Device("mems_parameter_sweep_layout")

    row_count     = len(mc.widths) * len(mc.gaps)
    section_width = mc.grid_origin_x + len(mc.lengths) * mc.cell_pitch_x

    cant_origin = (mc.master_margin, mc.master_margin + 200)
    cc_origin   = (
        cant_origin[0] + section_width + mc.family_gap_x,
        cant_origin[1],
    )

    add_section_label(
        master, "Cantilever Sweep",
        (cant_origin[0], mc.master_margin), mc.section_label_size,
    )
    add_section_label(
        master, "Clamped-Clamped Sweep",
        (cc_origin[0], mc.master_margin), mc.section_label_size,
    )

    place_parameter_grid(
        master, cant_origin, mc.lengths, mc.widths, mc.gaps,
        cantilever_cell, "cantilever_section", mc,
    )
    place_parameter_grid(
        master, cc_origin, mc.lengths, mc.widths, mc.gaps,
        clamped_clamped_cell, "clamped_clamped_section", mc,
    )

    master.write_gds(mc.output_gds)
    print(f"Wrote {mc.output_gds}")


if __name__ == "__main__":
    main()