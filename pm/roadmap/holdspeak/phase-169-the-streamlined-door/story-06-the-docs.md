# HS-169-06 - The docs (the guide's New Project + Project Room sections re-shot; MCP_SIDECAR regenerated; the design doc canonized)

- **Project:** holdspeak
- **Phase:** 169
- **Status:** in-progress
- **Depends on:** HS-169-02, HS-169-03
- **Unblocks:** HS-169-07
- **Owner:** unassigned

## Problem

Three sentences in 168's guide described things the face did not do. The new door and Room need a guide that matches the pixels.

## Scope

- **In:** docs/USER_GUIDE.md New Project + Project Room re-written to the built faces with shots from the rig; docs/MCP_SIDECAR.md regenerated (never hand-edited counts); the settled design linked from DESIGN_SYSTEM.md's mockup roster; the doc-drift guard green.
- **Out:** marketing copy.

## Acceptance criteria

- [ ] Every claim in the guide's two sections checked against the code (a checklist in the evidence).
- [ ] Shots in the guide are the rig's, at 1440.
- [ ] Doc-drift guard + roadmap-vocabulary guard green.

## Test plan

`uv run pytest -q tests/unit/test_doc_drift_guard.py tests/unit/test_product_copy.py` (the inherited product-copy failure named); the guide read end to end.

## Delivered

_(pending)_
