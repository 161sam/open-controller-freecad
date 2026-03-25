from __future__ import annotations

from ocf_freecad.commands.base import BaseCommand


class AddComponentCommand(BaseCommand):
    def GetResources(self):
        return {
            "MenuText": "Add Component",
            "ToolTip": "Open the component library task panel",
        }

    def Activated(self):
        import FreeCAD as App
        import FreeCADGui as Gui

        from ocf_freecad.gui.taskpanels.library_taskpanel import LibraryTaskPanel

        doc = App.ActiveDocument
        if doc is None:
            raise RuntimeError("No active FreeCAD document")
        Gui.Control.showDialog(LibraryTaskPanel(doc))
