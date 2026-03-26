from __future__ import annotations

from typing import Any

from ocf_freecad.gui.panels._common import (
    FallbackButton,
    FallbackCombo,
    FallbackLabel,
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
            return
        self.parts["status_badge"].set_status(selected["status"], selected["status_label"])
        set_label_text(self.parts["summary"], _summary(selected))
        set_enabled(self.parts["enable_button"], not selected["enabled"])
        set_enabled(self.parts["disable_button"], selected["enabled"] and not selected.get("non_disableable", False))


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
    summary = qtwidgets.QLabel("")
    summary.setWordWrap(True)
    row = qtwidgets.QHBoxLayout()
    row.addWidget(enable_button)
    row.addWidget(disable_button)
    row.addWidget(refresh_button)
    layout.addWidget(filter_combo)
    layout.addWidget(plugin_combo)
    layout.addWidget(badge.widget)
    layout.addWidget(summary)
    layout.addLayout(row)
    return {
        "widget": widget,
        "filter_combo": filter_combo,
        "plugin_combo": plugin_combo,
        "enable_button": enable_button,
        "disable_button": disable_button,
        "refresh_button": refresh_button,
        "summary": summary,
        "status_badge": badge,
    }
