# HS-69-11 — Node canvas — wiring + inspector

- **Status:** done
- **Priority:** HIGH (heavy)
- **Depends on:** HS-69-10, HS-69-05
- **Catalog pattern(s):** §2 Workbench, §5 sheets
- **Evidence:** [evidence-story-11.md](./evidence-story-11.md)

## Goal

Type-colored bezier cables with port-compatibility validation + the node palette
+ the inspector sheet — the second half of the iPad Workbench on the web.

## Scope

- **Port wiring:** drag an output port → a live cable follows the cursor; drop
  on a TYPE-COMPATIBLE input port commits a new cable; an incompatible drop is
  rejected with feedback. Compatibility = matching data type (the iPad PortType
  rule). Persisted.
- **Inspector:** tap a node → a premium right-drawer (the HS-69-05 sheet idiom)
  with the in/out type chips + an editable prompt that updates the node live.
- **Palette:** add a step node to the canvas, then wire it.
- Port colors honor the web status palette (text→accent / findings→ok /
  signal→info).

## Proof required

Type-colored bezier cables with port-compatibility validation + the node palette
+ the inspector sheet; screenshots of a wired graph.

## Done

Shipped and screenshot-proven. Dragging a port draws a live dashed cable; hovering
a **compatible** input port glows it green (and an incompatible one flashes
danger); a valid drop commits a new typed cable (proven 3→4 cables). The inspector
opens as a premium drawer with the node's in/out type chips and a prompt field
whose edits propagate live to the node (and persist). The palette adds a node
(4→5). The pan handler was fixed to not steal pointers from the palette/inspector.
Route pre-flight (zero page errors) + density guard = 7 passed.
