# Template Schema

## Parameter Definitions

Templates can declare a `parameters` list.

Each parameter entry supports:

- `id`
- `label`
- `type`
  - `int`
  - `float`
  - `bool`
  - `enum`
  - `string`
- `default`
- `min`
- `max`
- `step`
- `control`
  - `input`
  - `slider`
  - `select`
  - `toggle`
  - `button_group`
- `unit`
- `help`
- `options`
  - required for `enum`

Example:

```yaml
parameters:
  - id: "pad_count_x"
    label: "Pad Count X"
    type: "int"
    default: 4
    min: 2
    max: 8
    step: 1
    control: "slider"
    help: "Number of pad columns."
```

## Template Parameter Presets

Templates can also ship named parameter sets:

```yaml
parameter_presets:
  - id: "pad_grid_8x2"
    name: "8x2 Pad Grid"
    values:
      pad_count_x: 8
      pad_count_y: 2
      case_width: 300.0
      case_depth: 110.0
```

Preset values are applied before user overrides.

## Parameter Bindings

Templates apply parameters through `parameter_bindings`.

### Direct Value Bindings

Use `parameter_bindings.values` to copy a parameter into a controller, layout, zone, or component field.

```yaml
parameter_bindings:
  values:
    - target: "controller.width"
      parameter: "case_width"
    - target: "components[fader1].library_ref"
      parameter: "fader_length"
      value_map:
        "45": "generic_45mm_linear_fader"
        "60": "generic_60mm_linear_fader"
```

Supported target path patterns:

- `controller.width`
- `controller.surface.width`
- `layout.config.rows`
- `components[component_id].library_ref`
- `zones[zone_id].width`

### Generated Component Grids

Use `parameter_bindings.component_grids` for parameter-driven repeated component generation.

```yaml
parameter_bindings:
  component_grids:
    - id_prefix: "pad"
      count_x_parameter: "pad_count_x"
      count_y_parameter: "pad_count_y"
      component:
        type: "pad"
        library_ref: "generic_mpc_pad_30mm"
        zone: "pad_matrix"
```

This appends generated components to the template component list.

## Runtime And State

- Template defaults are applied automatically during template or variant resolution.
- Runtime parameter overrides use:

```yaml
overrides:
  parameters:
    case_width: 190.0
    fader_length: 45
  parameter_preset_id: "compact_fader"
```

- Resolved parameter values are stored in project state under `meta.parameters`.
- Project state stores:
  - `values`
  - `sources`
  - `preset_id`

## Compatibility

- Templates without parameter fields remain valid and unchanged.
- Variants continue to work and can add or replace `parameters`, `parameter_presets`, or `parameter_bindings` if needed.
- The current implementation is intentionally declarative and finite. It is not a scripting language or a general expression engine.
