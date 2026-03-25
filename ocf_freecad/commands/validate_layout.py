from __future__ import annotations

from ocf_freecad.commands.base import BaseCommand


class ValidateLayoutCommand(BaseCommand):
    def GetResources(self):
        return {
            "MenuText": "Validate Layout",
            "ToolTip": "Show constraint validation results",
        }

    def Activated(self):
        import FreeCAD as App
        import FreeCADGui as Gui

        from ocf_freecad.gui.taskpanels.constraints_taskpanel import ConstraintsTaskPanel

        doc = App.ActiveDocument
        if doc is None:
            raise RuntimeError("No active FreeCAD document")
        Gui.Control.showDialog(ConstraintsTaskPanel(doc))
