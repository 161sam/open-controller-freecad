from __future__ import annotations

from typing import Any

try:
    import FreeCAD as App
except ImportError:
    App = None

try:
    import FreeCADGui as Gui
except ImportError:
    Gui = None

from ocf_freecad.gui.panels._common import FallbackLabel, load_qt, set_label_text
from ocf_freecad.gui.panels.components_panel import ComponentsPanel
from ocf_freecad.gui.panels.constraints_panel import ConstraintsPanel
from ocf_freecad.gui.panels.create_panel import CreatePanel
from ocf_freecad.gui.panels.info_panel import InfoPanel
from ocf_freecad.gui.panels.layout_panel import LayoutPanel
from ocf_freecad.services.controller_service import ControllerService

_ACTIVE_WORKBENCH: ProductWorkbenchPanel | None = None
_ACTIVE_DOCK: Any | None = None


class OpenControllerWorkbench((Gui.Workbench if Gui is not None else object)):
    MenuText = "Open Controller"
    ToolTip = "Modular MIDI Controller Design"
    Icon = ""

    def Initialize(self) -> None:
        if Gui is None:
            return
        from ocf_freecad.commands.add_component import AddComponentCommand
        from ocf_freecad.commands.apply_layout import ApplyLayoutCommand
        from ocf_freecad.commands.create_from_template import CreateFromTemplateCommand
        from ocf_freecad.commands.select_component import SelectComponentCommand
        from ocf_freecad.commands.validate_constraints import ValidateConstraintsCommand

        Gui.addCommand("OCF_CreateController", CreateFromTemplateCommand())
        Gui.addCommand("OCF_AddComponent", AddComponentCommand())
        Gui.addCommand("OCF_ApplyLayout", ApplyLayoutCommand())
        Gui.addCommand("OCF_SelectComponent", SelectComponentCommand())
        Gui.addCommand("OCF_ValidateConstraints", ValidateConstraintsCommand())

        create_commands = ["OCF_CreateController"]
        edit_commands = [
            "OCF_AddComponent",
            "OCF_SelectComponent",
            "OCF_ApplyLayout",
            "OCF_ValidateConstraints",
        ]
        self.appendToolbar("OCF Create", create_commands)
        self.appendToolbar("OCF Edit", edit_commands)
        self.appendMenu("OCF", create_commands + edit_commands)
        self.appendMenu("OCF/Create", create_commands)
        self.appendMenu("OCF/Edit", edit_commands)

    def Activated(self) -> None:
        if App is None:
            return
        doc = App.ActiveDocument or App.newDocument("Controller")
        ensure_workbench_ui(doc, focus="create")

    def Deactivated(self) -> None:
        return


