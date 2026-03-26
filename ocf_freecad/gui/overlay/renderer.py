from __future__ import annotations

from typing import Any

from ocf_freecad.freecad_api import shapes
from ocf_freecad.freecad_api.metadata import set_document_data
from ocf_freecad.services.overlay_service import OverlayService


class OverlayRenderer:
    OVERLAY_OBJECT_NAME = "OCF_Overlay"

    def __init__(self, overlay_service: OverlayService | None = None) -> None:
        self.overlay_service = overlay_service or OverlayService()

    def refresh(self, doc: Any) -> dict[str, Any]:
        payload = self.overlay_service.build_overlay(doc)
        self.render(doc, payload)
        return payload

    def render(self, doc: Any, payload: dict[str, Any]) -> None:
        set_document_data(doc, "OCFOverlayState", payload)
        self._clear_overlay(doc)
        if not payload.get("enabled", True):
            return
        if not hasattr(doc, "addObject"):
            return
        z_base = float(payload.get("controller_height", 0.0)) + 0.25
        overlay_parts = []
        for index, item in enumerate(payload.get("items", [])):
            shape = self._item_shape(item, z_base + (index * 0.005))
            if shape is not None:
                overlay_parts.append(shape)
        compound = shapes.make_compound_shape(overlay_parts)
        if compound is None:
            return
        obj = shapes.create_feature(doc, self.OVERLAY_OBJECT_NAME, compound)
        obj.Label = self.OVERLAY_OBJECT_NAME
        self._apply_style(obj, self._overlay_style())
        if hasattr(doc, "recompute"):
            doc.recompute()

    def _clear_overlay(self, doc: Any) -> None:
        if not hasattr(doc, "Objects") or not hasattr(doc, "removeObject"):
            return
        for obj in list(doc.Objects):
            name = str(getattr(obj, "Name", ""))
            label = str(getattr(obj, "Label", ""))
            if name.startswith("OCF_OVERLAY_") or label.startswith("OCF_OVERLAY_") or name == self.OVERLAY_OBJECT_NAME or label == self.OVERLAY_OBJECT_NAME:
                doc.removeObject(name)

    def _item_shape(self, item: dict[str, Any], z: float) -> Any | None:
        geometry = item["geometry"]
        if item["type"] == "rect":
            return shapes.translate_shape(
                shapes.make_rect_prism_shape(
                    width=float(geometry["width"]),
                    depth=float(geometry["height"]),
                    height=0.15,
                ),
                x=float(geometry["x"]) - (float(geometry["width"]) / 2.0),
                y=float(geometry["y"]) - (float(geometry["height"]) / 2.0),
                z=z,
            )
        if item["type"] == "circle":
            return shapes.translate_shape(
                shapes.make_cylinder_shape(
                    radius=float(geometry["diameter"]) / 2.0,
                    height=0.15,
                ),
                x=float(geometry["x"]),
                y=float(geometry["y"]),
                z=z,
            )
        if item["type"] == "line":
            return shapes.make_line_shape(
                start=(float(geometry["start_x"]), float(geometry["start_y"])),
                end=(float(geometry["end_x"]), float(geometry["end_y"])),
                z=z,
            )
        return None

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
