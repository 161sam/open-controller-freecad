from __future__ import annotations

from ocw_workbench.commands.base import BaseCommand
from ocw_workbench.gui.interaction.placement_controller import PlacementController
from ocw_workbench.gui.runtime import show_error, show_info


class DragMoveComponentCommand(BaseCommand):
    ICON_NAME = "move_component"

    def GetResources(self):
        return self.resources(
            "Move",
            "Move a selected component directly in the 3D view.",
        )

    def IsActive(self):
        return self._has_controller()

    def Activated(self):
        try:
            import FreeCAD as App

            doc = App.ActiveDocument
            if doc is None:
                raise RuntimeError("No active FreeCAD document")
            started = PlacementController().start_move_mode(doc)
            if started:
                show_info("Drag Move Component", "Hover a component, drag to move it, and press ESC to cancel.")
        except Exception as exc:
            show_error("Drag Move Component", exc)
