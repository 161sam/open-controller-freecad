from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

CONTROLLER_OBJECT_NAME = "OCF_Controller"
CONTROLLER_OBJECT_LABEL = "OCF Controller"
GENERATED_GROUP_NAME = "OCF_Generated"
GENERATED_GROUP_LABEL = "OCF Generated"
MODEL_GROUP_NAME = "OpenController"
PROJECT_JSON_PROPERTY = "ProjectJson"
OVERLAY_OBJECT_NAME = "OCF_Overlay"
OVERLAY_OBJECT_LABEL = "OCF Overlay"

_STRING_PROPERTIES = {
    "ControllerId": "Controller id",
    "TemplateId": "Template id",
    "VariantId": "Variant id",
    "SelectionId": "Selected component id",
    "SurfaceShape": "Controller surface shape",
}

_FLOAT_PROPERTIES = {
    "Width": "Controller width (mm)",
    "Depth": "Controller depth (mm)",
    "Height": "Controller height (mm)",
    "TopThickness": "Top plate thickness (mm)",
    "WallThickness": "Wall thickness (mm)",
    "BottomThickness": "Bottom thickness (mm)",
    "LidInset": "Lid inset (mm)",
    "InnerClearance": "Inner clearance (mm)",
    "CornerRadius": "Surface corner radius (mm)",
}


def get_controller_object(doc: Any, create: bool = True) -> Any | None:
    if not hasattr(doc, "addObject"):
        return None
    existing = _find_object(doc, CONTROLLER_OBJECT_NAME, CONTROLLER_OBJECT_LABEL)
    if existing is not None or not create:
        if existing is not None:
            _ensure_controller_properties(existing)
            _attach_controller_proxy(existing)
            _attach_controller_view_provider(existing)
            _style_controller_object(existing)
        return existing
    controller = _create_object(doc, CONTROLLER_OBJECT_NAME, ("App::FeaturePython", "App::Feature"))
    _ensure_controller_properties(controller)
    _attach_controller_proxy(controller)
    _attach_controller_view_provider(controller)
    _style_controller_object(controller)
    return controller


def get_generated_group(doc: Any, create: bool = True) -> Any | None:
    if not hasattr(doc, "addObject"):
        return None
    existing = _find_object(doc, GENERATED_GROUP_NAME, GENERATED_GROUP_LABEL)
    if existing is not None or not create:
        return existing
    group = _create_object(
        doc,
        GENERATED_GROUP_NAME,
        ("App::DocumentObjectGroup", "App::DocumentObjectGroupPython", "App::Feature"),
    )
    _style_generated_group(group)
    return group


def write_project_state(doc: Any, state: dict[str, Any]) -> Any | None:
    controller = get_controller_object(doc, create=True)
    if controller is None:
        return None
    payload = json.dumps(deepcopy(state), sort_keys=True)
    _ensure_controller_properties(controller)
    setattr(controller, PROJECT_JSON_PROPERTY, payload)
    _sync_controller_properties(controller, state)
    _style_controller_object(controller)
    return controller


def read_project_state(doc: Any) -> dict[str, Any] | None:
    controller = get_controller_object(doc, create=False)
    if controller is None:
        return None
    payload = getattr(controller, PROJECT_JSON_PROPERTY, "")
    if not isinstance(payload, str) or not payload.strip():
        return None
    data = json.loads(payload)
    if not isinstance(data, dict):
        raise ValueError("Open Controller project JSON must decode to an object")
    return data


def has_project_state(doc: Any) -> bool:
    controller = get_controller_object(doc, create=False)
    if controller is None:
        return False
    payload = getattr(controller, PROJECT_JSON_PROPERTY, "")
    return isinstance(payload, str) and bool(payload.strip())


def group_generated_object(doc: Any, obj: Any) -> None:
    group = get_generated_group(doc, create=True)
    if group is None or obj is None:
        return
    if hasattr(group, "addObject"):
        try:
            group.addObject(obj)
            return
        except Exception:
            pass
    group_list = list(getattr(group, "Group", []))
    if obj not in group_list:
        group_list.append(obj)
        try:
            group.Group = group_list
        except Exception:
            pass


def iter_generated_objects(doc: Any) -> list[Any]:
    group = get_generated_group(doc, create=False)
    if group is not None:
        members = list(getattr(group, "Group", []))
        if members:
            return members
    objects = []
    for obj in getattr(doc, "Objects", []):
        name = str(getattr(obj, "Name", ""))
        label = str(getattr(obj, "Label", ""))
        if name in {CONTROLLER_OBJECT_NAME, GENERATED_GROUP_NAME}:
            continue
        if label in {CONTROLLER_OBJECT_LABEL, GENERATED_GROUP_LABEL}:
            continue
        if name.startswith("OCF_") or label.startswith("OCF_") or name in {"ControllerBody", "TopPlate"}:
            objects.append(obj)
    return objects


def clear_generated_group(doc: Any) -> None:
    if not hasattr(doc, "removeObject"):
        return
    for obj in list(iter_generated_objects(doc)):
        name = getattr(obj, "Name", "")
        if isinstance(name, str) and name:
            doc.removeObject(name)
    group = get_generated_group(doc, create=False)
    if group is not None:
        try:
            group.Group = []
        except Exception:
            pass


class ControllerProxy:
    def __init__(self, obj: Any) -> None:
        self.Object = obj
        obj.Proxy = self

    def execute(self, _obj: Any) -> None:
        return

    def onDocumentRestored(self, obj: Any) -> None:
        self.Object = obj
        _ensure_controller_properties(obj)
        _attach_controller_view_provider(obj)

    def __getstate__(self) -> dict[str, Any]:
        return {}

    def __setstate__(self, _state: dict[str, Any]) -> None:
        return


