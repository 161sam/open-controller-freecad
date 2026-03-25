from __future__ import annotations

from collections import Counter
from typing import Any

from ocf_freecad.gui.panels._common import (
    FallbackButton,
    FallbackCombo,
    FallbackLabel,
    FallbackText,
    current_text,
    load_qt,
    set_combo_items,
    set_enabled,
    set_label_text,
    set_text,
)
from ocf_freecad.services.controller_service import ControllerService
from ocf_freecad.services.template_service import TemplateService
from ocf_freecad.services.variant_service import VariantService


class CreatePanel:
    def __init__(
        self,
        doc: Any,
        controller_service: ControllerService | None = None,
        template_service: TemplateService | None = None,
        variant_service: VariantService | None = None,
        on_created: Any | None = None,
        on_status: Any | None = None,
    ) -> None:
        self.doc = doc
        self.controller_service = controller_service or ControllerService()
        self.template_service = template_service or TemplateService()
        self.variant_service = variant_service or VariantService()
        self.on_created = on_created
        self.on_status = on_status
        self._templates: list[dict[str, Any]] = []
        self._variants: list[dict[str, Any]] = []
        self.form = _build_form()
        self.widget = self.form["widget"]
        self._connect_events()
        self.refresh()

    def refresh(self) -> None:
        context = self.controller_service.get_ui_context(self.doc)
        active_template_id = context.get("template_id")
        active_variant_id = context.get("variant_id")
        previous_template = active_template_id or self.selected_template_id()
        previous_variant = active_variant_id or self.selected_variant_id()
        self._templates = self.template_service.list_templates()
        labels = [_template_label(item) for item in self._templates]
        set_combo_items(self.form["template"], labels)
        if previous_template:
            self._set_selected_template(previous_template)
        self.refresh_variants(active_variant_id=previous_variant)
        self.refresh_preview()
        self._sync_selected_context()
        self._update_actions()

    def refresh_variants(self, active_variant_id: str | None = None) -> None:
        template_id = self.selected_template_id()
        self._variants = self.variant_service.list_variants(template_id=template_id) if template_id else []
        labels = ["Template Default"] + [_variant_label(item) for item in self._variants]
        set_combo_items(self.form["variant"], labels)
        if active_variant_id:
            self._set_selected_variant(active_variant_id)
        self._set_variant_summary()

    def selected_template_id(self) -> str | None:
        label = current_text(self.form["template"])
        for item in self._templates:
            if _template_label(item) == label:
                return item["template"]["id"]
        return None

    def selected_variant_id(self) -> str | None:
        label = current_text(self.form["variant"])
        if label in {"", "Template Default"}:
            return None
        for item in self._variants:
            if _variant_label(item) == label:
                return item["variant"]["id"]
        return None

    def refresh_preview(self) -> str:
        preview = self._build_preview()
        set_text(self.form["preview"], preview)
        return preview

    def create_controller(self) -> dict[str, Any]:
        template_id = self.selected_template_id()
        if not template_id:
            raise ValueError("No template selected")
        variant_id = self.selected_variant_id()
        if variant_id:
            state = self.controller_service.create_from_variant(self.doc, variant_id)
            self._publish_status(f"Created controller from variant '{variant_id}'.")
        else:
            state = self.controller_service.create_from_template(self.doc, template_id)
            self._publish_status(f"Created controller from template '{template_id}'.")
        self.refresh()
        if self.on_created is not None:
            self.on_created(state)
        return state

    def handle_template_changed(self, *_args: Any) -> None:
        self.refresh_variants()
        self.refresh_preview()
        self._sync_selected_context()
        self._update_actions()

    def handle_variant_changed(self, *_args: Any) -> None:
        self.refresh_preview()
        self._set_variant_summary()

    def handle_create_clicked(self) -> None:
        try:
            self.create_controller()
        except Exception as exc:
            self._publish_status(str(exc))

    def accept(self) -> bool:
        self.create_controller()
        return True

    def _build_preview(self) -> str:
        template_id = self.selected_template_id()
        if not template_id:
            return "Select a template to see the controller preview."
        variant_id = self.selected_variant_id()
        if variant_id:
            project = self.variant_service.generate_from_variant(variant_id)
            title = f"Variant: {variant_id}"
        else:
            project = self.template_service.generate_from_template(template_id)
            title = f"Template: {template_id}"
        counts = Counter(component["type"] for component in project["components"])
        summary = ", ".join(f"{component_type} x{count}" for component_type, count in sorted(counts.items()))
        controller = project["controller"]
        surface = controller.get("surface") or {}
        shape = surface.get("shape") or surface.get("type") or "rectangle"
        width = surface.get("width", controller.get("width", "-"))
        height = surface.get("height", controller.get("depth", "-"))
        return "\n".join(
            [
                title,
                f"Surface: {shape} {width} x {height} mm",
                f"Components: {len(project['components'])}",
                f"Types: {summary or 'none'}",
            ]
        )

    def _set_selected_template(self, template_id: str) -> None:
        for item in self._templates:
            if item["template"]["id"] != template_id:
                continue
            self.form["template"].setCurrentIndex(_template_index(self._templates, template_id))
            return

    def _set_selected_variant(self, variant_id: str) -> None:
        for index, item in enumerate(self._variants, start=1):
            if item["variant"]["id"] == variant_id:
                self.form["variant"].setCurrentIndex(index)
                return
        self.form["variant"].setCurrentIndex(0)

    def _sync_selected_context(self) -> None:
        template_id = self.selected_template_id()
        template = next((item["template"] for item in self._templates if item["template"]["id"] == template_id), None)
        if template is None:
            set_label_text(self.form["template_summary"], "Choose a template to start.")
            return
        description = template.get("description") or "No template description available."
        set_label_text(self.form["template_summary"], f"{template['name']}: {description}")

    def _set_variant_summary(self) -> None:
        variant_id = self.selected_variant_id()
        if not variant_id:
            set_label_text(self.form["variant_summary"], "Template defaults are active.")
            return
        variant = next((item["variant"] for item in self._variants if item["variant"]["id"] == variant_id), None)
        if variant is None:
            set_label_text(self.form["variant_summary"], "Selected variant is not available.")
            return
        description = variant.get("description") or "No variant description available."
        set_label_text(self.form["variant_summary"], f"{variant['name']}: {description}")

    def _update_actions(self) -> None:
        set_enabled(self.form["create_button"], self.selected_template_id() is not None)

    def _publish_status(self, message: str) -> None:
        set_label_text(self.form["status"], message)
        if self.on_status is not None:
            self.on_status(message)

    def _connect_events(self) -> None:
        template = self.form["template"]
        variant = self.form["variant"]
        create_button = self.form["create_button"]
        if hasattr(template, "currentIndexChanged"):
            template.currentIndexChanged.connect(self.handle_template_changed)
        if hasattr(variant, "currentIndexChanged"):
            variant.currentIndexChanged.connect(self.handle_variant_changed)
        if hasattr(create_button, "clicked"):
            create_button.clicked.connect(self.handle_create_clicked)


