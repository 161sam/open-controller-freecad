def make_box_shape(width, depth, height):
    import Part

    return Part.makeBox(width, depth, height)


def make_rect_prism_shape(width, depth, height):
    return make_box_shape(width, depth, height)


def make_rounded_rect_prism_shape(width, depth, height, corner_radius):
    base = make_box_shape(width, depth, height)
    radius = min(float(corner_radius), width / 2.0, depth / 2.0)
    if radius > 0:
        vertical_edges = [
            edge
            for edge in base.Edges
            if hasattr(edge, "BoundBox") and abs(edge.BoundBox.ZLength - height) < 1e-6
        ]
        if vertical_edges:
            base = base.makeFillet(radius, vertical_edges)
    return base


def make_polygon_prism_shape(points, height):
    import FreeCAD as App
    import Part

    if len(points) < 3:
        raise ValueError("Polygon surface requires at least three points")

    vectors = [App.Vector(px, py, 0) for px, py in points]
    if vectors[0] != vectors[-1]:
        vectors.append(vectors[0])
    wire = Part.makePolygon(vectors)
    face = Part.Face(wire)
    return face.extrude(App.Vector(0, 0, height))


def make_cylinder_shape(radius, height):
    import Part

    return Part.makeCylinder(radius, height)


def translate_shape(shape, x=0, y=0, z=0):
    import FreeCAD as App

    translated = shape.copy()
    translated.translate(App.Vector(x, y, z))
    return translated


def create_box(doc, name, width, depth, height, x=0, y=0, z=0):
    import FreeCAD as App

    shape = make_box_shape(width, depth, height)
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape
    obj.Placement.Base = App.Vector(x, y, z)
    return obj


def create_rect_prism(doc, name, width, depth, height, x, y, z=0):
    return create_box(doc, name, width, depth, height, x=x, y=y, z=z)


def create_surface_prism(doc, name, surface, height, x=0, y=0, z=0):
    shape_type = surface.shape
    if shape_type == "rectangle":
        return create_box(doc, name, surface.width, surface.height, height, x=x, y=y, z=z)
    if shape_type == "rounded_rect":
        return create_rounded_rect_prism(
            doc,
            name,
            width=surface.width,
            depth=surface.height,
            height=height,
            corner_radius=surface.corner_radius or 0.0,
            x=x,
            y=y,
            z=z,
        )
    if shape_type == "polygon":
        return create_polygon_prism(
            doc,
            name,
            points=surface.points or (),
            height=height,
            x=x,
            y=y,
            z=z,
        )
    raise ValueError(f"Unsupported controller surface shape: {shape_type}")


def create_rounded_rect_prism(doc, name, width, depth, height, corner_radius, x=0, y=0, z=0):
    import FreeCAD as App

    base = make_rounded_rect_prism_shape(width, depth, height, corner_radius)

    obj = doc.addObject("Part::Feature", name)
    obj.Shape = base
    obj.Placement.Base = App.Vector(x, y, z)
    return obj


def create_polygon_prism(doc, name, points, height, x=0, y=0, z=0):
    import FreeCAD as App
    prism = make_polygon_prism_shape(points, height)

    obj = doc.addObject("Part::Feature", name)
    obj.Shape = prism
    obj.Placement.Base = App.Vector(x, y, z)
    return obj


def create_cylinder(doc, name, radius, height, x, y, z=0):
    import FreeCAD as App

    cylinder = make_cylinder_shape(radius, height)
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = cylinder
    obj.Placement.Base = App.Vector(x, y, z)
    return obj


def create_line(doc, name, start, end, z=0):
    wire = make_line_shape(start, end, z=z)
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = wire
    return obj


def make_line_shape(start, end, z=0):
    import FreeCAD as App
    import Part

    return Part.makePolygon(
        [
            App.Vector(float(start[0]), float(start[1]), float(z)),
            App.Vector(float(end[0]), float(end[1]), float(z)),
        ]
    )


def make_compound_shape(parts):
    import Part

    filtered = [part for part in parts if part is not None]
    if not filtered:
        return None
    return Part.makeCompound(filtered)


def create_feature(doc, name, shape):
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape
    return obj


def cut(base_obj, tool_obj, name=None):
    tool_shape = tool_obj.Shape if hasattr(tool_obj, "Shape") else tool_obj
    result = base_obj.Shape.cut(tool_shape)
    obj = base_obj.Document.addObject(
        "Part::Feature",
        name or f"{base_obj.Name}_cut",
    )
    obj.Shape = result
    return obj
