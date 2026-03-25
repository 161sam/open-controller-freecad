from __future__ import annotations

from ocf_freecad.commands.base import BaseCommand


class ApplyLayoutCommand(BaseCommand):
    def GetResources(self):
        return {
            "MenuText": "Apply Auto Layout",
            "ToolTip": "Open the layout panel and apply auto layout",
        }

    def Activated(self):
        import FreeCAD as App

        from ocf_freecad.workbench import ensure_workbench_ui

        doc = App.ActiveDocument
        if doc is None:
            raise RuntimeError("No active FreeCAD document")
        ensure_workbench_ui(doc, focus="layout")
