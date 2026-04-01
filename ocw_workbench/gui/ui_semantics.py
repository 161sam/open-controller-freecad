from __future__ import annotations

from typing import Any

BADGE_TEMPLATE = "Template"
BADGE_SELECTED = "Selected"
BADGE_TARGETING = "Targeting"
BADGE_NEXT = "Next"
BADGE_ACTIVE = "Active"
BADGE_DONE = "Done"

STATUS_READY = "Ready"
STATUS_MOVE_TARGET = "Move over target area"
STATUS_CLICK_TO_PLACE = "Click to place"
STATUS_INVALID_TARGET = "Invalid target"
STATUS_PLACEMENT_CANCELLED = "Placement cancelled"
STATUS_PLACEMENT_COMPLETE = "Placement complete"
STATUS_INTERACTION_ERROR = "Interaction error"


def context_badge(*, placement_active: bool, selection_count: int) -> str:
    if placement_active:
        return BADGE_TARGETING
    if selection_count > 0:
        return BADGE_SELECTED
    return BADGE_TEMPLATE


def workflow_badge(*, placement_active: bool, has_primary_action: bool, completed_steps: int, total_steps: int) -> str:
    if placement_active:
        return BADGE_ACTIVE
    if has_primary_action:
        return BADGE_NEXT
    if total_steps > 0 and completed_steps >= total_steps:
        return BADGE_DONE
    return BADGE_NEXT


def placement_status_text(preview: Any) -> str:
    if not isinstance(preview, dict) or str(preview.get("mode") or "") != "suggested_addition":
        return STATUS_READY
    placement_feedback = preview.get("placement_feedback") if isinstance(preview.get("placement_feedback"), dict) else {}
    if placement_feedback.get("active_zone_id"):
        return STATUS_CLICK_TO_PLACE
    if placement_feedback.get("invalid_target") and placement_feedback.get("hover_zone_id"):
        return STATUS_INVALID_TARGET
    return STATUS_MOVE_TARGET


def workflow_step_text(step: dict[str, Any]) -> str:
    status = str(step.get("status") or "open")
    label = str(step.get("short_label") or step.get("label") or "Step")
    marker = {
        "completed": BADGE_DONE,
        "current": BADGE_ACTIVE,
    }.get(status, BADGE_NEXT)
    return f"{marker} · {label}"
