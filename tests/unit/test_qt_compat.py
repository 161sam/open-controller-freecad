import builtins
import types

from ocw_workbench.gui import docking
from ocw_workbench.gui.panels import _common
from ocw_workbench.gui.taskpanels import constraints_taskpanel, layout_taskpanel, library_taskpanel
from ocw_workbench.gui.widgets import plugin_list
from ocw_workbench.gui.runtime import _show_message
from ocw_workbench.workbench import OpenControllerWorkbench


class _Recorder:
    def __init__(self) -> None:
        self.entries = []

    def __call__(self, message: str, level: str = "message") -> None:
        self.entries.append((level, message))


def test_load_qt_falls_back_after_non_importerror(monkeypatch):
    qtcore = object()
    qtgui = object()
    pyside6_module = types.SimpleNamespace(QtCore=qtcore, QtGui=qtgui, QtWidgets=None)
    calls = []
    original_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "PySide":
            calls.append(name)
            raise NameError("_init_pyside_extension is not defined")
        if name == "PySide6":
            calls.append(name)
            return pyside6_module
        if name == "PySide2":
            calls.append(name)
            raise AssertionError("PySide2 should not be tried after a successful PySide6 import")
        return original_import(name, globals, locals, fromlist, level)

    recorder = _Recorder()
    monkeypatch.setattr(_common, "_QT_MODULES", None)
    monkeypatch.setattr(_common, "log_to_console", recorder)
    monkeypatch.setattr(builtins, "__import__", fake_import)

    loaded_core, loaded_gui, loaded_widgets = _common.load_qt()

    assert calls == ["PySide", "PySide6"]
    assert loaded_core is qtcore
    assert loaded_gui is qtgui
    assert loaded_widgets is qtgui
    assert recorder.entries[0][0] == "warning"
    assert "PySide" in recorder.entries[0][1]
    assert recorder.entries[1] == ("message", "Qt binding loaded via PySide6.")


def test_load_qt_uses_qtgui_when_qtwidgets_is_missing(monkeypatch):
    qtcore = object()
    qtgui = object()
    pyside_module = types.SimpleNamespace(QtCore=qtcore, QtGui=qtgui)
    original_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "PySide":
            return pyside_module
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(_common, "_QT_MODULES", None)
    monkeypatch.setattr(_common, "log_to_console", lambda *args, **kwargs: None)
    monkeypatch.setattr(builtins, "__import__", fake_import)

    loaded_core, loaded_gui, loaded_widgets = _common.load_qt()

    assert loaded_core is qtcore
    assert loaded_gui is qtgui
    assert loaded_widgets is qtgui


def test_qt_self_check_logs_binding(monkeypatch):
    qtcore = object()
    qtgui = object()
    recorder = _Recorder()

    monkeypatch.setattr(_common, "_QT_MODULES", (qtcore, qtgui, qtgui))
    monkeypatch.setattr(_common, "_QT_BINDING_NAME", "PySide6")
    monkeypatch.setattr(_common, "log_to_console", recorder)

    message = _common.qt_self_check()

    assert "binding=PySide6" in message
    assert recorder.entries == [("message", message)]


def test_add_layout_content_routes_widgets_and_layouts(monkeypatch):
    class FakeWidget:
        pass

    class FakeLayout:
        def __init__(self, *_args, **_kwargs) -> None:
            self.widgets = []
            self.layouts = []

        def addWidget(self, widget, *_args):
            if isinstance(widget, FakeLayout):
                raise TypeError("layout passed to addWidget")
            self.widgets.append(widget)

        def addLayout(self, layout, *_args):
            if not isinstance(layout, FakeLayout):
                raise TypeError("widget passed to addLayout")
            self.layouts.append(layout)

    qtwidgets = types.SimpleNamespace(QLayout=FakeLayout)
    monkeypatch.setattr(_common, "load_qt", lambda: (None, None, qtwidgets))

    parent = FakeLayout()
    row_widget = FakeWidget()
    row_layout = FakeLayout()

    _common.add_layout_content(parent, row_widget)
    _common.add_layout_content(parent, row_layout)

    assert parent.widgets == [row_widget]
    assert parent.layouts == [row_layout]


