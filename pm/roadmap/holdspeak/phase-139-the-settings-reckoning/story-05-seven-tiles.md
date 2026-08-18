# HS-139-05 — Seven tiles

- **Project:** holdspeak
- **Phase:** 139
- **Status:** done
- **Depends on:** 139-01, 139-02, 139-03, 139-04
- **Unblocks:** 139-06, 139-07
- **Owner:** delegated Opus worker; orchestrator adjudicates

## Problem

After the cut, 14 tiles frame a room of ~33 controls — empty rooms and
operator names ("Cadence", "Presence") a person shouldn't need to
decode. And the room's most important surface — the Destinations table
(the one-dial law) — is unreadable below ~1200px (columns truncate to
three characters at 393).

## Scope

- **In:** collapse the drawer face to ~7 tiles named by what the owner
  DOES, merging emptied modules (proposed: Voice — hotkey, language,
  preview, voice commands, symbols, wake word; Sounds & Presence;
  Meetings pointer tile (opens the Meetings surface config); Rhythm
  (cadence user-facing); Models & Destinations; Integrations (secrets);
  System — posture, device name, desk reset; final grouping is the
  worker's proposal, ruled by the orchestrator against the census's
  KEEP set before implementation). Destinations at narrow width becomes
  readable: card-per-destination below the table's breakpoint, all
  fields legible, TEST/delete reachable. POSTURE and the precedence
  chain stay on the face. FILTER survives only if it still earns its
  place in a 7-tile room (worker judgment, reported).
- **Out:** new capability; theming; touching non-settings surfaces.

## Acceptance criteria

- [ ] The face shows ≤8 tiles; every tile opens a room whose face
  carries only KEEP controls; zero empty rooms.
- [ ] Total on-glass controls (excluding folded RAW) ≤ 40.
- [ ] Destinations is fully legible and operable at 393px — every field
  readable, every verb reachable, no horizontal page scroll.
- [ ] The joy bar: the owner's first-glance read of the face is jobs
  language, not subsystem names (owner may overrule the grouping at the
  sitting; the proposal ships in the story report).

## Test plan

- **Web:** vitest for the face roster + narrow destinations rendering.
- **Manual:** the walk (139-07) shoots every room at both widths.
