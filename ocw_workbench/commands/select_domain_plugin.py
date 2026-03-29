from __future__ import annotations

from ocw_workbench.commands.base import BaseCommand
from ocw_workbench.gui.panels._common import log_to_console
from ocw_workbench.gui.runtime import show_error


class SelectDomainPluginCommand(BaseCommand):
    ICON_NAME = "plugin_manager"

    def GetResources(self):
        return self.resources(
            "Select Domain",
            "Choose the active domain plugin for a new or still-switchable document.",
        )

    def Activated(self):
        try:
            import FreeCAD as App

            from ocw_workbench.workbench import choose_domain_plugin_interactive

            doc = App.ActiveDocument or App.newDocument("Controller")
            result = choose_domain_plugin_interactive(doc)
            if result is not None:
                log_to_console(
                    f"Domain selection command activated '{result['active_plugin_id']}' for document "
                    f"'{getattr(doc, 'Name', '<unnamed>')}'."
                )
        except Exception as exc:
            show_error("Select Domain", exc)
