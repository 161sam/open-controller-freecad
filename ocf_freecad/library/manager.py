from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from ocf_freecad.services.plugin_service import get_plugin_service_revision
from ocf_freecad.utils.yaml_io import load_yaml


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


class ComponentLibraryManager:
    def __init__(self, base_path: str | Path | None = None) -> None:
        self.base_path = Path(base_path) if base_path is not None else None
        self._components_by_id: dict[str, dict[str, Any]] = {}
        self._loaded = False
        self._loaded_revision = -1

    def load_all(self) -> None:
        components_by_id: dict[str, dict[str, Any]] = {}
        for source_path in self._source_paths():
            for yaml_file in sorted(source_path.glob("*.yaml")):
                payload = load_yaml(yaml_file)
                components = payload.get("components", [])
                if not isinstance(components, list):
                    raise ValueError(f"'components' must be a list in {yaml_file}")

                for component in components:
                    if not isinstance(component, dict):
                        raise ValueError(f"Invalid component entry in {yaml_file}: {component!r}")

                    component_id = component.get("id")
                    if not component_id or not isinstance(component_id, str):
                        raise ValueError(f"Component without valid 'id' in {yaml_file}")
                    if component_id in components_by_id:
                        raise ValueError(f"Duplicate component id detected: {component_id}")

                    self._validate_component_shape(component, yaml_file)
                    components_by_id[component_id] = deepcopy(component)

        self._components_by_id = components_by_id
        self._loaded = True
        self._loaded_revision = 0 if self.base_path is not None else get_plugin_service_revision()

    def _source_paths(self) -> list[Path]:
        if self.base_path is not None:
            if not self.base_path.exists():
                raise FileNotFoundError(f"Component library path not found: {self.base_path}")
            return [self.base_path]

        from ocf_freecad.services.plugin_service import get_plugin_service

        sources = get_plugin_service().component_sources()
        if sources:
            return sources

        fallback = Path(__file__).resolve().parent / "components"
        if not fallback.exists():
            raise FileNotFoundError(f"Component library path not found: {fallback}")
        return [fallback]

    def _validate_component_shape(self, component: dict[str, Any], source: Path) -> None:
        required = [
            "id",
            "category",
            "manufacturer",
            "part_number",
            "description",
            "mechanical",
            "electrical",
            "pcb",
            "ocf",
        ]
        component_id = component.get("id", "<unknown>")
        for field in required:
            if field not in component:
                raise ValueError(
                    f"Missing required field '{field}' in component '{component_id}' from {source}"
                )

    def _ensure_loaded(self) -> None:
        current_revision = 0 if self.base_path is not None else get_plugin_service_revision()
        if not self._loaded or self._loaded_revision != current_revision:
            self.load_all()

    def get_component(self, component_id: str) -> dict[str, Any]:
        self._ensure_loaded()
        try:
            return deepcopy(self._components_by_id[component_id])
        except KeyError as exc:
            raise KeyError(f"Unknown component id: {component_id}") from exc

    def list_components(self, category: str | None = None) -> list[dict[str, Any]]:
        self._ensure_loaded()
        items = list(self._components_by_id.values())
        if category is not None:
            items = [item for item in items if item.get("category") == category]
        return [deepcopy(item) for item in items]

    def resolve_component(
        self,
        library_ref: str,
        overrides: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        base_component = self.get_component(library_ref)
        if overrides is None:
            return base_component
        return _deep_merge(base_component, overrides)
