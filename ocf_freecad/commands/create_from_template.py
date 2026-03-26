from __future__ import annotations

from ocf_freecad.commands.base import BaseCommand
from ocf_freecad.gui.panels._common import log_to_console
from ocf_freecad.gui.runtime import show_error


class CreateFromTemplateCommand(BaseCommand):
    ICON_NAME = "create_controller"

    def GetResources(self):
        return self.resources(
            "Create Controller",
            "Create a new controller from a template or variant.",
        )

    def Activated(self):
        try:
            import FreeCAD as App

            from ocf_freecad.workbench import ensure_workbench_ui

            doc = App.ActiveDocument or App.newDocument("Controller")
            ensure_workbench_ui(doc, focus="create")
            log_to_console("Create Controller command focused the Create panel.")
        except Exception as exc:
            show_error("Create Controller", exc)
