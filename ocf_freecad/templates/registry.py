from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from ocf_freecad.services.plugin_service import get_plugin_service_revision
from ocf_freecad.templates.loader import TemplateLoader


class TemplateRegistry:
    def __init__(self, base_path: str | Path | None = None, loader: TemplateLoader | None = None) -> None:
        self.base_path = Path(base_path) if base_path is not None else None
        self.loader = loader or TemplateLoader()
        self._templates: dict[str, dict[str, Any]] = {}
        self._loaded = False
        self._loaded_revision = -1

    def load_all(self) -> None:
        templates: dict[str, dict[str, Any]] = {}
        for source_path in self._source_paths():
            for yaml_file in sorted(source_path.glob("*.yaml")):
                template = self.loader.load(yaml_file).to_dict()
                template_id = template["template"]["id"]
                if template_id in templates:
                    raise ValueError(f"Duplicate template id detected: {template_id}")
                templates[template_id] = template
        self._templates = templates
        self._loaded = True
        self._loaded_revision = 0 if self.base_path is not None else get_plugin_service_revision()

    def _source_paths(self) -> list[Path]:
        if self.base_path is not None:
            if not self.base_path.exists():
                raise FileNotFoundError(f"Template library path not found: {self.base_path}")
            return [self.base_path]

        from ocf_freecad.services.plugin_service import get_plugin_service

        sources = get_plugin_service().template_sources()
        if sources:
            return sources

        fallback = Path(__file__).resolve().parent / "library"
        if not fallback.exists():
            raise FileNotFoundError(f"Template library path not found: {fallback}")
        return [fallback]

    def _ensure_loaded(self) -> None:
        current_revision = 0 if self.base_path is not None else get_plugin_service_revision()
        if not self._loaded or self._loaded_revision != current_revision:
            self.load_all()

    def list_templates(self, category: str | None = None) -> list[dict[str, Any]]:
        self._ensure_loaded()
        items = list(self._templates.values())
        if category is not None:
            items = [item for item in items if item["template"].get("category") == category]
        return [deepcopy(item) for item in items]

    def get_template(self, template_id: str) -> dict[str, Any]:
        self._ensure_loaded()
        try:
            return deepcopy(self._templates[template_id])
        except KeyError as exc:
            raise KeyError(f"Unknown template id: {template_id}") from exc
