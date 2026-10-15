# Settings visual revision — owner direction

The owner rejected the production screenshots, then confirmed: keep the
Workbench style; make it consistent, delightful and much better. Functional
checkpoint `1b1b617d6` is not merged, pushed or deployed. The previous checks
prove behavior and geometry; they do not constitute visual acceptance.

## What the screenshots exposed

- A 680px form floats inside a maximized grey body. Tiny mono labels,
  facts and captions compete at the same level. Short pages have little
  composition; numeric and text controls have accidental proportions.
- The phone stacks every ordinary label and control. Eight Meetings rows
  consume most of the screen before any calendar appears.
- Home leads with a technical assignment headline and two nested window
  plates. Ordinary preferences begin near the bottom of the phone.
- Populated Jira and Confluence have the same domain/initial identity.
  Expanded command strings are their only visible provider distinction.
  Setup detail dominates Accounts before the user requests it.

## Direction

Use the existing light Workbench chrome, materials, library controls, wings,
writer and navigation. No theme framework, new settings API, OAuth capability,
global form manager or automatic window sizing.

Use body13 sans for labels, primary15 sans for identity, secondary12 mono for
hosts/times/counts, and the current native gadget chrome. Prefer consistent
ordinary row rhythm and control widths set by the kind of value. Long text
fills its value column; a single number does not fill500px. Short choices and
booleans remain paired with their label at393; wide editors can stack.

Home uses one compact module-choice grammar, grouped by real work and Desk
preferences. Keep direct Engines/Accounts access and useful current facts;
park the oversized lead plates and technical headline. Do not replace them
with another dashboard or decorative card collection.

Module content starts at the native content gutter. Use authored group
composition where it helps: Summary/Recording beside Calendar/Export when
the window has enough width; one coherent column when narrow. Keep short
pages honest instead of inventing content to fill a maximized window.

Accounts leads with provider and account identity, useful state and its real
next action. Commands/details open only by an explicit action, inside the
existing well. Add/Retry/Cancel belong to the edited account. Full destinations
stay visible at the actions that use them. Preserve destination drafts while
their existing missing-account recovery opens account setup.

People, speech, Guide and Wallpaper use the same type and spacing grammar.
Maintain known/unknown/error truth, existing keyboard behavior, actual actions,
and the repaired read/write custody. No capability expansion.

## Build and review scope

Main lane owns SettingsCore/settingsPrefs/settings.css and the main canvas2.
Satellite lane owns ConnectionsPane/connections.css and the existing satellite
modules/canvas2. Main owns shared Settings typography/layout. Other lanes'
files remain do-not-touch. Shared hooks can be requested by exact class name.

Root first reads native canvas2 at1440/393, then settles the implementation.
Root inspects rebuilt production faces and the actual operations again before
the combined PR. Focused regressions, full quick check and an independent
finished-change source review remain required. The owner judges the live face.
