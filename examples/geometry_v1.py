import FreeCAD as App

from ocf_freecad.domain.component import Component
from ocf_freecad.domain.controller import Controller
from ocf_freecad.generator.controller_builder import ControllerBuilder


doc = App.newDocument("TestController")

controller = Controller(
    id="test",
    width=120,
    depth=80,
    height=30,
    top_thickness=3,
)

components = [
    Component("enc1", "encoder", 40, 30, 3.5),
    Component("enc2", "encoder", 80, 30, 3.5),
]

builder = ControllerBuilder(doc)

body = builder.build_body(controller)
top = builder.build_top_plate(controller)
top_cut = builder.apply_cutouts(top, components)

doc.recompute()
