from __future__ import annotations

from copy import deepcopy
from typing import Any

from ocw_workbench.geometry.planar import normalize_rotation


SUPPORTED_TRANSFORM_OPERATIONS = {
    "rotate_cw_90",
    "rotate_ccw_90",
    "rotate_180",
    "mirror_horizontal",
    "mirror_vertical",
}


class ComponentTransformService:
    """Build component rotation updates for selection-wide transform commands."""

    def build_updates(
        self,
        components: list[dict[str, Any]],
        operation: str,
    ) -> dict[str, Any]:
        if operation not in SUPPORTED_TRANSFORM_OPERATIONS:
            raise ValueError(f"Unsupported transform operation: {operation}")
        normalized = [self._normalize_component(component) for component in components]
        if not normalized:
            raise ValueError("Transform requires at least 1 selected component")
        updates_by_component: dict[str, dict[str, float]] = {}
        for component in normalized:
            current_rotation = float(component.get("rotation", 0.0) or 0.0)
            target_rotation = self._target_rotation(current_rotation, operation)
            if abs(target_rotation - current_rotation) <= 1e-9:
                continue
            updates_by_component[str(component["id"])] = {"rotation": target_rotation}
        return {
            "operation": operation,
            "kind": "transform",
            "component_ids": [str(component["id"]) for component in normalized],
            "updates_by_component": updates_by_component,
            "moved_count": len(updates_by_component),
            "transaction_name": f"OCW {self._label_for_operation(operation)}",
            "rotation_model": "component_center",
            "mirror_model": "rotation_only",
        }

    def _normalize_component(self, component: dict[str, Any]) -> dict[str, Any]:
        component_id = component.get("id")
        if not isinstance(component_id, str) or not component_id:
            raise ValueError("Selected components must define a non-empty id")
        normalized = deepcopy(component)
        normalized["rotation"] = normalize_rotation(component.get("rotation", 0.0))
        return normalized

    def _target_rotation(self, current_rotation: float, operation: str) -> float:
        if operation == "rotate_cw_90":
            return normalize_rotation(current_rotation + 90.0)
        if operation == "rotate_ccw_90":
            return normalize_rotation(current_rotation - 90.0)
        if operation == "rotate_180":
            return normalize_rotation(current_rotation + 180.0)
        if operation == "mirror_horizontal":
            return normalize_rotation(180.0 - current_rotation)
        if operation == "mirror_vertical":
            return normalize_rotation(-current_rotation)
        raise ValueError(f"Unsupported transform operation: {operation}")

    def _label_for_operation(self, operation: str) -> str:
        labels = {
            "rotate_cw_90": "Rotate +90",
            "rotate_ccw_90": "Rotate -90",
            "rotate_180": "Rotate 180",
            "mirror_horizontal": "Mirror Horizontally",
            "mirror_vertical": "Mirror Vertically",
        }
        return labels[operation]
