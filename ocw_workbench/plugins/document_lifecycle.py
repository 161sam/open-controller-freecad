from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from ocw_workbench.freecad_api.metadata import get_document_data, set_document_data
from ocw_workbench.freecad_api.state import has_persisted_state, read_state, write_state
from ocw_workbench.plugins.activation import activate_plugin
from ocw_workbench.services.plugin_service import get_plugin_service

DOCUMENT_BINDING_KEY = "OCWDocumentBinding"
DEFAULT_DOCUMENT_TYPE = "generator_workbench_project"
LEGACY_DEFAULT_PLUGIN_ID = "midicontroller"


def get_document_plugin_binding(doc: Any) -> dict[str, str] | None:
    state = read_state(doc) if has_persisted_state(doc) else None
    binding = _binding_from_state(state)
    if binding is not None:
        set_document_data(doc, DOCUMENT_BINDING_KEY, binding)
        return binding
    cached = get_document_data(doc, DOCUMENT_BINDING_KEY)
    if isinstance(cached, dict):
        normalized = _normalize_binding(cached)
        if normalized is not None:
            return normalized
    inferred_plugin_id = infer_document_plugin_id(doc)
    if inferred_plugin_id is None:
        return None
    plugin = _require_domain_plugin(inferred_plugin_id)
    binding = {
        "plugin_id": plugin.plugin_id,
        "plugin_version": plugin.version,
        "document_type": DEFAULT_DOCUMENT_TYPE,
    }
    set_document_data(doc, DOCUMENT_BINDING_KEY, binding)
    return binding


def get_document_plugin_id(doc: Any) -> str | None:
    binding = get_document_plugin_binding(doc)
    return None if binding is None else binding["plugin_id"]


def list_domain_plugins() -> list[dict[str, str]]:
    registry = get_plugin_service().registry()
    plugins = []
    for plugin in registry.get_domain_plugins():
        plugins.append(
            {
                "id": plugin.plugin_id,
                "name": plugin.name,
                "version": plugin.version,
                "domain_type": str(plugin.domain_type or plugin.plugin_id),
            }
        )
    return plugins


def can_switch_plugin_for_document(doc: Any, plugin_id: str) -> bool:
    existing = get_document_plugin_binding(doc)
    if existing is None:
        return True
    if existing["plugin_id"] == plugin_id:
        return True
    return document_is_plugin_switchable(doc)


def get_document_plugin_status(doc: Any) -> dict[str, Any]:
    binding = get_document_plugin_binding(doc)
    active_plugin = get_plugin_service().registry().get_active_plugin()
    switchable = document_is_plugin_switchable(doc)
    state = read_state(doc) if has_persisted_state(doc) else None
    has_state = isinstance(state, dict)
    meaningful = _has_meaningful_state(state) if isinstance(state, dict) else False
    if binding is not None and meaningful:
        mode = "bound"
    elif binding is not None and switchable:
        mode = "switchable"
    elif binding is None and has_state:
        mode = "legacy_unbound"
    else:
        mode = "empty"
    bound_plugin_id = binding["plugin_id"] if binding is not None else None
    active_plugin_id = active_plugin.plugin_id if active_plugin is not None else None
    if mode == "bound":
        message = f"Document is bound to domain '{bound_plugin_id}'. Domain switch is blocked."
    elif mode == "switchable":
        message = (
            f"Domain '{bound_plugin_id or active_plugin_id or 'none'}' is active. "
            "The document is still switchable until a project is created."
        )
    elif mode == "legacy_unbound":
        message = "Legacy document detected without explicit plugin binding. A domain can still be selected."
    else:
        message = "Empty document. Select a domain before creating a project."
    return {
        "mode": mode,
        "bound": bound_plugin_id is not None,
        "switchable": switchable,
        "active_plugin_id": active_plugin_id,
        "bound_plugin_id": bound_plugin_id,
        "binding": deepcopy(binding) if binding is not None else None,
        "message": message,
    }


