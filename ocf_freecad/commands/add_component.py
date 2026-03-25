from __future__ import annotations

from ocf_freecad.commands.base import BaseCommand


class AddComponentCommand(BaseCommand):
    def GetResources(self):
        return {
            "MenuText": "Add Component",
            "ToolTip": "Open the components panel with library picker",
        }

    def Activated(self):
        import FreeCAD as App

        from ocf_freecad.workbench import ensure_workbench_ui

        doc = App.ActiveDocument
        if doc is None:
            raise RuntimeError("No active FreeCAD document")
        ensure_workbench_ui(doc, focus="components")
