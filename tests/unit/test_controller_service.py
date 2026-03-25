from ocf_freecad.services.controller_service import ControllerService


class FakeDocument:
    def __init__(self) -> None:
        self.Objects = []
        self.removed = []
        self.recompute_count = 0

    def recompute(self) -> None:
        self.recompute_count += 1


def test_create_controller_and_add_components_without_freecad_objects():
    service = ControllerService()
    doc = FakeDocument()

    service.create_controller(doc, {"id": "demo", "width": 180.0, "depth": 100.0})
    service.add_component(doc, "alps_ec11e15204a3", x=20.0, y=20.0)
    service.add_component(doc, "omron_b3f_1000", x=40.0, y=20.0)

    state = service.get_state(doc)

    assert state["controller"]["id"] == "demo"
    assert len(state["components"]) == 2
    assert doc.OCFLastSync["component_count"] == 2


def test_auto_layout_and_validate_work_on_document_state():
    service = ControllerService()
    doc = FakeDocument()

    service.create_controller(doc, {"id": "demo", "width": 200.0, "depth": 120.0})
    service.add_component(doc, "alps_ec11e15204a3")
    service.add_component(doc, "alps_ec11e15204a3")
    service.add_component(doc, "omron_b3f_1000")
    service.add_component(doc, "omron_b3f_1000")
    service.add_component(doc, "omron_b3f_1000")
    service.add_component(doc, "omron_b3f_1000")
    service.add_component(doc, "adafruit_oled_096_i2c_ssd1306")

    layout = service.auto_layout(doc, strategy="grid", config={"spacing_x_mm": 30.0, "spacing_y_mm": 24.0, "padding_mm": 16.0})
    report = service.validate_layout(doc)

    assert len(layout["placements"]) >= 6
    assert report["summary"]["error_count"] == 0
    assert doc.recompute_count > 0


def test_move_component_updates_state():
    service = ControllerService()
    doc = FakeDocument()

    service.create_controller(doc, {"id": "demo"})
    service.add_component(doc, "alps_ec11e15204a3", component_id="enc1", x=10.0, y=10.0)
    service.move_component(doc, "enc1", x=55.0, y=35.0, rotation=15.0)

    state = service.get_state(doc)

    assert state["components"][0]["x"] == 55.0
    assert state["components"][0]["y"] == 35.0
    assert state["components"][0]["rotation"] == 15.0
