
# Development Guide

## Setup

```bash
git clone https://github.com/161sam/open-controller-freecad.git
cd open-controller-freecad
pip install -e .
```

Für FreeCAD-Entwicklung zusätzlich:

```bash
mkdir -p ~/.local/share/FreeCAD/Mod
ln -s "$(pwd)" ~/.local/share/FreeCAD/Mod/OpenControllerFreeCAD
```

## FreeCAD-Modulstruktur

```text
open-controller-freecad/
├── Init.py
├── InitGui.py
├── ocf_freecad/
│   ├── commands/
│   ├── domain/
│   ├── freecad_api/
│   ├── generator/
│   ├── geometry/
│   ├── gui/
│   ├── layout/
│   ├── library/
│   ├── plugins/
│   ├── schema/
│   ├── services/
│   ├── templates/
│   └── variants/
├── ocf_kicad/
├── resources/
└── docs/
```

Wichtig:
- FreeCAD lädt den Modulroot
- `InitGui.py` registriert die Workbench
- Ressourcen im Top-Level-Ordner `resources/` müssen relativ zum Modulroot auffindbar bleiben
- Laufzeit-YAML-Daten liegen im Package unter `ocf_freecad/`

## Prinzipien

- keine Logik in Commands
- Domain unabhängig von FreeCAD
- Geometry testbar
- Repo-Root bleibt FreeCAD-kompatibler Modulroot

## Einstiegspunkte

- `InitGui.py`
- `ocf_freecad/workbench.py`
- `ocf_freecad/services/controller_service.py`
- `ocf_freecad/generator/controller_builder.py`

## Packaging

Für Packaging müssen mitkommen:
- `Init.py`
- `InitGui.py`
- `resources/icons/*`
- YAML-Dateien in `ocf_freecad/library/`
- YAML-Dateien in `ocf_freecad/templates/`
- YAML-Dateien in `ocf_freecad/variants/`
- interne Plugin-Manifest- und Daten-Dateien in `ocf_freecad/plugins/internal/`

## Roadmap Dev

1. Schema erweitern
2. Mapping bauen
3. Builder testen
4. GUI erweitern
5. Export stabilisieren

## Tests

- Schema
- Builder
- Resolver
- Workbench-/Command-Flows
