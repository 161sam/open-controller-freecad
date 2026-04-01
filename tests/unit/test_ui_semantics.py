from __future__ import annotations

from ocw_workbench.gui.ui_semantics import (
    placement_status_text,
    workflow_step_text,
)


def test_placement_status_text_uses_shared_short_states() -> None:
    assert placement_status_text(None) == "Ready"
    assert placement_status_text({"mode": "suggested_addition"}) == "Move over target area"
    assert placement_status_text(
        {"mode": "suggested_addition", "placement_feedback": {"hover_zone_id": "zone1", "invalid_target": True}}
    ) == "Invalid target"
    assert placement_status_text(
        {"mode": "suggested_addition", "placement_feedback": {"active_zone_id": "zone1"}}
    ) == "Click to place"


def test_workflow_step_text_uses_badge_style_markers() -> None:
    assert workflow_step_text({"label": "Utility Strip", "status": "current"}) == "Active · Utility Strip"
    assert workflow_step_text({"label": "Display Header", "status": "completed"}) == "Done · Display Header"
    assert workflow_step_text({"label": "Navigation Pair", "status": "open"}) == "Next · Navigation Pair"
