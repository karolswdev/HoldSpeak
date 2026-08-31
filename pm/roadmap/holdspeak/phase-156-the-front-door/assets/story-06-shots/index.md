# HS-156-06 shot sheet -- the topology map

Reviewer: ______________ Verdict: ______________ Date: ______________

## Topology map at both widths

| Shot | Width | What to look for |
|------|-------|-----------------|
| topology-map-1440.png | 1440 | This Mac (home node, accent border, star badge) + LAN endpoint node visible; bundled flow labels legible; Map/Table toggle present with Map selected; no horizontal overflow |
| topology-map-393.png | 393 | Same structure at mobile width; map pans inside its container; no horizontal page overflow; nodes and labels do not clip off-screen |

## Node selected / inspector

| Shot | Width | What to look for |
|------|-------|-----------------|
| topology-node-selected-1440.png | 1440 | A node is selected (accent border, elevated shadow); inspector panel visible on the right with node label, state chip, kind, and re-point action |
| topology-node-selected-393.png | 393 | Selected node at mobile; inspector docks to the bottom of the map container |

## Keyboard focus frame

| Shot | Width | What to look for |
|------|-------|-----------------|
| topology-keyboard-focus-1440.png | 1440 | Focus ring visible on a node (the ring uses --focus-ring token); roving tabindex active |
| topology-keyboard-focus-393.png | 393 | Focus ring visible at mobile width |

## Add-node flow (in-world Disclosure)

| Shot | Width | What to look for |
|------|-------|-----------------|
| topology-add-node-choices-1440.png | 1440 | Add-node Disclosure open; choices: "Define endpoint" and "Connect hosted" buttons visible |
| topology-add-node-choices-393.png | 393 | Add-node choices at mobile width; disclosure pushes layout, no overlay |
| topology-add-node-form-1440.png | 1440 | Define-endpoint form: Name, Endpoint, Model fields (StringGadget); Key input; Add button |
| topology-add-node-form-393.png | 393 | Same form at mobile width; fields stack vertically; no overflow |

## Gate verdict

**Reviewer:** ________________ **Verdict:** ________________


## Gate verdict

**Reviewer:** the orchestrator (Fable), 2026-08-31. **Pass 1: FAIL**
(flows invisible — self-looped seeding; inspector/Add-node collision;
weak default framing; 393 home node half-clipped). **Pass 2: PASS.**
The retaken frames show the bundled labeled flow ("THOUGHTS & NOTES
+4") running desk-to-server, the Add-node toolbar in its own row, the
home node anchoring the composition at 1440 and fully visible at 393
(the clipped flow label pans into view — the pan contract). Recorded,
non-blocking: the edge stroke deserves more visual presence at 1440 —
polish for the walk's exhibit eye, not a gate blocker. The inspector
content (Models, seven Jobs with Fix actions, RE-POINT A FLOW) held
from pass 1.
