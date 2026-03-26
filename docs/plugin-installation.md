
# Plugin Installation

## Voraussetzungen

- FreeCAD
- Python + pip
- Git

## Installation (Dev)

```bash
git clone https://github.com/161sam/open-controller-freecad.git
cd open-controller-freecad
pip install -e .
````

## FreeCAD Integration

```bash
mkdir -p ~/.local/share/FreeCAD/Mod
ln -s "$(pwd)/ocf_freecad" ~/.local/share/FreeCAD/Mod/OpenController
```

## Start

* FreeCAD öffnen
* Workbench: "Open Controller"

## Troubleshooting

### Workbench fehlt

* Pfad prüfen
* Neustart

### Importfehler

* pip install prüfen
* Python-Version von FreeCAD beachten

## Zukunft

* Addon Manager Integration
* Release ZIPs
