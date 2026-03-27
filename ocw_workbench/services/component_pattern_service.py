from __future__ import annotations

from copy import deepcopy
from typing import Any


class ComponentPatternService:
    """Generate duplicate and array component payloads from a selected base group."""

    def duplicate_once(
        self,
        components: list[dict[str, Any]],
        existing_components: list[dict[str, Any]],
        *,
        offset_x: float,
        offset_y: float,
    ) -> dict[str, Any]:
        return self._build_plan(
            components,
            existing_components,
            placements=[(1, float(offset_x), float(offset_y))],
            kind="duplicate",
            transaction_name="OCW Duplicate Components",
        )

    def linear_array(
        self,
        components: list[dict[str, Any]],
        existing_components: list[dict[str, Any]],
        *,
        axis: str,
        count: int,
        spacing: float,
    ) -> dict[str, Any]:
        if count <= 0:
            raise ValueError("Array count must be positive")
        if axis not in {"x", "y"}:
            raise ValueError("Linear array axis must be 'x' or 'y'")
        placements = []
        for index in range(1, count + 1):
            delta = float(spacing) * float(index)
            placements.append((index, delta if axis == "x" else 0.0, delta if axis == "y" else 0.0))
        direction = "horizontal" if axis == "x" else "vertical"
        return self._build_plan(
            components,
            existing_components,
            placements=placements,
            kind=f"array_{direction}",
            transaction_name=f"OCW Array {direction.title()}",
        )

    def grid_array(
        self,
        components: list[dict[str, Any]],
        existing_components: list[dict[str, Any]],
        *,
        rows: int,
        cols: int,
        spacing_x: float,
        spacing_y: float,
    ) -> dict[str, Any]:
        if rows <= 0 or cols <= 0:
            raise ValueError("Grid array rows and cols must be positive")
        if rows == 1 and cols == 1:
            raise ValueError("Grid array must create at least 1 duplicate cell")
        placements = []
        copy_index = 0
        for row in range(rows):
            for col in range(cols):
                if row == 0 and col == 0:
                    continue
                copy_index += 1
                placements.append((copy_index, float(col) * float(spacing_x), float(row) * float(spacing_y)))
        return self._build_plan(
            components,
            existing_components,
            placements=placements,
            kind="grid_array",
            transaction_name="OCW Grid Array",
        )

    def _build_plan(
        self,
        components: list[dict[str, Any]],
        existing_components: list[dict[str, Any]],
        *,
        placements: list[tuple[int, float, float]],
        kind: str,
        transaction_name: str,
    ) -> dict[str, Any]:
        normalized = [self._normalize_component(component) for component in components]
        if not normalized:
            raise ValueError("Pattern creation requires at least 1 selected component")
        existing_ids = {str(component.get("id") or "") for component in existing_components}
        new_components: list[dict[str, Any]] = []
        new_ids: list[str] = []
        for copy_index, offset_x, offset_y in placements:
            for component in normalized:
                new_id = self._next_component_id(existing_ids, str(component.get("type") or "component"))
                existing_ids.add(new_id)
                duplicate = deepcopy(component)
                duplicate["id"] = new_id
                duplicate["x"] = float(component["x"]) + float(offset_x)
                duplicate["y"] = float(component["y"]) + float(offset_y)
                duplicate["rotation"] = float(component.get("rotation", 0.0) or 0.0)
                self._update_label(duplicate, copy_index)
                new_components.append(duplicate)
                new_ids.append(new_id)
        return {
            "kind": kind,
            "transaction_name": transaction_name,
            "new_components": new_components,
            "new_ids": new_ids,
            "count": len(new_components),
        }

    def _normalize_component(self, component: dict[str, Any]) -> dict[str, Any]:
        component_id = component.get("id")
        if not isinstance(component_id, str) or not component_id:
            raise ValueError("Selected components must define a non-empty id")
        normalized = deepcopy(component)
        normalized["x"] = float(component.get("x", 0.0) or 0.0)
        normalized["y"] = float(component.get("y", 0.0) or 0.0)
        normalized["rotation"] = float(component.get("rotation", 0.0) or 0.0)
        return normalized

    def _update_label(self, component: dict[str, Any], copy_index: int) -> None:
        label = component.get("label")
        if not isinstance(label, str) or not label.strip():
            return
        component["label"] = f"{label.strip()} Copy {copy_index}"

    def _next_component_id(self, existing_ids: set[str], component_type: str) -> str:
        prefix = {
            "encoder": "enc",
            "button": "btn",
            "display": "disp",
            "fader": "fader",
            "pad": "pad",
            "rgb_button": "rgb",
        }.get(component_type, "comp")
        index = 1
        while f"{prefix}{index}" in existing_ids:
            index += 1
        return f"{prefix}{index}"
