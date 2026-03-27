from ocw_workbench.services.component_transform_service import ComponentTransformService


def test_rotate_cw_90_updates_each_selected_component_around_own_center():
    service = ComponentTransformService()

    result = service.build_updates(
        [
            {"id": "a", "x": 10.0, "y": 20.0, "rotation": 0.0},
            {"id": "b", "x": 40.0, "y": 25.0, "rotation": 90.0},
        ],
        "rotate_cw_90",
    )

    assert result["rotation_model"] == "component_center"
    assert result["updates_by_component"] == {
        "a": {"rotation": 90.0},
        "b": {"rotation": 180.0},
    }


def test_rotate_ccw_90_normalizes_into_zero_to_360_range():
    service = ComponentTransformService()

    result = service.build_updates(
        [{"id": "a", "x": 10.0, "y": 20.0, "rotation": 0.0}],
        "rotate_ccw_90",
    )

    assert result["updates_by_component"] == {"a": {"rotation": 270.0}}


def test_rotate_180_updates_multiple_components():
    service = ComponentTransformService()

    result = service.build_updates(
        [
            {"id": "a", "x": 10.0, "y": 20.0, "rotation": 0.0},
            {"id": "b", "x": 30.0, "y": 40.0, "rotation": 270.0},
        ],
        "rotate_180",
    )

    assert result["updates_by_component"] == {
        "a": {"rotation": 180.0},
        "b": {"rotation": 90.0},
    }


def test_mirror_horizontal_uses_rotation_only_semantics():
    service = ComponentTransformService()

    result = service.build_updates(
        [{"id": "disp1", "x": 20.0, "y": 20.0, "rotation": 0.0}],
        "mirror_horizontal",
    )

    assert result["mirror_model"] == "rotation_only"
    assert result["updates_by_component"] == {"disp1": {"rotation": 180.0}}


def test_mirror_vertical_flips_rotation_sign():
    service = ComponentTransformService()

    result = service.build_updates(
        [{"id": "f1", "x": 20.0, "y": 20.0, "rotation": 90.0}],
        "mirror_vertical",
    )

    assert result["updates_by_component"] == {"f1": {"rotation": 270.0}}


def test_transform_requires_non_empty_selection():
    service = ComponentTransformService()

    try:
        service.build_updates([], "rotate_180")
    except ValueError as exc:
        assert str(exc) == "Transform requires at least 1 selected component"
    else:
        raise AssertionError("Expected transform validation error")