def bind_document_to_plugin(
    doc: Any,
    plugin_id: str,
    *,
    allow_rebind: bool = False,
    document_type: str = DEFAULT_DOCUMENT_TYPE,
) -> dict[str, str]:
    plugin = _require_domain_plugin(plugin_id)
    existing = get_document_plugin_binding(doc)
    if existing is not None and existing["plugin_id"] != plugin_id and not (allow_rebind or document_is_plugin_switchable(doc)):
        raise ValueError(
            f"Document '{getattr(doc, 'Name', '<unnamed>')}' is already bound to plugin "
            f"'{existing['plugin_id']}' and cannot be switched to '{plugin_id}'."
        )
    binding = {
        "plugin_id": plugin.plugin_id,
        "plugin_version": plugin.version,
        "document_type": str(document_type or DEFAULT_DOCUMENT_TYPE),
    }
    if has_persisted_state(doc):
        state = read_state(doc) or {"controller": {}, "components": [], "meta": {}}
        state = merge_document_plugin_binding(state, binding)
        write_state(doc, state)
    set_document_data(doc, DOCUMENT_BINDING_KEY, binding)
    return binding


def activate_plugin_for_document(
    doc: Any,
    requested_plugin_id: str | None = None,
    *,
    bind_if_missing: bool = True,
) -> dict[str, str]:
    binding = get_document_plugin_binding(doc)
    target_plugin_id = requested_plugin_id or (binding["plugin_id"] if binding is not None else None)
    if target_plugin_id is None:
        active_plugin = get_plugin_service().registry().get_active_plugin()
        target_plugin_id = active_plugin.plugin_id if active_plugin is not None else None
    if target_plugin_id is None:
        raise RuntimeError("No active domain plugin is available for the current document.")
    if binding is not None and binding["plugin_id"] != target_plugin_id and not can_switch_plugin_for_document(doc, target_plugin_id):
        raise ValueError(
            f"Document '{getattr(doc, 'Name', '<unnamed>')}' is bound to plugin '{binding['plugin_id']}' "
            f"and cannot activate '{target_plugin_id}'."
        )
    plugin = activate_plugin(target_plugin_id)
    resolved_binding = {
        "plugin_id": plugin.plugin_id,
        "plugin_version": plugin.version,
        "document_type": binding["document_type"] if binding is not None else DEFAULT_DOCUMENT_TYPE,
    }
    if bind_if_missing or binding is not None or document_is_plugin_switchable(doc):
        resolved_binding = bind_document_to_plugin(
            doc,
            plugin.plugin_id,
            allow_rebind=document_is_plugin_switchable(doc),
            document_type=resolved_binding["document_type"],
        )
    return resolved_binding


def select_domain_plugin_for_document(doc: Any, plugin_id: str) -> dict[str, Any]:
    if not can_switch_plugin_for_document(doc, plugin_id):
        status = get_document_plugin_status(doc)
        bound_plugin_id = status.get("bound_plugin_id") or "<unknown>"
        raise ValueError(
            f"Document '{getattr(doc, 'Name', '<unnamed>')}' is already bound to domain '{bound_plugin_id}'. "
            "Create a new document to switch domains."
        )
    activate_plugin_for_document(doc, requested_plugin_id=plugin_id, bind_if_missing=True)
    return get_document_plugin_status(doc)


def merge_document_plugin_binding(
    state: dict[str, Any],
    binding: dict[str, Any] | None,
) -> dict[str, Any]:
    merged = deepcopy(state)
    meta = merged.setdefault("meta", {})
    if binding is None:
        return merged
    plugin_id = str(binding.get("plugin_id") or "").strip()
    plugin_version = str(binding.get("plugin_version") or "").strip()
    document_type = str(binding.get("document_type") or DEFAULT_DOCUMENT_TYPE).strip() or DEFAULT_DOCUMENT_TYPE
    meta["plugin_id"] = plugin_id or None
    meta["plugin_version"] = plugin_version or None
    meta["document_type"] = document_type
    return merged


