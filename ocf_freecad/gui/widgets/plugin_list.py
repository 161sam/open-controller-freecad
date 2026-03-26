from __future__ import annotations

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
)
from ocf_freecad.gui.widgets.plugin_status_badge import PluginStatusBadgeWidget


class PluginListWidget:
    def __init__(self) -> None:
        self._lookup: dict[str, dict[str, Any]] = {}
        self.parts = _build_widget()
        self.widget = self.parts["widget"]

    def set_entries(self, entries: list[dict[str, Any]]) -> None:
        labels = [_entry_label(entry) for entry in entries]
        self._lookup = {label: entry for label, entry in zip(labels, entries)}
        set_combo_items(self.parts["plugin_combo"], labels)
        self.sync_selection_state()

    def selected(self) -> dict[str, Any] | None:
        return self._lookup.get(current_text(self.parts["plugin_combo"]))

    def selected_filter(self) -> str:
        return current_text(self.parts["filter_combo"]) or "all"

    def sync_selection_state(self) -> None:
        selected = self.selected()
        if selected is None:
            self.parts["status_badge"].set_status("disabled", "No Plugin")
            set_label_text(self.parts["summary"], "No plugin selected.")
            set_enabled(self.parts["enable_button"], False)
            set_enabled(self.parts["disable_button"], False)
            set_enabled(self.parts["export_button"], False)
            return
        self.parts["status_badge"].set_status(selected["status"], selected["status_label"])
        set_label_text(self.parts["summary"], _summary(selected))
        set_enabled(self.parts["enable_button"], not selected["enabled"])
        set_enabled(self.parts["disable_button"], selected["enabled"] and not selected.get("non_disableable", False))
        set_enabled(self.parts["export_button"], bool(selected.get("is_data_plugin")))


def _entry_label(entry: dict[str, Any]) -> str:
    marker = {
        "enabled": "[on]",
        "disabled": "[off]",
        "error": "[err]",
        "incompatible": "[api]",
    }.get(entry["status"], "[?]")
    return f"{marker} {entry['name']} ({entry['id']})"


def _summary(entry: dict[str, Any]) -> str:
    origin = "internal" if entry.get("is_internal") else "external"
    locked = "required" if entry.get("non_disableable") else "toggleable"
    return f"{entry['type']} | {origin} | {locked}"


def _build_widget() -> dict[str, Any]:
    _qtcore, _qtgui, qtwidgets = load_qt()
    badge = PluginStatusBadgeWidget()
    if qtwidgets is None:
        return {
            "widget": object(),
            "filter_combo": FallbackCombo(["all", "enabled", "disabled", "errors"]),
            "plugin_combo": FallbackCombo(),
            "enable_button": FallbackButton("Enable"),
            "disable_button": FallbackButton("Disable"),
            "refresh_button": FallbackButton("Refresh"),
            "export_path": FallbackText(".plugin_packs"),
            "import_path": FallbackText(""),
            "export_button": FallbackButton("Export ZIP"),
            "import_button": FallbackButton("Import ZIP"),
            "summary": FallbackLabel(""),
            "status_badge": badge,
        }

    widget = qtwidgets.QGroupBox("Plugin List")
    layout = qtwidgets.QVBoxLayout(widget)
    filter_combo = qtwidgets.QComboBox()
    filter_combo.addItems(["all", "enabled", "disabled", "errors"])
    plugin_combo = qtwidgets.QComboBox()
    enable_button = qtwidgets.QPushButton("Enable")
    disable_button = qtwidgets.QPushButton("Disable")
    refresh_button = qtwidgets.QPushButton("Refresh")
    export_path = qtwidgets.QLineEdit(".plugin_packs")
    import_path = qtwidgets.QLineEdit()
    export_button = qtwidgets.QPushButton("Export ZIP")
    import_button = qtwidgets.QPushButton("Import ZIP")
    summary = qtwidgets.QLabel("")
    summary.setWordWrap(True)
    row = qtwidgets.QHBoxLayout()
    row.addWidget(enable_button)
    row.addWidget(disable_button)
    row.addWidget(refresh_button)
    export_row = qtwidgets.QHBoxLayout()
    export_row.addWidget(qtwidgets.QLabel("Export"))
    export_row.addWidget(export_path, 1)
    export_row.addWidget(export_button)
    import_row = qtwidgets.QHBoxLayout()
    import_row.addWidget(qtwidgets.QLabel("Import"))
    import_row.addWidget(import_path, 1)
    import_row.addWidget(import_button)
    layout.addWidget(filter_combo)
    layout.addWidget(plugin_combo)
    layout.addWidget(badge.widget)
    layout.addWidget(summary)
    layout.addLayout(row)
    layout.addLayout(export_row)
    layout.addLayout(import_row)
    return {
        "widget": widget,
        "filter_combo": filter_combo,
        "plugin_combo": plugin_combo,
        "enable_button": enable_button,
        "disable_button": disable_button,
        "refresh_button": refresh_button,
        "export_path": export_path,
        "import_path": import_path,
        "export_button": export_button,
        "import_button": import_button,
        "summary": summary,
        "status_badge": badge,
    }
