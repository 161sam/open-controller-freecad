from __future__ import annotations

from pathlib import Path

import pytest

from ocw_workbench.commands.factory import command_specs_by_command_id, component_toolbar_groups
from ocw_workbench.components.adapter import get_component_source_entries
from ocw_workbench.library.manager import ComponentLibraryManager
from ocw_workbench.plugins.activation import activate_plugin
from ocw_workbench.plugins.loader import PluginLoader
from ocw_workbench.services.controller_service import ControllerService
from ocw_workbench.services.plugin_service import reset_plugin_service
from ocw_workbench.templates.adapter import get_template_source_entries
from ocw_workbench.templates.generator import TemplateGenerator
from ocw_workbench.templates.registry import TemplateRegistry


@pytest.fixture(autouse=True)
def _reset_plugin_service_state():
    reset_plugin_service()
    yield
    reset_plugin_service()


class FakeFeatureDocument:
    def __init__(self) -> None:
        self.Objects = []
        self.removed = []
        self.recompute_count = 0
        self.transactions: list[tuple[str, str | None]] = []
        self._objects_by_name: dict[str, FakeFeature] = {}

    def recompute(self) -> None:
        self.recompute_count += 1

    def openTransaction(self, label: str) -> None:
        self.transactions.append(("open", label))

    def commitTransaction(self) -> None:
        self.transactions.append(("commit", None))

    def abortTransaction(self) -> None:
        self.transactions.append(("abort", None))

    def addObject(self, type_name: str, name: str):
        obj = FakeFeature(type_name, name)
        self.Objects.append(obj)
        self._objects_by_name[name] = obj
        return obj

    def getObject(self, name: str):
        return self._objects_by_name.get(name)

    def removeObject(self, name: str) -> None:
        self.removed.append(name)
        self.Objects = [obj for obj in self.Objects if obj.Name != name]
        self._objects_by_name.pop(name, None)


class FakeFeature:
    def __init__(self, type_name: str, name: str) -> None:
        self.TypeId = type_name
        self.Name = name
        self.Label = name
        self.PropertiesList = []
        self.Group = []
        self.ViewObject = type("FakeViewObject", (), {"Visibility": True, "ShapeColor": None, "LineColor": None})()

    def addProperty(self, _type_name: str, name: str, _group: str, _doc: str) -> None:
        if name not in self.PropertiesList:
            self.PropertiesList.append(name)
            setattr(self, name, "")

    def setEditorMode(self, _name: str, _mode: int) -> None:
        return

    def addObject(self, obj) -> None:
        if obj not in self.Group:
            self.Group.append(obj)


def test_bike_trailer_plugin_is_loaded_and_can_be_activated() -> None:
    reset_plugin_service()
    registry = PluginLoader().load_all()

    assert registry.has_plugin("bike_trailer")
    active = activate_plugin("bike_trailer", registry=registry)

    assert active.plugin_id == "bike_trailer"
    assert registry.get_active_domain() == "bike_trailer"


def test_bike_trailer_templates_and_components_are_available_via_plugin_data() -> None:
    reset_plugin_service()
    activate_plugin("bike_trailer")

    templates = {item["template"]["id"] for item in TemplateRegistry().list_templates()}
    components = {item["id"] for item in ComponentLibraryManager().list_components()}

    assert "bike_trailer.trailer_basic" in templates
    assert "bike_trailer.trailer_box" in templates
    assert "bike_trailer.wheel_20in_spoked" in components
    assert "bike_trailer.drawbar_hitch_standard" in components


def test_bike_trailer_sources_prefer_plugin_roots_when_active() -> None:
    reset_plugin_service()
    activate_plugin("bike_trailer")

    template_sources = get_template_source_entries()
    component_sources = get_component_source_entries()

    assert template_sources[0].plugin_id == "bike_trailer"
    assert component_sources[0].plugin_id == "bike_trailer"
    assert template_sources[0].path == Path("plugins/plugin_bike_trailer/templates").resolve()
    assert component_sources[0].path == Path("plugins/plugin_bike_trailer/components").resolve()


def test_bike_trailer_command_metadata_is_plugin_driven() -> None:
    reset_plugin_service()
    activate_plugin("bike_trailer")

    specs = command_specs_by_command_id()

    assert specs["OCW_PlaceWheel"].component == "wheel"
    assert specs["OCW_PlaceHitch"].plugin_id == "bike_trailer"
    assert specs["OCW_PlaceFrameConnector"].category == "Frame"
    groups = dict(component_toolbar_groups(active_plugin_id="bike_trailer"))
    assert groups["OCW Running Gear"] == ["OCW_PlaceHitch", "OCW_PlaceWheel"]


def test_bike_trailer_template_builds_non_midi_project() -> None:
    reset_plugin_service()
    activate_plugin("bike_trailer")

    project = TemplateGenerator().generate_from_template("trailer_basic")

    assert project["template"]["id"] == "bike_trailer.trailer_basic"
    assert any(component["type"] == "wheel" for component in project["components"])
    assert any(component["type"] == "hitch" for component in project["components"])
    assert any(component["group_id"] == "frame_core" for component in project["components"])


