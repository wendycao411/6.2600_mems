from phidl import Device
import phidl.geometry as pg

import mems_parameter_sweep_layout as base
import array_4x4 as array_module


MASK_LAYER = 1


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

    mask = Device("inverted_mems_array_mask")
    mask << inverted
    return mask


def main():
    source = array_module.make_array_4x4()
    mask = invert_layout(source, border=200, output_layer=MASK_LAYER)
    output_gds = "mems_parameter_sweep_array_4x4_inverted.gds"
    mask.write_gds(output_gds)
    print(f"Wrote {output_gds}")


if __name__ == "__main__":
    main()