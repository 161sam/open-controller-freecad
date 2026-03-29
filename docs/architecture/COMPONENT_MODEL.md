# OCW Component Model

## Current Domain Split

- `Plugin`: extension packaging and source registration. Plugins contribute component libraries, templates, variants, exporters, layouts, and constraints. They are an extension mechanism, not the primary project model.
- `Template`: a controller-level project blueprint. A template defines controller defaults, zones, layout defaults, parameter bindings, and optional starter components.
- `Component`: an instantiated control element inside one controller state. Components carry placement, type, library reference, and mechanical/electrical metadata.

## Practical Meaning

- Plugins answer: where do templates, component libraries, and exporters come from?
- Templates answer: what complete controller configuration should be generated?
- Components answer: which concrete controls exist in this controller document right now?

## Template vs Component

- A `4x4 pad grid` is a template-level configuration plus generated component instances.
- In state terms it is not one component. It becomes many `pad` components placed from template bindings and layout rules.
- In the FreeCAD tree this should therefore appear as many component objects, optionally grouped under `OCW_Components`, not just as one hole pattern.

## FreeCAD Document Model

- `OCW_Controller`: persistent project/state object
- `OCW_Generated`: generated model root
- `OCW_ControllerBody`: visible body solid
- `OCW_TopPlate` or `OCW_TopPlateCut`: visible plate solid
- `OCW_Components`: generated component group
- `OCW_Group_<group_id>`: optional subgroup inside `OCW_Components` for grouped component sets
- `OCW_Component_<id>`: one visible document object per component instance

Component groups do not create geometry. They exist only as tree structure so grouped template output such as pad matrices remains visible and navigable in the FreeCAD document.

## Geometry Relationship

- Controller body and top plate remain generated from controller state.
- Plate cutouts are still derived from component mechanical cutout geometry.
- Visible component objects are derived from the same component mechanical source. Key control types (`button`, `encoder`, `display`, `fader`, `pad`, `rgb_button`) now build type-specific solids from library mechanical metadata; unknown types still fall back to keepout-based extrusion.
- Component document objects store stable metadata (`OCWComponentId`, `OCWComponentType`, `OCWLibraryRef`, `OCWGroupId`, `OCWGroupRole`, placement fields) to support later editing and selection mapping.
