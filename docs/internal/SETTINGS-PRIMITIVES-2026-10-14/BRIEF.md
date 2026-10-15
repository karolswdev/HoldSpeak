# Shared preference primitives — owner direction

Owner rejected the Voice face after release1204: it remains vanilla and needs
a substantial makeover built from reusable primitives. Workbench stays.
Base22de063e3, branchfeat/settings-primitives-20261014, isolated worktree
wt-settings-primitives-20261014. One coherent Settings/library release.

## Tuesday

Can the owner see the current state, change a value, add a spoken symbol, and
recover an edit without hunting across a grey canvas or repeating work?

## Settled boundaries

Extend existing GadgetGroup/GadgetRow/CheckGadget/GadgetTable and the existing
SurfaceColumns composition. Native controls, armed verbs, off-roster values,
keyboard semantics, voice entry and transparent fact material remain.
Inset control sheets use the existing well material; the window owns chrome.
Group actions are intrinsic library Buttons, never a full-width Add banner.
Boolean controls show On/Off while retaining real labelled checkboxes.
Record fields reflow with labels at393. No form state, persistence, validation,
feature flags, global form manager or duplicate settings framework is added.

Root first inspects the native Voice canvas in empty and populated states at
1440/393. Workers then implement the settled pattern and apply it to Voice,
Meetings, Rhythm, Sounds, People and System. Existing Accounts/directory/Engine
composition is not rebuilt as a new dashboard. Window footer/save custody stays.

## Lanes and held shipping

- preferences_kit_design: native canvas, then shared primitive source, barrel,
  contract and focused primitive checks after root settles the canvas.
- preferences_adoption_audit: audit, then Settings adoption and removal of
  superseded local form overrides after root settles the canvas/API.
- independent finished-change reviewer: source review after build, one fix
  recheck. Root owns evidence inspection, combined quick, PR and deployment.

All product edits occur in the named worktree. Workers do not stage or commit.
No worker runs a broad suite, install, real native access or owner-state walk.
Focused checks use the shared lock and isolated HOME; collect/run tails are
read before any result is repeated. The main quick check is scoped by the
changed concern; no full suite or metal run. Actual producer-backed isolated
walks cover populated fields, failures/retry, touch ownership and narrow fit.
Owner judges the live desk; a canvas and green checks do not claim acceptance.
