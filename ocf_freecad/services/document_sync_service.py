from __future__ import annotations

from time import perf_counter
from typing import Any, Callable

from ocf_freecad.freecad_api import gui as freecad_gui
from ocf_freecad.freecad_api.metadata import get_document_data, set_document_data, update_document_data
from ocf_freecad.freecad_api.model import (
    CONTROLLER_OBJECT_LABEL,
    CONTROLLER_OBJECT_NAME,
    GENERATED_GROUP_LABEL,
    GENERATED_GROUP_NAME,
    OVERLAY_OBJECT_LABEL,
    OVERLAY_OBJECT_NAME,
    clear_generated_group,
    get_controller_object,
    get_generated_group,
    group_generated_object,
    iter_generated_objects,
)
from ocf_freecad.freecad_api.state import STATE_CONTAINER_LABEL, STATE_CONTAINER_NAME
from ocf_freecad.generator.controller_builder import ControllerBuilder
from ocf_freecad.services._logging import log_to_console


class DocumentSyncService:
    def __init__(
        self,
        builder_factory: Callable[..., Any] | None = None,
        gui_module: Any | None = None,
    ) -> None:
        self.builder_factory = builder_factory or ControllerBuilder
        self.gui_module = gui_module or freecad_gui

    def sync_document(self, doc: Any, state: dict[str, Any]) -> None:
        started_at = perf_counter()
        controller_object = get_controller_object(doc, create=hasattr(doc, "addObject"))
        generated_group = get_generated_group(doc, create=hasattr(doc, "addObject"))
        set_document_data(doc, "OCFLastSync", {
            "controller_id": state["controller"]["id"],
            "component_count": len(state["components"]),
            "template_id": state["meta"].get("template_id"),
            "variant_id": state["meta"].get("variant_id"),
            "selection": state["meta"].get("selection"),
            "controller_object": getattr(controller_object, "Name", CONTROLLER_OBJECT_NAME) if controller_object is not None else None,
            "generated_group": getattr(generated_group, "Name", GENERATED_GROUP_NAME) if generated_group is not None else None,
        })
        log_to_console(
            f"Syncing document '{getattr(doc, 'Name', '<unnamed>')}' "
            f"for controller '{state['controller']['id']}' with {len(state['components'])} components."
        )
        if not hasattr(doc, "addObject"):
            if hasattr(doc, "recompute"):
                doc.recompute()
            update_document_data(
                doc,
                "OCFLastSync",
                {
                    "sync_duration_ms": round((perf_counter() - started_at) * 1000.0, 3),
                    "sync_mode": "state_only",
                },
            )
            log_to_console(
                f"Document '{getattr(doc, 'Name', '<unnamed>')}' has no FreeCAD object API; state-only sync complete.",
                level="warning",
            )
            return

        self._clear_generated_objects(doc)
        controller = self._build_controller(state["controller"])
        components = [self._build_component(item) for item in state["components"]]
        builder = self.builder_factory(doc=doc)
        body = builder.build_body(controller)
        self._set_generated_label(body, "OCF_ControllerBody")
        group_generated_object(doc, body)
        top = builder.build_top_plate(controller)
        top_cut = builder.apply_cutouts(top, components)
        self._set_generated_label(top_cut, "OCF_TopPlateCut" if state["components"] else "OCF_TopPlate")
        group_generated_object(doc, top_cut)
        self._create_component_markers(doc, builder, components, float(state["controller"]["height"]))
        self._apply_selection_highlight(doc, state["meta"].get("selection"))
        if hasattr(doc, "recompute"):
            doc.recompute()
        generated_count = self._generated_object_count(doc)
        duration_ms = round((perf_counter() - started_at) * 1000.0, 3)
        update_document_data(
            doc,
            "OCFLastSync",
            {
                "generated_object_count": generated_count,
                "sync_duration_ms": duration_ms,
                "sync_mode": "full",
            },
        )
        revealed = self.gui_module.reveal_generated_objects(doc)
        self.gui_module.activate_document(doc)
        self.gui_module.focus_view(doc, fit=True)
        log_to_console(
            f"Document sync complete for '{getattr(doc, 'Name', '<unnamed>')}': "
            f"{generated_count} generated objects, {revealed} visible in the 3D view, {duration_ms:.3f} ms."
        )

    def refresh_document_visuals(
        self,
        doc: Any,
        selection: str | None,
        recompute: bool = False,
    ) -> None:
        update_document_data(
            doc,
            "OCFLastSync",
            {
                "selection": selection,
                "sync_mode": "visual_only",
            },
        )
        if not hasattr(doc, "addObject"):
            return
        self._apply_selection_highlight(doc, selection)
        if recompute and hasattr(doc, "recompute"):
            doc.recompute()

    def _create_component_markers(self, doc: Any, builder: Any, components: list[Any], z_height: float) -> None:
        if not self._should_materialize_component_markers(doc):
            return
        shapes_api = __import__("ocf_freecad.freecad_api.shapes", fromlist=["create_cylinder"])
        for keepout in builder.build_keepouts(components):
            name = f"OCF_{keepout['component_id']}_{keepout['feature']}"
            if keepout["shape"] == "circle":
                marker = shapes_api.create_cylinder(
                    doc,
                    name,
                    radius=float(keepout["diameter"]) / 2.0,
                    height=1.0,
                    x=float(keepout["x"]),
                    y=float(keepout["y"]),
                    z=float(z_height),
                )
                self._set_generated_label(marker, name)
                group_generated_object(doc, marker)
                continue
            if keepout["shape"] in {"rect", "slot"}:
                shape_factory = shapes_api.make_rect_prism_shape if keepout["shape"] == "rect" else shapes_api.make_slot_prism_shape
                marker_shape = shapes_api.translate_shape(
                    shape_factory(
                        width=float(keepout["width"]),
                        depth=float(keepout["height"]),
                        height=1.0,
                    ),
                    x=float(keepout["x"]) - (float(keepout["width"]) / 2.0),
                    y=float(keepout["y"]) - (float(keepout["height"]) / 2.0),
                    z=float(z_height),
                )
                if float(keepout.get("rotation", 0.0) or 0.0) != 0.0:
                    marker_shape = shapes_api.rotate_shape(
                        marker_shape,
                        float(keepout["rotation"]),
                        center=(float(keepout["x"]), float(keepout["y"]), float(z_height)),
                    )
                marker = shapes_api.create_feature(doc, name, marker_shape)
                self._set_generated_label(marker, name)
                group_generated_object(doc, marker)

    def _clear_generated_objects(self, doc: Any) -> None:
        if not hasattr(doc, "Objects") or not hasattr(doc, "removeObject"):
            return
        clear_generated_group(doc)
        for obj in list(doc.Objects):
            name = getattr(obj, "Name", "")
            label = getattr(obj, "Label", "")
            if name in {STATE_CONTAINER_NAME, CONTROLLER_OBJECT_NAME, GENERATED_GROUP_NAME, OVERLAY_OBJECT_NAME}:
                continue
            if label in {STATE_CONTAINER_LABEL, CONTROLLER_OBJECT_LABEL, GENERATED_GROUP_LABEL, OVERLAY_OBJECT_LABEL}:
                continue
            if (
                str(name).startswith("OCF_")
                or str(label).startswith("OCF_")
                or name in {"ControllerBody", "TopPlate"}
                or str(name).startswith("TopPlate_")
                or str(name).startswith("cutout_")
            ):
                doc.removeObject(name)

    def _set_generated_label(self, obj: Any, label: str) -> None:
        if hasattr(obj, "Label"):
            obj.Label = label
        else:
            setattr(obj, "Name", label)

    def _should_materialize_component_markers(self, doc: Any) -> bool:
        debug_ui = get_document_data(doc, "OCFDebugUI", {})
        if isinstance(debug_ui, dict):
            return bool(debug_ui.get("materialize_component_markers", False))
        return False

    def _apply_selection_highlight(self, doc: Any, selected_component_id: str | None) -> None:
        if not hasattr(doc, "Objects"):
            return
        for obj in getattr(doc, "Objects", []):
            label = str(getattr(obj, "Label", getattr(obj, "Name", "")))
            if not label.startswith("OCF_"):
                continue
            if label.startswith("OCF_OVERLAY_") or label == OVERLAY_OBJECT_LABEL:
                continue
            view = getattr(obj, "ViewObject", None)
            if view is None:
                continue
            is_selected = selected_component_id is not None and selected_component_id in label
            if hasattr(view, "ShapeColor"):
                view.ShapeColor = (0.9, 0.3, 0.2) if is_selected else (0.7, 0.7, 0.7)
            if hasattr(view, "LineColor"):
                view.LineColor = (0.9, 0.3, 0.2) if is_selected else (0.2, 0.2, 0.2)

    def _generated_object_count(self, doc: Any) -> int:
        return len(iter_generated_objects(doc))

    def _build_controller(self, controller_data: dict[str, Any]) -> Any:
        from ocf_freecad.domain.controller import Controller

        return Controller(**controller_data)

    def _build_component(self, component_data: dict[str, Any]) -> Any:
        from ocf_freecad.domain.component import Component

        return Component(**component_data)
