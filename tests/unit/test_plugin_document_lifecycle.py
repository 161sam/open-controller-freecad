from __future__ import annotations

import pytest

from ocw_workbench.freecad_api.state import read_state, write_state
from ocw_workbench.plugins.activation import activate_plugin
from ocw_workbench.plugins.document_lifecycle import (
    activate_plugin_for_document,
    can_switch_plugin_for_document,
    get_document_plugin_binding,
    get_document_plugin_status,
    select_domain_plugin_for_document,
)
from ocw_workbench.services.controller_state_service import ControllerStateService
from ocw_workbench.services.controller_service import ControllerService
from ocw_workbench.services.plugin_service import get_plugin_service


class FakeViewObject:
    def __init__(self) -> None:
        self.Visibility = True
        self.Object = None
        self.Proxy = None


class FakeDocumentObject:
    def __init__(self, document, type_name: str, name: str) -> None:
        self.Document = document
        self.TypeId = type_name
        self.Name = name
        self.Label = name
        self.PropertiesList: list[str] = []
        self.ViewObject = FakeViewObject()
        self.ViewObject.Object = self
        self.Group: list[FakeDocumentObject] = []
        self.Proxy = None

    def addProperty(self, _type_name: str, name: str, _group: str, _doc: str) -> None:
        if name not in self.PropertiesList:
            self.PropertiesList.append(name)
            setattr(self, name, "")

    def setEditorMode(self, _name: str, _mode: int) -> None:
        return

    def addObject(self, obj) -> None:
        if obj not in self.Group:
            self.Group.append(obj)


class FakeDocument:
    def __init__(self, name: str = "Doc") -> None:
        self.Name = name
        self.Objects: list[FakeDocumentObject] = []
        self.removed: list[str] = []
        self.recompute_count = 0
        self.transactions: list[tuple[str, str | None]] = []

    def addObject(self, type_name: str, name: str) -> FakeDocumentObject:
        obj = FakeDocumentObject(self, type_name, name)
        self.Objects.append(obj)
        return obj

    def getObject(self, name: str):
        for obj in self.Objects:
            if obj.Name == name:
                return obj
        return None

    def removeObject(self, name: str) -> None:
        self.removed.append(name)
        self.Objects = [obj for obj in self.Objects if obj.Name != name]

    def recompute(self) -> None:
        self.recompute_count += 1

    def openTransaction(self, label: str) -> None:
        self.transactions.append(("open", label))

    def commitTransaction(self) -> None:
        self.transactions.append(("commit", None))

    def abortTransaction(self) -> None:
        self.transactions.append(("abort", None))


class FakeLayoutEngine:
    def place(self, _controller, components, strategy: str = "grid", config=None):
        placements = []
        for index, component in enumerate(components):
            placements.append(
                {
                    "component_id": component.id,
                    "x": float(index * 20.0),
                    "y": float(index * 10.0),
                    "rotation": float(getattr(component, "rotation", 0.0) or 0.0),
                    "zone_id": getattr(component, "zone_id", None),
                }
            )
        return {
            "placements": placements,
            "placed_components": [component.id for component in components],
            "unplaced_component_ids": [],
            "warnings": [],
        }


class FakeSyncService:
    def update_document(self, doc, state=None, mode=None, selection=None, recompute=True):
        doc.OCWLastSync = {
            "sync_mode": mode,
            "component_count": len((state or {}).get("components", [])),
            "selection": selection,
            "recompute": recompute,
        }
        return None


def _service() -> ControllerService:
    state_service = ControllerStateService(layout_engine=FakeLayoutEngine())
    return ControllerService(state_service=state_service, sync_service=FakeSyncService())


