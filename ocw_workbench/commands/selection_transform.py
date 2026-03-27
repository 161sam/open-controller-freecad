from __future__ import annotations

from ocw_workbench.commands.base import BaseCommand
from ocw_workbench.gui.runtime import show_error, show_info


class SelectionTransformCommand(BaseCommand):
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
            result = panel.apply_selection_transform(self.operation)
            if result["moved_count"] <= 0:
                show_info(menu_text, f"{menu_text} left {result['selected_count']} selected components unchanged.")
            else:
                show_info(menu_text, f"{menu_text} applied to {result['selected_count']} selected components.")
        except Exception as exc:
            show_error(menu_text, exc)


def _command_text(operation: str) -> tuple[str, str]:
    labels = {
        "rotate_cw_90": ("Rotate +90", "Rotate the selected components by +90 degrees around each component center."),
        "rotate_ccw_90": ("Rotate -90", "Rotate the selected components by -90 degrees around each component center."),
        "rotate_180": ("Rotate 180", "Rotate the selected components by 180 degrees around each component center."),
        "mirror_horizontal": (
            "Mirror Horizontally",
            "Mirror the selected component orientation across the local vertical axis through each component center.",
        ),
        "mirror_vertical": (
            "Mirror Vertically",
            "Mirror the selected component orientation across the local horizontal axis through each component center.",
        ),
    }
    if operation not in labels:
        raise ValueError(f"Unsupported transform operation: {operation}")
    return labels[operation]