def test_bike_trailer_sync_generates_tree_groups_and_component_objects(monkeypatch) -> None:
    class FakeBuilder:
        def __init__(self, doc):
            self.doc = doc

        def build_body(self, _controller):
            return self.doc.addObject("Part::Feature", "ControllerBody")

        def build_top_plate(self, _controller):
            top = self.doc.addObject("Part::Feature", "TopPlate")
            top.Shape = type("Shape", (), {"BoundBox": type("BoundBox", (), {"ZMin": 29.0, "ZLength": 3.0})(), "copy": lambda self: self})()
            return top

        def apply_cutout_plan(self, top, _plan):
            top.Shape = "cut"
            return top

        def plan_cutout_boolean(self, _top, components):
            return type("CutPlan", (), {"tools": [object() for _ in components], "diagnostics": []})()

        def build_component_feature(self, _controller, component):
            return self.doc.addObject("Part::Feature", f"OCW_Component_{component['id']}")

        def build_keepouts(self, _components):
            return []

    monkeypatch.setattr("ocw_workbench.services.document_sync_service.ControllerBuilder", FakeBuilder)
    monkeypatch.setattr("ocw_workbench.services.controller_service.ControllerBuilder", FakeBuilder)
    monkeypatch.setattr("ocw_workbench.services.document_sync_service.freecad_gui.reveal_generated_objects", lambda _doc: 0)
    monkeypatch.setattr("ocw_workbench.services.document_sync_service.freecad_gui.activate_document", lambda _doc: True)
    monkeypatch.setattr("ocw_workbench.services.document_sync_service.freecad_gui.focus_view", lambda _doc, fit=True: True)

    reset_plugin_service()
    activate_plugin("bike_trailer")
    project = TemplateGenerator().generate_from_template("trailer_box")

    service = ControllerService()
    doc = FakeFeatureDocument()
    service.create_controller(doc, project["controller"])
    service.add_components(doc, project["components"], transaction_name="Bike Trailer Template Components")

    components_group = doc.getObject("OCW_Components")
    running_gear_group = doc.getObject("OCW_Group_running_gear")
    cargo_group = doc.getObject("OCW_Group_cargo_area")

    assert components_group is not None
    assert running_gear_group is not None
    assert cargo_group is not None
    assert doc.getObject("OCW_Component_wheel_left") is not None
    assert doc.getObject("OCW_Component_cargo_box") is not None
    assert [obj.Name for obj in components_group.Group] == ["OCW_Group_running_gear", "OCW_Group_frame_core", "OCW_Group_cargo_area"]


def test_bike_trailer_components_support_generic_move_workflow(monkeypatch) -> None:
    class FakeBuilder:
        def __init__(self, doc):
            self.doc = doc

        def build_body(self, _controller):
            return self.doc.addObject("Part::Feature", "ControllerBody")

        def build_top_plate(self, _controller):
            top = self.doc.addObject("Part::Feature", "TopPlate")
            top.Shape = type("Shape", (), {"BoundBox": type("BoundBox", (), {"ZMin": 29.0, "ZLength": 3.0})(), "copy": lambda self: self})()
            return top

        def apply_cutout_plan(self, top, _plan):
            top.Shape = "cut"
            return top

        def plan_cutout_boolean(self, _top, components):
            return type("CutPlan", (), {"tools": [object() for _ in components], "diagnostics": []})()

        def build_component_feature(self, _controller, component):
            return self.doc.addObject("Part::Feature", f"OCW_Component_{component['id']}")

        def build_keepouts(self, _components):
            return []

    monkeypatch.setattr("ocw_workbench.services.document_sync_service.ControllerBuilder", FakeBuilder)
    monkeypatch.setattr("ocw_workbench.services.controller_service.ControllerBuilder", FakeBuilder)
    monkeypatch.setattr("ocw_workbench.services.document_sync_service.freecad_gui.reveal_generated_objects", lambda _doc: 0)
    monkeypatch.setattr("ocw_workbench.services.document_sync_service.freecad_gui.activate_document", lambda _doc: True)
    monkeypatch.setattr("ocw_workbench.services.document_sync_service.freecad_gui.focus_view", lambda _doc, fit=True: True)
    activate_plugin("bike_trailer")

    service = ControllerService()
    doc = FakeFeatureDocument()
    service.create_controller(doc, {"id": "trailer-demo", "width": 220.0, "depth": 120.0, "height": 28.0})
    service.add_component(doc, "bike_trailer.wheel_20in_spoked", component_id="wheel_left", component_type="wheel", x=42.0, y=92.0)
    state = service.move_component(doc, "wheel_left", x=55.0, y=94.0, rotation=5.0)

    component = next(item for item in state["components"] if item["id"] == "wheel_left")
    assert component["type"] == "wheel"
    assert component["x"] == 55.0
    assert component["rotation"] == 5.0
