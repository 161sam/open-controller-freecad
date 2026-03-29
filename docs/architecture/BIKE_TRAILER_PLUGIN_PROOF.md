# Bike Trailer Plugin Proof

## Purpose

`plugin_bike_trailer` is a proof-domain plugin for the GeneratorWorkbench architecture.

It demonstrates that the same core workbench can drive a second, non-MIDI domain by reusing:

- plugin loading and activation
- template loading
- component library loading
- plugin-driven command metadata
- toolbar generation
- tree grouping
- direct placement and drag workflows

## Included Data

Templates:

- `trailer_basic`
- `trailer_box`

Components:

- `wheel_20in_spoked`
- `drawbar_hitch_standard`
- `axle_mount_plate_pair`
- `frame_connector_crossbar`
- `cargo_box_module_standard`

Commands:

- `place_wheel`
- `place_hitch`
- `place_frame_connector`
- `place_axle_mount`
- `place_cargo_box_module`

## What This Validates

- Core template flow is not MIDI-specific.
- Core component flow is not MIDI-specific.
- Toolbar commands can come entirely from plugin metadata.
- Tree grouping and generated component objects are reusable across domains.
- Direct placement and drag interactions work without plugin-specific UI code.

## Current Boundaries

- The generated document model still uses historic `OCW_*` object naming.
- The geometric host model is still the existing generic enclosure/body pipeline.
- Bike trailer uses the generic component fallback geometry path for non-MIDI component types.

These are acceptable for the proof because the architecture goal is plugin genericity, not final trailer-specific CAD semantics.
