# Feature Improvement Review — Open Controller Workbench UI

**Date:** 2026-03-28
**Scope:** Existing features only. No new features. Stability, UX, and maintainability.

---

## 1. What Is Already Good

- **Stepper shell** ([workbench.py:681](../../ocw_workbench/workbench.py)): clean `QStackedWidget` base, clear step buttons, good shell ↔ panel separation.
- **Service injection** in all panels: consistent constructor pattern with sensible defaults.
- **`_common.py`** ([panels/_common.py](../../ocw_workbench/gui/panels/_common.py)): solid UI utility layer — `configure_layout`, `set_size_policy`, Fallback classes for non-Qt environments.
- **Overlay system** (Coin3D via `OverlayRenderer`): FreeCAD-correct render path selection.
- **All panels have fallback dicts**: testable without FreeCAD/Qt.
- **`ConstraintsPanel`**: summary cards, QTreeWidget with 4 columns — structurally clear.
- **`LayoutPanel`**: Settings form + Primary Action + collapsible Helpers — good layering.
- **`SetMinAndMaxSize` constraint**: set consistently, prevents layout explosions.
- **`wrap_widget_in_scroll_area()`**: used consistently in all panels.
- **Stylesheet scope**: limited to `OCWWorkbenchShell` — no global CSS bleed.

---

## 2. Biggest Problems

### BUG (critical): Orphaned Widgets in CreatePanel

**File:** [`create_panel.py:916–919`](../../ocw_workbench/gui/panels/create_panel.py)

Only the combo boxes are added to the layout:

```python
selection_form.addRow("Template", template)
selection_form.addRow("Variant", variant)
```

The following widgets are **created, connected, and populated with data — but never inserted into any layout:**

- `template_summary` — template description text (always invisible)
- `variant_summary` — variant description text (always invisible)
- `favorite_template_button` — "Favorite" button (not clickable, not visible)
- `favorite_variant_button` — "Favorite" button (not clickable, not visible)
- `favorite_template_status` / `favorite_variant_status` — status labels (redundant with ★ in combo)

**Impact:** Users cannot read template descriptions or set favorites, even though all backend code works correctly.

### UX: `active_project` buried in collapsed section

**File:** [`create_panel.py:941–948`](../../ocw_workbench/gui/panels/create_panel.py)

The `active_project` label (shows: "template X | 3 components | layout grid | ...") is inside `document_actions_section`, which is **collapsed by default**. Users cannot see whether a project is already loaded.

### Fragile level detector in `set_status()`

**File:** [`workbench.py:431–436`](../../ocw_workbench/workbench.py)

Level is determined by string matching:
```python
level = "error" if message.lower().startswith("could not") ...
```
Any text change in a panel status message breaks the feedback level.

### Inefficiency: `ControllerService()` instantiated per call

**File:** [`workbench.py:158`](../../ocw_workbench/workbench.py)

`_FavoriteComponentCommand._favorite_component()` creates a new `ControllerService()` on every call, transitively initializing all sub-services.

### Inline stylesheet is 250+ lines of Python string

**File:** [`workbench.py:1182`](../../ocw_workbench/workbench.py)

No IDE syntax highlighting, no CSS tooling, hard to maintain.

---

## 3. Prioritized Improvement Fields

### HIGH — Fix now

| Problem | File | Line |
|---|---|---|
| Orphaned widgets: template/variant summary + favorite buttons | `create_panel.py` | 900–920 |
| `active_project` always visible (not collapsed) | `create_panel.py` | 941–948 |

### MEDIUM — Fix next

| Problem | File | Line |
|---|---|---|
| `set_status()` level heuristic → explicit level parameter | `workbench.py` | 431 |
| `LayoutPanel`: validation status out of collapsible | `layout_panel.py` | 386–401 |
| `ConstraintsPanel`: `results_overview` + `next_step` redundant outputs | `constraints_panel.py` | 375–376 |

### LOW — Fix later

| Problem | File | Line |
|---|---|---|
| `_FavoriteComponentCommand` creates new service per call | `workbench.py` | 158 |
| `favorite_template_status` / `favorite_variant_status` labels redundant | `create_panel.py` | 861–866 |
| Extract stylesheet from Python string | `workbench.py` | 1182 |

---

## 4. Recommended Implementation Order

### Package 1 (this session) — CreatePanel visible context
1. Fix orphaned widgets: template_summary, variant_summary, favorite buttons
2. Move `active_project` out of collapsed section

### Package 2 — Shell feedback stability
3. Fix `set_status()` level detection

### Package 3 — Layout/Validate panel improvements
4. LayoutPanel: current state inline
5. ConstraintsPanel: reduce redundancy

### Package 4 — Code quality
6. `_FavoriteComponentCommand` optimization
7. Stylesheet extraction

---

## 5. FreeCAD Workbench Fit Assessment

- Stepper flow maps well to FreeCAD task panels. ✓
- Dock widget management is correct for FreeCAD dock areas. ✓
- Overlay via Coin3D is the correct FreeCAD approach. ✓
- 3D interaction (drag, place) hooks into the view correctly. ✓
- **Concern:** Dock height — many collapsed sections still take vertical space in narrow FreeCAD dock areas.
- **Concern:** No visible "first run" hero state — empty project + Create panel doesn't strongly guide new users.
- The `InfoPanel` embedded via splitter in the Create step is logical but makes the Create step tall.
