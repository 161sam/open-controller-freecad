# Core Naming Cleanup

## Scope

This cleanup keeps behavior unchanged and only improves generic naming at stable core boundaries.

## Preferred Generic Core Terms

Use these terms in generic core code when possible:

- `project`
- `document`
- `generated`
- `component`
- `group`
- `template`
- `variant`
- `plugin`
- `placement`
- `geometry`

## Legacy Terms Kept As Compatibility Aliases

These names still exist because they are already used across persisted state, tests, and older call sites:

- `ControllerService`
- `ControllerStateService`
- `get_controller_object(...)`
- `OCW_Controller`
- `ControllerId`

Generic aliases now exist alongside them:

- `ProjectService`
- `ProjectStateService`
- `get_project_object(...)`
- `PROJECT_OBJECT_NAME`
- `PROJECT_OBJECT_LABEL`

## Terms That Stay Domain-Specific

The following remain valid inside domain plugins or domain-heavy generators:

- `controller`
- `pcb`
- `top_plate`
- `midi`
- `midicontroller`

These names describe real domain concepts and should not be removed from plugin code just for style symmetry.

## Deliberately Deferred Cleanup

The following were left unchanged in this step because they affect compatibility or persisted FreeCAD state:

- FreeCAD object names such as `OCW_Controller`, `OCW_PCB`, `OCW_TopPlate`
- persisted property names such as `ControllerId`
- file names such as `controller_service.py`
- builder and domain model class names that are still coupled to controller-style generated geometry

## Outcome

The core now exposes generic project-facing aliases without breaking older imports, document persistence, or tree/object access.