def test_wrap_widget_in_scroll_area_sets_resizable_container_and_layout_constraint(monkeypatch):
    class FakeLayout:
        SetMinAndMaxSize = 7

        def __init__(self) -> None:
            self.constraint = None

        def setSizeConstraint(self, value) -> None:
            self.constraint = value

    class FakeWidget:
        def __init__(self) -> None:
            self._layout = FakeLayout()
            self.minimum_size = None
            self.size_policy = None

        def layout(self):
            return self._layout

        def setMinimumSize(self, width: int, height: int) -> None:
            self.minimum_size = (width, height)

        def setSizePolicy(self, horizontal, vertical) -> None:
            self.size_policy = (horizontal, vertical)

    class FakeScrollArea:
        def __init__(self) -> None:
            self.resizable = False
            self.widget = None
            self.minimum_size = None
            self.size_policy = None

        def setWidgetResizable(self, value: bool) -> None:
            self.resizable = value

        def setHorizontalScrollBarPolicy(self, *_args) -> None:
            return

        def setVerticalScrollBarPolicy(self, *_args) -> None:
            return

        def setFrameShape(self, *_args) -> None:
            return

        def setWidget(self, widget) -> None:
            self.widget = widget

        def setMinimumSize(self, width: int, height: int) -> None:
            self.minimum_size = (width, height)

        def setSizePolicy(self, horizontal, vertical) -> None:
            self.size_policy = (horizontal, vertical)

    class FakeFrame:
        NoFrame = 0

    class FakeSizePolicy:
        Fixed = 0
        Minimum = 1
        Preferred = 2
        MinimumExpanding = 3
        Expanding = 4

    qtcore = types.SimpleNamespace(Qt=types.SimpleNamespace(ScrollBarAsNeeded=1))
    qtwidgets = types.SimpleNamespace(
        QScrollArea=FakeScrollArea,
        QFrame=FakeFrame,
        QSizePolicy=FakeSizePolicy,
        QLayout=FakeLayout,
    )
    monkeypatch.setattr(_common, "load_qt", lambda: (qtcore, object(), qtwidgets))

    content = FakeWidget()
    scroll_area = _common.wrap_widget_in_scroll_area(content)

    assert scroll_area.resizable is True
    assert scroll_area.widget is content
    assert content._layout.constraint == FakeLayout.SetMinAndMaxSize


def test_build_group_box_uses_layout_margin_and_minimum_expanding_policy(monkeypatch):
    class FakeLayout:
        def __init__(self, parent=None) -> None:
            self.margins = None
            self.spacing = None
            self.constraint = None
            if parent is not None and hasattr(parent, "setLayout"):
                parent.setLayout(self)

        def setContentsMargins(self, *margins) -> None:
            self.margins = margins

        def setSpacing(self, spacing) -> None:
            self.spacing = spacing

        def setSizeConstraint(self, value) -> None:
            self.constraint = value

        def setVerticalSpacing(self, value) -> None:
            self.vertical_spacing = value

        def setHorizontalSpacing(self, value) -> None:
            self.horizontal_spacing = value

    class FakeGroupBox:
        def __init__(self, title) -> None:
            self.title = title
            self.object_name = None
            self.flat = None
            self.layout_ref = None
            self.minimum_size = None
            self.size_policy = None

        def setObjectName(self, name: str) -> None:
            self.object_name = name

        def setFlat(self, flat: bool) -> None:
            self.flat = flat

        def setLayout(self, layout) -> None:
            self.layout_ref = layout

        def setMinimumSize(self, width: int, height: int) -> None:
            self.minimum_size = (width, height)

        def setSizePolicy(self, horizontal, vertical) -> None:
            self.size_policy = (horizontal, vertical)

    class FakeQLayout:
        SetMinAndMaxSize = 9

    class FakeSizePolicy:
        Fixed = 0
        Minimum = 1
        Preferred = 2
        MinimumExpanding = 3
        Expanding = 4

    qtwidgets = types.SimpleNamespace(
        QGroupBox=FakeGroupBox,
        QVBoxLayout=FakeLayout,
        QHBoxLayout=FakeLayout,
        QFormLayout=FakeLayout,
        QGridLayout=FakeLayout,
        QLayout=FakeQLayout,
        QSizePolicy=FakeSizePolicy,
    )
    monkeypatch.setattr(_common, "load_qt", lambda: (None, object(), qtwidgets))

    group, layout = _common.build_group_box(qtwidgets, "Placement Settings", layout_kind="form")

    assert group.object_name == "OCWSectionGroup"
    assert group.flat is True
    assert group.minimum_size == (0, 0)
    assert group.size_policy == (FakeSizePolicy.Expanding, FakeSizePolicy.MinimumExpanding)
    assert layout.margins == (0, _common.SPACE_1, 0, 0)
    assert layout.constraint == FakeQLayout.SetMinAndMaxSize
    assert layout.vertical_spacing == _common.SPACE_2
    assert layout.horizontal_spacing == _common.SPACE_2


