from __future__ import annotations

from copy import deepcopy
from typing import Any

from ocf_freecad.freecad_api import shapes
from ocf_freecad.generator.component_resolver import ComponentResolver
from ocf_freecad.geometry.primitives import Cutout, ResolvedMechanical, ShapePrimitive, SurfacePrimitive


class ControllerBuilder:
    def __init__(self, doc=None, component_resolver: ComponentResolver | None = None):
        self.doc = doc
        self.component_resolver = component_resolver or ComponentResolver()

    def build_body(self, controller):
        surface = self.resolve_surface(controller)
        return shapes.create_surface_prism(
            self.doc,
            "ControllerBody",
            surface,
            controller.height,
        )

    def build_top_plate(self, controller):
        surface = self.resolve_surface(controller)
        z_offset = controller.height - controller.top_thickness
        return shapes.create_surface_prism(
            self.doc,
            "TopPlate",
            surface,
            controller.top_thickness,
            z=z_offset,
        )

    def resolve_surface(self, controller: Any) -> SurfacePrimitive:
        controller_data = self._controller_to_dict(controller)
        width = float(controller_data["width"])
        depth = float(controller_data["depth"])
        surface_data = deepcopy(controller_data.get("surface"))

        if surface_data is None:
            return SurfacePrimitive(shape="rectangle", width=width, height=depth)
        if not isinstance(surface_data, dict):
            raise ValueError("Controller surface must be a mapping")

        shape = surface_data.get("shape", "rectangle")
        if shape == "rectangle":
            return SurfacePrimitive(
                shape="rectangle",
                width=float(surface_data.get("width", width)),
                height=float(surface_data.get("height", depth)),
            )
        if shape == "rounded_rect":
            corner_radius = float(surface_data.get("corner_radius", 0.0))
            return SurfacePrimitive(
                shape="rounded_rect",
                width=float(surface_data.get("width", width)),
                height=float(surface_data.get("height", depth)),
                corner_radius=corner_radius,
            )
        if shape == "polygon":
            points = surface_data.get("points")
            if not isinstance(points, list) or len(points) < 3:
                raise ValueError("Polygon controller surface requires at least three points")
            normalized_points = []
            for point in points:
                if not isinstance(point, (list, tuple)) or len(point) != 2:
                    raise ValueError("Polygon controller surface points must be [x, y] pairs")
                normalized_points.append((float(point[0]), float(point[1])))
            return SurfacePrimitive(
                shape="polygon",
                width=float(surface_data.get("width", width)),
                height=float(surface_data.get("height", depth)),
                points=tuple(normalized_points),
            )
        raise ValueError(f"Unsupported controller surface shape: {shape}")

    def resolve_components(self, components: list[Any]) -> list[dict[str, Any]]:
        return self.component_resolver.resolve_many(components)

    def build_keepouts(self, components: list[Any]) -> list[dict[str, Any]]:
        keepouts: list[dict[str, Any]] = []
        for component in self.resolve_components(components):
            mechanical = component["resolved_mechanical"]
            keepouts.append(
                self._placed_feature(component["id"], component["x"], component["y"], mechanical.keepout_top, "top")
            )
            keepouts.append(
                self._placed_feature(
                    component["id"],
                    component["x"],
                    component["y"],
                    mechanical.keepout_bottom,
                    "bottom",
                )
            )
        return keepouts

    def apply_cutouts(self, base_obj, components):
        result_shape = base_obj.Shape.copy() if hasattr(base_obj.Shape, "copy") else base_obj.Shape
        z_start = base_obj.Shape.BoundBox.ZMin
        cut_height = base_obj.Shape.BoundBox.ZLength

        for component in self.resolve_components(components):
            tool = self._create_cutout_shape(
                x=component["x"],
                y=component["y"],
                cutout=component["resolved_mechanical"].cutout,
                cut_height=cut_height,
                z_start=z_start,
            )
            result_shape = result_shape.cut(tool)

        base_obj.Shape = result_shape
        return base_obj

    def build_cutout_primitives(self, components: list[Any]) -> list[dict[str, Any]]:
        cutouts: list[dict[str, Any]] = []
        for component in self.resolve_components(components):
            placed = Cutout(
                x=component["x"],
                y=component["y"],
                shape=component["resolved_mechanical"].cutout,
            )
            cutouts.append(
                {
                    "component_id": component["id"],
                    "feature": "cutout",
                    **placed.to_dict(),
                }
            )
        return cutouts

    def _create_cutout_shape(
        self,
        x: float,
        y: float,
        cutout: ShapePrimitive,
        cut_height: float,
        z_start: float,
    ):
        if cutout.shape == "circle":
            return shapes.translate_shape(
                shapes.make_cylinder_shape(
                    radius=cutout.diameter / 2.0,
                    height=cut_height,
                ),
                x=x,
                y=y,
                z=z_start,
            )
        if cutout.shape == "rect":
            return shapes.translate_shape(
                shapes.make_rect_prism_shape(
                    width=cutout.width,
                    depth=cutout.height,
                    height=cut_height,
                ),
                x=x - (cutout.width / 2.0),
                y=y - (cutout.height / 2.0),
                z=z_start,
            )
        raise ValueError(f"Unsupported cutout shape: {cutout.shape}")

    def _placed_feature(
        self,
        component_id: str,
        x: float,
        y: float,
        shape: ResolvedMechanical | ShapePrimitive,
        layer: str,
    ) -> dict[str, Any]:
        if isinstance(shape, ResolvedMechanical):
            raise TypeError("Expected ShapePrimitive for placed feature generation")
        return {
            "component_id": component_id,
            "feature": f"keepout_{layer}",
            "x": x,
            "y": y,
            **shape.to_dict(),
        }

    def _controller_to_dict(self, controller: Any) -> dict[str, Any]:
        if isinstance(controller, dict):
            return deepcopy(controller)
        if hasattr(controller, "__dict__"):
            return deepcopy(vars(controller))
        raise TypeError(f"Unsupported controller representation: {type(controller)!r}")


def build_controller(domain_controller):
    return domain_controller
