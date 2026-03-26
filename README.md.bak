
# Open Controller FreeCAD

FreeCAD Workbench for designing modular MIDI controllers.

## Goals

- Parametric controller design
- Hardware-aware layout (encoders, buttons, displays, etc.)
- Automatic generation of:
  - Mechanical models (FreeCAD)
  - Hardware schema (`controller.hw.yaml`)
  - KiCad PCB layout (future)
  - OCF device descriptors (future)

## Architecture

This plugin follows a layered architecture:

- **Workbench/UI** → FreeCAD integration
- **Domain** → Controller + components
- **Schema** → YAML import/export
- **Generator** → geometry + layout
- **Library** → component definitions
- **Exporters** → outputs (CAD, KiCad, OCF)

## Status

🚧 Early development (v1 bootstrap)

## Dev Setup

```bash
pip install -e .
````

Then symlink into FreeCAD:

```bash
ln -s $(pwd)/ocf_freecad ~/.FreeCAD/Mod/OpenController
```

## License

MIT (or to be defined)
