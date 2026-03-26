from __future__ import annotations

from ocw_workbench.commands.base import BaseCommand
from ocw_workbench.gui.runtime import show_error, show_info


class SelectionArrangeCommand(BaseCommand):
    ICON_NAME = "default"

    def __init__(self, operation: str) -> None:
        self.operation = operation

    def GetResources(self):
        menu_text, tooltip = _command_text(self.operation)
        return self.resources(menu_text, tooltip)

    def Activated(self):
        menu_text, _tooltip = _command_text(self.operation)
        try:
            import FreeCAD as App

            from ocw_workbench.workbench import ensure_workbench_ui

            doc = App.ActiveDocument
            if doc is None:
                raise RuntimeError("No active FreeCAD document")
            panel = ensure_workbench_ui(doc, focus="components")
            result = panel.apply_selection_arrangement(self.operation)
            if result["moved_count"] <= 0:
                show_info(menu_text, f"{menu_text} left {result['selected_count']} selected components unchanged.")
            else:
                show_info(menu_text, f"{menu_text} applied to {result['selected_count']} selected components.")
        except Exception as exc:
            show_error(menu_text, exc)


def _command_text(operation: str) -> tuple[str, str]:
    labels = {
        "align_left": ("Align Left", "Align selected component centers to the left-most selected X position."),
        "align_center_x": ("Align Center X", "Align selected component centers to the horizontal selection midpoint."),
        "align_right": ("Align Right", "Align selected component centers to the right-most selected X position."),
        "align_top": ("Align Top", "Align selected component centers to the top-most selected Y position."),
        "align_center_y": ("Align Center Y", "Align selected component centers to the vertical selection midpoint."),
        "align_bottom": ("Align Bottom", "Align selected component centers to the bottom-most selected Y position."),
        "distribute_horizontal": (
            "Distribute Horizontally",
            "Evenly distribute selected component centers along X, keeping the outer-most selected components fixed.",
        ),
        "distribute_vertical": (
            "Distribute Vertically",
            "Evenly distribute selected component centers along Y, keeping the outer-most selected components fixed.",
        ),
    }
    if operation not in labels:
        raise ValueError(f"Unsupported arrangement operation: {operation}")
    return labels[operation]
