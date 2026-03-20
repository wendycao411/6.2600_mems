from phidl import Device
import phidl.geometry as pg


##########################################
# Layers:
# 1 = device silicon / structural geometry
# 2 = optional contact blocks
# 3 = labels
# 11 = optional outline / visualization
##########################################


class EmptyClass:
    pass


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


def reference_left_anchor_x(mc, beam_length):
    return mc.center_x - (beam_length / 2 + mc.anchor_width)


def beam_center_x(mc, left_anchor_x, beam_length):
    return left_anchor_x + mc.anchor_width + beam_length / 2


def outline(mc):
    """Optional unit-cell outline for visualization."""
    cell_outline = Device("outline")
    cell_outline << pg.rectangle(size=(mc.unit_width, mc.unit_height), layer=11)
    return cell_outline


def make_anchor(mc):
    anchor = Device("anchor")
    anchor << pg.rectangle(size=(mc.anchor_width, mc.anchor_height), layer=1)
    return anchor


def make_beam(mc, L, W):
    beam = Device("beam")
    beam << pg.rectangle(size=(L, W), layer=1)
    return beam


def make_electrode_contact(mc):
    contact = Device("electrode_contact")
    contact << pg.rectangle(
        size=(mc.contact_width, mc.contact_height),
        layer=2,
    )
    return contact


def make_center_electrode(mc, beam_ref, gap, is_top):
    """Create one centered electrode with a wide active region, thin stem, and contact."""
    electrode = Device("center_electrode")

    max_active_length = beam_ref.xsize - 2 * mc.anchor_clearance
    if max_active_length <= 0:
        raise ValueError("Beam is too short for the requested anchor clearance")

    target_active_length = min(
        mc.electrode_coverage_fraction * beam_ref.xsize,
        beam_ref.xsize + mc.electrode_tip_overhang,
    )
    active_length = min(target_active_length, max_active_length)

    active_center_x = beam_ref.center[0]
    active_x = active_center_x - active_length / 2
    contact_x = mc.fixed_contact_x
    contact_center_x = contact_x + mc.contact_width / 2
    stem_core_width = min(mc.stem_width_max, mc.contact_width, active_length)
    stem_x = active_x
    stem_right = max(contact_center_x + stem_core_width / 2, active_x + stem_core_width)
    stem_width = stem_right - stem_x

    if is_top:
        active_y = beam_ref.ymax + gap
        stem_y = active_y + mc.active_electrode_height
        contact_y = stem_y + mc.stem_length
    else:
        active_y = beam_ref.ymin - gap - mc.active_electrode_height
        contact_y = active_y - mc.stem_length - mc.contact_height
        stem_y = contact_y + mc.contact_height

    electrode << pg.rectangle(
        size=(active_length, mc.active_electrode_height),
        layer=1,
    ).move((active_x, active_y))
    electrode << pg.rectangle(
        size=(stem_width, mc.stem_length),
        layer=1,
    ).move((stem_x, stem_y))
    electrode << make_electrode_contact(mc).move((contact_x, contact_y))

    return electrode


def clamped_clamped_cell(mc, L, W, gap):
    """Build one clamped-clamped beam resonator cell."""
    cell = Device(f"clamped_clamped_L{L}_W{W}_G{gap}")

    if mc.draw_outline:
        cell << outline(mc)

    beam_y = mc.unit_height / 2 - W / 2
    left_anchor_x = mc.fixed_left_anchor_x
    right_anchor_x = mc.center_x + L / 2
    right_anchor_x = left_anchor_x + mc.anchor_width + L
    anchor_y = mc.unit_height / 2 - mc.anchor_height / 2

    left_anchor = cell << make_anchor(mc)
    left_anchor.move((left_anchor_x, anchor_y))

    beam = cell << make_beam(mc, L, W)
    beam.move((left_anchor_x + mc.anchor_width, beam_y))

    fillets = make_fillet_pieces(mc.fillet_radius, layer=1)
    left_jx = left_anchor_x + mc.anchor_width
    right_jx = right_anchor_x

    cell << fillets["tr"].move((left_jx, beam_y + W))
    cell << fillets["br"].move((left_jx, beam_y))
    cell << fillets["tl"].move((right_jx, beam_y + W))
    cell << fillets["bl"].move((right_jx, beam_y))

    right_anchor = cell << make_anchor(mc)
    right_anchor.move((right_anchor_x, anchor_y))

    cell << make_center_electrode(mc, beam, gap=gap, is_top=True)
    cell << make_center_electrode(mc, beam, gap=gap, is_top=False)

    label = cell << pg.text(
        text=f"L={L} W={W} G={gap}",
        size=mc.label_size,
        layer=3,
        font="Arial",
    )
    label.move((mc.label_x, mc.label_y))

    return cell


def build_parameter_object():
    mc = EmptyClass()

    mc.unit_width = 1500
    mc.unit_height = 1500
    mc.center_x = mc.unit_width / 2
    mc.draw_outline = True

    mc.anchor_width = 250
    mc.anchor_height = 250

    mc.contact_width = 250
    mc.contact_height = 250
    mc.stem_width_max = 60
    mc.stem_length = 140
    mc.active_electrode_height = 10
    mc.electrode_coverage_fraction = 0.9
    mc.electrode_tip_overhang = 15
    mc.anchor_clearance = 25
    mc.fillet_radius = 5
    mc.reference_beam_length = 100
    mc.fixed_left_anchor_x = reference_left_anchor_x(mc, mc.reference_beam_length)
    mc.fixed_contact_x = (
        beam_center_x(mc, mc.fixed_left_anchor_x, mc.reference_beam_length)
        - mc.contact_width / 2
    )

    mc.label_size = 55
    mc.label_x = 120
    mc.label_y = 120

    mc.output_gds = "clamped_clamped_cell.gds"

    return mc


def main():
    mc = build_parameter_object()
    cell = clamped_clamped_cell(mc, L=300, W=3, gap=3)
    cell.write_gds(mc.output_gds)
    print(f"Wrote {mc.output_gds}")


if __name__ == "__main__":
    main()
