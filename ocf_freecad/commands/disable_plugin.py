from __future__ import annotations

from ocf_freecad.commands.base import BaseCommand


class DisablePluginCommand(BaseCommand):
    def GetResources(self):
        return {
            "MenuText": "Disable Selected Plugin",
            "ToolTip": "Disable the selected plugin in the plugin manager",
        }

    def Activated(self):
        import FreeCAD as App

        from ocf_freecad.workbench import ensure_workbench_ui

        doc = App.ActiveDocument
        if doc is None:
            raise RuntimeError("No active FreeCAD document")
        ensure_workbench_ui(doc, focus="plugins").disable_selected_plugin()
