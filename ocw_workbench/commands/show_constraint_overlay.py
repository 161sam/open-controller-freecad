from __future__ import annotations

from ocw_workbench.commands.base import BaseCommand
from ocw_workbench.gui.runtime import show_error, show_info


class ShowConstraintOverlayCommand(BaseCommand):
    ICON_NAME = "constraint_overlay"

    def GetResources(self):
        return self.resources(
            "Issue Overlay",
            "Show or hide validation issues in the 3D view.",
        )

    def IsActive(self):
        return self._has_controller()

    def Activated(self):
        try:
            import FreeCAD as App

            from ocw_workbench.workbench import toggle_constraint_overlay_direct

            doc = App.ActiveDocument
            if doc is None:
                raise RuntimeError("No active FreeCAD document")
            settings = toggle_constraint_overlay_direct(doc)
            show_info(
                "Constraint Overlay",
                f"Constraint overlay {'enabled' if settings['show_constraints'] else 'disabled'}.",
            )
        except Exception as exc:
            show_error("Constraint Overlay", exc)
