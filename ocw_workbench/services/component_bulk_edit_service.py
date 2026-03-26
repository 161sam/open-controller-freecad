from __future__ import annotations

from copy import deepcopy
from typing import Any

from ocw_workbench.services.component_property_service import ComponentPropertyService
from ocw_workbench.services.library_service import LibraryService


class ComponentBulkEditService:
    def __init__(
        self,
        property_service: ComponentPropertyService | None = None,
        library_service: LibraryService | None = None,
    ) -> None:
        self.library_service = library_service or LibraryService()
        self.property_service = property_service or ComponentPropertyService(self.library_service)

    def build_bulk_model(self, components: list[dict[str, Any]]) -> dict[str, Any]:
        if not components:
            raise ValueError("Bulk edit requires at least one component")
        property_models = [self.property_service.build_property_model(component) for component in components]
        categories = sorted({str(model["category"]) for model in property_models})
        component_ids = [str(component["id"]) for component in components]
        fields: list[dict[str, Any]] = []
        fields.append(self._common_field(property_models, "rotation"))
        fields.append(self._common_field(property_models, "visible"))
        fields.append(
            {
                "id": "label_prefix",
                "label": "Label Prefix",
                "type": "string",
                "value": "",
                "mixed": False,
                "editable": True,
                "group": "generic",
                "options": [],
                "bulk_only": True,
            }
        )
        if len(categories) == 1:
            variant_field = self._common_field(property_models, "library_ref")
            if variant_field.get("editable", False):
                fields.append(variant_field)
            for field_id in self._bulk_property_field_ids(categories[0]):
                common_field = self._common_field(property_models, field_id)
                if common_field.get("editable", False):
                    fields.append(common_field)
        return {
            "component_ids": component_ids,
            "count": len(component_ids),
            "categories": categories,
            "fields": fields,
            "details": self._details_text(len(component_ids), categories),
        }

    def build_updates(
        self,
        model: dict[str, Any],
        values: dict[str, Any],
        apply_fields: set[str],
    ) -> dict[str, dict[str, Any]]:
        if not apply_fields:
            return {}
        updates_by_component = {component_id: {} for component_id in model["component_ids"]}
        for field in model["fields"]:
            field_id = field["id"]
            if field_id not in apply_fields:
                continue
            raw_value = values.get(field_id)
            if field_id == "label_prefix":
                prefix = str(raw_value or "").strip()
                if not prefix:
                    raise ValueError("Label Prefix must not be empty when applied")
                for index, component_id in enumerate(model["component_ids"], start=1):
                    updates_by_component[component_id]["label"] = f"{prefix}{index}"
                continue
            if field_id in {"rotation", "visible", "library_ref"}:
                for component_id in model["component_ids"]:
                    updates_by_component[component_id][field_id] = raw_value
                continue
            for component_id in model["component_ids"]:
                updates_by_component[component_id].setdefault("properties", {})
                updates_by_component[component_id]["properties"][field_id] = raw_value
        return {component_id: updates for component_id, updates in updates_by_component.items() if updates}

    def _common_field(self, property_models: list[dict[str, Any]], field_id: str) -> dict[str, Any]:
        base = next((field for field in property_models[0]["fields"] if field["id"] == field_id), None)
        if base is None:
            raise KeyError(f"Unknown bulk field id: {field_id}")
        values = []
        editable = bool(base.get("editable", True))
        for model in property_models:
            field = next((item for item in model["fields"] if item["id"] == field_id), None)
            if field is None:
                editable = False
                continue
            editable = editable and bool(field.get("editable", True))
            values.append(deepcopy(field.get("value")))
        mixed = not _all_equal(values)
        field_value = deepcopy(values[0]) if values and not mixed else self._mixed_placeholder(base)
        result = deepcopy(base)
        result["value"] = field_value
        result["mixed"] = mixed
        result["editable"] = editable
        return result

    def _bulk_property_field_ids(self, category: str) -> list[str]:
        return {
            "fader": ["cap_width"],
            "display": ["orientation", "bezel"],
        }.get(category, [])

    def _mixed_placeholder(self, field: dict[str, Any]) -> Any:
        field_type = str(field.get("type") or "string")
        if field_type == "bool":
            return False
        if field_type in {"int", "float"}:
            return 0.0
        if field_type == "enum":
            options = field.get("options", [])
            if options:
                return options[0]["value"]
            return ""
        return ""

    def _details_text(self, count: int, categories: list[str]) -> str:
        family_text = ", ".join(categories) if categories else "-"
        return (
            f"Bulk edit for {count} selected components.\n"
            f"Families: {family_text}\n"
            "Only shared, conservative fields are exposed. Mixed values must be explicitly applied."
        )


def _all_equal(values: list[Any]) -> bool:
    if not values:
        return True
    first = values[0]
    return all(item == first for item in values[1:])
