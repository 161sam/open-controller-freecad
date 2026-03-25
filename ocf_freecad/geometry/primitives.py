class BoxPrimitive:
    def __init__(self, width, depth, height):
        self.width = width
        self.depth = depth
        self.height = height


class CylinderPrimitive:
    def __init__(self, radius, height):
        self.radius = radius
        self.height = height


class Cutout:
    def __init__(self, x, y, shape):
        self.x = x
        self.y = y
        self.shape = shape
