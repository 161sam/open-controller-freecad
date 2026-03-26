from __future__ import annotations

import sys
from types import SimpleNamespace

from ocf_freecad.generator.controller_builder import ControllerBuilder
from ocf_freecad.userdata.persistence import _default_base_dir


class FakeShape:
    def __init__(self, name: str = "shape") -> None:
        self.name = name
        self.BoundBox = SimpleNamespace(ZMin=0.0, ZLength=3.0)

    def cut(self, _other):
        return FakeShape("cut-result")


class FakeBaseObject:
    def __init__(self) -> None:
        self.Name = "TopPlate"
        self.Shape = FakeShape("base")
        self.Document = SimpleNamespace(addObject=self._add_object)
        self.created = []

    def _add_object(self, _type_name: str, name: str):
        obj = SimpleNamespace(Name=name, Shape=None)
        self.created.append(obj)
        return obj


def test_apply_cutouts_uses_in_memory_shapes(monkeypatch):
    builder = ControllerBuilder(doc="doc")
    monkeypatch.setattr(
        builder,
        "resolve_components",
        lambda _components: [
            {
                "id": "enc1",
                "x": 10.0,
                "y": 20.0,
                "resolved_mechanical": SimpleNamespace(cutout=SimpleNamespace(shape="circle", diameter=8.0)),
            }
        ],
    )
    monkeypatch.setattr(
        "ocf_freecad.generator.controller_builder.shapes.make_cylinder_shape",
        lambda radius, height: SimpleNamespace(radius=radius, height=height, copy=lambda: SimpleNamespace(translate=lambda *_args: None)),
    )
    monkeypatch.setattr(
        "ocf_freecad.generator.controller_builder.shapes.translate_shape",
        lambda shape, x=0, y=0, z=0: SimpleNamespace(shape=shape, x=x, y=y, z=z),
    )

    base = FakeBaseObject()
    result = builder.apply_cutouts(base, components=["ignored"])

    assert result is base
    assert result.Shape.name == "cut-result"
    assert len(base.created) == 0


def test_overlay_renderer_materializes_single_overlay_object(monkeypatch):
    from ocf_freecad.gui.overlay.renderer import OverlayRenderer

    created = []

    class FakeDoc:
        def __init__(self) -> None:
            self.Objects = []
            self.recompute_count = 0

        def addObject(self, _type_name: str, name: str):
            obj = SimpleNamespace(Name=name, Label=name, Shape=None, ViewObject=SimpleNamespace())
            self.Objects.append(obj)
            created.append(obj)
            return obj

        def removeObject(self, name: str) -> None:
            self.Objects = [obj for obj in self.Objects if obj.Name != name]

        def recompute(self) -> None:
            self.recompute_count += 1

    monkeypatch.setattr("ocf_freecad.gui.overlay.renderer.shapes.make_rect_prism_shape", lambda width, depth, height: SimpleNamespace(kind="rect", width=width, depth=depth, height=height, copy=lambda: SimpleNamespace(translate=lambda *_args: None)))
    monkeypatch.setattr("ocf_freecad.gui.overlay.renderer.shapes.make_cylinder_shape", lambda radius, height: SimpleNamespace(kind="cyl", radius=radius, height=height, copy=lambda: SimpleNamespace(translate=lambda *_args: None)))
    monkeypatch.setattr("ocf_freecad.gui.overlay.renderer.shapes.translate_shape", lambda shape, x=0, y=0, z=0: SimpleNamespace(shape=shape, x=x, y=y, z=z))
    monkeypatch.setattr("ocf_freecad.gui.overlay.renderer.shapes.make_line_shape", lambda start, end, z=0: SimpleNamespace(kind="line", start=start, end=end, z=z))
    monkeypatch.setattr("ocf_freecad.gui.overlay.renderer.shapes.make_compound_shape", lambda parts: SimpleNamespace(parts=list(parts)))

    doc = FakeDoc()
    renderer = OverlayRenderer()
    renderer.render(
        doc,
        {
            "enabled": True,
            "controller_height": 10.0,
            "items": [
                {"id": "surface", "type": "rect", "geometry": {"x": 10.0, "y": 10.0, "width": 20.0, "height": 10.0}, "style": {}},
                {"id": "line", "type": "line", "geometry": {"start_x": 0.0, "start_y": 0.0, "end_x": 5.0, "end_y": 5.0}, "style": {}},
            ],
        },
    )

    assert len(created) == 1
    assert created[0].Name == "OCF_Overlay"
    assert len(created[0].Shape.parts) == 2


def test_userdata_base_dir_uses_home_fallback(monkeypatch, tmp_path):
    monkeypatch.delenv("OCF_USERDATA_DIR", raising=False)
    monkeypatch.delenv("XDG_STATE_HOME", raising=False)
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    monkeypatch.setitem(sys.modules, "FreeCAD", None)

    base_dir = _default_base_dir()

    assert base_dir == str(tmp_path / ".local" / "state" / "open-controller-freecad")
