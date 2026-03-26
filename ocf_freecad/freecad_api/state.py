from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

from ocf_freecad.freecad_api.metadata import get_document_data, has_document_data, set_document_data
from ocf_freecad.freecad_api.model import has_project_state, read_project_state, write_project_state

STATE_CONTAINER_NAME = "OCF_State"
STATE_CONTAINER_LABEL = "OCF State"
STATE_PROPERTY_NAME = "StateJson"
STATE_GROUP_NAME = "OpenController"
STATE_CACHE_KEY = "OCFStateCache"
STATE_CACHE_JSON_KEY = "OCFStateCacheJson"
LEGACY_STATE_KEY = "OCFState"
LEGACY_STATE_JSON_KEY = "OCF_State_JSON"


def get_state_container(doc: Any, create: bool = True) -> Any | None:
    if not hasattr(doc, "addObject"):
        return None
    existing = _find_state_container(doc)
    if existing is not None or not create:
        return existing
    container = _create_state_container(doc)
    _ensure_state_properties(container)
    _hide_state_container(container)
    return container


def has_persisted_state(doc: Any) -> bool:
    migrate_legacy_state(doc)
    if has_project_state(doc):
        return True
    return has_document_data(doc, STATE_CACHE_KEY) or has_document_data(doc, STATE_CACHE_JSON_KEY)


def read_state(doc: Any) -> dict[str, Any] | None:
    migrate_legacy_state(doc)
    state = read_project_state(doc)
    if isinstance(state, dict):
        return deepcopy(state)
    state = get_document_data(doc, STATE_CACHE_KEY)
    if isinstance(state, dict):
        return deepcopy(state)
    payload = get_document_data(doc, STATE_CACHE_JSON_KEY)
    if isinstance(payload, str) and payload.strip():
        return _load_json(payload)
    return None


def write_state(doc: Any, state: dict[str, Any]) -> None:
    normalized = deepcopy(state)
    payload = json.dumps(normalized, sort_keys=True)
    controller = write_project_state(doc, normalized)
    set_document_data(doc, STATE_CACHE_KEY, normalized)
    set_document_data(doc, STATE_CACHE_JSON_KEY, payload)
    if controller is None:
        set_document_data(doc, LEGACY_STATE_KEY, normalized)
        set_document_data(doc, LEGACY_STATE_JSON_KEY, payload)


def migrate_legacy_state(doc: Any) -> None:
    if has_project_state(doc):
        return
    container = get_state_container(doc, create=False)
    existing = getattr(container, STATE_PROPERTY_NAME, "") if container is not None else ""
    if isinstance(existing, str) and existing.strip():
        try:
            write_state(doc, _load_json(existing))
        except ValueError:
            return
        return
    state = get_document_data(doc, LEGACY_STATE_KEY)
    if isinstance(state, dict):
        write_state(doc, state)
        return
    payload = get_document_data(doc, LEGACY_STATE_JSON_KEY)
    if isinstance(payload, str) and payload.strip():
        try:
            write_state(doc, _load_json(payload))
        except ValueError:
            return


def _find_state_container(doc: Any) -> Any | None:
    if hasattr(doc, "getObject"):
        try:
            obj = doc.getObject(STATE_CONTAINER_NAME)
            if obj is not None:
                return obj
        except Exception:
            pass
    for obj in getattr(doc, "Objects", []):
        if getattr(obj, "Name", None) == STATE_CONTAINER_NAME or getattr(obj, "Label", None) == STATE_CONTAINER_LABEL:
            return obj
    return None


def _create_state_container(doc: Any) -> Any:
    for object_type in ("App::FeaturePython", "App::Feature"):
        try:
            return doc.addObject(object_type, STATE_CONTAINER_NAME)
        except Exception:
            continue
    raise RuntimeError("Failed to create Open Controller state container")


def _ensure_state_properties(container: Any) -> None:
    properties = list(getattr(container, "PropertiesList", []))
    if STATE_PROPERTY_NAME not in properties and hasattr(container, "addProperty"):
        container.addProperty("App::PropertyString", STATE_PROPERTY_NAME, STATE_GROUP_NAME, "Open Controller state JSON")


def _hide_state_container(container: Any) -> None:
    if hasattr(container, "Label"):
        container.Label = STATE_CONTAINER_LABEL
    view = getattr(container, "ViewObject", None)
    if view is not None and hasattr(view, "Visibility"):
        view.Visibility = False
    if hasattr(container, "setEditorMode"):
        for name in ("Label", STATE_PROPERTY_NAME):
            try:
                container.setEditorMode(name, 2)
            except Exception:
                continue


def _load_json(payload: str) -> dict[str, Any]:
    data = json.loads(payload)
    if not isinstance(data, dict):
        raise ValueError("Controller state JSON must decode to an object")
    return data
