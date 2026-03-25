from ocf_freecad.library.manager import ComponentLibraryManager
from ocf_freecad.utils.yaml_io import load_yaml


def test_load_all_components():
    manager = ComponentLibraryManager()
    manager.load_all()

    components = manager.list_components()
    ids = {component["id"] for component in components}
    fixture = load_yaml("tests/fixtures/library_lookup_expected.yaml")

    assert ids == set(fixture["expected_components"])


def test_get_component():
    manager = ComponentLibraryManager()
    component = manager.get_component("alps_ec11e15204a3")

    assert component["manufacturer"] == "Alps Alpine"
    assert component["category"] == "encoder"
    assert component["mechanical"]["panel"]["recommended_hole_diameter_mm"] == 7.0


def test_list_components_by_category():
    manager = ComponentLibraryManager()
    displays = manager.list_components(category="display")

    assert len(displays) == 1
    assert displays[0]["id"] == "adafruit_oled_096_i2c_ssd1306"


def test_resolve_component_with_overrides():
    manager = ComponentLibraryManager()
    resolved = manager.resolve_component(
        "alps_ec11e15204a3",
        overrides={
            "ocf": {
                "default_logical_role": "master_encoder",
            },
            "mechanical": {
                "panel": {
                    "recommended_hole_diameter_with_tolerance_mm": 7.4,
                },
            },
        },
    )

    assert resolved["ocf"]["default_logical_role"] == "master_encoder"
    assert resolved["mechanical"]["panel"]["recommended_hole_diameter_mm"] == 7.0
    assert resolved["mechanical"]["panel"]["recommended_hole_diameter_with_tolerance_mm"] == 7.4


def test_unknown_component_raises_key_error():
    manager = ComponentLibraryManager()

    try:
        manager.get_component("does_not_exist")
        assert False, "Expected KeyError"
    except KeyError as exc:
        assert "Unknown component id" in str(exc)
