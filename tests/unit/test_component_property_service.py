from __future__ import annotations

from ocw_workbench.services.component_property_service import ComponentPropertyService


def _field(model: dict, field_id: str) -> dict:
    return next(field for field in model["fields"] if field["id"] == field_id)


def test_property_model_maps_button_family_to_pad_fields():
    service = ComponentPropertyService()

    model = service.build_property_model(
        {
            "id": "pad1",
            "type": "button",
            "library_ref": "omron_b3f_1000",
            "x": 10.0,
            "y": 12.0,
        }
    )

    assert model["category"] == "pad"
    assert _field(model, "library_ref")["type"] == "enum"
    assert _field(model, "pad_size")["editable"] is False


def test_property_model_exposes_type_specific_fields_for_fader_display_and_encoder():
    service = ComponentPropertyService()

    fader = service.build_property_model(
        {
            "id": "f1",
            "type": "fader",
            "library_ref": "generic_45mm_linear_fader",
            "properties": {"cap_width": 14.0},
        }
    )
    display = service.build_property_model(
        {
            "id": "d1",
            "type": "display",
            "library_ref": "adafruit_oled_096_i2c_ssd1306",
            "properties": {"orientation": "landscape", "bezel": False},
        }
    )
    encoder = service.build_property_model(
        {
            "id": "e1",
            "type": "encoder",
            "library_ref": "alps_ec11e15204a3",
        }
    )

    assert _field(fader, "cap_width")["value"] == 14.0
    assert _field(display, "orientation")["value"] == "landscape"
    assert _field(display, "bezel")["value"] is False
    assert _field(encoder, "shaft_diameter")["editable"] is False
    assert _field(encoder, "knob_diameter")["group"] == "mounting"


def test_normalize_updates_separates_generic_and_property_values():
    service = ComponentPropertyService()
    model = service.build_property_model(
        {
            "id": "d1",
            "type": "display",
            "library_ref": "adafruit_oled_096_i2c_ssd1306",
        }
    )

    updates = service.normalize_updates(
        model,
        {
            "x": 22.0,
            "label": "Main Display",
            "tags": "ui, primary",
            "visible": False,
            "orientation": "landscape",
            "bezel": False,
        },
    )

    assert updates["x"] == 22.0
    assert updates["label"] == "Main Display"
    assert updates["tags"] == ["ui", "primary"]
    assert updates["visible"] is False
    assert updates["properties"] == {
        "orientation": "landscape",
        "bezel": False,
    }


def test_reset_values_returns_current_component_defaults():
    service = ComponentPropertyService()
    model = service.build_property_model(
        {
            "id": "f1",
            "type": "fader",
            "library_ref": "generic_60mm_linear_fader",
            "label": "Deck A",
            "tags": ["mix", "lead"],
            "visible": False,
            "properties": {"cap_width": 16.0},
        }
    )

    values = service.reset_values(model)

    assert values["label"] == "Deck A"
    assert values["tags"] == "mix, lead"
    assert values["visible"] is False
    assert values["cap_width"] == 16.0
