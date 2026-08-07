# HS-121-02 — One footer

- **Project:** holdspeak
- **Phase:** 121
- **Status:** backlog
- **Depends on:** HS-121-01 (the kit — SurfaceFooter must exist)
- **Unblocks:** HS-121-03 through HS-121-11 (every surface needs a footer)
- **Owner:** unassigned

## The thesis (the bar)

The audit found 8 footer species and 10 programs with no footer at all.
This story migrates every window and pullout to `SurfaceFooter` with
its three fixed slots: `egress | receipt | verbs`.

When this ships:

1. Every pullout that uses `<footer className="desk-pullout-foot">`
   migrates to `<SurfaceFooter>`.
2. Every window that uses `<DeskWindowFooter>` migrates to
   `<SurfaceFooter>`.
3. The 10 footerless programs (ActivityCore, CadenceCore,
   CommandsCore, CompanionCore, ComponentsCore,
   ConstitutionalContextCore, RuntimeDocsCore, SetupCore,
   WorkbenchCore, WorkbenchesHomeCore) each get a `<SurfaceFooter>`
   with at minimum an egress slot (if applicable) and a receipt slot
   (for future undo/copy receipts).
4. `DeskWindowFooter` becomes a thin wrapper around `SurfaceFooter`
   or is deprecated.
5. The old ad-hoc footer CSS classes (`desk-pullout-foot`,
   `desk-ask-foot`, `desk-chat-foot`, `desk-roadmap-footer`,
   `prefs-status`, `speak-status`, `surface-receiptbar` as footer)
   are consolidated into `SurfaceFooter`'s CSS.
6. SessionPullout's double-footer (two consecutive `<footer>` elements)
   collapses to one.

## Acceptance criteria

- [ ] `grep -rn "desk-pullout-foot" web/src/` hits only CSS definition
      and SurfaceFooter internals, not direct usage.
- [ ] `grep -rn "desk-ask-foot\|desk-chat-foot\|desk-roadmap-footer"
      web/src/` returns zero hits.
- [ ] Every program/pullout renders `<SurfaceFooter>`.
- [ ] SessionPullout has exactly one footer.
- [ ] All footers have the same three-slot layout.
- [ ] Receipt slot works (test with useCopyReceipt in one pullout).

## Test plan

- Open every program. Verify footer renders with consistent layout.
- Open every pullout type. Verify footer renders.
- Grep for old footer class names. Verify zero direct consumers.
- Visual: compare footer layouts across 5+ surfaces. Verify
  consistent slot ordering.

## Files in scope

- Every pullout under `web/src/desk/pullouts/`
- Every window component under `web/src/desk/components/`
- Every core under `web/src/pages/cores/`
- `web/src/desk/components/DeskWindowFooter.tsx`
- `web/src/desk/components/pullout.css` (footer rules)
- `web/src/desk/surface/SurfaceFooter.tsx` (from story 01)
