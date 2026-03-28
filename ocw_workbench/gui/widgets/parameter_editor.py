from __future__ import annotations

from typing import Any

from ocw_workbench.gui.panels._common import (
    build_group_box,
    create_button_row,
    FallbackButton,
    FallbackCombo,
    FallbackLabel,
    FallbackSignal,
    FallbackText,
    FallbackValue,
    current_text,
    load_qt,
    set_combo_items,
    set_label_text,
    set_text,
    set_tooltip,
    widget_value,
)


class FallbackCheckBox:
    def __init__(self, checked: bool = False) -> None:
        self.checked = bool(checked)
        self.enabled = True
        self.stateChanged = FallbackSignal()

    def isChecked(self) -> bool:
        return self.checked

    def setChecked(self, checked: bool) -> None:
        self.checked = bool(checked)
        self.stateChanged.emit(int(self.checked))


class ParameterEditorWidget:
    def __init__(self) -> None:
        self.parts = _build_widget()
        self.widget = self.parts["widget"]
        self._definitions: list[dict[str, Any]] = []
        self._controls: dict[str, Any] = {}
        self._presets: list[dict[str, Any]] = []
        self._preset_lookup: dict[str, dict[str, Any]] = {}
        self.changed = FallbackSignal()
        self.preset_changed = FallbackSignal()

    def set_schema(
        self,
        definitions: list[dict[str, Any]],
        presets: list[dict[str, Any]],
        values: dict[str, Any],
        *,
        sources: dict[str, str] | None = None,
        preset_id: str | None = None,
    ) -> None:
        self._definitions = list(definitions)
        self._presets = list(presets)
        self._preset_lookup = {item["name"]: item for item in presets}
        self._set_presets(preset_id)
        self._rebuild_controls(values=values, sources=sources or {})

    def clear(self) -> None:
        self.set_schema([], [], {}, sources={}, preset_id=None)

    def values(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for definition in self._definitions:
            result[definition["id"]] = self._read_widget_value(definition, self._controls[definition["id"]])
        return result

    def control_widget(self, parameter_id: str) -> Any:
        return self._controls[parameter_id]

    def selected_preset_id(self) -> str | None:
        label = current_text(self.parts["preset"])
        if label in {"", "Template Default"}:
            return None
        preset = self._preset_lookup.get(label)
        return str(preset["id"]) if preset is not None else None

    def apply_selected_preset(self) -> dict[str, Any]:
        preset_id = self.selected_preset_id()
        if preset_id is None:
            return {}
        preset = next((item for item in self._presets if item["id"] == preset_id), None)
        if preset is None:
            return {}
        for parameter_id, value in preset["values"].items():
            widget = self._controls.get(parameter_id)
            definition = next((item for item in self._definitions if item["id"] == parameter_id), None)
            if widget is None or definition is None:
                continue
            self._write_widget_value(definition, widget, value)
        self.preset_changed.emit(preset_id)
        self.changed.emit()
        return dict(preset["values"])

    def _set_presets(self, preset_id: str | None) -> None:
        labels = ["Template Default"] + [item["name"] for item in self._presets]
        set_combo_items(self.parts["preset"], labels)
        if preset_id is None:
            if hasattr(self.parts["preset"], "setCurrentIndex"):
                self.parts["preset"].setCurrentIndex(0)
            return
        for index, item in enumerate(self._presets, start=1):
            if item["id"] == preset_id:
                self.parts["preset"].setCurrentIndex(index)
                return
        self.parts["preset"].setCurrentIndex(0)

    def _rebuild_controls(self, *, values: dict[str, Any], sources: dict[str, str]) -> None:
        self._controls = {}
        qtcore, _qtgui, qtwidgets = load_qt()
        container = self.parts["controls_container"]
        if qtwidgets is not None and hasattr(container, "layout"):
            layout = container.layout()
            while layout.count():
                child = layout.takeAt(0)
                widget = child.widget()
                if widget is not None and hasattr(widget, "deleteLater"):
                    widget.deleteLater()
        else:
            container.rows = []
        if not self._definitions:
            set_label_text(self.parts["summary"], "No parameters for the selected template.")
            return
        for definition in self._definitions:
            value = values.get(definition["id"], definition["default"])
            source = sources.get(definition["id"], "default")
            widget = self._build_control(definition, value)
            self._controls[definition["id"]] = widget
            label = f"{definition['label']}"
            if definition.get("unit"):
                label = f"{label} ({definition['unit']})"
            if qtwidgets is not None and hasattr(container, "layout"):
                row_layout = qtwidgets.QHBoxLayout()
                row_layout.addWidget(widget, 1)
                source_label = qtwidgets.QLabel(source)
                source_label.setMinimumWidth(56)
                row_layout.addWidget(source_label)
                container.layout().addRow(label, row_layout)
            else:
                container.rows.append({"label": label, "widget": widget, "source": source})
            help_text = definition.get("help")
            if help_text:
                set_tooltip(widget, help_text)
            self._connect_widget(definition, widget)
        set_label_text(self.parts["summary"], f"{len(self._definitions)} parameters available.")

    def _build_control(self, definition: dict[str, Any], value: Any) -> Any:
        _qtcore, _qtgui, qtwidgets = load_qt()
        control = definition["control"]
        parameter_type = definition["type"]
        if qtwidgets is None:
            if parameter_type == "bool":
                widget = FallbackCheckBox(bool(value))
            elif parameter_type == "enum":
                widget = FallbackCombo([str(item["label"]) for item in definition.get("options", [])])
                options = [item["value"] for item in definition.get("options", [])]
                try:
                    widget.setCurrentIndex(options.index(value))
                except ValueError:
                    widget.setCurrentIndex(0)
            elif parameter_type == "string":
                widget = FallbackText(str(value))
            else:
                widget = FallbackValue(float(value))
            return widget

        if parameter_type == "bool":
            widget = qtwidgets.QCheckBox()
            widget.setChecked(bool(value))
            return widget
        if parameter_type == "enum":
            widget = qtwidgets.QComboBox()
            labels = [str(item["label"]) for item in definition.get("options", [])]
            widget.addItems(labels)
            option_values = [item["value"] for item in definition.get("options", [])]
            if value in option_values:
                widget.setCurrentIndex(option_values.index(value))
            return widget
        if parameter_type == "string":
            return qtwidgets.QLineEdit(str(value))
        numeric_control = qtwidgets.QSlider() if control == "slider" and hasattr(qtwidgets, "QSlider") else None
        if numeric_control is not None:
            numeric_control.setOrientation(_qtcore.Qt.Horizontal)
            numeric_control.setMinimum(int(definition.get("min", 0) or 0))
            numeric_control.setMaximum(int(definition.get("max", 100) or 100))
            numeric_control.setSingleStep(int(definition.get("step", 1) or 1))
            numeric_control.setValue(int(value))
            return numeric_control
        if parameter_type == "int":
            widget = qtwidgets.QSpinBox()
            widget.setRange(
                int(definition.get("min", -999999) if definition.get("min") is not None else -999999),
                int(definition.get("max", 999999) if definition.get("max") is not None else 999999),
            )
            widget.setSingleStep(int(definition.get("step", 1) or 1))
            widget.setValue(int(value))
            return widget
        widget = qtwidgets.QDoubleSpinBox()
        widget.setRange(
            float(definition.get("min", -999999.0) if definition.get("min") is not None else -999999.0),
            float(definition.get("max", 999999.0) if definition.get("max") is not None else 999999.0),
        )
        widget.setSingleStep(float(definition.get("step", 1.0) or 1.0))
        widget.setDecimals(3)
        widget.setValue(float(value))
        return widget

    def _connect_widget(self, definition: dict[str, Any], widget: Any) -> None:
        parameter_type = definition["type"]
        if parameter_type == "bool" and hasattr(widget, "stateChanged"):
            widget.stateChanged.connect(lambda *_args: self.changed.emit())
            return
        if parameter_type == "enum" and hasattr(widget, "currentIndexChanged"):
            widget.currentIndexChanged.connect(lambda *_args: self.changed.emit())
            return
        if parameter_type == "string" and hasattr(widget, "textChanged"):
            widget.textChanged.connect(lambda *_args: self.changed.emit())
            return
        signal = getattr(widget, "valueChanged", None)
        if signal is not None and hasattr(signal, "connect"):
            signal.connect(lambda *_args: self.changed.emit())

    def _read_widget_value(self, definition: dict[str, Any], widget: Any) -> Any:
        parameter_type = definition["type"]
        if parameter_type == "bool":
            return bool(widget.isChecked()) if hasattr(widget, "isChecked") else bool(getattr(widget, "checked", False))
        if parameter_type == "enum":
            label = current_text(widget)
            for item in definition.get("options", []):
                if str(item["label"]) == label:
                    return item["value"]
            return definition["default"]
        if parameter_type == "string":
            return widget.text() if hasattr(widget, "text") and callable(widget.text) else getattr(widget, "text", "")
        value = widget_value(widget)
        if parameter_type == "int":
            return int(round(value))
        return float(value)

    def _write_widget_value(self, definition: dict[str, Any], widget: Any, value: Any) -> None:
        parameter_type = definition["type"]
        if parameter_type == "bool":
            widget.setChecked(bool(value))
            return
        if parameter_type == "enum":
            option_labels = [str(item["label"]) for item in definition.get("options", [])]
            option_values = [item["value"] for item in definition.get("options", [])]
            if value in option_values:
                widget.setCurrentIndex(option_values.index(value))
            elif option_labels:
                widget.setCurrentIndex(0)
            return
        if parameter_type == "string":
            set_text(widget, str(value))
            return
        widget.setValue(value)


def _build_widget() -> dict[str, Any]:
    _qtcore, _qtgui, qtwidgets = load_qt()
    if qtwidgets is None:
        return {
            "widget": object(),
            "preset": FallbackCombo(["Template Default"]),
            "apply_preset_button": FallbackButton("Apply Preset"),
            "controls_container": type("FallbackContainer", (), {"rows": []})(),
            "summary": FallbackLabel("No parameters for the selected template."),
        }

    widget, layout = build_group_box(qtwidgets, "Parameters")
    preset = qtwidgets.QComboBox()
    apply_preset_button = qtwidgets.QPushButton("Apply Preset")
    preset_row = create_button_row(qtwidgets, preset, apply_preset_button)
    controls_container = qtwidgets.QWidget()
    controls_layout = qtwidgets.QFormLayout(controls_container)
    summary = qtwidgets.QLabel("No parameters for the selected template.")
    summary.setWordWrap(True)
    layout.addLayout(preset_row)
    layout.addWidget(controls_container)
    layout.addWidget(summary)
    return {
        "widget": widget,
        "preset": preset,
        "apply_preset_button": apply_preset_button,
        "controls_container": controls_container,
        "summary": summary,
    }
