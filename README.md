# MEMS PHIDL Layouts

This directory contains PHIDL scripts for two MEMS resonator families and a combined parameter-sweep layout:

- cantilever beam devices
- clamped-clamped beam devices
- an organized sweep layout containing both families
- an inverted one-layer mask layout derived from the sweep

## Files

- `cantilever_design.py`
  Generates a single cantilever reference cell and writes `cantilever_reference_cell.gds`.

- `clamped_clamped_cell.py`
  Generates a single clamped-clamped reference cell and writes `clamped_clamped_cell.gds`.

- `mems_parameter_sweep_layout.py`
  Generates the full organized sweep layout for both families and writes `mems_parameter_sweep_layout.gds`.

- `invert_mems_layout.py`
  Rebuilds the sweep layout, subtracts it from a background rectangle, and writes a one-layer inverted mask `mems_parameter_sweep_layout_inverted.gds`.

- `solarcellS26.py`
  Older solar-cell script kept in the repo but not part of the MEMS layout flow.

## Layer Convention

- `1`: structural / device geometry
- `2`: contact blocks / pads
- `3`: text labels
- `11`: visualization outlines only

The inverted mask script writes a single output layer.

## Device Families

### Cantilever

Geometry intent:

- single left anchor
- horizontal beam extending right
- top and bottom electrodes near the beam
- fixed contact-pad positions for consistency across the sweep

Current reference parameters in `cantilever_design.py`:

- unit cell: `1500 x 1500 um`
- border margin check: `150 um`
- anchor: `250 x 250 um`
- default single-cell beam: `L=500 um`, `W=3 um`, `G=3 um`
- contact pads: `250 x 250 um`
- stem width: fixed at `60 um`
- stem length: `180 um`
- electrode finger height: `10 um`
- electrode start offset from beam start: `30 um`
- electrode tip overhang: `15 um`

Placement rules:

- the cantilever anchor is fixed to the reference position from the `500 um` beam case
- the contact pads are fixed to the position centered over the `100 um` beam case
- the stem width is fixed using the `100 um` beam reference
- the stem begins at the same left `x` coordinate as the electrode finger
- the electrode finger length changes with beam length

### Clamped-Clamped

Geometry intent:

- left anchor, free beam span, right anchor
- centered top drive electrode
- centered bottom sense electrode
- fixed left-side reference features for consistency across the sweep

Current reference parameters in `clamped_clamped_cell.py`:

- unit cell: `1500 x 1500 um`
- anchor blocks: `250 x 250 um`
- contact pads: `250 x 250 um`
- stem width cap: `60 um`
- stem length: `140 um`
- active electrode height: `10 um`
- electrode coverage fraction: `0.9`
- electrode tip overhang: `15 um`
- anchor clearance: `25 um`
- default single-cell beam: `L=300 um`, `W=3 um`, `G=3 um`

Placement rules:

- the left anchor stays fixed to the `100 um` beam reference position
- the top and bottom contact pads stay fixed to the `100 um` beam reference position
- the right anchor moves to extend the beam length
- the beam extends rightward from the fixed left side
- the stem starts at the left edge of the active electrode, so there is no extra stem overhang to the left of the electrode

## Parameter Sweep Layout

`mems_parameter_sweep_layout.py` generates two labeled sections:

- `Cantilever Sweep`
- `Clamped-Clamped Sweep`

Each section includes all combinations of:

- beam length: `[100, 200, 300, 400, 500] um`
- beam width: `[3, 4, 5] um`
- gap: `[2, 3, 5] um`

That is:

- `45` cells per family
- `90` total cells in the full sweep layout

Grid organization:

- columns correspond to beam length
- rows correspond to `(W, G)` combinations in this order:
  - `W=3, G=2`
  - `W=3, G=3`
  - `W=3, G=5`
  - `W=4, G=2`
  - `W=4, G=3`
  - `W=4, G=5`
  - `W=5, G=2`
  - `W=5, G=3`
  - `W=5, G=5`

Layout spacing is intentionally generous for inspection in KLayout rather than compact chip packing.

Current sweep-layout pitch:

- cell pitch x: `1800 um`
- cell pitch y: `1700 um`
- family spacing x: `1200 um`
- total master layout size: approximately `20840 um x 15720 um`

## Notes

- The code is structured around small helper functions so beam length, width, gap, and placement rules can be adjusted later.
- The current layout is optimized for readability and repeatable pad placement, not compact chip fitting.
- The inverted mask script currently inverts layers `1`, `2`, and `3` together into one mask layer.