def test_task_panel_builders_use_shared_layout_defaults(monkeypatch):
    class FakeWidget:
        def __init__(self, *_args, **_kwargs) -> None:
            self.layout_ref = None
            self.minimum_size = None
            self.size_policy = None
            self.read_only = False
            self.line_wrap_mode = None

        def setLayout(self, layout) -> None:
            self.layout_ref = layout

        def layout(self):
            return self.layout_ref

        def setMinimumSize(self, width: int, height: int) -> None:
            self.minimum_size = (width, height)

        def setSizePolicy(self, horizontal, vertical) -> None:
            self.size_policy = (horizontal, vertical)

        def setReadOnly(self, value: bool) -> None:
            self.read_only = value

        def setLineWrapMode(self, value) -> None:
            self.line_wrap_mode = value

        def setMinimumHeight(self, value: int) -> None:
            self.minimum_height = value

    class FakeComboBox(FakeWidget):
        AdjustToMinimumContentsLengthWithIcon = 1

        def addItems(self, items) -> None:
            self.items = list(items)

        def setMinimumContentsLength(self, value: int) -> None:
            self.minimum_contents_length = value

        def setSizeAdjustPolicy(self, value) -> None:
            self.size_adjust_policy = value

    class FakeSpinBox(FakeWidget):
        def setRange(self, low: float, high: float) -> None:
            self.range = (low, high)

        def setValue(self, value: float) -> None:
            self.value = value

    class FakePlainTextEdit(FakeWidget):
        WidgetWidth = 1

    class FakeLayout:
        def __init__(self, parent=None) -> None:
            self.margins = None
            self.spacing = None
            self.vertical_spacing = None
            self.horizontal_spacing = None
            self.constraint = None
            self.widgets = []
            self.layouts = []
            if parent is not None and hasattr(parent, "setLayout"):
                parent.setLayout(self)

        def setContentsMargins(self, *margins) -> None:
            self.margins = margins

        def setSpacing(self, spacing) -> None:
            self.spacing = spacing

        def setVerticalSpacing(self, spacing) -> None:
            self.vertical_spacing = spacing

        def setHorizontalSpacing(self, spacing) -> None:
            self.horizontal_spacing = spacing

        def setFieldGrowthPolicy(self, value) -> None:
            self.field_growth_policy = value

        def setLabelAlignment(self, value) -> None:
            self.label_alignment = value

        def setFormAlignment(self, value) -> None:
            self.form_alignment = value

        def setSizeConstraint(self, value) -> None:
            self.constraint = value

        def addRow(self, *_args) -> None:
            return

        def addWidget(self, widget, *_args) -> None:
            self.widgets.append(widget)

        def addLayout(self, layout, *_args) -> None:
            self.layouts.append(layout)

    class FakeQLayout:
        SetMinAndMaxSize = 7

    class FakeQFormLayout(FakeLayout):
        AllNonFixedFieldsGrow = 11

    class FakeSizePolicy:
        Fixed = 0
        Minimum = 1
        Preferred = 2
        MinimumExpanding = 3
        Expanding = 4

    qtcore = types.SimpleNamespace(Qt=types.SimpleNamespace(AlignLeft=1, AlignTop=2, AlignVCenter=4))
    qtwidgets = types.SimpleNamespace(
        QWidget=FakeWidget,
        QVBoxLayout=FakeLayout,
        QHBoxLayout=FakeLayout,
        QFormLayout=FakeQFormLayout,
        QComboBox=FakeComboBox,
        QDoubleSpinBox=FakeSpinBox,
        QPlainTextEdit=FakePlainTextEdit,
        QSizePolicy=FakeSizePolicy,
        QLayout=FakeQLayout,
    )

    monkeypatch.setattr(_common, "load_qt", lambda: (qtcore, object(), qtwidgets))
    for module in (layout_taskpanel, library_taskpanel, constraints_taskpanel):
        monkeypatch.setattr(module, "load_qt", lambda: (qtcore, object(), qtwidgets))

    layout_form = layout_taskpanel._build_layout_form()
    library_form = library_taskpanel._build_library_form()
    constraints_form = constraints_taskpanel._build_constraints_form()

    assert layout_form["widget"].minimum_size == (0, 0)
    assert layout_form["widget"].size_policy == (FakeSizePolicy.Expanding, FakeSizePolicy.Expanding)
    assert layout_form["strategy"].size_policy == (FakeSizePolicy.Expanding, FakeSizePolicy.Preferred)
    assert library_form["widget"].minimum_size == (0, 0)
    assert library_form["category"].size_policy == (FakeSizePolicy.Expanding, FakeSizePolicy.Preferred)
    assert constraints_form["widget"].minimum_size == (0, 0)
    assert constraints_form["results"].read_only is True