class ViewProviderController:
    def __init__(self, view_object: Any) -> None:
        self.ViewObject = view_object
        self.Object = getattr(view_object, "Object", None)
        view_object.Proxy = self

    def attach(self, view_object: Any) -> None:
        self.ViewObject = view_object
        self.Object = getattr(view_object, "Object", self.Object)

    def claimChildren(self) -> list[Any]:
        obj = self.Object or getattr(self.ViewObject, "Object", None)
        doc = getattr(obj, "Document", None)
        if doc is None:
            return []
        children = []
        generated = get_generated_group(doc, create=False)
        overlay = _find_object(doc, OVERLAY_OBJECT_NAME, OVERLAY_OBJECT_LABEL)
        for child in (generated, overlay):
            if child is not None and child not in children:
                children.append(child)
        return children

    def getDisplayModes(self, _obj: Any) -> list[str]:
        return ["Default"]

    def getDefaultDisplayMode(self) -> str:
        return "Default"

    def setDisplayMode(self, mode: str) -> str:
        return mode

    def onChanged(self, _vp: Any, _prop: str) -> None:
        return

    def updateData(self, _obj: Any, _prop: str) -> None:
        return

    def __getstate__(self) -> dict[str, Any]:
        return {}

    def __setstate__(self, _state: dict[str, Any]) -> None:
        return


def _sync_controller_properties(controller: Any, state: dict[str, Any]) -> None:
    controller_state = state.get("controller", {})
    meta = state.get("meta", {})
    surface = controller_state.get("surface") or {}
    setattr(controller, "ControllerId", str(controller_state.get("id", "")))
    setattr(controller, "TemplateId", str(meta.get("template_id") or ""))
    setattr(controller, "VariantId", str(meta.get("variant_id") or ""))
    setattr(controller, "SelectionId", str(meta.get("selection") or ""))
    setattr(controller, "Width", float(controller_state.get("width", 0.0) or 0.0))
    setattr(controller, "Depth", float(controller_state.get("depth", 0.0) or 0.0))
    setattr(controller, "Height", float(controller_state.get("height", 0.0) or 0.0))
    setattr(controller, "TopThickness", float(controller_state.get("top_thickness", 0.0) or 0.0))
    setattr(controller, "WallThickness", float(controller_state.get("wall_thickness", 0.0) or 0.0))
    setattr(controller, "BottomThickness", float(controller_state.get("bottom_thickness", 0.0) or 0.0))
    setattr(controller, "LidInset", float(controller_state.get("lid_inset", 0.0) or 0.0))
    setattr(controller, "InnerClearance", float(controller_state.get("inner_clearance", 0.0) or 0.0))
    setattr(controller, "SurfaceShape", str(surface.get("shape") or "rectangle"))
    setattr(controller, "CornerRadius", float(surface.get("corner_radius", 0.0) or 0.0))


def _ensure_controller_properties(controller: Any) -> None:
    properties = list(getattr(controller, "PropertiesList", []))
    if PROJECT_JSON_PROPERTY not in properties and hasattr(controller, "addProperty"):
        controller.addProperty("App::PropertyString", PROJECT_JSON_PROPERTY, MODEL_GROUP_NAME, "Open Controller project JSON")
    for name, description in _STRING_PROPERTIES.items():
        if name not in properties and hasattr(controller, "addProperty"):
            controller.addProperty("App::PropertyString", name, MODEL_GROUP_NAME, description)
    for name, description in _FLOAT_PROPERTIES.items():
        if name not in properties and hasattr(controller, "addProperty"):
            controller.addProperty("App::PropertyFloat", name, MODEL_GROUP_NAME, description)


def _attach_controller_proxy(controller: Any) -> None:
    proxy = getattr(controller, "Proxy", None)
    if isinstance(proxy, ControllerProxy):
        proxy.Object = controller
        return
    ControllerProxy(controller)


def _attach_controller_view_provider(controller: Any) -> None:
    view = getattr(controller, "ViewObject", None)
    if view is None:
        return
    if getattr(view, "Object", None) is None:
        try:
            view.Object = controller
        except Exception:
            pass
    proxy = getattr(view, "Proxy", None)
    if isinstance(proxy, ViewProviderController):
        proxy.attach(view)
        return
    try:
        ViewProviderController(view)
    except Exception:
        return


def _style_controller_object(controller: Any) -> None:
    if hasattr(controller, "Label"):
        controller.Label = CONTROLLER_OBJECT_LABEL
    view = getattr(controller, "ViewObject", None)
    if view is not None and hasattr(view, "Visibility"):
        view.Visibility = False
    if hasattr(controller, "setEditorMode"):
        for name in (PROJECT_JSON_PROPERTY,):
            try:
                controller.setEditorMode(name, 2)
            except Exception:
                continue


def _style_generated_group(group: Any) -> None:
    if hasattr(group, "Label"):
        group.Label = GENERATED_GROUP_LABEL
    view = getattr(group, "ViewObject", None)
    if view is not None and hasattr(view, "Visibility"):
        view.Visibility = False


def _find_object(doc: Any, object_name: str, label: str) -> Any | None:
    if hasattr(doc, "getObject"):
        try:
            obj = doc.getObject(object_name)
            if obj is not None:
                return obj
        except Exception:
            pass
    for obj in getattr(doc, "Objects", []):
        if getattr(obj, "Name", None) == object_name or getattr(obj, "Label", None) == label:
            return obj
    return None


def _create_object(doc: Any, name: str, object_types: tuple[str, ...]) -> Any:
    for object_type in object_types:
        try:
            return doc.addObject(object_type, name)
        except Exception:
            continue
    raise RuntimeError(f"Failed to create Open Controller document object '{name}'")
