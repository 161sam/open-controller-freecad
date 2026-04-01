from __future__ import annotations

from ocw_workbench.commands.base import BaseCommand
from ocw_workbench.gui.panels._common import log_to_console
from ocw_workbench.gui.runtime import open_dialog, show_error


class ImportTemplateFromFCStdCommand(BaseCommand):
    ICON_NAME = "import_template"

    def GetResources(self):
        return self.resources(
            "Import Template",
            "Import a template from an FCStd file.",
        )

    def Activated(self):
        try:
            from ocw_workbench.gui.panels.import_template_from_fcstd_panel import ImportTemplateFromFCStdPanel
            from ocw_workbench.gui.panels.template_inspector_panel import TemplateInspectorPanel

            def handle_imported(path):
                try:
                    import FreeCAD as App
                    from ocw_workbench.gui.runtime import open_dialog
                    from ocw_workbench.workbench import _ACTIVE_WORKBENCH, _refresh_create_panel_if_open

                    doc = App.ActiveDocument or App.newDocument("Controller")
                    _refresh_create_panel_if_open(doc)
                    on_status = _ACTIVE_WORKBENCH.set_status if _ACTIVE_WORKBENCH is not None and _ACTIVE_WORKBENCH.doc is doc else None
                    open_dialog(
                        "Template Inspector",
                        TemplateInspectorPanel(
                            path,
                            on_saved=lambda _saved_path: _refresh_create_panel_if_open(doc),
                            on_status=on_status,
                        ),
                        width=920,
                        height=760,
                    )
                except Exception:
                    return

            panel = ImportTemplateFromFCStdPanel(on_imported=handle_imported)
            open_dialog("Import Template from FCStd", panel, width=860, height=520)
            log_to_console("Import Template from FCStd dialog opened.")
        except Exception as exc:
            show_error("Import Template from FCStd", exc)