class ProductWorkbenchPanel:
    def __init__(self, doc: Any, controller_service: ControllerService | None = None) -> None:
        self.doc = doc
        self.controller_service = controller_service or ControllerService()
        self.form = self._build_shell()
        self.widget = self.form["widget"]
        self.create_panel = CreatePanel(
            doc,
            controller_service=self.controller_service,
            on_created=self._handle_created,
            on_status=self.set_status,
        )
        self.layout_panel = LayoutPanel(
            doc,
            controller_service=self.controller_service,
            on_applied=self._handle_layout_applied,
            on_status=self.set_status,
        )
        self.components_panel = ComponentsPanel(
            doc,
            controller_service=self.controller_service,
            on_selection_changed=self._handle_selection_changed,
            on_components_changed=self._handle_components_changed,
            on_status=self.set_status,
        )
        self.constraints_panel = ConstraintsPanel(
            doc,
            controller_service=self.controller_service,
            on_selection_changed=self._handle_selection_changed,
            on_validated=self._handle_validated,
            on_status=self.set_status,
        )
        self.info_panel = InfoPanel(doc, controller_service=self.controller_service)
        self._mount_panels()
        self.refresh_all()
        self.focus_panel("create")

    def refresh_all(self) -> None:
        self.create_panel.refresh()
        self.layout_panel.refresh()
        self.components_panel.refresh()
        self.constraints_panel.refresh()
        self.info_panel.refresh()

    def focus_panel(self, panel_name: str) -> None:
        widget = {
            "create": self.create_panel.widget,
            "layout": self.layout_panel.widget,
            "components": self.components_panel.widget,
            "constraints": self.constraints_panel.widget,
            "info": self.info_panel.widget,
        }.get(panel_name)
        if widget is not None and hasattr(widget, "setFocus"):
            widget.setFocus()
        titles = {
            "create": "Create",
            "layout": "Layout",
            "components": "Components",
            "constraints": "Constraints",
            "info": "Info",
        }
        self.set_status(f"{titles.get(panel_name, 'Workbench')} panel active.")

    def set_status(self, message: str) -> None:
        set_label_text(self.form["status"], message)

    def accept(self) -> bool:
        self.refresh_all()
        return True

    def reject(self) -> bool:
        return True

    def _build_shell(self) -> dict[str, Any]:
        qtcore, _qtgui, qtwidgets = load_qt()
        if qtwidgets is None or qtcore is None:
            return {"widget": object(), "status": FallbackLabel("Open Controller workbench ready.")}

        widget = qtwidgets.QWidget()
        root = qtwidgets.QVBoxLayout(widget)
        title = qtwidgets.QLabel("Open Controller Studio")
        title.setStyleSheet("font-size: 16px; font-weight: 600;")
        subtitle = qtwidgets.QLabel("Create, lay out, validate and refine controllers without leaving the workbench.")
        subtitle.setWordWrap(True)
        status = qtwidgets.QLabel("Open Controller workbench ready.")
        status.setWordWrap(True)
        splitter = qtwidgets.QSplitter(qtcore.Qt.Horizontal)
        left_column = qtwidgets.QWidget()
        left_layout = qtwidgets.QVBoxLayout(left_column)
        center_column = qtwidgets.QWidget()
        center_layout = qtwidgets.QVBoxLayout(center_column)
        right_column = qtwidgets.QWidget()
        right_layout = qtwidgets.QVBoxLayout(right_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setContentsMargins(0, 0, 0, 0)
        splitter.addWidget(left_column)
        splitter.addWidget(center_column)
        splitter.addWidget(right_column)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 2)
        root.addWidget(title)
        root.addWidget(subtitle)
        root.addWidget(splitter, 1)
        root.addWidget(status)
        return {
            "widget": widget,
            "status": status,
            "left_layout": left_layout,
            "center_layout": center_layout,
            "right_layout": right_layout,
        }

    def _mount_panels(self) -> None:
        if "left_layout" not in self.form:
            return
        self.form["left_layout"].addWidget(_group_box("Start / Create", self.create_panel.widget))
        self.form["left_layout"].addWidget(_group_box("Template / Variant Info", self.info_panel.widget))
        self.form["center_layout"].addWidget(_group_box("Layout", self.layout_panel.widget))
        self.form["center_layout"].addWidget(_group_box("Constraints", self.constraints_panel.widget))
        self.form["right_layout"].addWidget(_group_box("Components", self.components_panel.widget))

    def _handle_created(self, _state: dict[str, Any]) -> None:
        self.components_panel.refresh()
        self.layout_panel.refresh()
        self.constraints_panel.refresh()
        self.info_panel.refresh()
        self.focus_panel("layout")

    def _handle_layout_applied(self, _result: dict[str, Any]) -> None:
        self.components_panel.refresh()
        self.constraints_panel.validate()
        self.info_panel.refresh()
        self.focus_panel("constraints")

    def _handle_components_changed(self, _state: dict[str, Any]) -> None:
        self.layout_panel.refresh()
        self.constraints_panel.validate()
        self.info_panel.refresh()
        self.focus_panel("components")

    def _handle_selection_changed(self, _component_id: str | None) -> None:
        self.info_panel.refresh()

    def _handle_validated(self, _report: dict[str, Any]) -> None:
        self.info_panel.refresh()


def ensure_workbench_ui(doc: Any | None = None, focus: str = "create") -> ProductWorkbenchPanel:
    global _ACTIVE_DOCK
    global _ACTIVE_WORKBENCH

    if doc is None and App is not None:
        doc = App.ActiveDocument or App.newDocument("Controller")
    if doc is None:
        raise RuntimeError("No active FreeCAD document")

    if _ACTIVE_WORKBENCH is None or _ACTIVE_WORKBENCH.doc is not doc:
        if _ACTIVE_DOCK is not None and hasattr(_ACTIVE_DOCK, "close"):
            _ACTIVE_DOCK.close()
        _ACTIVE_WORKBENCH = ProductWorkbenchPanel(doc)
        _ACTIVE_DOCK = _show_in_dock(_ACTIVE_WORKBENCH)
    else:
        _ACTIVE_WORKBENCH.refresh_all()
        _show_existing_dock(_ACTIVE_DOCK)
    _ACTIVE_WORKBENCH.focus_panel(focus)
    return _ACTIVE_WORKBENCH


def _group_box(title: str, child: Any) -> Any:
    _qtcore, _qtgui, qtwidgets = load_qt()
    if qtwidgets is None:
        return child
    group = qtwidgets.QGroupBox(title)
    layout = qtwidgets.QVBoxLayout(group)
    layout.addWidget(child)
    return group


def _show_in_dock(panel: ProductWorkbenchPanel) -> Any | None:
    qtcore, _qtgui, qtwidgets = load_qt()
    if Gui is None or qtcore is None or qtwidgets is None or not hasattr(Gui, "getMainWindow"):
        if Gui is not None and hasattr(Gui, "Control"):
            Gui.Control.showDialog(panel)
        return None
    main_window = Gui.getMainWindow()
    dock = qtwidgets.QDockWidget("Open Controller", main_window)
    dock.setObjectName("OCFWorkbenchV2Dock")
    dock.setAllowedAreas(qtcore.Qt.LeftDockWidgetArea | qtcore.Qt.RightDockWidgetArea)
    dock.setWidget(panel.widget)
    main_window.addDockWidget(qtcore.Qt.RightDockWidgetArea, dock)
    dock.show()
    dock.raise_()
    return dock


def _show_existing_dock(dock: Any | None) -> None:
    if dock is None:
        return
    if hasattr(dock, "show"):
        dock.show()
    if hasattr(dock, "raise_"):
        dock.raise_()
