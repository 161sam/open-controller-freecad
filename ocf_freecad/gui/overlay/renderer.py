from __future__ import annotations

import math
from typing import Any

from ocf_freecad.freecad_api import shapes
from ocf_freecad.freecad_api.metadata import set_document_data
from ocf_freecad.gui.panels._common import log_to_console
from ocf_freecad.services.overlay_service import OverlayService


class OverlayRenderer:
    OVERLAY_OBJECT_NAME = "OCF_Overlay"
    MIN_GEOMETRY_EPSILON = 1e-6

    def __init__(self, overlay_service: OverlayService | None = None) -> None:
        self.overlay_service = overlay_service or OverlayService()

    def refresh(self, doc: Any) -> dict[str, Any]:
        payload = self.overlay_service.build_overlay(doc)
        return self.render(doc, payload)

    def render(self, doc: Any, payload: dict[str, Any]) -> dict[str, Any]:
        self._clear_overlay(doc)
        stats = {
            "total_items": len(payload.get("items", [])),
            "rendered_items": 0,
            "dropped_items": 0,
            "dropped_reasons": {},
            "render_path": "disabled",
        }
        if not payload.get("enabled", True):
            updated = self._with_render_summary(payload, stats)
            self._store_overlay_state(doc, updated)
            self._log_render_summary(updated)
            return updated
        if not hasattr(doc, "addObject"):
            stats["render_path"] = "headless"
            updated = self._with_render_summary(payload, stats)
            self._store_overlay_state(doc, updated)
            self._log_render_summary(updated)
            return updated
        z_base = float(payload.get("controller_height", 0.0)) + 0.25
        overlay_parts = []
        for index, item in enumerate(payload.get("items", [])):
            shape, drop_reason = self._item_shape(item, z_base + (index * 0.005))
            if shape is not None:
                overlay_parts.append(shape)
                stats["rendered_items"] += 1
                continue
            stats["dropped_items"] += 1
            key = drop_reason or "unknown"
            stats["dropped_reasons"][key] = int(stats["dropped_reasons"].get(key, 0)) + 1
        compound = shapes.make_compound_shape(overlay_parts)
        if compound is None:
            stats["render_path"] = "compound-empty"
            updated = self._with_render_summary(payload, stats)
            self._store_overlay_state(doc, updated)
            self._log_render_summary(updated)
            return updated
        obj = shapes.create_feature(doc, self.OVERLAY_OBJECT_NAME, compound)
        obj.Label = self.OVERLAY_OBJECT_NAME
        self._apply_style(obj, self._overlay_style())
        if hasattr(doc, "recompute"):
            doc.recompute()
        stats["render_path"] = "compound"
        updated = self._with_render_summary(payload, stats)
        self._store_overlay_state(doc, updated)
        self._log_render_summary(updated)
        return updated

    def _clear_overlay(self, doc: Any) -> None:
        if not hasattr(doc, "Objects") or not hasattr(doc, "removeObject"):
            return
        for obj in list(doc.Objects):
            name = str(getattr(obj, "Name", ""))
            label = str(getattr(obj, "Label", ""))
            if name.startswith("OCF_OVERLAY_") or label.startswith("OCF_OVERLAY_") or name == self.OVERLAY_OBJECT_NAME or label == self.OVERLAY_OBJECT_NAME:
                doc.removeObject(name)

    def _item_shape(self, item: dict[str, Any], z: float) -> tuple[Any | None, str | None]:
        try:
            geometry = item["geometry"]
            item_type = str(item.get("type", ""))
            if item_type == "text_marker":
                return None, "text_marker"
            if item_type == "rect":
                width = float(geometry["width"])
                height = float(geometry["height"])
                rotation = float(geometry.get("rotation", 0.0) or 0.0)
                if not self._is_positive(width) or not self._is_positive(height):
                    return None, "degenerate_rect"
                rect_shape = shapes.translate_shape(
                    shapes.make_rect_prism_shape(
                        width=width,
                        depth=height,
                        height=0.15,
                    ),
                    x=float(geometry["x"]) - (width / 2.0),
                    y=float(geometry["y"]) - (height / 2.0),
                    z=z,
                )
                if rotation != 0.0:
                    rect_shape = shapes.rotate_shape(
                        rect_shape,
                        rotation,
                        center=(float(geometry["x"]), float(geometry["y"]), z),
                    )
                return (rect_shape, None)
            if item_type == "circle":
                diameter = float(geometry["diameter"])
                if not self._is_positive(diameter):
                    return None, "degenerate_circle"
                return (
                    shapes.translate_shape(
                        shapes.make_cylinder_shape(
                            radius=diameter / 2.0,
                            height=0.15,
                        ),
                        x=float(geometry["x"]),
                        y=float(geometry["y"]),
                        z=z,
                    ),
                    None,
                )
            if item_type == "line":
                start_x = float(geometry["start_x"])
                start_y = float(geometry["start_y"])
                end_x = float(geometry["end_x"])
                end_y = float(geometry["end_y"])
                if math.hypot(end_x - start_x, end_y - start_y) <= self.MIN_GEOMETRY_EPSILON:
                    return None, "degenerate_line"
                return (
                    shapes.make_line_shape(
                        start=(start_x, start_y),
                        end=(end_x, end_y),
                        z=z,
                    ),
                    None,
                )
            return None, f"unsupported:{item_type or 'unknown'}"
        except Exception:
            return None, "build_error"

    def _is_positive(self, value: float) -> bool:
        return math.isfinite(value) and value > self.MIN_GEOMETRY_EPSILON

    def _with_render_summary(self, payload: dict[str, Any], stats: dict[str, Any]) -> dict[str, Any]:
        updated = dict(payload)
        summary = dict(updated.get("summary", {}))
        summary.update(
            {
                "render_item_count": int(stats["rendered_items"]),
                "dropped_item_count": int(stats["dropped_items"]),
                "render_path": str(stats["render_path"]),
            }
        )
        if stats.get("dropped_reasons"):
            summary["dropped_reasons"] = dict(stats["dropped_reasons"])
        updated["summary"] = summary
        return updated

    def _store_overlay_state(self, doc: Any, payload: dict[str, Any]) -> None:
        set_document_data(doc, "OCFOverlayState", payload)
        set_document_data(
            doc,
            "OCFOverlayRender",
            {
                "render_path": payload.get("summary", {}).get("render_path"),
                "render_item_count": payload.get("summary", {}).get("render_item_count", 0),
                "dropped_item_count": payload.get("summary", {}).get("dropped_item_count", 0),
                "dropped_reasons": dict(payload.get("summary", {}).get("dropped_reasons", {})),
            },
        )

    def _log_render_summary(self, payload: dict[str, Any]) -> None:
        summary = payload.get("summary", {})
        log_to_console(
            "Overlay render "
            f"path={summary.get('render_path', 'unknown')} "
            f"items={summary.get('item_count', 0)} "
            f"rendered={summary.get('render_item_count', 0)} "
            f"dropped={summary.get('dropped_item_count', 0)}."
        )

    def _overlay_style(self) -> dict[str, Any]:
        return {
            "rgb": (0.2, 0.8, 0.7),
            "line_rgb": (0.1, 0.45, 0.4),
            "line_width": 2,
            "transparency": 82,
        }

    def _apply_style(self, obj: Any, style: dict[str, Any]) -> None:
        view = getattr(obj, "ViewObject", None)
        if view is None:
            return
        rgb = style.get("rgb")
        line_rgb = style.get("line_rgb")
        if rgb is not None and hasattr(view, "ShapeColor"):
            view.ShapeColor = rgb
        if line_rgb is not None and hasattr(view, "LineColor"):
            view.LineColor = line_rgb
        line_width = style.get("line_width")
        if line_width is not None and hasattr(view, "LineWidth"):
            view.LineWidth = int(line_width)
        transparency = style.get("transparency")
        if transparency is not None and hasattr(view, "Transparency"):
            view.Transparency = int(transparency)
        draw_style = style.get("draw_style")
        if draw_style is not None and hasattr(view, "DrawStyle"):
            view.DrawStyle = draw_style
