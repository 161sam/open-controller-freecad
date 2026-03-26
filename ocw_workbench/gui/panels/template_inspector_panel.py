from __future__ import annotations

from pathlib import Path
from typing import Any

from ocw_workbench.gui.feedback import apply_status_message, friendly_ui_error
from ocw_workbench.gui.panels._common import (
    FallbackButton,
    FallbackLabel,
    FallbackText,
    FallbackValue,
    configure_text_panel,
    load_qt,
    set_text,
    set_tooltip,
    text_value,
    widget_value,
)
from ocw_workbench.gui.widgets.parameter_editor import ParameterEditorWidget
from ocw_workbench.services.template_editor_service import TemplateEditorService


class _FallbackCheck:
    def __init__(self, checked: bool = False) -> None:
        self._checked = bool(checked)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool) -> None:
        self._checked = bool(checked)


class TemplateInspectorPanel:
    def __init__(
        self,
        template_path: str | Path,
        template_editor_service: TemplateEditorService | None = None,
        on_saved: Any | None = None,
        on_status: Any | None = None,
    ) -> None:
        self.template_path = Path(template_path)
        self.template_editor_service = template_editor_service or TemplateEditorService()
        self.on_saved = on_saved
        self.on_status = on_status
        self._payload: dict[str, Any] | None = None
        self._parameter_values: dict[str, Any] = {}
        self._parameter_sources: dict[str, str] = {}
        self._parameter_preset_id: str | None = None
        self.form = _build_form()
        self.widget = self.form["widget"]
        self._configure_tooltips()
        self._connect_events()
        self.load_template()

    def load_template(self) -> dict[str, Any]:
        payload = self.template_editor_service.load_template(self.template_path)
        self._payload = payload
        template_meta = payload["template"]
        resolved_preview = self.template_editor_service.inspector_preview_payload(payload)
        controller = resolved_preview["controller"]
        surface = controller.get("surface", {}) if isinstance(controller.get("surface"), dict) else {}
        geometry = controller.get("geometry", {}) if isinstance(controller.get("geometry"), dict) else {}
        metadata = payload.get("metadata", {})
        source = metadata.get("source", {}) if isinstance(metadata.get("source"), dict) else {}
        origin = source.get("origin", {}) if isinstance(source.get("origin"), dict) else {}
        editor_info = payload.get("_editor", {})

        set_text(self.form["file_path"], str(self.template_path))
        set_text(self.form["template_status"], str(editor_info.get("status") or "Imported raw template"))
        set_text(self.form["template_id"], str(template_meta.get("id") or ""))
        set_text(self.form["name"], str(template_meta.get("name") or ""))
        set_text(self.form["description"], str(template_meta.get("description") or ""))
        self.form["width"].setValue(float(controller.get("width", 0.0) or 0.0))
        self.form["depth"].setValue(float(controller.get("depth", 0.0) or 0.0))
        self.form["height"].setValue(float(controller.get("height", 0.0) or 0.0))
        set_text(
            self.form["surface_info"],
            self.template_editor_service.dump_yaml_mapping(
                {
                    "surface": surface,
                    "geometry": geometry,
                }
            ),
        )
        self.form["rotation"].setValue(float(source.get("rotation_deg", 0.0) or 0.0))
        self.form["offset_x"].setValue(float(origin.get("offset_x", 0.0) or 0.0))
        self.form["offset_y"].setValue(float(origin.get("offset_y", 0.0) or 0.0))
        set_text(self.form["origin_type"], str(origin.get("type") or "manual"))
        set_text(self.form["origin_reference"], str(origin.get("reference") or "-"))
        set_text(self.form["zones"], self.template_editor_service.dump_yaml_block(payload.get("zones", [])))
        set_text(
            self.form["mounting_holes"],
            self.template_editor_service.dump_yaml_block(controller.get("mounting_holes", [])),
        )
        set_text(self.form["source_metadata"], self.template_editor_service.dump_yaml_block([source]))
        self._load_parameter_editor(payload)
        self.refresh_parameter_preview(publish=False)
        self.validate_current_payload(publish=False)
        return payload

    def save_template(self) -> Path:
        payload = self._collect_payload()
        overwrite = bool(self.form["overwrite"].isChecked())
        output_path = self.template_editor_service.save_template_to_path(
            payload,
            self.template_path,
            overwrite=overwrite,
            require_user_template_path=True,
        )
        self.template_path = output_path
        self.load_template()
        self._publish_status(f"Saved template '{output_path.name}'.", level="success")
        if self.on_saved is not None:
            self.on_saved(output_path)
        return output_path

    def save_user_template(self) -> Path:
        payload = self._collect_payload()
        overwrite = bool(self.form["overwrite"].isChecked())
        output_path = self.template_editor_service.save_user_template(payload, overwrite=overwrite)
        self.template_path = output_path
        self.load_template()
        self._publish_status(f"Saved validated user template '{output_path.name}'.", level="success")
        if self.on_saved is not None:
            self.on_saved(output_path)
        return output_path

    def refresh_parameter_preview(self, publish: bool = True) -> dict[str, Any]:
        payload = self._collect_payload(include_parameter_defaults=False)
        preview = self.template_editor_service.inspector_preview_payload(
            payload,
            values=self._parameter_values,
            preset_id=self._parameter_preset_id,
        )
        parameter_meta = preview.get("resolved_parameters", {})
        set_text(
            self.form["resolved_parameters"],
            self.template_editor_service.dump_yaml_mapping(
                {
                    "values": parameter_meta.get("values", {}),
                    "sources": parameter_meta.get("sources", {}),
                    "preset_id": parameter_meta.get("preset_id"),
                }
            ),
        )
        set_text(
            self.form["resolved_preview"],
            self.template_editor_service.inspector_preview_text(
                payload,
                values=self._parameter_values,
                preset_id=self._parameter_preset_id,
            ),
        )
        if publish:
            self._publish_status("Updated parameter preview.")
        return preview

    def validate_current_payload(self, publish: bool = True) -> dict[str, Any]:
        payload = self._collect_payload()
        result = self.template_editor_service.validate_template(payload)
        lines: list[str] = []
        if result["errors"]:
            lines.extend(f"Error: {entry}" for entry in result["errors"])
        if result["warnings"]:
            lines.extend(f"Warning: {entry}" for entry in result["warnings"])
        if not lines:
            lines.append("Template validation passed.")
        set_text(self.form["validation"], "\n".join(lines))
        if publish:
            level = "error" if result["errors"] else ("warning" if result["warnings"] else "success")
            self._publish_status(lines[0], level=level)
        return result

    def handle_reload_clicked(self) -> None:
        try:
            self.load_template()
            self._publish_status("Reloaded template from disk.")
        except Exception as exc:
            self._publish_status(friendly_ui_error("Could not reload template", exc), level="error")

    def handle_validate_clicked(self) -> None:
        try:
            self.refresh_parameter_preview(publish=False)
            self.validate_current_payload(publish=True)
        except Exception as exc:
            self._publish_status(friendly_ui_error("Could not validate template", exc), level="error")

    def handle_apply_clicked(self) -> None:
        try:
            self.refresh_parameter_preview(publish=True)
        except Exception as exc:
            self._publish_status(friendly_ui_error("Could not apply parameter preview", exc), level="error")

    def handle_reset_all_clicked(self) -> None:
        try:
            if self._payload is None:
                raise ValueError("No template loaded")
            self._load_parameter_editor(self._payload)
            self.refresh_parameter_preview(publish=False)
            self._publish_status("Reset parameters to template defaults.")
        except Exception as exc:
            self._publish_status(friendly_ui_error("Could not reset parameters", exc), level="error")

    def handle_save_template_clicked(self) -> None:
        try:
            self.save_template()
        except Exception as exc:
            self._publish_status(friendly_ui_error("Could not save template", exc), level="error")

    def handle_save_clicked(self) -> None:
        try:
            self.save_user_template()
        except Exception as exc:
            self._publish_status(friendly_ui_error("Could not save template", exc), level="error")

    def handle_parameter_widget_changed(self, *_args: Any) -> None:
        self._parameter_values = self.form["parameter_editor"].values()
        self._parameter_preset_id = self.form["parameter_editor"].selected_preset_id()
        self._parameter_sources = {parameter_id: "user" for parameter_id in self._parameter_values}

    def handle_apply_preset_clicked(self) -> None:
        try:
            self.form["parameter_editor"].apply_selected_preset()
            self._parameter_values = self.form["parameter_editor"].values()
            self._parameter_preset_id = self.form["parameter_editor"].selected_preset_id()
            self.refresh_parameter_preview(publish=False)
            self._publish_status("Applied template preset.")
        except Exception as exc:
            self._publish_status(friendly_ui_error("Could not apply preset", exc), level="error")

    def _collect_payload(self, *, include_parameter_defaults: bool = True) -> dict[str, Any]:
        base = {} if self._payload is None else {key: value for key, value in self._payload.items() if key != "_editor"}
        payload = self.template_editor_service.normalize_payload(base)
        payload["template"]["id"] = text_value(self.form["template_id"]).strip()
        payload["template"]["name"] = text_value(self.form["name"]).strip()
        payload["template"]["description"] = text_value(self.form["description"]).strip()
        payload["controller"]["id"] = payload["template"]["id"]
        payload["controller"]["width"] = widget_value(self.form["width"])
        payload["controller"]["depth"] = widget_value(self.form["depth"])
        payload["controller"]["height"] = widget_value(self.form["height"])
        source = payload["metadata"].setdefault("source", {})
        origin = source.setdefault("origin", {})
        source["rotation_deg"] = widget_value(self.form["rotation"])
        origin["offset_x"] = widget_value(self.form["offset_x"])
        origin["offset_y"] = widget_value(self.form["offset_y"])
        payload["zones"] = self.template_editor_service.parse_yaml_list(text_value(self.form["zones"]), "Zones")
        payload["controller"]["mounting_holes"] = self.template_editor_service.parse_yaml_list(
            text_value(self.form["mounting_holes"]),
            "Mounting holes",
        )
        if include_parameter_defaults:
            payload = self.template_editor_service.apply_parameter_defaults(
                payload,
                values=self._parameter_values,
                preset_id=self._parameter_preset_id,
            )
        return payload

    def _load_parameter_editor(self, payload: dict[str, Any]) -> None:
        editor_meta = payload.get("metadata", {}).get("editor", {})
        initial_preset_id = editor_meta.get("parameter_preset_id") if isinstance(editor_meta, dict) else None
        model = self.template_editor_service.build_parameter_editor_model(payload, preset_id=initial_preset_id)
        self._parameter_values = dict(model["values"])
        self._parameter_sources = dict(model["sources"])
        self._parameter_preset_id = model["preset_id"]
        self.form["parameter_editor"].set_schema(
            model["definitions"],
            model["presets"],
            model["values"],
            sources=model["sources"],
            preset_id=model["preset_id"],
        )

    def _connect_events(self) -> None:
        if hasattr(self.form["reload_button"], "clicked"):
            self.form["reload_button"].clicked.connect(self.handle_reload_clicked)
        if hasattr(self.form["apply_button"], "clicked"):
            self.form["apply_button"].clicked.connect(self.handle_apply_clicked)
        if hasattr(self.form["reset_all_button"], "clicked"):
            self.form["reset_all_button"].clicked.connect(self.handle_reset_all_clicked)
        if hasattr(self.form["validate_button"], "clicked"):
            self.form["validate_button"].clicked.connect(self.handle_validate_clicked)
        if hasattr(self.form["save_template_button"], "clicked"):
            self.form["save_template_button"].clicked.connect(self.handle_save_template_clicked)
        if hasattr(self.form["save_button"], "clicked"):
            self.form["save_button"].clicked.connect(self.handle_save_clicked)
        self.form["parameter_editor"].changed.connect(self.handle_parameter_widget_changed)
        if hasattr(self.form["parameter_editor"].parts["apply_preset_button"], "clicked"):
            self.form["parameter_editor"].parts["apply_preset_button"].clicked.connect(self.handle_apply_preset_clicked)

    def _configure_tooltips(self) -> None:
        set_tooltip(self.form["template_id"], "Unique user template id used for the saved YAML filename.")
        set_tooltip(self.form["name"], "Display name shown in the Create panel.")
        set_tooltip(self.form["description"], "Short summary for the template.")
        set_tooltip(self.form["width"], "Controller width in millimeters.")
        set_tooltip(self.form["depth"], "Controller depth in millimeters.")
        set_tooltip(self.form["height"], "Controller height in millimeters.")
        set_tooltip(self.form["surface_info"], "Resolved surface and geometry metadata from the current template payload.")
        set_tooltip(self.form["rotation"], "Imported source rotation in degrees.")
        set_tooltip(self.form["offset_x"], "Origin offset X in millimeters.")
        set_tooltip(self.form["offset_y"], "Origin offset Y in millimeters.")
        set_tooltip(self.form["zones"], "YAML list of rudimentary zones. Each entry should define id, x, y, width, and height.")
        set_tooltip(
            self.form["mounting_holes"],
            "YAML list of mounting holes. Each entry should define id, x, y, and diameter.",
        )
        set_tooltip(self.form["resolved_parameters"], "Resolved parameter values, their source, and the currently selected preset.")
        set_tooltip(self.form["resolved_preview"], "Preview of the resolved template result before saving.")

    def _publish_status(self, message: str, level: str = "info") -> None:
        apply_status_message(self.form["status"], message, level=level)
        if self.on_status is not None:
            self.on_status(message)


