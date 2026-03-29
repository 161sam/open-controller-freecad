from __future__ import annotations

from typing import Any

from ocw_workbench.commands.base import BaseCommand
from ocw_workbench.gui.panels._common import exec_dialog, load_qt
from ocw_workbench.gui.runtime import show_error, show_info


class DuplicateSelectionCommand(BaseCommand):
    ICON_NAME = "duplicate_selected"

    def GetResources(self):
        return self.resources(
            "Duplicate Selected",
            "Duplicate the current selection once with an offset.",
        )

    def IsActive(self):
        return self._has_selection()

    def Activated(self):
        title = "Duplicate Selected"
        try:
            import FreeCAD as App

            from ocw_workbench.workbench import ensure_workbench_ui

            doc = App.ActiveDocument
            if doc is None:
                raise RuntimeError("No active FreeCAD document")
            panel = ensure_workbench_ui(doc, focus="components")
            values = _collect_duplicate_values()
            result = panel.duplicate_selection_once(offset_x=values["offset_x"], offset_y=values["offset_y"])
            show_info(title, f"Created {result['created_count']} duplicated components.")
        except Exception as exc:
            show_error(title, exc)


class LinearArrayCommand(BaseCommand):
    ICON_NAME = "array_horizontal"

    def __init__(self, axis: str) -> None:
        self.axis = axis

    def icon_name(self) -> str:
        return "array_horizontal" if self.axis == "x" else "array_vertical"

    def GetResources(self):
        title = "Array Horizontally" if self.axis == "x" else "Array Vertically"
        tooltip = "Create a linear array from the current selection."
        return self.resources(title, tooltip)

    def IsActive(self):
        return self._has_selection()

    def Activated(self):
        title = "Array Horizontally" if self.axis == "x" else "Array Vertically"
        try:
            import FreeCAD as App

            from ocw_workbench.workbench import ensure_workbench_ui

            doc = App.ActiveDocument
            if doc is None:
                raise RuntimeError("No active FreeCAD document")
            panel = ensure_workbench_ui(doc, focus="components")
            values = _collect_linear_array_values(self.axis)
            result = panel.array_selection_linear(axis=self.axis, count=values["count"], spacing=values["spacing"])
            show_info(title, f"Created {result['created_count']} array components.")
        except Exception as exc:
            show_error(title, exc)


class GridArrayCommand(BaseCommand):
    ICON_NAME = "grid_array"

    def GetResources(self):
        return self.resources(
            "Grid Array",
            "Create a grid array from the current selection.",
        )

    def IsActive(self):
        return self._has_selection()

    def Activated(self):
        title = "Grid Array"
        try:
            import FreeCAD as App

            from ocw_workbench.workbench import ensure_workbench_ui

            doc = App.ActiveDocument
            if doc is None:
                raise RuntimeError("No active FreeCAD document")
            panel = ensure_workbench_ui(doc, focus="components")
            values = _collect_grid_array_values()
            result = panel.array_selection_grid(
                rows=values["rows"],
                cols=values["cols"],
                spacing_x=values["spacing_x"],
                spacing_y=values["spacing_y"],
            )
            show_info(title, f"Created {result['created_count']} grid-array components.")
        except Exception as exc:
            show_error(title, exc)


def _collect_duplicate_values() -> dict[str, float]:
    return _run_pattern_dialog(
        "Duplicate Selected",
        [
            {"id": "offset_x", "label": "Offset X", "type": "float", "value": 10.0},
            {"id": "offset_y", "label": "Offset Y", "type": "float", "value": 10.0},
        ],
    )


def _collect_linear_array_values(axis: str) -> dict[str, float]:
    default_spacing = 20.0
    axis_label = "X" if axis == "x" else "Y"
    return _run_pattern_dialog(
        "Linear Array",
        [
            {"id": "count", "label": "Copies", "type": "int", "value": 3},
            {"id": "spacing", "label": f"Spacing {axis_label}", "type": "float", "value": default_spacing},
        ],
    )


def _collect_grid_array_values() -> dict[str, float]:
    return _run_pattern_dialog(
        "Grid Array",
        [
            {"id": "rows", "label": "Rows", "type": "int", "value": 2},
            {"id": "cols", "label": "Cols", "type": "int", "value": 2},
            {"id": "spacing_x", "label": "Spacing X", "type": "float", "value": 20.0},
            {"id": "spacing_y", "label": "Spacing Y", "type": "float", "value": 20.0},
        ],
    )


def _run_pattern_dialog(title: str, fields: list[dict[str, Any]]) -> dict[str, Any]:
    _qtcore, _qtgui, qtwidgets = load_qt()
    if qtwidgets is None:
        return {field["id"]: field["value"] for field in fields}
    dialog = qtwidgets.QDialog()
    dialog.setWindowTitle(title)
    layout = qtwidgets.QVBoxLayout(dialog)
    form = qtwidgets.QFormLayout()
    widgets: dict[str, Any] = {}
    for field in fields:
        if field["type"] == "int":
            widget = qtwidgets.QSpinBox()
            widget.setRange(1, 999)
            widget.setValue(int(field["value"]))
        else:
            widget = qtwidgets.QDoubleSpinBox()
            widget.setDecimals(2)
            widget.setRange(-10000.0, 10000.0)
            widget.setValue(float(field["value"]))
        widgets[field["id"]] = widget
        form.addRow(field["label"], widget)
    layout.addLayout(form)
    buttons = qtwidgets.QDialogButtonBox(qtwidgets.QDialogButtonBox.Ok | qtwidgets.QDialogButtonBox.Cancel)
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)
    result = exec_dialog(dialog)
    accepted = False
    if isinstance(result, int):
        accepted = bool(result)
    elif hasattr(dialog, "result"):
        accepted = bool(dialog.result())
    if not accepted:
        raise RuntimeError("Operation cancelled")
    values: dict[str, Any] = {}
    for field in fields:
        widget = widgets[field["id"]]
        values[field["id"]] = int(widget.value()) if field["type"] == "int" else float(widget.value())
    return values