def test_show_message_prefers_exec(monkeypatch):
    class FakeMessageBox:
        Critical = 1
        Information = 2

        def __init__(self, *_args, **_kwargs) -> None:
            self.executed = None
            self.details = None

        def setDetailedText(self, details):
            self.details = details

        def exec(self):
            self.executed = "exec"

        def exec_(self):
            self.executed = "exec_"

    qtwidgets = types.SimpleNamespace(QMessageBox=FakeMessageBox)
    monkeypatch.setattr("ocw_workbench.gui.runtime.load_qt", lambda: (object(), object(), qtwidgets))
    monkeypatch.setattr("ocw_workbench.gui.runtime._main_window", lambda: None)

    captured = {}

    def fake_exec_dialog(dialog):
        result = _common.exec_dialog(dialog)
        captured["executed"] = dialog.executed
        captured["details"] = dialog.details
        return result

    monkeypatch.setattr("ocw_workbench.gui.runtime.exec_dialog", fake_exec_dialog)

    _show_message("critical", "Failure", "Broken", details="trace")

    assert captured["executed"] == "exec"
    assert captured["details"] == "trace"


def test_workbench_activated_logs_instead_of_raising(monkeypatch):
    fake_doc = types.SimpleNamespace(Name="Controller", Objects=[], recompute=lambda: None)
    fake_app = types.SimpleNamespace(ActiveDocument=fake_doc, newDocument=lambda name: fake_doc)
    logged = []

    monkeypatch.setattr("ocw_workbench.workbench.App", fake_app)
    monkeypatch.setattr("ocw_workbench.workbench.ensure_workbench_ui", lambda *_args, **_kwargs: (_ for _ in ()).throw(NameError("_init_pyside_extension is not defined")))
    monkeypatch.setattr("ocw_workbench.workbench.log_exception", lambda context, exc: logged.append((context, str(exc))))
    monkeypatch.setattr("ocw_workbench.workbench.ControllerService", lambda: types.SimpleNamespace(create_controller=lambda *_args, **_kwargs: None))

    workbench = OpenControllerWorkbench()
    workbench.Activated()

    assert logged == [("Workbench activation failed", "_init_pyside_extension is not defined")]


