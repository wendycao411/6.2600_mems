from phidl import Device
import phidl.geometry as pg


##########################################
# Layers:
# 1 = device geometry
# 2 = contact blocks
# 3 = labels
##########################################


class EmptyClass:
    pass


def validate_within_border(device, mc):
    """Ensure all geometry stays inside the cell edge exclusion margin."""
    xmin, ymin = device.xmin, device.ymin
    xmax, ymax = device.xmax, device.ymax

    if xmin < mc.edge_margin or ymin < mc.edge_margin:
        raise ValueError("Geometry violates the minimum border on the left or bottom edge")
    if xmax > mc.unit_width - mc.edge_margin or ymax > mc.unit_height - mc.edge_margin:
        raise ValueError("Geometry violates the minimum border on the right or top edge")


def make_contact_block(size, layer=2):
    """Create a rectangular contact block."""
    block = Device("contact_block")
    block << pg.rectangle(size=size, layer=layer)
    return block


def cantilever_total_width(mc, beam_length):
    """Return the full horizontal span of the cantilever geometry."""
    right_extension = mc.electrode_tip_overhang + (
        mc.electrode_contact_width - mc.electrode_stem_width
    ) / 2
    return mc.anchor_width + beam_length + right_extension


def cantilever_reference_beam_xmax(mc, beam_length):
    """Keep the cantilever tip at the reference location for a given beam length."""
    anchor_x = (mc.unit_width - cantilever_total_width(mc, beam_length)) / 2
    return anchor_x + mc.anchor_width + beam_length


def make_electrode_structure(mc, beam, is_top):
    """Create one sketch-style electrode: contact block, stem, and wide finger."""
    electrode = Device("electrode_structure")
    beam_xmin = beam.xmin
    beam_xmax = beam.xmax
    beam_ymin = beam.ymin
    beam_ymax = beam.ymax

    finger_left = beam_xmin + mc.electrode_start_offset
    finger_right = beam_xmax + mc.electrode_tip_overhang
    stem_x = finger_right - mc.electrode_stem_width
    contact_x = stem_x + mc.electrode_stem_width / 2 - mc.electrode_contact_width / 2
    contact_x = min(
        max(contact_x, mc.edge_margin),
        mc.unit_width - mc.edge_margin - mc.electrode_contact_width,
    )

    if is_top:
        finger_y = beam_ymax + mc.beam_gap
        stem_y = finger_y + mc.electrode_finger_height
        stem_length = mc.electrode_stem_length
        contact_y = stem_y + stem_length
    else:
        finger_y = beam_ymin - mc.beam_gap - mc.electrode_finger_height
        contact_y = finger_y - mc.electrode_stem_length - mc.electrode_contact_height
        stem_y = contact_y + mc.electrode_contact_height
        stem_length = mc.electrode_stem_length

    if contact_y < mc.edge_margin:
        raise ValueError("Bottom contact block violates edge margin; adjust stem length")
    if contact_y + mc.electrode_contact_height > mc.unit_height - mc.edge_margin:
        raise ValueError("Top contact block violates edge margin; adjust stem length")

    contact = electrode << make_contact_block(
        (mc.electrode_contact_width, mc.electrode_contact_height), layer=2
    )
    contact.move((contact_x, contact_y))

    if stem_length <= 0:
        raise ValueError("Electrode stem length is non-positive; adjust geometry")

    stem = electrode << pg.rectangle(
        size=(mc.electrode_stem_width, stem_length),
        layer=1,
    )
    stem.move((stem_x, stem_y))

    finger_width = finger_right - finger_left
    if finger_width <= 0:
        raise ValueError("Electrode finger width is non-positive; adjust geometry")

    finger = electrode << pg.rectangle(
        size=(finger_width, mc.electrode_finger_height),
        layer=1,
    )
    finger.move((finger_left, finger_y))

    return electrode


def cantilever_core(mc):
    """Create the anchor, beam, and paired electrodes."""
    core = Device("cantilever_core")

    anchor = core << pg.rectangle(
        size=(mc.anchor_width, mc.anchor_height), layer=1
    )
    anchor.move((mc.anchor_x, mc.anchor_y))

    beam_y = mc.anchor_y + (mc.anchor_height - mc.beam_width) / 2
    beam = core << pg.rectangle(size=(mc.beam_length, mc.beam_width), layer=1)
    beam.move((mc.anchor_x + mc.anchor_width, beam_y))

    core << make_electrode_structure(mc, beam, is_top=True)
    core << make_electrode_structure(mc, beam, is_top=False)

    label = core << pg.text(
        text=f"L={mc.beam_length} W={mc.beam_width} G={mc.beam_gap}",
        size=mc.label_size,
        layer=3,
        font="Arial",
    )
    label.move((mc.label_x, mc.label_y))

    return core


def cantilever_reference_cell(mc):
    """Create one single uncluttered cantilever reference cell."""
    cell = Device("cantilever_reference_cell")
    core = cell << cantilever_core(mc)
    validate_within_border(core, mc)
    return cell


def build_parameter_object():
    mc = EmptyClass()

    mc.unit_width = 1500
    mc.unit_height = 1500
    mc.edge_margin = 150

    mc.beam_center_y = mc.unit_height / 2
    mc.anchor_width = 250
    mc.anchor_height = 250
    mc.beam_length = 500
    mc.beam_width = 10
    mc.beam_gap = 3

    mc.electrode_contact_width = 250
    mc.electrode_contact_height = 250
    mc.electrode_stem_width = 20
    mc.electrode_stem_length = 180
    mc.electrode_finger_height = 90
    mc.electrode_start_offset = 30
    mc.electrode_tip_overhang = 15

    mc.reference_beam_length = 500
    mc.fixed_beam_xmax = cantilever_reference_beam_xmax(mc, mc.reference_beam_length)
    mc.anchor_x = mc.fixed_beam_xmax - mc.beam_length - mc.anchor_width
    mc.anchor_y = mc.beam_center_y - mc.anchor_height / 2

    mc.label_size = 65
    mc.label_x = mc.edge_margin + 20
    mc.label_y = mc.unit_height - mc.edge_margin - mc.label_size - 40

    return mc


def main():
    mc = build_parameter_object()
    cell = cantilever_reference_cell(mc)
    cell.write_gds("cantilever_reference_cell.gds")
    print("Wrote cantilever_reference_cell.gds")


if __name__ == "__main__":
    main()
