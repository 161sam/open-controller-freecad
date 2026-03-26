from __future__ import annotations

from ocf_freecad.commands.base import BaseCommand


class ReloadPluginsCommand(BaseCommand):
    def GetResources(self):
        return {
            "MenuText": "Refresh Plugins",
            "ToolTip": "Re-scan plugin manifests and rebuild plugin status",
        }

    def Activated(self):
        import FreeCAD as App

        from ocf_freecad.workbench import ensure_workbench_ui

        doc = App.ActiveDocument
        if doc is None:
            raise RuntimeError("No active FreeCAD document")
        ensure_workbench_ui(doc, focus="plugins").reload_plugins()
