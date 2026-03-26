from __future__ import annotations

from ocf_freecad.commands.base import BaseCommand
from ocf_freecad.gui.panels._common import log_to_console
from ocf_freecad.gui.runtime import show_error


class AddComponentCommand(BaseCommand):
    ICON_NAME = "add_component"

    def GetResources(self):
        return self.resources(
            "Add Component",
            "Add a component from the library to the current controller.",
        )

    def Activated(self):
        try:
            import FreeCAD as App

            from ocf_freecad.workbench import ensure_workbench_ui

            doc = App.ActiveDocument or App.newDocument("Controller")
            ensure_workbench_ui(doc, focus="components")
            log_to_console("Add Component command focused the Components panel.")
        except Exception as exc:
            show_error("Add Component", exc)
