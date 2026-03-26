from __future__ import annotations

from ocf_freecad.commands.base import BaseCommand
from ocf_freecad.gui.panels._common import log_to_console
from ocf_freecad.gui.runtime import show_error


class ValidateConstraintsCommand(BaseCommand):
    ICON_NAME = "validate_constraints"

    def GetResources(self):
        return self.resources(
            "Validate Layout",
            "Validate spacing, edge distance, and placement constraints.",
        )

    def Activated(self):
        try:
            import FreeCAD as App

            from ocf_freecad.workbench import ensure_workbench_ui

            doc = App.ActiveDocument
            if doc is None:
                raise RuntimeError("No active FreeCAD document")
            panel = ensure_workbench_ui(doc, focus="constraints")
            report = panel.constraints_panel.validate()
            panel.set_status(
                f"Validated layout: {report['summary']['error_count']} errors, {report['summary']['warning_count']} warnings."
            )
            log_to_console(
                f"Constraint validation finished with {report['summary']['error_count']} errors and "
                f"{report['summary']['warning_count']} warnings."
            )
        except Exception as exc:
            show_error("Validate Constraints", exc)
