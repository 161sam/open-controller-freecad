from ocw_workbench.services.alignment_service import AlignmentService


def test_align_left_uses_selection_center_span_minimum():
    service = AlignmentService()

    result = service.build_updates(
        [
            {"id": "a", "x": 40.0, "y": 20.0},
            {"id": "b", "x": 10.0, "y": 30.0},
            {"id": "c", "x": 25.0, "y": 50.0},
        ],
        "align_left",
    )

    assert result["anchor_mode"] == "component_center"
    assert result["reference_mode"] == "selection_span"
    assert result["target"] == 10.0
    assert result["updates_by_component"] == {
        "a": {"x": 10.0},
        "c": {"x": 10.0},
    }


def test_align_center_y_uses_selection_midpoint():
    service = AlignmentService()

    result = service.build_updates(
        [
            {"id": "a", "x": 10.0, "y": 20.0},
            {"id": "b", "x": 30.0, "y": 40.0},
            {"id": "c", "x": 50.0, "y": 80.0},
        ],
        "align_center_y",
    )

    assert result["target"] == 50.0
    assert result["updates_by_component"] == {
        "a": {"y": 50.0},
        "b": {"y": 50.0},
        "c": {"y": 50.0},
    }


def test_distribute_horizontal_sorts_by_x_and_keeps_outer_components_fixed():
    service = AlignmentService()

    result = service.build_updates(
        [
            {"id": "left", "x": 0.0, "y": 10.0},
            {"id": "mid_b", "x": 70.0, "y": 10.0},
            {"id": "right", "x": 90.0, "y": 10.0},
            {"id": "mid_a", "x": 10.0, "y": 10.0},
        ],
        "distribute_horizontal",
    )

    assert result["reference_mode"] == "sorted_selection_span"
    assert result["span"] == {"start": 0.0, "end": 90.0, "step": 30.0}
    assert result["component_ids"] == ["left", "mid_a", "mid_b", "right"]
    assert result["updates_by_component"] == {
        "mid_a": {"x": 30.0},
        "mid_b": {"x": 60.0},
    }


def test_distribute_vertical_with_identical_positions_is_a_safe_noop():
    service = AlignmentService()

    result = service.build_updates(
        [
            {"id": "a", "x": 10.0, "y": 25.0},
            {"id": "b", "x": 20.0, "y": 25.0},
            {"id": "c", "x": 30.0, "y": 25.0},
        ],
        "distribute_vertical",
    )

    assert result["span"] == {"start": 25.0, "end": 25.0, "step": 0.0}
    assert result["updates_by_component"] == {}


def test_align_requires_at_least_two_components():
    service = AlignmentService()

    try:
        service.build_updates([{"id": "solo", "x": 10.0, "y": 20.0}], "align_right")
    except ValueError as exc:
        assert str(exc) == "Align requires at least 2 selected components"
    else:
        raise AssertionError("Expected align validation error")


def test_distribute_requires_at_least_three_components():
    service = AlignmentService()

    try:
        service.build_updates(
            [
                {"id": "a", "x": 10.0, "y": 20.0},
                {"id": "b", "x": 20.0, "y": 20.0},
            ],
            "distribute_horizontal",
        )
    except ValueError as exc:
        assert str(exc) == "Distribute requires at least 3 selected components"
    else:
        raise AssertionError("Expected distribute validation error")