def test_create_or_reuse_dock_tabifies_existing_right_dock(monkeypatch):
    class FakeDockWidget:
        DockWidgetClosable = 1
        DockWidgetMovable = 2

        def __init__(self, title, parent):
            self.title = title
            self.parent = parent
            self._object_name = ""
            self._widget = None
            self.features = None
            self.allowed_areas = None
            self.shown = False
            self.raised = False
            self.activated = False

        def setObjectName(self, name):
            self._object_name = name

        def objectName(self):
            return self._object_name

        def setAllowedAreas(self, areas):
            self.allowed_areas = areas

        def setFeatures(self, features):
            self.features = features

        def widget(self):
            return self._widget

        def setWidget(self, widget):
            self._widget = widget

        def show(self):
            self.shown = True

        def raise_(self):
            self.raised = True

        def activateWindow(self):
            self.activated = True

    class FakeMainWindow:
        def __init__(self):
            self.children = []
            self.tabified = []
            self.areas = {}

        def findChild(self, cls, object_name):
            for child in self.children:
                if isinstance(child, cls) and child.objectName() == object_name:
                    return child
            return None

        def addDockWidget(self, area, dock):
            self.children.append(dock)
            self.areas[dock] = area

        def findChildren(self, cls):
            return [child for child in self.children if isinstance(child, cls)]

        def dockWidgetArea(self, dock):
            return self.areas[dock]

        def tabifyDockWidget(self, candidate, dock):
            self.tabified.append((candidate.objectName(), dock.objectName()))

    fake_main_window = FakeMainWindow()
    existing = FakeDockWidget("Existing", fake_main_window)
    existing.setObjectName("PropertyView")
    fake_main_window.children.append(existing)
    fake_main_window.areas[existing] = 2

    qtcore = types.SimpleNamespace(Qt=types.SimpleNamespace(LeftDockWidgetArea=1, RightDockWidgetArea=2))
    qtwidgets = types.SimpleNamespace(QDockWidget=FakeDockWidget)
    logs = []

    monkeypatch.setattr("ocw_workbench.gui.docking.load_qt", lambda: (qtcore, object(), qtwidgets))
    monkeypatch.setattr("ocw_workbench.gui.docking.get_main_window", lambda: fake_main_window)
    monkeypatch.setattr("ocw_workbench.gui.docking.log_to_console", lambda message, level="message": logs.append((level, message)))

    dock_widget = object()
    dock_ref = docking.create_or_reuse_dock("Open Controller", dock_widget)

    assert dock_ref is not None
    assert dock_ref.widget() is dock_widget
    assert fake_main_window.tabified == [("PropertyView", "OCWWorkbenchDock")]
    assert dock_ref.shown is True
    assert dock_ref.raised is True
    assert dock_ref.activated is True
    assert all("setFloating" not in message for _level, message in logs)


def test_product_workbench_panel_uses_tab_shell():
    from ocw_workbench.services.controller_service import ControllerService
    from ocw_workbench.workbench import ProductWorkbenchPanel

    class FakeDocument:
        def __init__(self) -> None:
            self.Objects = []

        def recompute(self) -> None:
            return

    doc = FakeDocument()
    panel = ProductWorkbenchPanel(doc, controller_service=ControllerService())

    assert panel.form["primary_navigation"] == "tabs"
    assert panel.form["navigation_items"] == ["Create", "Layout", "Components", "Validate", "Plugins"]
    assert "tabs" not in panel.form or panel.form["tabs"] is not None
    assert panel.form["title"].text == "Open Controller Workbench"
    assert panel.form["context_summary"].text.startswith("Create |")


