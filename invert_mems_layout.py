from phidl import Device
import phidl.geometry as pg

import mems_parameter_sweep_layout as base


MASK_LAYER = 1


def build_source_layout():
    """Recreate the current MEMS parameter sweep layout."""
    mc = base.build_parameter_object()
    master = Device("mems_parameter_sweep_layout")

    row_count = len(mc.widths) * len(mc.gaps)
    section_width = mc.grid_origin_x + len(mc.lengths) * mc.cell_pitch_x

    cant_origin = (mc.master_margin, mc.master_margin + 200)
    cc_origin = (
        cant_origin[0] + section_width + mc.family_gap_x,
        cant_origin[1],
    )

    base.add_section_label(
        master,
        "Cantilever Sweep",
        (cant_origin[0], mc.master_margin),
        mc.section_label_size,
    )
    base.add_section_label(
        master,
        "Clamped-Clamped Sweep",
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
        "cantilever_section",
        mc,
    )
    base.place_parameter_grid(
        master,
        cc_origin,
        mc.lengths,
        mc.widths,
        mc.gaps,
        base.clamped_clamped_cell,
        "clamped_clamped_section",
        mc,
    )
    return master


def invert_layout(source, border=200, output_layer=MASK_LAYER):
    """
    Create a one-layer inverted mask by subtracting the design geometry from
    a background rectangle.
    """
    mask_source = pg.extract(source, layers=[1, 2, 3])
    xmin, ymin = mask_source.xmin, mask_source.ymin
    xmax, ymax = mask_source.xmax, mask_source.ymax

    background = Device("mask_background")
    background << pg.rectangle(
        size=(xmax - xmin + 2 * border, ymax - ymin + 2 * border),
        layer=output_layer,
    ).move((xmin - border, ymin - border))

    inverted = pg.boolean(
        A=background,
        B=mask_source,
        operation="A-B",
        precision=1e-6,
        layer=output_layer,
    )

    mask = Device("inverted_mems_mask")
    mask << inverted
    return mask


def main():
    source = build_source_layout()
    mask = invert_layout(source, border=200, output_layer=MASK_LAYER)
    output_gds = "mems_parameter_sweep_layout_inverted.gds"
    mask.write_gds(output_gds)
    print(f"Wrote {output_gds}")


if __name__ == "__main__":
    main()
