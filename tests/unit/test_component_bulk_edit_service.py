from __future__ import annotations

from ocw_workbench.services.component_bulk_edit_service import ComponentBulkEditService


def _field(model: dict, field_id: str) -> dict:
    return next(field for field in model["fields"] if field["id"] == field_id)


def test_bulk_model_detects_common_generic_and_fader_fields():
    service = ComponentBulkEditService()

    model = service.build_bulk_model(
        [
            {
                "id": "f1",
                "type": "fader",
                "library_ref": "generic_45mm_linear_fader",
                "rotation": 15.0,
                "visible": True,
                "properties": {"cap_width": 12.0},
            },
            {
                "id": "f2",
                "type": "fader",
                "library_ref": "generic_60mm_linear_fader",
                "rotation": 15.0,
                "visible": True,
                "properties": {"cap_width": 12.0},
            },
        ]
    )

    assert model["count"] == 2
    assert model["categories"] == ["fader"]
    assert _field(model, "rotation")["mixed"] is False
    assert _field(model, "library_ref")["editable"] is True
    assert _field(model, "cap_width")["editable"] is True


def test_bulk_model_marks_mixed_values_for_different_component_values():
    service = ComponentBulkEditService()

    model = service.build_bulk_model(
        [
            {
                "id": "d1",
                "type": "display",
                "library_ref": "adafruit_oled_096_i2c_ssd1306",
                "rotation": 0.0,
                "visible": True,
                "properties": {"orientation": "portrait", "bezel": True},
            },
            {
                "id": "d2",
                "type": "display",
                "library_ref": "adafruit_oled_096_i2c_ssd1306",
                "rotation": 90.0,
                "visible": False,
                "properties": {"orientation": "landscape", "bezel": False},
            },
        ]
    )

    assert _field(model, "rotation")["mixed"] is True
    assert _field(model, "visible")["mixed"] is True
    assert _field(model, "orientation")["mixed"] is True
    assert _field(model, "bezel")["mixed"] is True


def test_bulk_model_stays_conservative_for_mixed_families():
    service = ComponentBulkEditService()

    model = service.build_bulk_model(
        [
            {"id": "f1", "type": "fader", "library_ref": "generic_45mm_linear_fader"},
            {"id": "d1", "type": "display", "library_ref": "adafruit_oled_096_i2c_ssd1306"},
        ]
    )

    field_ids = {field["id"] for field in model["fields"]}

    assert "rotation" in field_ids
    assert "visible" in field_ids
    assert "label_prefix" in field_ids
    assert "library_ref" not in field_ids
    assert "orientation" not in field_ids
    assert "cap_width" not in field_ids


def test_bulk_build_updates_maps_shared_values_and_label_prefix():
    service = ComponentBulkEditService()
    model = service.build_bulk_model(
        [
            {"id": "f1", "type": "fader", "library_ref": "generic_45mm_linear_fader", "properties": {"cap_width": 10.0}},
            {"id": "f2", "type": "fader", "library_ref": "generic_60mm_linear_fader", "properties": {"cap_width": 11.0}},
        ]
    )

    updates = service.build_updates(
        model,
        {
            "rotation": 30.0,
            "label_prefix": "Deck",
            "cap_width": 14.0,
            "library_ref": "generic_60mm_linear_fader",
        },
        {"rotation", "label_prefix", "cap_width", "library_ref"},
    )

    assert updates["f1"]["rotation"] == 30.0
    assert updates["f1"]["label"] == "Deck1"
    assert updates["f1"]["library_ref"] == "generic_60mm_linear_fader"
    assert updates["f2"]["properties"]["cap_width"] == 14.0