def test_plugin_list_build_uses_widget_safe_row_insertion(monkeypatch):
    class FakeWidget:
        def __init__(self, *_args, **_kwargs) -> None:
            self.layout_ref = None
            self.visible = True
            self.object_name = ""
            self.text_value = ""

        def setLayout(self, layout) -> None:
            self.layout_ref = layout

        def setObjectName(self, name: str) -> None:
            self.object_name = name

        def setVisible(self, visible: bool) -> None:
            self.visible = visible

        def setWordWrap(self, *_args) -> None:
            return

        def setText(self, text: str) -> None:
            self.text_value = text

        def setCheckable(self, *_args) -> None:
            return

        def setChecked(self, *_args) -> None:
            return

        def setToolButtonStyle(self, *_args) -> None:
            return

        def setArrowType(self, *_args) -> None:
            return

        def setReadOnly(self, *_args) -> None:
            return

        def setLineWrapMode(self, *_args) -> None:
            return

        def setMaximumHeight(self, *_args) -> None:
            return

        def setMinimumHeight(self, *_args) -> None:
            return

        def setSizePolicy(self, *_args) -> None:
            return

        def setToolTip(self, *_args) -> None:
            return

        def setMinimumSize(self, *_args) -> None:
            return

    class FakeSignal:
        def connect(self, *_args, **_kwargs) -> None:
            return

    class FakeToolButton(FakeWidget):
        def __init__(self, *_args, **_kwargs) -> None:
            super().__init__()
            self.toggled = FakeSignal()

    class FakePlainTextEdit(FakeWidget):
        WidgetWidth = 1

    class FakeLayout:
        def __init__(self, parent=None) -> None:
            self.widgets = []
            self.layouts = []
            if parent is not None and hasattr(parent, "setLayout"):
                parent.setLayout(self)

        def setContentsMargins(self, *_args) -> None:
            return

        def setSpacing(self, *_args) -> None:
            return

        def addWidget(self, widget, *_args) -> None:
            if isinstance(widget, FakeLayout):
                raise TypeError("layout passed to addWidget")
            self.widgets.append(widget)

        def addLayout(self, layout, *_args) -> None:
            if not isinstance(layout, FakeLayout):
                raise TypeError("widget passed to addLayout")
            self.layouts.append(layout)

    class FakeComboBox(FakeWidget):
        AdjustToMinimumContentsLengthWithIcon = 1

        def addItems(self, items) -> None:
            self.items = list(items)

        def setSizeAdjustPolicy(self, *_args) -> None:
            return

        def setMinimumContentsLength(self, *_args) -> None:
            return

    class FakeLineEdit(FakeWidget):
        pass

    class FakePushButton(FakeWidget):
        pass

    class FakeLabel(FakeWidget):
        pass

    class FakeGroupBox(FakeWidget):
        pass

    class FakeFrame(FakeWidget):
        NoFrame = 0

        def setFrameShape(self, *_args) -> None:
            return

    class FakeScrollArea(FakeWidget):
        def setWidgetResizable(self, *_args) -> None:
            return

        def setHorizontalScrollBarPolicy(self, *_args) -> None:
            return

        def setVerticalScrollBarPolicy(self, *_args) -> None:
            return

        def setFrameShape(self, *_args) -> None:
            return

        def setWidget(self, widget) -> None:
            self.widget = widget

    class FakeSizePolicy:
        Fixed = 0
        Minimum = 1
        Preferred = 2
        Expanding = 3

    qtcore = types.SimpleNamespace(
        Qt=types.SimpleNamespace(
            ToolButtonTextBesideIcon=1,
            DownArrow=2,
            RightArrow=3,
            ScrollBarAsNeeded=4,
        )
    )
    qtwidgets = types.SimpleNamespace(
        QWidget=FakeWidget,
        QLayout=FakeLayout,
        QVBoxLayout=FakeLayout,
        QHBoxLayout=FakeLayout,
        QFormLayout=FakeLayout,
        QGridLayout=FakeLayout,
        QGroupBox=FakeGroupBox,
        QComboBox=FakeComboBox,
        QLineEdit=FakeLineEdit,
        QPushButton=FakePushButton,
        QLabel=FakeLabel,
        QPlainTextEdit=FakePlainTextEdit,
        QToolButton=FakeToolButton,
        QFrame=FakeFrame,
        QScrollArea=FakeScrollArea,
        QSizePolicy=FakeSizePolicy,
    )

    monkeypatch.setattr(plugin_list, "load_qt", lambda: (qtcore, object(), qtwidgets))
    monkeypatch.setattr("ocw_workbench.gui.widgets.plugin_status_badge.load_qt", lambda: (qtcore, object(), qtwidgets))
    monkeypatch.setattr("ocw_workbench.gui.panels._common.load_qt", lambda: (qtcore, object(), qtwidgets))

    widget = plugin_list.PluginListWidget()

    assert widget.widget is not None


def test_product_workbench_panel_survives_plugin_panel_init_failure(monkeypatch):
    from ocw_workbench.services.controller_service import ControllerService
    from ocw_workbench.workbench import ProductWorkbenchPanel, _UnavailablePluginManagerPanel

    class FakeDocument:
        def __init__(self) -> None:
            self.Objects = []

        def recompute(self) -> None:
            return

    monkeypatch.setattr("ocw_workbench.workbench.PluginManagerPanel", lambda *args, **kwargs: (_ for _ in ()).throw(TypeError("broken plugin panel")))

    panel = ProductWorkbenchPanel(FakeDocument(), controller_service=ControllerService())

    assert isinstance(panel.plugin_manager_panel, _UnavailablePluginManagerPanel)
    assert panel.plugin_manager_panel.error_message == "Plugins panel unavailable. Check the report view for details."
