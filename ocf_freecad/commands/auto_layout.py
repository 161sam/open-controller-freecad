from __future__ import annotations

from ocf_freecad.commands.base import BaseCommand


class AutoLayoutCommand(BaseCommand):
    def GetResources(self):
        return {
            "MenuText": "Auto Layout",
            "ToolTip": "Open the auto-layout task panel",
        }

    def Activated(self):
        import FreeCAD as App
        import FreeCADGui as Gui

        from ocf_freecad.gui.taskpanels.layout_taskpanel import LayoutTaskPanel

        doc = App.ActiveDocument
        if doc is None:
            raise RuntimeError("No active FreeCAD document")
        Gui.Control.showDialog(LayoutTaskPanel(doc))