def _build_form() -> dict[str, Any]:
    _qtcore, _qtgui, qtwidgets = load_qt()
    if qtwidgets is None:
        return {
            "widget": object(),
            "template": FallbackCombo(),
            "template_summary": FallbackLabel(),
            "variant": FallbackCombo(["Template Default"]),
            "variant_summary": FallbackLabel("Template defaults are active."),
            "preview": FallbackText(),
            "create_button": FallbackButton("Create Controller"),
            "status": FallbackLabel(),
        }

    widget = qtwidgets.QWidget()
    layout = qtwidgets.QVBoxLayout(widget)
    header = qtwidgets.QLabel("Create a controller from a template and optional variant.")
    header.setWordWrap(True)
    form = qtwidgets.QFormLayout()
    template = qtwidgets.QComboBox()
    variant = qtwidgets.QComboBox()
    template_summary = qtwidgets.QLabel()
    template_summary.setWordWrap(True)
    variant_summary = qtwidgets.QLabel()
    variant_summary.setWordWrap(True)
    preview = qtwidgets.QPlainTextEdit()
    preview.setReadOnly(True)
    create_button = qtwidgets.QPushButton("Create Controller")
    status = qtwidgets.QLabel()
    status.setWordWrap(True)
    form.addRow("Template", template)
    form.addRow("", template_summary)
    form.addRow("Variant", variant)
    form.addRow("", variant_summary)
    layout.addWidget(header)
    layout.addLayout(form)
    layout.addWidget(preview)
    layout.addWidget(create_button)
    layout.addWidget(status)
    return {
        "widget": widget,
        "template": template,
        "template_summary": template_summary,
        "variant": variant,
        "variant_summary": variant_summary,
        "preview": preview,
        "create_button": create_button,
        "status": status,
    }


def _template_label(item: dict[str, Any]) -> str:
    template = item["template"]
    return f"{template['name']} ({template['id']})"


def _variant_label(item: dict[str, Any]) -> str:
    variant = item["variant"]
    return f"{variant['name']} ({variant['id']})"


def _template_index(templates: list[dict[str, Any]], template_id: str) -> int:
    for index, item in enumerate(templates):
        if item["template"]["id"] == template_id:
            return index
    return 0
