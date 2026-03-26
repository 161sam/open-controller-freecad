# Plugin Installation

## Zielstruktur

Dieses Repository ist selbst der FreeCAD-Modulordner.

FreeCAD erwartet im Modulroot:

```text
OpenControllerFreeCAD/
├── Init.py
├── InitGui.py
├── ocf_freecad/
├── ocf_kicad/
└── resources/
```

Deshalb muss der Symlink immer auf den Repository-Root zeigen.

## Voraussetzungen

- FreeCAD
- Python + pip
- Git

## Dev-Setup unter Linux

```bash
git clone https://github.com/161sam/open-controller-freecad.git
cd open-controller-freecad
pip install -e .
mkdir -p ~/.local/share/FreeCAD/Mod
ln -s "$(pwd)" ~/.local/share/FreeCAD/Mod/OpenControllerFreeCAD
```

## Dev-Setup für Snap-FreeCAD

```bash
git clone https://github.com/161sam/open-controller-freecad.git
cd open-controller-freecad
pip install -e .
mkdir -p ~/snap/freecad/common/Mod
ln -s "$(pwd)" ~/snap/freecad/common/Mod/OpenControllerFreeCAD
```

## Start

```bash
freecad
```

Dann:
- FreeCAD öffnen
- Workbench `Open Controller` auswählen

## Prüfung

Wenn die Installation korrekt ist:
- FreeCAD findet `InitGui.py`
- die Workbench erscheint in der Workbench-Liste
- Icons werden geladen
- Templates, Varianten und Library-YAMLs sind verfügbar

## Troubleshooting

### Workbench fehlt

- prüfen, ob der Link auf den Repo-Root zeigt
- prüfen, ob im Zielordner `Init.py` und `InitGui.py` direkt liegen
- FreeCAD vollständig neu starten

### Icons fehlen

- prüfen, ob `resources/icons/` im Modulroot vorhanden ist
- prüfen, ob nicht versehentlich nur `ocf_freecad/` verlinkt wurde

### YAML-/Template-Daten fehlen

- prüfen, ob `ocf_freecad/templates/`, `ocf_freecad/variants/`, `ocf_freecad/library/` und `ocf_freecad/plugins/internal/` vorhanden sind
- prüfen, ob FreeCAD das richtige Modulverzeichnis lädt

### Importfehler

- `pip install -e .` erneut ausführen
- Python-Umgebung von FreeCAD beachten

## Zukunft

- Addon-Manager-Integration
- Release-ZIP mit kompletter Modulstruktur
