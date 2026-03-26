
# User Guide

## Zielgruppe

- Maker
- Hardware Devs
- DIY Controller Builder

## Einstieg

1. Plugin installieren
2. Workbench öffnen
3. Projekt starten

## Workflow

1. Größe definieren
2. Komponenten platzieren
3. Cutouts prüfen
4. Export

## Component Palette

- Öffne die Palette über `OCW_OpenComponentPalette`
- Suche live über Name, ID, Part Number und Tags
- Filtere nach UI-Kategorie oder nur nach Favoriten
- Ein Klick wählt ein Component Template für den nächsten Add/Place-Schritt vor
- Favoriten können direkt in der Palette per Stern markiert werden
- Bis zu 8 Favoriten erscheinen als Icon-Buttons in der Toolbar `OCW Favorites`
- Favoriten werden in UserData gespeichert und bleiben über Neustarts erhalten
- `Place In 3D` startet den interaktiven Platzierungsmodus im 3D-View
- Die Ghost-Vorschau folgt der Maus nur über Overlay-Preview
- Klick platziert die Komponente, `ESC` bricht den Modus ohne Modelländerung ab
- `OCW_DragMoveComponent` startet den Drag-Modus für bestehende Komponenten
- Klicke eine vorhandene Komponente im 3D-View an, ziehe sie und lasse los zum Commit
- Während des Ziehens bleibt das Modell unverändert; nur das Overlay-Ghost wird aktualisiert

## Import Template From FCStd

- Starte `OCW_ImportTemplateFromFCStd`
- Wähle eine `.FCStd` Datei und lade die importierbaren Objekte oder Flächen
- Wähle die Referenzfläche für die Top Surface und optional einen Origin-Vertex
- Passe Offsets, Rotation und optional die Höhe an
- Der Import erzeugt ein YAML-Template im User-Templates-Ordner und macht es anschließend in der Template-Auswahl sichtbar

## Begriffe

- Controller
- Component
- Cutout
- Keepout

## Status

Noch Early Stage – Fokus aktuell auf Dev & Architektur
