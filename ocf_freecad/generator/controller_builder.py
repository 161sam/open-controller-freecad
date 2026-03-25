from ocf_freecad.freecad_api import shapes


class ControllerBuilder:
    def __init__(self, doc):
        self.doc = doc

    def build_body(self, controller):
        return shapes.create_box(
            self.doc,
            "ControllerBody",
            controller.width,
            controller.depth,
            controller.height,
        )

    def build_top_plate(self, controller):
        z_offset = controller.height - controller.top_thickness
        return shapes.create_box(
            self.doc,
            "TopPlate",
            controller.width,
            controller.depth,
            controller.top_thickness,
            z=z_offset,
        )

    def apply_cutouts(self, base_obj, components):
        result = base_obj
        z_start = base_obj.Shape.BoundBox.ZMin
        cut_height = base_obj.Shape.BoundBox.ZLength

        for component in components:
            if component.type != "encoder":
                continue

            tool = shapes.create_cylinder(
                self.doc,
                f"cutout_{component.id}",
                radius=component.cutout_radius,
                height=cut_height,
                x=component.x,
                y=component.y,
                z=z_start,
            )
            result = shapes.cut(result, tool, name=f"{base_obj.Name}_{component.id}_cut")

        return result


def build_controller(domain_controller):
    return domain_controller
