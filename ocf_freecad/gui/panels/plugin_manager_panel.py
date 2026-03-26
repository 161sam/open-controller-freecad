from __future__ import annotations

from typing import Any

from ocf_freecad.gui.panels._common import load_qt, text_value
from ocf_freecad.gui.widgets.plugin_details import PluginDetailsWidget
from ocf_freecad.gui.widgets.plugin_list import PluginListWidget
from ocf_freecad.services.plugin_manager_service import PluginManagerService
from ocf_freecad.services.plugin_pack_service import PluginPackService


class PluginManagerPanel:
    def __init__(
        self,
        plugin_manager_service: PluginManagerService | None = None,
        plugin_pack_service: PluginPackService | None = None,
        on_status: Any | None = None,
        on_plugins_changed: Any | None = None,
    ) -> None:
        self.plugin_manager_service = plugin_manager_service or PluginManagerService()
        self.plugin_pack_service = plugin_pack_service or PluginPackService(
            plugin_manager_service=self.plugin_manager_service
        )
        self.on_status = on_status
        self.on_plugins_changed = on_plugins_changed
        self.form = _build_form()
        self.widget = self.form["widget"]
        self._connect_events()
        self.refresh()

    def refresh(self) -> list[dict[str, Any]]:
        entries = self.plugin_manager_service.list_plugins(filter_by=self.form["plugin_list"].selected_filter())
        self.form["plugin_list"].set_entries(entries)
        self.form["plugin_details"].set_plugin(self.form["plugin_list"].selected())
        return entries

    def selected_plugin_id(self) -> str | None:
        selected = self.form["plugin_list"].selected()
        return None if selected is None else str(selected["id"])

    def enable_selected_plugin(self) -> dict[str, Any]:
        plugin_id = self.selected_plugin_id()
        if plugin_id is None:
            raise ValueError("No plugin selected")
        plugin = self.plugin_manager_service.set_enabled(plugin_id, True)
        self.refresh()
        self._publish_status(f"Enabled plugin '{plugin_id}'.")
        self._notify_plugins_changed()
        return plugin

    def disable_selected_plugin(self) -> dict[str, Any]:
        plugin_id = self.selected_plugin_id()
        if plugin_id is None:
            raise ValueError("No plugin selected")
        plugin = self.plugin_manager_service.set_enabled(plugin_id, False)
        self.refresh()
        self._publish_status(f"Disabled plugin '{plugin_id}'.")
        self._notify_plugins_changed()
        return plugin

    def reload_plugins(self) -> list[dict[str, Any]]:
        plugins = self.plugin_manager_service.reload_plugins()
        self.refresh()
        self._publish_status(f"Refreshed plugins ({len(plugins)} discovered).")
        self._notify_plugins_changed()
        return plugins

    def export_selected_plugin_pack(self) -> dict[str, Any]:
        plugin_id = self.selected_plugin_id()
        if plugin_id is None:
            raise ValueError("No plugin selected")
        output_path = text_value(self.form["plugin_list"].parts["export_path"]).strip()
        if not output_path:
            raise ValueError("Export path is required")
        result = self.plugin_pack_service.export_plugin_pack(plugin_id, output_path)
        self._publish_status(f"Exported plugin '{plugin_id}' to {result['zip_path']}.")
        return result

    def import_plugin_pack(self) -> dict[str, Any]:
        zip_path = text_value(self.form["plugin_list"].parts["import_path"]).strip()
        if not zip_path:
            raise ValueError("Import ZIP path is required")
        result = self.plugin_pack_service.import_plugin_pack(zip_path)
        self.refresh()
        self._publish_status(f"Imported plugin '{result['plugin_id']}'.")
        self._notify_plugins_changed()
        return result

    def handle_selection_changed(self, *_args: Any) -> None:
        self.form["plugin_list"].sync_selection_state()
        self.form["plugin_details"].set_plugin(self.form["plugin_list"].selected())

    def handle_filter_changed(self, *_args: Any) -> None:
        self.refresh()

    def handle_enable_clicked(self) -> None:
        try:
            self.enable_selected_plugin()
        except Exception as exc:
            self._publish_status(str(exc))

    def handle_disable_clicked(self) -> None:
        try:
            self.disable_selected_plugin()
        except Exception as exc:
            self._publish_status(str(exc))

    def handle_refresh_clicked(self) -> None:
        try:
            self.reload_plugins()
        except Exception as exc:
            self._publish_status(str(exc))

    def handle_export_clicked(self) -> None:
        try:
            self.export_selected_plugin_pack()
        except Exception as exc:
            self._publish_status(str(exc))

    def handle_import_clicked(self) -> None:
        try:
            self.import_plugin_pack()
        except Exception as exc:
            self._publish_status(str(exc))

    def _connect_events(self) -> None:
        parts = self.form["plugin_list"].parts
        parts["plugin_combo"].currentIndexChanged.connect(self.handle_selection_changed)
        parts["filter_combo"].currentIndexChanged.connect(self.handle_filter_changed)
        parts["enable_button"].clicked.connect(self.handle_enable_clicked)
        parts["disable_button"].clicked.connect(self.handle_disable_clicked)
        parts["refresh_button"].clicked.connect(self.handle_refresh_clicked)
        parts["export_button"].clicked.connect(self.handle_export_clicked)
        parts["import_button"].clicked.connect(self.handle_import_clicked)

    def _publish_status(self, message: str) -> None:
        if self.on_status is not None:
            self.on_status(message)

    def _notify_plugins_changed(self) -> None:
        if self.on_plugins_changed is not None:
            self.on_plugins_changed()


def _build_form() -> dict[str, Any]:
    _qtcore, _qtgui, qtwidgets = load_qt()
    plugin_list = PluginListWidget()
    plugin_details = PluginDetailsWidget()
    if qtwidgets is None:
        return {
            "widget": object(),
            "plugin_list": plugin_list,
            "plugin_details": plugin_details,
        }

    widget = qtwidgets.QWidget()
    layout = qtwidgets.QVBoxLayout(widget)
    layout.addWidget(plugin_list.widget)
    layout.addWidget(plugin_details.widget)
    return {
        "widget": widget,
        "plugin_list": plugin_list,
        "plugin_details": plugin_details,
    }
