def create_box(doc, width, depth, height):
    obj = doc.addObject("Part::Box", "ControllerBody")
    obj.Length = width
    obj.Width = depth
    obj.Height = height
    return obj