from __future__ import annotations

from ocw_workbench.gui.runtime import icon_path


class BaseCommand:
    ICON_NAME = "default"

    def icon_name(self) -> str:
        return self.ICON_NAME

    def resources(self, menu_text: str, tooltip: str, accel: str | None = None) -> dict[str, str]:
        payload = {
            "MenuText": menu_text,
            "ToolTip": tooltip,
            "Pixmap": icon_path(self.icon_name()),
        }
        if accel:
            payload["Accel"] = accel
        return payload

    def GetResources(self):
        return self.resources("Base Command", "Base Command")

    def IsActive(self):
        return True

    @staticmethod
    def _has_controller() -> bool:
        """Return True when an active FreeCAD document with an OCW controller exists."""
        try:
            import FreeCAD as App
            from ocw_workbench.freecad_api.metadata import get_document_data
            doc = App.ActiveDocument
            if doc is None:
                return False
            # Fast path: check runtime cache; avoids disk read
            return isinstance(get_document_data(doc, "OCWStateCache"), dict)
        except Exception:
            return False

    @staticmethod
    def _has_selection() -> bool:
        """Return True when an active controller exists and a component is selected."""
        try:
            import FreeCAD as App
            from ocw_workbench.freecad_api.metadata import get_document_data
            doc = App.ActiveDocument
            if doc is None:
                return False
            state = get_document_data(doc, "OCWStateCache")
            if not isinstance(state, dict):
                return False
            return state.get("meta", {}).get("selection") is not None
        except Exception:
            return False
