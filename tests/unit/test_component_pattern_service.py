from ocw_workbench.services.component_pattern_service import ComponentPatternService


def test_duplicate_once_keeps_relative_group_layout_and_generates_unique_ids():
    service = ComponentPatternService()

    plan = service.duplicate_once(
        [
            {"id": "btn1", "type": "button", "library_ref": "omron_b3f_1000", "x": 10.0, "y": 10.0, "rotation": 0.0},
            {"id": "btn2", "type": "button", "library_ref": "omron_b3f_1000", "x": 25.0, "y": 10.0, "rotation": 0.0},
        ],
        [
            {"id": "btn1", "type": "button"},
            {"id": "btn2", "type": "button"},
        ],
        offset_x=30.0,
        offset_y=5.0,
    )

    assert plan["kind"] == "duplicate"
    assert plan["new_ids"] == ["btn3", "btn4"]
    assert [(item["x"], item["y"]) for item in plan["new_components"]] == [(40.0, 15.0), (55.0, 15.0)]


def test_linear_array_horizontal_creates_requested_number_of_copy_groups():
    service = ComponentPatternService()

    plan = service.linear_array(
        [{"id": "f1", "type": "fader", "library_ref": "generic_45mm_linear_fader", "x": 10.0, "y": 20.0, "rotation": 0.0}],
        [{"id": "f1", "type": "fader"}],
        axis="x",
        count=3,
        spacing=25.0,
    )

    assert [item["id"] for item in plan["new_components"]] == ["fader1", "fader2", "fader3"]
    assert [item["x"] for item in plan["new_components"]] == [35.0, 60.0, 85.0]
    assert [item["y"] for item in plan["new_components"]] == [20.0, 20.0, 20.0]


def test_grid_array_creates_matrix_cells_except_the_original_base_cell():
    service = ComponentPatternService()

    plan = service.grid_array(
        [{"id": "pad1", "type": "pad", "library_ref": "generic_mpc_pad_30mm", "x": 10.0, "y": 10.0, "rotation": 0.0}],
        [{"id": "pad1", "type": "pad"}],
        rows=2,
        cols=3,
        spacing_x=20.0,
        spacing_y=30.0,
    )

    assert len(plan["new_components"]) == 5
    assert [(item["x"], item["y"]) for item in plan["new_components"]] == [
        (30.0, 10.0),
        (50.0, 10.0),
        (10.0, 40.0),
        (30.0, 40.0),
        (50.0, 40.0),
    ]


def test_duplicate_copies_explicit_labels_with_copy_suffix():
    service = ComponentPatternService()

    plan = service.duplicate_once(
        [{"id": "disp1", "type": "display", "library_ref": "adafruit_oled_096_i2c_ssd1306", "x": 10.0, "y": 10.0, "rotation": 0.0, "label": "Status"}],
        [{"id": "disp1", "type": "display"}],
        offset_x=10.0,
        offset_y=0.0,
    )

    assert plan["new_components"][0]["label"] == "Status Copy 1"


def test_grid_array_rejects_single_cell_request():
    service = ComponentPatternService()

    try:
        service.grid_array(
            [{"id": "pad1", "type": "pad", "library_ref": "generic_mpc_pad_30mm", "x": 10.0, "y": 10.0, "rotation": 0.0}],
            [{"id": "pad1", "type": "pad"}],
            rows=1,
            cols=1,
            spacing_x=20.0,
            spacing_y=20.0,
        )
    except ValueError as exc:
        assert str(exc) == "Grid array must create at least 1 duplicate cell"
    else:
        raise AssertionError("Expected grid array validation error")