def test_new_document_is_bound_to_active_plugin_on_create_controller() -> None:
    activate_plugin("bike_trailer")
    doc = FakeDocument("BikeDoc")

    state = _service().create_controller(doc, {"id": "bike_doc"})
    binding = get_document_plugin_binding(doc)

    assert binding is not None
    assert binding["plugin_id"] == "bike_trailer"
    assert state["meta"]["plugin_id"] == "bike_trailer"
    assert state["meta"]["document_type"] == "generator_workbench_project"


def test_domain_selection_sets_active_plugin_for_new_document() -> None:
    doc = FakeDocument("ChooserDoc")

    status = select_domain_plugin_for_document(doc, "bike_trailer")

    assert status["active_plugin_id"] == "bike_trailer"
    assert status["bound_plugin_id"] == "bike_trailer"
    assert status["switchable"] is True
    assert "still switchable" in status["message"]


def test_existing_document_reactivates_bound_plugin() -> None:
    service = _service()
    doc = FakeDocument("TrailerDoc")

    activate_plugin("midicontroller")
    service.create_from_template(doc, "trailer_basic")
    activate_plugin("midicontroller")

    binding = activate_plugin_for_document(doc)
    active_plugin = get_plugin_service().registry().get_active_plugin()

    assert binding["plugin_id"] == "bike_trailer"
    assert active_plugin is not None
    assert active_plugin.plugin_id == "bike_trailer"


def test_bound_document_rejects_conflicting_plugin_activation() -> None:
    service = _service()
    doc = FakeDocument("MidiDoc")

    service.create_from_template(doc, "pad_grid_4x4")

    with pytest.raises(ValueError, match="bound to plugin 'midicontroller'"):
        activate_plugin_for_document(doc, requested_plugin_id="bike_trailer")

    with pytest.raises(ValueError, match="already bound to domain 'midicontroller'"):
        select_domain_plugin_for_document(doc, "bike_trailer")

    assert can_switch_plugin_for_document(doc, "bike_trailer") is False


def test_document_plugin_status_reports_bound_and_switchable_states() -> None:
    service = _service()
    empty_doc = FakeDocument("EmptyDoc")
    project_doc = FakeDocument("ProjectDoc")

    switchable_status = select_domain_plugin_for_document(empty_doc, "midicontroller")
    service.create_from_template(project_doc, "trailer_basic")
    bound_status = get_document_plugin_status(project_doc)

    assert switchable_status["mode"] == "switchable"
    assert switchable_status["switchable"] is True
    assert "still switchable" in switchable_status["message"]
    assert bound_status["mode"] == "bound"
    assert bound_status["switchable"] is False
    assert "switch is blocked" in bound_status["message"]


def test_missing_plugin_metadata_is_inferred_from_persisted_template() -> None:
    service = _service()
    doc = FakeDocument("LegacyTrailerDoc")

    service.create_from_template(doc, "trailer_box")
    state = read_state(doc)
    assert state is not None
    state["meta"].pop("plugin_id", None)
    state["meta"].pop("plugin_version", None)
    state["meta"].pop("document_type", None)
    write_state(doc, state)

    activate_plugin("midicontroller")
    binding = activate_plugin_for_document(doc)

    assert binding["plugin_id"] == "bike_trailer"
    assert get_plugin_service().registry().get_active_plugin().plugin_id == "bike_trailer"


def test_multi_plugin_documents_stay_separated_by_binding() -> None:
    service = _service()
    midi_doc = FakeDocument("MidiProject")
    trailer_doc = FakeDocument("TrailerProject")

    service.create_from_template(midi_doc, "pad_grid_4x4")
    service.create_from_template(trailer_doc, "trailer_basic")

    midi_binding = activate_plugin_for_document(midi_doc)
    assert midi_binding["plugin_id"] == "midicontroller"
    assert get_plugin_service().registry().get_active_plugin().plugin_id == "midicontroller"

    trailer_binding = activate_plugin_for_document(trailer_doc)
    assert trailer_binding["plugin_id"] == "bike_trailer"
    assert get_plugin_service().registry().get_active_plugin().plugin_id == "bike_trailer"
