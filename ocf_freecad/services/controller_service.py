from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

from ocf_freecad.domain.component import Component
from ocf_freecad.domain.controller import Controller
from ocf_freecad.generator.controller_builder import ControllerBuilder
from ocf_freecad.layout.engine import LayoutEngine
from ocf_freecad.services.constraint_service import ConstraintService
from ocf_freecad.services.library_service import LibraryService


DEFAULT_CONTROLLER = {
    "id": "controller",
    "width": 160.0,
    "depth": 100.0,
    "height": 30.0,
    "top_thickness": 3.0,
    "surface": None,
    "mounting_holes": [],
    "reserved_zones": [],
    "layout_zones": [],
}


class ControllerService:
    def __init__(
        self,
        library_service: LibraryService | None = None,
        layout_engine: LayoutEngine | None = None,
        constraint_service: ConstraintService | None = None,
    ) -> None:
        self.library_service = library_service or LibraryService()
        self.layout_engine = layout_engine or LayoutEngine()
        self.constraint_service = constraint_service or ConstraintService()

    def create_controller(self, doc: Any, controller_data: dict[str, Any] | None = None) -> dict[str, Any]:
        state = {
            "controller": deepcopy(DEFAULT_CONTROLLER),
            "components": [],
        }
        if controller_data is not None:
            state["controller"].update(deepcopy(controller_data))
        self.save_state(doc, state)
        self.sync_document(doc)
        return deepcopy(state)

    def get_state(self, doc: Any) -> dict[str, Any]:
        state = getattr(doc, "OCFState", None)
        if isinstance(state, dict):
            return deepcopy(state)
        serialized = getattr(doc, "OCF_State_JSON", None)
        if isinstance(serialized, str) and serialized:
            return json.loads(serialized)
        return {
            "controller": deepcopy(DEFAULT_CONTROLLER),
            "components": [],
        }

    def save_state(self, doc: Any, state: dict[str, Any]) -> None:
        normalized = deepcopy(state)
        doc.OCFState = normalized
        doc.OCF_State_JSON = json.dumps(normalized)

    def list_library_components(self, category: str | None = None) -> list[dict[str, Any]]:
        return self.library_service.list_by_category(category=category)

    def add_component(
        self,
        doc: Any,
        library_ref: str,
        component_id: str | None = None,
        component_type: str | None = None,
        x: float = 0.0,
        y: float = 0.0,
        rotation: float = 0.0,
        zone_id: str | None = None,
    ) -> dict[str, Any]:
        state = self.get_state(doc)
        library_component = self.library_service.get(library_ref)
        component_type = component_type or library_component["category"]
        component_id = component_id or self._next_component_id(state["components"], component_type)
        state["components"].append(
            {
                "id": component_id,
                "type": component_type,
                "library_ref": library_ref,
                "x": float(x),
                "y": float(y),
                "rotation": float(rotation),
                "zone_id": zone_id,
            }
        )
        self.save_state(doc, state)
        self.sync_document(doc)
        return deepcopy(state)

    def move_component(
        self,
        doc: Any,
        component_id: str,
        x: float,
        y: float,
        rotation: float | None = None,
    ) -> dict[str, Any]:
        state = self.get_state(doc)
        for component in state["components"]:
            if component["id"] == component_id:
                component["x"] = float(x)
                component["y"] = float(y)
                if rotation is not None:
                    component["rotation"] = float(rotation)
                self.save_state(doc, state)
                self.sync_document(doc)
                return deepcopy(state)
        raise KeyError(f"Unknown component id: {component_id}")

    def auto_layout(
        self,
        doc: Any,
        strategy: str = "grid",
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        state = self.get_state(doc)
        controller = self._build_controller(state["controller"])
        components = [self._build_component(item) for item in state["components"]]
        result = self.layout_engine.place(controller, components, strategy=strategy, config=config)
        placements = {placement["component_id"]: placement for placement in result["placements"]}
        for component in state["components"]:
            placement = placements.get(component["id"])
            if placement is None:
                continue
            component["x"] = placement["x"]
            component["y"] = placement["y"]
            component["rotation"] = placement["rotation"]
            if placement.get("zone_id") is not None:
                component["zone_id"] = placement["zone_id"]
        self.save_state(doc, state)
        self.sync_document(doc)
        return result

    def validate_layout(self, doc: Any, config: dict[str, Any] | None = None) -> dict[str, Any]:
        state = self.get_state(doc)
        controller = self._build_controller(state["controller"])
        components = [self._build_component(item) for item in state["components"]]
        return self.constraint_service.validate(controller, components, config=config)

    def sync_document(self, doc: Any) -> None:
        state = self.get_state(doc)
        doc.OCFLastSync = {
            "controller_id": state["controller"]["id"],
            "component_count": len(state["components"]),
        }
        if not hasattr(doc, "addObject"):
            if hasattr(doc, "recompute"):
                doc.recompute()
            return

        self._clear_generated_objects(doc)
        controller = self._build_controller(state["controller"])
        components = [self._build_component(item) for item in state["components"]]
        builder = ControllerBuilder(doc=doc)
        body = builder.build_body(controller)
        self._set_generated_label(body, "OCF_ControllerBody")
        top = builder.build_top_plate(controller)
        self._set_generated_label(top, "OCF_TopPlate")
        top_cut = builder.apply_cutouts(top, components)
        self._set_generated_label(top_cut, "OCF_TopPlateCut")
        self._create_component_markers(doc, builder, components, controller.height)
        if hasattr(doc, "recompute"):
            doc.recompute()

    def _create_component_markers(self, doc: Any, builder: ControllerBuilder, components: list[Component], z_height: float) -> None:
        for keepout in builder.build_keepouts(components):
            name = f"OCF_{keepout['component_id']}_{keepout['feature']}"
            if keepout["shape"] == "circle":
                marker = __import__("ocf_freecad.freecad_api.shapes", fromlist=["create_cylinder"]).create_cylinder(
                    doc,
                    name,
                    radius=float(keepout["diameter"]) / 2.0,
                    height=1.0,
                    x=float(keepout["x"]),
                    y=float(keepout["y"]),
                    z=float(z_height),
                )
                self._set_generated_label(marker, name)
                continue
            if keepout["shape"] == "rect":
                marker = __import__("ocf_freecad.freecad_api.shapes", fromlist=["create_rect_prism"]).create_rect_prism(
                    doc,
                    name,
                    width=float(keepout["width"]),
                    depth=float(keepout["height"]),
                    height=1.0,
                    x=float(keepout["x"]) - (float(keepout["width"]) / 2.0),
                    y=float(keepout["y"]) - (float(keepout["height"]) / 2.0),
                    z=float(z_height),
                )
                self._set_generated_label(marker, name)

    def _clear_generated_objects(self, doc: Any) -> None:
        if not hasattr(doc, "Objects") or not hasattr(doc, "removeObject"):
            return
        for obj in list(doc.Objects):
            name = getattr(obj, "Name", "")
            label = getattr(obj, "Label", "")
            if (
                str(name).startswith("OCF_")
                or str(label).startswith("OCF_")
                or name in {"ControllerBody", "TopPlate"}
                or str(name).startswith("TopPlate_")
            ):
                doc.removeObject(name)

    def _build_controller(self, controller_data: dict[str, Any]) -> Controller:
        return Controller(**controller_data)

    def _build_component(self, component_data: dict[str, Any]) -> Component:
        return Component(**component_data)

    def _next_component_id(self, components: list[dict[str, Any]], component_type: str) -> str:
        prefix = {
            "encoder": "enc",
            "button": "btn",
            "display": "disp",
            "fader": "fader",
            "pad": "pad",
            "rgb_button": "rgb",
        }.get(component_type, "comp")
        index = 1
        existing_ids = {component["id"] for component in components}
        while f"{prefix}{index}" in existing_ids:
            index += 1
        return f"{prefix}{index}"

    def _set_generated_label(self, obj: Any, label: str) -> None:
        if hasattr(obj, "Label"):
            obj.Label = label
        else:
            setattr(obj, "Name", label)
