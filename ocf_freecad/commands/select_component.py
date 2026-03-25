from __future__ import annotations

from ocf_freecad.commands.base import BaseCommand


class SelectComponentCommand(BaseCommand):
    def GetResources(self):
        return {
            "MenuText": "Components",
            "ToolTip": "Open the components panel for selection and editing",
        }

    def Activated(self):
        import FreeCAD as App

        from ocf_freecad.workbench import ensure_workbench_ui

        doc = App.ActiveDocument
        if doc is None:
            raise RuntimeError("No active FreeCAD document")
        ensure_workbench_ui(doc, focus="components")
