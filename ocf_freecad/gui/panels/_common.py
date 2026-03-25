from __future__ import annotations

from typing import Any


def load_qt() -> tuple[Any, Any, Any]:
    try:
        from PySide2 import QtCore, QtGui, QtWidgets

        return QtCore, QtGui, QtWidgets
    except ImportError:
        try:
            from PySide import QtCore, QtGui

            return QtCore, QtGui, QtGui
        except ImportError:
            return None, None, None


def set_combo_items(combo: Any, items: list[str]) -> None:
    if hasattr(combo, "clear"):
        combo.clear()
    if hasattr(combo, "addItems"):
        combo.addItems(items)
    else:
        combo.items = list(items)
        combo.index = 0


def current_text(combo: Any) -> str:
    if hasattr(combo, "currentText"):
        return str(combo.currentText())
    return combo.items[combo.index] if combo.items else ""


def set_current_text(combo: Any, value: str) -> bool:
    if hasattr(combo, "findText") and hasattr(combo, "setCurrentIndex"):
        index = combo.findText(value)
        if index >= 0:
            combo.setCurrentIndex(index)
            return True
        return False
    if value in getattr(combo, "items", []):
        combo.index = combo.items.index(value)
        return True
    return False


def set_text(widget: Any, value: str) -> None:
    if hasattr(widget, "setPlainText"):
        widget.setPlainText(value)
        return
    if hasattr(widget, "setText"):
        widget.setText(value)
        return
    widget.text = value


def text_value(widget: Any) -> str:
    if hasattr(widget, "toPlainText"):
        return str(widget.toPlainText())
    if hasattr(widget, "text"):
        attr = widget.text
        if callable(attr):
            result = attr()
            return result if isinstance(result, str) else str(result)
        return str(attr)
    return str(getattr(widget, "text", ""))


def set_value(widget: Any, value: float) -> None:
    if hasattr(widget, "setValue"):
        widget.setValue(value)
        return
    widget.value = float(value)


def widget_value(widget: Any) -> float:
    if hasattr(widget, "value"):
        attr = widget.value
        if callable(attr):
            result = attr()
            return float(result) if not isinstance(result, float) else result
        return float(attr)
    return float(widget.value)


def set_enabled(widget: Any, enabled: bool) -> None:
    if hasattr(widget, "setEnabled"):
        widget.setEnabled(enabled)
        return
    widget.enabled = bool(enabled)


def set_label_text(widget: Any, value: str) -> None:
    if hasattr(widget, "setText"):
        widget.setText(value)
        return
    widget.text = value


class FallbackSignal:
    def __init__(self) -> None:
        self._callbacks: list[Any] = []

    def connect(self, callback: Any) -> None:
        self._callbacks.append(callback)

    def emit(self, *args: Any, **kwargs: Any) -> None:
        for callback in list(self._callbacks):
            callback(*args, **kwargs)


class FallbackCombo:
    def __init__(self, items: list[str] | None = None) -> None:
        self.items = list(items or [])
        self.index = 0
        self.enabled = True
        self.currentIndexChanged = FallbackSignal()

    def clear(self) -> None:
        self.items = []
        self.index = 0

    def addItems(self, items: list[str]) -> None:
        self.items.extend(items)

    def currentText(self) -> str:
        return self.items[self.index] if self.items else ""

    def findText(self, value: str) -> int:
        try:
            return self.items.index(value)
        except ValueError:
            return -1

    def setCurrentIndex(self, index: int) -> None:
        if not self.items:
            self.index = 0
        else:
            self.index = max(0, min(index, len(self.items) - 1))
        self.currentIndexChanged.emit(self.index)


class FallbackText:
    def __init__(self, text: str = "") -> None:
        self.text = text

    def setPlainText(self, value: str) -> None:
        self.text = value

    def setText(self, value: str) -> None:
        self.text = value

    def toPlainText(self) -> str:
        return self.text


class FallbackValue:
    def __init__(self, value: float = 0.0) -> None:
        self.value = float(value)
        self.enabled = True

    def setValue(self, value: float) -> None:
        self.value = float(value)


class FallbackButton:
    def __init__(self, text: str = "") -> None:
        self.text = text
        self.enabled = True
        self.clicked = FallbackSignal()

    def setEnabled(self, enabled: bool) -> None:
        self.enabled = bool(enabled)


class FallbackLabel(FallbackText):
    pass
