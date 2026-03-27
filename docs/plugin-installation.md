# Installation

## Module root requirement

This repository is the FreeCAD module root.

FreeCAD expects the following structure directly in the module directory:

```text
OpenControllerWorkbench/
├── Init.py
├── InitGui.py
├── ocw_workbench/
├── ocw_kicad/
└── resources/
```

Always link or copy the repository root itself. Do not point FreeCAD only at `ocw_workbench/`.

## Requirements

- FreeCAD
- Python and `pip`
- Git

## Linux development install

```bash
git clone https://github.com/161sam/open-controller-workbench.git
cd open-controller-workbench
pip install -e .
mkdir -p ~/.local/share/FreeCAD/Mod
ln -s "$(pwd)" ~/.local/share/FreeCAD/Mod/OpenControllerWorkbench
```

## Snap FreeCAD development install

```bash
git clone https://github.com/161sam/open-controller-workbench.git
cd open-controller-workbench
pip install -e .
mkdir -p ~/snap/freecad/common/Mod
ln -s "$(pwd)" ~/snap/freecad/common/Mod/OpenControllerWorkbench
```

## Startup check

1. Start FreeCAD.
2. Open the workbench selector.
3. Select `Open Controller Workbench`.

If installation is correct:

- FreeCAD finds `InitGui.py`
- the workbench appears in the workbench list
- icons load
- templates, variants, and library YAML data are available

## Troubleshooting

### Workbench does not appear

- Confirm the symlink points to the repository root.
- Confirm `Init.py` and `InitGui.py` are directly inside the target directory.
- Restart FreeCAD completely.

### Icons are missing

- Confirm `resources/icons/` exists in the linked module root.
- Confirm only the repository root is linked, not `ocw_workbench/` alone.

### YAML template or library data is missing

- Confirm these paths exist in the linked module root:
  - `ocw_workbench/templates/`
  - `ocw_workbench/variants/`
  - `ocw_workbench/library/`
  - `ocw_workbench/plugins/internal/`
- Confirm FreeCAD loaded the expected module directory.

### Import errors

- Re-run `pip install -e .`
- Verify which Python environment your FreeCAD build uses

## Distribution note

`v0.1.0` is prepared for source and wheel builds, but no public package publication is performed in this task.
