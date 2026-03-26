from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from ocf_freecad.services.plugin_service import get_plugin_service_revision
from ocf_freecad.variants.loader import VariantLoader


class VariantRegistry:
    def __init__(self, base_path: str | Path | None = None, loader: VariantLoader | None = None) -> None:
        self.base_path = Path(base_path) if base_path is not None else None
        self.loader = loader or VariantLoader()
        self._variants: dict[str, dict[str, Any]] = {}
        self._loaded = False
        self._loaded_revision = -1

    def load_all(self) -> None:
        variants: dict[str, dict[str, Any]] = {}
        for source_path in self._source_paths():
            for yaml_file in sorted(source_path.glob("*.yaml")):
                variant = self.loader.load(yaml_file).to_dict()
                variant_id = variant["variant"]["id"]
                if variant_id in variants:
                    raise ValueError(f"Duplicate variant id detected: {variant_id}")
                variants[variant_id] = variant

        self._variants = variants
        self._loaded = True
        self._loaded_revision = 0 if self.base_path is not None else get_plugin_service_revision()

    def _source_paths(self) -> list[Path]:
        if self.base_path is not None:
            if not self.base_path.exists():
                raise FileNotFoundError(f"Variant library path not found: {self.base_path}")
            return [self.base_path]

        from ocf_freecad.services.plugin_service import get_plugin_service

        sources = get_plugin_service().variant_sources()
        if sources:
            return sources

        fallback = Path(__file__).resolve().parent / "library"
        if not fallback.exists():
            raise FileNotFoundError(f"Variant library path not found: {fallback}")
        return [fallback]

    def _ensure_loaded(self) -> None:
        current_revision = 0 if self.base_path is not None else get_plugin_service_revision()
        if not self._loaded or self._loaded_revision != current_revision:
            self.load_all()

    def list_variants(
        self,
        template_id: str | None = None,
        category: str | None = None,
        tag: str | None = None,
    ) -> list[dict[str, Any]]:
        self._ensure_loaded()
        items = list(self._variants.values())
        if template_id is not None:
            items = [item for item in items if item["variant"].get("template_id") == template_id]
        if category is not None:
            items = [item for item in items if item["variant"].get("category") == category]
        if tag is not None:
            items = [item for item in items if tag in item["variant"].get("tags", [])]
        return [deepcopy(item) for item in items]

    def get_variant(self, variant_id: str) -> dict[str, Any]:
        self._ensure_loaded()
        try:
            return deepcopy(self._variants[variant_id])
        except KeyError as exc:
            raise KeyError(f"Unknown variant id: {variant_id}") from exc
