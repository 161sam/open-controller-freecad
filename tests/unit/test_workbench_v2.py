from ocf_freecad.gui.panels.components_panel import ComponentsPanel
from ocf_freecad.gui.panels.constraints_panel import ConstraintsPanel
from ocf_freecad.gui.panels.create_panel import CreatePanel
from ocf_freecad.gui.panels.info_panel import InfoPanel
from ocf_freecad.gui.panels.layout_panel import LayoutPanel
from ocf_freecad.services.controller_service import ControllerService
from ocf_freecad.workbench import ProductWorkbenchPanel


class FakeDocument:
    def __init__(self) -> None:
        self.Objects = []
        self.recompute_count = 0

    def recompute(self) -> None:
        self.recompute_count += 1


def _select_combo_by_suffix(combo, suffix: str) -> None:
    for index, item in enumerate(combo.items):
        if item.endswith(suffix):
            combo.setCurrentIndex(index)
            return
    raise AssertionError(f"Missing combo entry with suffix {suffix!r}")


def test_create_panel_supports_template_and_variant_flow():
    doc = FakeDocument()
    service = ControllerService()
    panel = CreatePanel(doc, controller_service=service)

    _select_combo_by_suffix(panel.form["template"], "(encoder_module)")
    panel.handle_template_changed()
    _select_combo_by_suffix(panel.form["variant"], "(encoder_module_compact)")

    preview = panel.refresh_preview()
    state = panel.create_controller()

    assert "Components: 4" in preview
    assert state["meta"]["template_id"] == "encoder_module"
    assert state["meta"]["variant_id"] == "encoder_module_compact"


def test_layout_components_constraints_and_info_panels_share_document_state():
    doc = FakeDocument()
    service = ControllerService()
    service.create_controller(doc, {"id": "demo", "width": 200.0, "depth": 120.0})
    service.add_component(doc, "alps_ec11e15204a3")
    service.add_component(doc, "alps_ec11e15204a3")
    service.add_component(doc, "omron_b3f_1000")
    service.add_component(doc, "omron_b3f_1000")

    layout_panel = LayoutPanel(doc, controller_service=service)
    components_panel = ComponentsPanel(doc, controller_service=service)
    constraints_panel = ConstraintsPanel(doc, controller_service=service)
    info_panel = InfoPanel(doc, controller_service=service)

    layout_result = layout_panel.apply_auto_layout()
    report = constraints_panel.validate()
    component = components_panel.load_selected_component()
    components_panel.update_selected_component()
    info_text = info_panel.refresh()

    assert len(layout_result["placements"]) >= 1
    assert report["summary"]["error_count"] == 0
    assert component["id"] in info_text
    assert "Components: 4" in info_text


def test_product_workbench_panel_orchestrates_iteration_flow():
    doc = FakeDocument()
    service = ControllerService()
    workbench = ProductWorkbenchPanel(doc, controller_service=service)

    _select_combo_by_suffix(workbench.create_panel.form["template"], "(encoder_module)")
    workbench.create_panel.handle_template_changed()
    workbench.create_panel.create_controller()
    workbench.layout_panel.apply_auto_layout()
    workbench.components_panel.add_component()

    context = service.get_ui_context(doc)
    constraints_text = workbench.constraints_panel.form["results"].text
    info_text = workbench.info_panel.form["info"].text

    assert context["template_id"] == "encoder_module"
    assert context["validation"] is not None
    assert context["component_count"] == 5
    assert "Errors:" in constraints_text
    assert "Components: 5" in info_text
