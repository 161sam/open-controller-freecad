from __future__ import annotations

from copy import deepcopy
from typing import Any

from ocw_workbench.services.library_service import LibraryService


class ComponentPropertyService:
    def __init__(self, library_service: LibraryService | None = None) -> None:
        self.library_service = library_service or LibraryService()

    def build_property_model(self, component: dict[str, Any]) -> dict[str, Any]:
        library_ref = str(component.get("library_ref") or "")
        library_component = self.library_service.get(library_ref)
        actual_category = str(component.get("type") or library_component.get("category") or "component")
        category = "pad" if actual_category == "button" else actual_category
        ui = library_component.get("ui", {}) if isinstance(library_component.get("ui"), dict) else {}
        mechanical = library_component.get("mechanical", {}) if isinstance(library_component.get("mechanical"), dict) else {}
        panel = mechanical.get("panel", {}) if isinstance(mechanical.get("panel"), dict) else {}
        properties = component.get("properties", {}) if isinstance(component.get("properties"), dict) else {}

        generic_fields = [
            self._field("x", "X", "float", float(component.get("x", 0.0) or 0.0), unit="mm", group="placement"),
            self._field("y", "Y", "float", float(component.get("y", 0.0) or 0.0), unit="mm", group="placement"),
            self._field("rotation", "Rotation", "float", float(component.get("rotation", 0.0) or 0.0), unit="deg", group="placement"),
            self._field("label", "Label", "string", str(component.get("label") or component.get("id") or ""), group="generic"),
            self._field("tags", "Tags", "string", ", ".join(component.get("tags", [])) if isinstance(component.get("tags"), list) else "", group="generic"),
            self._field("visible", "Visible", "bool", bool(component.get("visible", True)), group="generic"),
        ]
        fields = generic_fields + self._category_fields(actual_category, category, library_component, properties)
        details = self._build_details(category, library_component)
        return {
            "component_id": str(component.get("id") or ""),
            "category": category,
            "library_ref": library_ref,
            "library_label": str(ui.get("label") or library_ref),
            "groups": ["placement", "generic", "dimensions", "mounting", "display", "advanced"],
            "fields": fields,
            "details": details,
            "library_component": deepcopy(library_component),
            "panel": deepcopy(panel),
        }

    def classify_updates(self, updates: dict[str, Any]) -> str:
        geometry_fields = {"x", "y", "rotation", "library_ref", "zone_id", "type"}
        if any(field in geometry_fields for field in updates):
            return "geometry"
        return "metadata"

    def normalize_updates(self, model: dict[str, Any], values: dict[str, Any]) -> dict[str, Any]:
        updates: dict[str, Any] = {}
        properties: dict[str, Any] = {}
        for field in model["fields"]:
            field_id = field["id"]
            if field_id not in values:
                continue
            raw = values[field_id]
            if field_id in {"x", "y", "rotation", "label", "visible", "library_ref"}:
                updates[field_id] = raw
                continue
            if field_id == "tags":
                updates["tags"] = [item.strip() for item in str(raw).split(",") if item.strip()]
                continue
            properties[field_id] = raw
        if properties:
            updates["properties"] = properties
        return updates

    def reset_values(self, model: dict[str, Any]) -> dict[str, Any]:
        return {field["id"]: deepcopy(field["value"]) for field in model["fields"]}

    def _category_fields(
        self,
        actual_category: str,
        category: str,
        library_component: dict[str, Any],
        properties: dict[str, Any],
    ) -> list[dict[str, Any]]:
        fields: list[dict[str, Any]] = []
        if category == "pad":
            fields.extend(
                [
                    self._variant_field(actual_category, library_component),
                    self._field("pad_size", "Pad Size", "float", self._read_mm(library_component, ("mechanical", "panel", "recommended_window_mm", "width")), unit="mm", editable=False, group="dimensions"),
                ]
            )
        elif category == "fader":
            fields.extend(
                [
                    self._variant_field(actual_category, library_component),
                    self._field("fader_length", "Fader Length", "float", self._read_mm(library_component, ("mechanical", "travel_mm")), unit="mm", editable=False, group="dimensions"),
                    self._field("travel", "Travel", "float", self._read_mm(library_component, ("mechanical", "travel_mm")), unit="mm", editable=False, group="dimensions"),
                    self._field("cap_width", "Cap Width", "float", float(properties.get("cap_width", 10.0) or 10.0), unit="mm", group="dimensions"),
                ]
            )
        elif category == "display":
            fields.extend(
                [
                    self._variant_field(actual_category, library_component),
                    self._field("display_size", "Display Size", "string", str(library_component.get("part_number") or ""), editable=False, group="display"),
                    self._field("orientation", "Orientation", "enum", str(properties.get("orientation", "portrait") or "portrait"), options=[{"value": "portrait", "label": "Portrait"}, {"value": "landscape", "label": "Landscape"}], group="display"),
                    self._field("bezel", "Bezel", "bool", bool(properties.get("bezel", True)), group="display"),
                ]
            )
        elif category == "encoder":
            fields.extend(
                [
                    self._variant_field(actual_category, library_component),
                    self._field("shaft_diameter", "Shaft Diameter", "float", self._read_mm(library_component, ("mechanical", "shaft", "diameter_mm")), unit="mm", editable=False, group="mounting"),
                    self._field("knob_diameter", "Knob Diameter", "float", self._read_mm(library_component, ("mechanical", "panel", "recommended_keepout_top_diameter_mm")), unit="mm", editable=False, group="mounting"),
                    self._field("mounting_hole", "Mounting Hole", "float", self._read_mm(library_component, ("mechanical", "panel", "recommended_hole_diameter_mm")), unit="mm", editable=False, group="mounting"),
                ]
            )
        else:
            fields.append(self._variant_field(actual_category, library_component))
        return fields

    def _variant_field(self, category: str, library_component: dict[str, Any]) -> dict[str, Any]:
        options = []
        for item in self.library_service.list_by_category(category):
            ui = item.get("ui", {}) if isinstance(item.get("ui"), dict) else {}
            options.append({"value": item["id"], "label": str(ui.get("label") or item["id"])})
        return self._field("library_ref", "Variant", "enum", str(library_component.get("id") or ""), options=options, group="dimensions")

    def _field(
        self,
        field_id: str,
        label: str,
        field_type: str,
        value: Any,
        *,
        unit: str | None = None,
        options: list[dict[str, Any]] | None = None,
        editable: bool = True,
        group: str = "advanced",
    ) -> dict[str, Any]:
        return {
            "id": field_id,
            "label": label,
            "type": field_type,
            "value": value,
            "unit": unit,
            "options": options or [],
            "editable": editable,
            "group": group,
        }

    def _read_mm(self, payload: dict[str, Any], path: tuple[str, ...]) -> float:
        cursor: Any = payload
        for key in path:
            if not isinstance(cursor, dict):
                return 0.0
            cursor = cursor.get(key)
        return float(cursor or 0.0)

    def _build_details(self, category: str, library_component: dict[str, Any]) -> str:
        ui = library_component.get("ui", {}) if isinstance(library_component.get("ui"), dict) else {}
        mechanical = library_component.get("mechanical", {}) if isinstance(library_component.get("mechanical"), dict) else {}
        panel = mechanical.get("panel", {}) if isinstance(mechanical.get("panel"), dict) else {}
        lines = [
            f"Family: {category}",
            f"Library: {library_component.get('id', '-')}",
            f"Label: {ui.get('label') or library_component.get('id', '-')}",
        ]
        if category == "fader":
            lines.append(f"Travel: {self._read_mm(library_component, ('mechanical', 'travel_mm')):.1f} mm")
        if category == "display":
            lines.append(f"Window: {self._read_mm(library_component, ('mechanical', 'screen_window_mm', 'width')):.1f} x {self._read_mm(library_component, ('mechanical', 'screen_window_mm', 'height')):.1f} mm")
        if category == "encoder":
            lines.append(f"Shaft diameter: {self._read_mm(library_component, ('mechanical', 'shaft', 'diameter_mm')):.1f} mm")
        if category == "pad":
            lines.append(f"Pad window: {self._read_mm(library_component, ('mechanical', 'panel', 'recommended_window_mm', 'width')):.1f} mm")
        if panel:
            lines.append("Property panel groups placement, dimensions, mounting, display, and advanced values.")
        return "\n".join(lines)