def _build_form() -> dict[str, Any]:
    _qtcore, _qtgui, qtwidgets = load_qt()
    if qtwidgets is None:
        return {
            "widget": object(),
            "file_path": FallbackText(),
            "template_status": FallbackLabel(),
            "template_id": FallbackText(),
            "name": FallbackText(),
            "description": FallbackText(),
            "width": FallbackValue(0.0),
            "depth": FallbackValue(0.0),
            "height": FallbackValue(0.0),
            "surface_info": FallbackText(),
            "rotation": FallbackValue(0.0),
            "offset_x": FallbackValue(0.0),
            "offset_y": FallbackValue(0.0),
            "origin_type": FallbackLabel(),
            "origin_reference": FallbackLabel(),
            "zones": FallbackText(),
            "mounting_holes": FallbackText(),
            "parameter_editor": ParameterEditorWidget(),
            "resolved_parameters": FallbackText(),
            "resolved_preview": FallbackText(),
            "source_metadata": FallbackText(),
            "validation": FallbackText(),
            "overwrite": _FallbackCheck(False),
            "reload_button": FallbackButton("Reload"),
            "apply_button": FallbackButton("Apply"),
            "reset_all_button": FallbackButton("Reset All"),
            "validate_button": FallbackButton("Validate"),
            "save_template_button": FallbackButton("Save Template"),
            "save_button": FallbackButton("Save As User Template"),
            "status": FallbackLabel(),
        }

    widget = qtwidgets.QWidget()
    layout = qtwidgets.QVBoxLayout(widget)
    form = qtwidgets.QFormLayout()

    file_path = qtwidgets.QLineEdit()
    file_path.setReadOnly(True)
    template_status = qtwidgets.QLabel()
    template_id = qtwidgets.QLineEdit()
    name = qtwidgets.QLineEdit()
    description = qtwidgets.QLineEdit()
    width = qtwidgets.QDoubleSpinBox()
    depth = qtwidgets.QDoubleSpinBox()
    height = qtwidgets.QDoubleSpinBox()
    surface_info = qtwidgets.QPlainTextEdit()
    rotation = qtwidgets.QDoubleSpinBox()
    offset_x = qtwidgets.QDoubleSpinBox()
    offset_y = qtwidgets.QDoubleSpinBox()
    origin_type = qtwidgets.QLabel("-")
    origin_reference = qtwidgets.QLabel("-")
    zones = qtwidgets.QPlainTextEdit()
    mounting_holes = qtwidgets.QPlainTextEdit()
    parameter_editor = ParameterEditorWidget()
    resolved_parameters = qtwidgets.QPlainTextEdit()
    resolved_preview = qtwidgets.QPlainTextEdit()
    source_metadata = qtwidgets.QPlainTextEdit()
    validation = qtwidgets.QPlainTextEdit()
    overwrite = qtwidgets.QCheckBox("Allow overwrite of existing user template")
    reload_button = qtwidgets.QPushButton("Reload")
    apply_button = qtwidgets.QPushButton("Apply")
    reset_all_button = qtwidgets.QPushButton("Reset All")
    validate_button = qtwidgets.QPushButton("Validate")
    save_template_button = qtwidgets.QPushButton("Save Template")
    save_button = qtwidgets.QPushButton("Save As User Template")
    status = qtwidgets.QLabel("Template inspector ready.")
    status.setWordWrap(True)

    for spinbox in (width, depth, height, rotation, offset_x, offset_y):
        spinbox.setRange(-100000.0, 100000.0)
        spinbox.setDecimals(3)
    width.setMinimum(0.001)
    depth.setMinimum(0.001)
    height.setMinimum(0.001)
    configure_text_panel(surface_info, max_height=100)
    configure_text_panel(resolved_parameters, max_height=120)
    configure_text_panel(resolved_preview, max_height=120)
    configure_text_panel(source_metadata, max_height=110)
    configure_text_panel(validation, max_height=110)
    if hasattr(surface_info, "setReadOnly"):
        surface_info.setReadOnly(True)
    if hasattr(resolved_parameters, "setReadOnly"):
        resolved_parameters.setReadOnly(True)
    if hasattr(resolved_preview, "setReadOnly"):
        resolved_preview.setReadOnly(True)
    if hasattr(source_metadata, "setReadOnly"):
        source_metadata.setReadOnly(True)
    if hasattr(validation, "setReadOnly"):
        validation.setReadOnly(True)
    if hasattr(zones, "setReadOnly"):
        zones.setReadOnly(False)
    if hasattr(mounting_holes, "setReadOnly"):
        mounting_holes.setReadOnly(False)

    form.addRow("Template File", file_path)
    form.addRow("Template State", template_status)
    form.addRow("Template ID", template_id)
    form.addRow("Name", name)
    form.addRow("Description", description)
    form.addRow("Width", width)
    form.addRow("Depth", depth)
    form.addRow("Height", height)
    form.addRow("Surface / Geometry", surface_info)
    form.addRow("Rotation", rotation)
    form.addRow("Origin Type", origin_type)
    form.addRow("Origin Ref", origin_reference)
    form.addRow("Offset X", offset_x)
    form.addRow("Offset Y", offset_y)
    form.addRow("Parameters", parameter_editor.widget)
    form.addRow("Resolved Parameters", resolved_parameters)
    form.addRow("Resolved Preview", resolved_preview)
    form.addRow("Zones", zones)
    form.addRow("Mounting Holes", mounting_holes)
    form.addRow("Source Metadata", source_metadata)
    form.addRow("Validation", validation)
    form.addRow("", overwrite)

    button_row = qtwidgets.QHBoxLayout()
    button_row.addWidget(reload_button)
    button_row.addWidget(apply_button)
    button_row.addWidget(reset_all_button)
    button_row.addWidget(validate_button)
    button_row.addWidget(save_template_button)
    button_row.addWidget(save_button)

    layout.addLayout(form)
    layout.addLayout(button_row)
    layout.addWidget(status)
    return {
        "widget": widget,
        "file_path": file_path,
        "template_status": template_status,
        "template_id": template_id,
        "name": name,
        "description": description,
        "width": width,
        "depth": depth,
        "height": height,
        "surface_info": surface_info,
        "rotation": rotation,
        "offset_x": offset_x,
        "offset_y": offset_y,
        "origin_type": origin_type,
        "origin_reference": origin_reference,
        "zones": zones,
        "mounting_holes": mounting_holes,
        "parameter_editor": parameter_editor,
        "resolved_parameters": resolved_parameters,
        "resolved_preview": resolved_preview,
        "source_metadata": source_metadata,
        "validation": validation,
        "overwrite": overwrite,
        "reload_button": reload_button,
        "apply_button": apply_button,
        "reset_all_button": reset_all_button,
        "validate_button": validate_button,
        "save_template_button": save_template_button,
        "save_button": save_button,
        "status": status,
    }
