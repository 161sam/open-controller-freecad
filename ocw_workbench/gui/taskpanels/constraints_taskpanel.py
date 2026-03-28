from __future__ import annotations

from typing import Any

from ocw_workbench.gui.panels._common import (
    build_panel_container,
    configure_text_panel,
    finalize_panel_widget,
    load_qt,
)
from ocw_workbench.services.controller_service import ControllerService


class ConstraintsTaskPanel:
    def __init__(self, doc: Any, controller_service: ControllerService | None = None) -> None:
        self.doc = doc
        self.controller_service = controller_service or ControllerService()
        self.form = _build_constraints_form()

    def validate(self) -> dict[str, Any]:
        report = self.controller_service.validate_layout(self.doc)
        _set_text(self.form["results"], _format_report(report))
        return report

    def accept(self) -> bool:
        self.validate()
        return True


def _build_constraints_form() -> dict[str, Any]:
    _qtcore, _qtgui, qtwidgets = load_qt()
    if qtwidgets is None:
        return {"results": _FallbackText()}

    widget, layout = build_panel_container(qtwidgets, spacing=12, margins=(12, 12, 12, 12))
    results = qtwidgets.QPlainTextEdit()
    configure_text_panel(results, max_height=180)
    layout.addWidget(results)
    finalize_panel_widget(widget)
    return {"widget": widget, "results": results}


def _format_report(report: dict[str, Any]) -> str:
    lines = [
        f"Errors: {report['summary']['error_count']}",
        f"Warnings: {report['summary']['warning_count']}",
        "",
    ]
    for item in report["errors"]:
        lines.append(f"[ERROR] {item['rule_id']}: {item['message']}")
    for item in report["warnings"]:
        lines.append(f"[WARN] {item['rule_id']}: {item['message']}")
    return "\n".join(lines)


def _set_text(widget: Any, value: str) -> None:
    if hasattr(widget, "setPlainText"):
        widget.setPlainText(value)
    else:
        widget.text = value


class _FallbackText:
    def __init__(self) -> None:
        self.text = ""
