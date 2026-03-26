from __future__ import annotations

from typing import Any

from ocf_freecad.freecad_api import gui as freecad_gui
from ocf_freecad.generator.controller_builder import ControllerBuilder
from ocf_freecad.layout.engine import LayoutEngine
from ocf_freecad.services.constraint_service import ConstraintService
from ocf_freecad.services.controller_state_service import (
    DEFAULT_CONTROLLER,
    DEFAULT_META,
    ControllerStateService,
)
from ocf_freecad.services.document_sync_service import DocumentSyncService
from ocf_freecad.services.library_service import LibraryService
from ocf_freecad.services.template_service import TemplateService
from ocf_freecad.services.variant_service import VariantService


class ControllerService:
    def __init__(
        self,
        library_service: LibraryService | None = None,
        template_service: TemplateService | None = None,
        variant_service: VariantService | None = None,
        layout_engine: LayoutEngine | None = None,
        constraint_service: ConstraintService | None = None,
        state_service: ControllerStateService | None = None,
        sync_service: DocumentSyncService | None = None,
    ) -> None:
        self.state_service = state_service or ControllerStateService(
            library_service=library_service,
            template_service=template_service,
            variant_service=variant_service,
            layout_engine=layout_engine,
            constraint_service=constraint_service,
        )
        self.sync_service = sync_service or DocumentSyncService(
            builder_factory=ControllerBuilder,
            gui_module=freecad_gui,
        )
        self.library_service = self.state_service.library_service
        self.template_service = self.state_service.template_service
        self.variant_service = self.state_service.variant_service
        self.layout_engine = self.state_service.layout_engine
        self.constraint_service = self.state_service.constraint_service

    def create_controller(self, doc: Any, controller_data: dict[str, Any] | None = None) -> dict[str, Any]:
        state = self.state_service.create_controller(doc, controller_data)
        self.sync_document(doc)
        return state

    def create_from_template(
        self,
        doc: Any,
        template_id: str,
        overrides: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        state = self.state_service.create_from_template(doc, template_id, overrides=overrides)
        self.sync_document(doc)
        return state

    def create_from_variant(
        self,
        doc: Any,
        variant_id: str,
        overrides: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        state = self.state_service.create_from_variant(doc, variant_id, overrides=overrides)
        self.sync_document(doc)
        return state

    def get_state(self, doc: Any) -> dict[str, Any]:
        return self.state_service.get_state(doc)

    def save_state(self, doc: Any, state: dict[str, Any]) -> None:
        self.state_service.save_state(doc, state)

    def list_library_components(self, category: str | None = None) -> list[dict[str, Any]]:
        return self.state_service.list_library_components(category=category)

    def list_templates(self, category: str | None = None) -> list[dict[str, Any]]:
        return self.state_service.list_templates(category=category)

    def list_variants(
        self,
        template_id: str | None = None,
        category: str | None = None,
        tag: str | None = None,
    ) -> list[dict[str, Any]]:
        return self.state_service.list_variants(template_id=template_id, category=category, tag=tag)

    def get_ui_context(self, doc: Any) -> dict[str, Any]:
        return self.state_service.get_ui_context(doc)

    def add_component(
        self,
        doc: Any,
        library_ref: str,
        component_id: str | None = None,
        component_type: str | None = None,
        x: float = 0.0,
        y: float = 0.0,
        rotation: float = 0.0,
        zone_id: str | None = None,
    ) -> dict[str, Any]:
        state = self.state_service.add_component(
            doc,
            library_ref=library_ref,
            component_id=component_id,
            component_type=component_type,
            x=x,
            y=y,
            rotation=rotation,
            zone_id=zone_id,
        )
        self.sync_document(doc)
        return state

    def move_component(
        self,
        doc: Any,
        component_id: str,
        x: float,
        y: float,
        rotation: float | None = None,
    ) -> dict[str, Any]:
        state = self.state_service.move_component(doc, component_id, x=x, y=y, rotation=rotation)
        self.sync_document(doc)
        return state

    def update_controller(self, doc: Any, updates: dict[str, Any]) -> dict[str, Any]:
        state = self.state_service.update_controller(doc, updates)
        self.sync_document(doc)
        return state

    def update_component(self, doc: Any, component_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        state = self.state_service.update_component(doc, component_id, updates)
        self.sync_document(doc)
        return state

    def select_component(self, doc: Any, component_id: str | None) -> dict[str, Any]:
        state = self.state_service.select_component(doc, component_id)
        self.refresh_document_visuals(doc, recompute=False)
        return state

    def get_component(self, doc: Any, component_id: str) -> dict[str, Any]:
        return self.state_service.get_component(doc, component_id)

    def auto_layout(
        self,
        doc: Any,
        strategy: str = "grid",
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        state, result = self.state_service.auto_layout(doc, strategy=strategy, config=config)
        self.sync_document(doc, state=state)
        return result

    def validate_layout(self, doc: Any, config: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.state_service.validate_layout(doc, config=config)

    def sync_document(self, doc: Any, state: dict[str, Any] | None = None) -> None:
        resolved_state = state if state is not None else self.state_service.get_state(doc)
        self.sync_service.sync_document(doc, resolved_state)

    def refresh_document_visuals(self, doc: Any, recompute: bool = False) -> None:
        selection = self.state_service.get_ui_context(doc).get("selection")
        self.sync_service.refresh_document_visuals(doc, selection=selection, recompute=recompute)
