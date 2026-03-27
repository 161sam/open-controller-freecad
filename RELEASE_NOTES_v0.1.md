# Release Notes v0.1.0

## Summary

`v0.1.0` is the first release-preparation milestone for Open Controller Workbench.

This release packages the current FreeCAD workbench architecture into a coherent alpha feature set for:

- template-driven controller creation
- component placement and refinement
- parameterized controller regeneration
- FCStd-assisted template import
- constraint and overlay-assisted layout iteration

## Included in v0.1.0

- FreeCAD workbench bootstrap through `InitGui.py`
- Create flow from templates and variants
- Template parameters, presets, and project-scoped parameter persistence
- Re-parameterization of reopened projects when source metadata is available
- FCStd import:
  - Stage A YAML template generation
  - Stage B FCStd-backed base geometry references
- Template inspector and validated save flow
- Interactive placement and drag with preview validation and cleanup hardening
- Undo-safe transaction boundaries for interactive commit actions
- Component property editing
- Multi-selection and conservative bulk edit
- Layout productivity operations:
  - align and distribute
  - rotate and mirror
  - duplicate and array placement

## Installation

Use the repository root as the FreeCAD module directory. See:

- [README](README.md)
- [Installation guide](docs/plugin-installation.md)

## Recommended validation before tagging

- Run the unit test suite
- Run `tests/unit/test_release_metadata.py`
- Verify FreeCAD loads the workbench from a clean symlinked module root
- Verify icons, template YAML files, variants, and component libraries are available at runtime

## Known limitations

- Alpha-quality release with active architectural evolution
- No final public license selection yet
- Mirror is modeled through component rotation semantics
- Duplicate and array placement do not perform smart constraint-aware packing
- No release publishing automation is included in this repository yet

## Explicit non-goals for v0.1.0

- No full constraint solver
- No advanced interactive layout gizmos
- No complete PartDesign-native parametric rebuild model
- No release publishing from CI in this task
