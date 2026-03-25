from __future__ import annotations

from ocf_freecad.commands.base import BaseCommand


class CreateFromTemplateCommand(BaseCommand):
    def GetResources(self):
        return {
            "MenuText": "Create Controller",
            "ToolTip": "Open the template and variant create workflow",
        }

    def Activated(self):
        import FreeCAD as App

        from ocf_freecad.workbench import ensure_workbench_ui

        doc = App.ActiveDocument or App.newDocument("Controller")
        ensure_workbench_ui(doc, focus="create")
