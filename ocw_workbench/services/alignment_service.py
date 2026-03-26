from __future__ import annotations

from copy import deepcopy
from typing import Any


ALIGN_OPERATIONS = {
    "align_left",
    "align_center_x",
    "align_right",
    "align_top",
    "align_center_y",
    "align_bottom",
}

DISTRIBUTE_OPERATIONS = {
    "distribute_horizontal",
    "distribute_vertical",
}

SUPPORTED_OPERATIONS = ALIGN_OPERATIONS | DISTRIBUTE_OPERATIONS


class AlignmentService:
    """Calculate multi-selection alignment and distribution updates."""

    def build_updates(
        self,
        components: list[dict[str, Any]],
        operation: str,
    ) -> dict[str, Any]:
        if operation not in SUPPORTED_OPERATIONS:
            raise ValueError(f"Unsupported alignment operation: {operation}")
        normalized = [self._normalize_component(component) for component in components]
        if operation in ALIGN_OPERATIONS:
            return self._build_alignment_updates(normalized, operation)
        return self._build_distribution_updates(normalized, operation)

    def _build_alignment_updates(
        self,
        components: list[dict[str, Any]],
        operation: str,
    ) -> dict[str, Any]:
        if len(components) < 2:
            raise ValueError("Align requires at least 2 selected components")
        axis = "x" if operation in {"align_left", "align_center_x", "align_right"} else "y"
        positions = [float(component[axis]) for component in components]
        if operation in {"align_left", "align_top"}:
            target = min(positions)
        elif operation in {"align_right", "align_bottom"}:
            target = max(positions)
        else:
            target = (min(positions) + max(positions)) / 2.0
        updates_by_component = self._updates_for_axis(components, axis=axis, targets_by_id={component["id"]: target for component in components})
        return {
            "kind": "align",
            "operation": operation,
            "axis": axis,
            "anchor_mode": "component_center",
            "reference_mode": "selection_span",
            "target": target,
            "component_ids": [component["id"] for component in components],
            "updates_by_component": updates_by_component,
            "moved_count": len(updates_by_component),
            "transaction_name": f"OCW {self._label_for_operation(operation)}",
        }

    def _build_distribution_updates(
        self,
        components: list[dict[str, Any]],
        operation: str,
    ) -> dict[str, Any]:
        if len(components) < 3:
            raise ValueError("Distribute requires at least 3 selected components")
        axis = "x" if operation == "distribute_horizontal" else "y"
        ordered = sorted(components, key=lambda component: (float(component[axis]), str(component["id"])))
        start = float(ordered[0][axis])
        end = float(ordered[-1][axis])
        step = (end - start) / float(len(ordered) - 1)
        targets_by_id = {
            component["id"]: start + (index * step)
            for index, component in enumerate(ordered)
        }
        updates_by_component = self._updates_for_axis(components, axis=axis, targets_by_id=targets_by_id)
        return {
            "kind": "distribute",
            "operation": operation,
            "axis": axis,
            "anchor_mode": "component_center",
            "reference_mode": "sorted_selection_span",
            "span": {"start": start, "end": end, "step": step},
            "component_ids": [component["id"] for component in ordered],
            "updates_by_component": updates_by_component,
            "moved_count": len(updates_by_component),
            "transaction_name": f"OCW {self._label_for_operation(operation)}",
        }

    def _normalize_component(self, component: dict[str, Any]) -> dict[str, Any]:
        component_id = component.get("id")
        if not isinstance(component_id, str) or not component_id:
            raise ValueError("Selected components must define a non-empty id")
        normalized = deepcopy(component)
        try:
            normalized["x"] = float(component["x"])
            normalized["y"] = float(component["y"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Component '{component_id}' is missing a valid x/y position") from exc
        return normalized

    def _updates_for_axis(
        self,
        components: list[dict[str, Any]],
        *,
        axis: str,
        targets_by_id: dict[str, float],
    ) -> dict[str, dict[str, float]]:
        updates_by_component: dict[str, dict[str, float]] = {}
        for component in components:
            component_id = str(component["id"])
            target = float(targets_by_id[component_id])
            if abs(float(component[axis]) - target) <= 1e-9:
                continue
            updates_by_component[component_id] = {axis: target}
        return updates_by_component

    def _label_for_operation(self, operation: str) -> str:
        labels = {
            "align_left": "Align Left",
            "align_center_x": "Align Center X",
            "align_right": "Align Right",
            "align_top": "Align Top",
            "align_center_y": "Align Center Y",
            "align_bottom": "Align Bottom",
            "distribute_horizontal": "Distribute Horizontally",
            "distribute_vertical": "Distribute Vertically",
        }
        return labels[operation]