def infer_document_plugin_id(doc: Any) -> str | None:
    state = read_state(doc) if has_persisted_state(doc) else None
    if not isinstance(state, dict):
        return None
    meta = state.get("meta", {})
    if isinstance(meta, dict):
        for key in ("template_id", "variant_id"):
            inferred = _infer_from_identifier(meta.get(key), root_kind="templates" if key == "template_id" else "variants")
            if inferred is not None:
                return inferred
    components = state.get("components", [])
    if isinstance(components, list):
        for component in components:
            if not isinstance(component, dict):
                continue
            inferred = _infer_from_identifier(component.get("library_ref"), root_kind="components")
            if inferred is not None:
                return inferred
    if _has_meaningful_state(state):
        registry = get_plugin_service().registry()
        if registry.has_plugin(LEGACY_DEFAULT_PLUGIN_ID):
            return LEGACY_DEFAULT_PLUGIN_ID
    return None


def document_is_plugin_switchable(doc: Any) -> bool:
    state = read_state(doc) if has_persisted_state(doc) else None
    if not isinstance(state, dict):
        objects = list(getattr(doc, "Objects", []))
        return len(objects) == 0
    return not _has_meaningful_state(state)


def _binding_from_state(state: dict[str, Any] | None) -> dict[str, str] | None:
    if not isinstance(state, dict):
        return None
    meta = state.get("meta")
    if not isinstance(meta, dict):
        return None
    return _normalize_binding(meta)


def _normalize_binding(payload: dict[str, Any]) -> dict[str, str] | None:
    plugin_id = str(payload.get("plugin_id") or "").strip()
    if not plugin_id:
        return None
    plugin_version = str(payload.get("plugin_version") or "").strip()
    document_type = str(payload.get("document_type") or DEFAULT_DOCUMENT_TYPE).strip() or DEFAULT_DOCUMENT_TYPE
    return {
        "plugin_id": plugin_id,
        "plugin_version": plugin_version,
        "document_type": document_type,
    }


def _require_domain_plugin(plugin_id: str):
    registry = get_plugin_service().registry()
    if not registry.has_plugin(plugin_id):
        raise KeyError(f"Unknown document plugin id: {plugin_id}")
    plugin = registry.plugin(plugin_id)
    if plugin.plugin_type != "domain":
        raise ValueError(f"Plugin '{plugin_id}' is not a domain plugin")
    return plugin


def _infer_from_identifier(identifier: Any, *, root_kind: str) -> str | None:
    value = str(identifier or "").strip()
    if not value:
        return None
    if "." in value:
        prefix = value.split(".", 1)[0]
        registry = get_plugin_service().registry()
        if registry.has_plugin(prefix):
            plugin = registry.plugin(prefix)
            if plugin.plugin_type == "domain":
                return prefix
    filename = f"{Path(value).stem}.yaml"
    registry = get_plugin_service().registry()
    matches: list[str] = []
    for plugin in registry.get_domain_plugins():
        root = {
            "templates": plugin.template_root(),
            "variants": plugin.variant_root(),
            "components": plugin.component_root(),
        }.get(root_kind)
        if root is not None and (root / filename).exists():
            matches.append(plugin.plugin_id)
    if len(matches) == 1:
        return matches[0]
    return None


def _has_meaningful_state(state: dict[str, Any]) -> bool:
    components = state.get("components", [])
    if isinstance(components, list) and len(components) > 0:
        return True
    meta = state.get("meta", {})
    if not isinstance(meta, dict):
        return False
    if meta.get("template_id") or meta.get("variant_id"):
        return True
    overrides = meta.get("overrides")
    if isinstance(overrides, dict) and overrides:
        return True
    parameters = meta.get("parameters")
    if isinstance(parameters, dict):
        values = parameters.get("values")
        if isinstance(values, dict) and values:
            return True
    return False
