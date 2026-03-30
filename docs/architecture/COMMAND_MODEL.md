# Command Model

## Scope

This model keeps the existing workbench interaction flow intact while moving generic standard commands into the core.

## Core Standard Commands

The core command factory auto-generates standard place commands from active-plugin component metadata.

Current standard scope:

- place library item in the 3D view
- expose label, icon, tooltip, category, and order
- populate the component toolbar and plugin-specific toolbars

The generated command still uses the existing generic placement flow.

## Component Metadata Source

Auto-generated place commands are derived from component metadata under `ui.command`.

Relevant fields:

- `placeable`
- `toolbar`
- `order`
- `category`
- `label`
- `tooltip`
- optional `command_id`

The command factory also uses existing component metadata:

- `ui.label`
- `ui.icon`
- `ui.category`
- `description`
- `ocf.control_type`

## Plugin Domain Actions

Plugin `commands/` remains valid, but it is now reserved for:

- domain-specific actions
- explicit overrides of standard commands
- optional advanced workflows that are not generic placement

Plugins no longer need one `place_*` file per standard component.

## Priority Rule

Resolution order is:

1. core auto-generated standard place command from component metadata
2. explicit plugin command override with the same `command_id`

This keeps the default path simple while still allowing a plugin to override a standard command intentionally.

## Templates

Template-driven create commands are intentionally deferred in this step.

Reason:

- the existing Create flow already covers template selection well
- standard place-command simplification had higher priority
- no extra template command surface was needed to remove current redundancy

## Migration Decision

`plugin_midicontroller` and `plugin_bike_trailer` now expose standard placement through component metadata only.

Result:

- less redundant plugin YAML
- no loss of toolbar behavior
- better support for user-generated plugins and component libraries
- explicit plugin commands stay optional instead of mandatory
