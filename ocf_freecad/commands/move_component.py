from __future__ import annotations

from ocf_freecad.commands.base import BaseCommand


class MoveComponentCommand(BaseCommand):
    def GetResources(self):
        return {
            "MenuText": "Move Component",
            "ToolTip": "Open the layout task panel for position editing",
        }

    def Activated(self):
        import FreeCAD as App
        import FreeCADGui as Gui

        from ocf_freecad.gui.taskpanels.layout_taskpanel import LayoutTaskPanel

        doc = App.ActiveDocument
        if doc is None:
            raise RuntimeError("No active FreeCAD document")
        Gui.Control.showDialog(LayoutTaskPanel(doc))
