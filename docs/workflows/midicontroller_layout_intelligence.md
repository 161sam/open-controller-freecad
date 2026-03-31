# MIDI Controller Layout Intelligence

## Scope

This MVP adds lightweight layout guidance to `plugin_midicontroller`.

It does not attempt full auto-layout or generic recommendation logic across every domain.
The workflow card is now state-aware for MIDI templates and recomputes from the current document state.

## What The MVP Adds

Templates can now describe:

- `workflow_hint`
- `ideal_for`
- `next_step`
- `layout_zones`
- `smart_defaults`
- `suggested_additions`

Components can now describe:

- `ocf.role`
- `ocf.placement_preference`

Suggested additions can also carry UI-facing metadata:

- `label`
- `short_label`
- `tooltip`
- `icon`
- `priority`
- `group`
- `order`
- `command_id`
- `status_message`
- `requires`
- `excludes`
- `promote_if`

These rules stay intentionally small:

- `requires`: show only when all listed state signals are present
- `excludes`: hide once any listed state signal is present
- `promote_if`: keep the action visible, but raise it to the current primary recommendation when all signals match

## Template Patterns

Current high-value patterns:

- `pad_grid_4x4`
  - utility strip on the right
  - navigation encoder pair on the top row
  - centered display header
- `encoder_module`
  - centered display header
  - compact utility buttons below
- `fader_strip`
  - display or label area above the lane
  - one top encoder above the strip
- `display_nav_module`
  - transport row below the navigation controls
- `transport_module`
  - display header above the row
  - jog encoder on the right

## Placement Heuristics

The MVP uses a small deterministic rule set:

- `right_of_main`
- `top_row`
- `centered_above_group`
- `bottom_transport_row`
- `aligned_with_group`

Anchor selection prefers:

1. template smart default primary zone
2. template smart default primary group role
3. current component bounds

## What It Can Do

- expose template-specific next-step suggestions
- derive a small workflow state from the current component set
- build template-specific workflow cards with one primary action and a short secondary action list
- surface those suggestions in the existing `InfoPanel` as clickable workflow actions
- register suggested additions as direct commands such as `OCW_AddUtilityStrip`
- generate deterministic default positions for suggested additions
- suggest a sensible default position for a newly added component type
- keep added controls grouped through `group_id` and `group_role`
- hide completed workflow steps once they are already present
- promote a different primary action after earlier workflow steps were applied
- show lightweight progress such as `1 of 3 typical setup steps completed.`

## Workflow State Signals

The MVP only uses a small set of robust plugin-specific signals:

- `has_utility_strip`
- `has_feedback_display`
- `has_navigation_encoder`
- `has_navigation_pair`
- `has_channel_display`
- `has_transport_buttons`
- `has_secondary_encoder_row`
- `has_top_encoder`
- `addition:<suggested_addition_id>`

Signals are derived from already persisted component data such as:

- `group_role`
- `group_id`
- `zone_id`
- `type`
- `properties.suggested_addition_id`

## How Users Trigger It

After creating a MIDI controller template, the `InfoPanel` now shows a compact `Workflow Card`.

Each card includes:

- the template title
- a short workflow hint
- a compact `Ideal for` summary
- one `Primary Action`
- a short `Next Steps` list

Typical actions include:

- `Add Utility Strip`
- `Add Display Header`
- `Add Navigation Encoder`
- `Add Transport Buttons`

These actions:

- stay hidden when the current document has no relevant suggestion
- apply the existing layout-intelligence heuristics
- add grouped components with deterministic default positions
- reuse the same plugin logic as the command path
- surface the most likely next build step first
- refresh immediately after each suggested addition so the next primary action can change

Example guided flow for `pad_grid_4x4`:

1. `Add Utility Strip`
2. `Add Display Header`
3. `Add Navigation Encoder Pair`

## What It Does Not Do

- full controller relayout
- collision solving beyond normal layout / validation paths
- adaptive optimization or AI placement
- generic cross-domain recommendation logic
- free-form expressions or a generic rule engine for every plugin

## Next Evolution

Later product work can build on this metadata to add:

- template-aware one-click add flows
- richer secondary-layout patterns for larger controllers
- lightweight placement previews for next-step actions
