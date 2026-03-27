# Changelog

All notable changes to Open Controller Workbench are documented in this file.

The format follows a lightweight Keep a Changelog style.

## [0.1.0] - 2026-03-27

### Added

- FreeCAD workbench bootstrap and dock-based OCW UI shell
- Template and variant driven controller creation flow
- Template parameter model, presets, resolver flow, and project parameter roundtrip
- FCStd import workflow with:
  - Stage A YAML template generation
  - Stage B `custom_fcstd` base geometry support
- Template inspector with parameter editing and validated save flow
- Interactive place and drag tools with preview-only metadata, cleanup hardening, and undo-safe commit boundaries
- Live preview validation feedback for bounds, overlap risk, and keepout warnings
- Component property panel with dynamic family-specific fields
- Multi-selection, bulk edit, align/distribute, rotate/mirror, duplicate, and array placement productivity commands
- Overlay, constraint validation, plugin, export, and template/library data flows

### Changed

- README, installation guidance, workflows, and release documentation were hardened for the `v0.1.0` release target
- Packaging metadata was aligned to `0.1.0`
- Setuptools distribution metadata now explicitly includes icon resources as install data

### Known limitations

- The project remains alpha-quality and should be treated as an early workflow release
- No final public license has been selected yet
- Mirror uses the current rotation-based orientation model
- Duplicate and array placement are intentionally simple and not constraint-aware
- The repository is prepared for release, but no GitHub release or package publication is performed in this task
