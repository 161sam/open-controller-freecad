from ocf_freecad.schema.loader import load_schema

def test_load_schema():
    data = load_schema("tests/fixtures/simple_controller.hw.yaml")
    assert "controller" in data