from ocw_workbench.gui.interaction.view_event_helpers import (
    extract_position,
    is_escape_event,
    is_left_click_down,
    is_left_click_up,
    is_mouse_move,
)


def test_extract_position_canonical():
    assert extract_position({"Position": [12.0, 34.0]}) == (12.0, 34.0)


def test_extract_position_lowercase():
    assert extract_position({"position": (5.5, 9.0)}) == (5.5, 9.0)


def test_extract_position_missing():
    assert extract_position({}) is None


def test_is_mouse_move_location_event():
    assert is_mouse_move("SoLocation2Event", {}) is True


def test_is_mouse_move_not_for_button_down():
    assert is_mouse_move("SoLocation2Event", {"State": "DOWN"}) is False


def test_is_mouse_move_not_for_button_events():
    assert is_mouse_move("SoMouseButtonEvent", {}) is False


def test_is_left_click_down_button1():
    assert is_left_click_down("SoMouseButtonEvent", {"Button": "BUTTON1", "State": "DOWN"}) is True


def test_is_left_click_down_rejects_up():
    assert is_left_click_down("SoMouseButtonEvent", {"Button": "BUTTON1", "State": "UP"}) is False


def test_is_left_click_down_rejects_button2():
    assert is_left_click_down("SoMouseButtonEvent", {"Button": "BUTTON2", "State": "DOWN"}) is False


def test_is_left_click_up_button1():
    assert is_left_click_up("SoMouseButtonEvent", {"Button": "BUTTON1", "State": "UP"}) is True


def test_is_left_click_up_rejects_down():
    assert is_left_click_up("SoMouseButtonEvent", {"Button": "BUTTON1", "State": "DOWN"}) is False


def test_is_escape_event_keyboard():
    assert is_escape_event("SoKeyboardEvent", {"Key": "ESCAPE", "State": "DOWN"}) is True


def test_is_escape_event_esc_key():
    assert is_escape_event("SoKeyboardEvent", {"Key": "ESC", "State": "DOWN"}) is True


def test_is_escape_event_other_key():
    assert is_escape_event("SoKeyboardEvent", {"Key": "RETURN", "State": "DOWN"}) is False


def test_is_escape_event_wrong_event_type():
    assert is_escape_event("SoMouseButtonEvent", {"Key": "ESCAPE", "State": "DOWN"}) is False
