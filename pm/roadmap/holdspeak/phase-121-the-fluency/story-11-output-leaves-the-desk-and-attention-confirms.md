# HS-121-11 — Output leaves the desk and attention confirms

- **Project:** holdspeak
- **Phase:** 121
- **Status:** backlog
- **Depends on:** HS-121-01 (useCopyReceipt), HS-121-02 (SurfaceFooter)
- **Unblocks:** HS-121-12 (the walk)
- **Owner:** unassigned

## The thesis (the bar)

Two merged concerns: generated text can't be copied, and workbench
state changes are silent.

### Copy

Ask answers, persona chat turns, workbench item results, and pullout
bodies have no copy button. Journal export is row-by-row.
`useCopyReceipt` (story 01) and `SurfaceFooter` receipt slot (story 02)
make this a wiring job.

### Attention

Workbench item completion is silent (cards flip with no signal). Item
failure doesn't explain the error. Field saves show no confirmation.
Dock badges are undifferentiated.

When this ships:

1. COPY button (using `useCopyReceipt`) on: Ask answers, persona chat
   turns, workbench item results, note/KB/artifact/decision pullout
   footers.
2. Journal export verb on the Speak footer (MD or JSON).
3. Workbench item completion: visible done-flash verified/strengthened.
4. Workbench field saves: transient "Saved" LampGadget.
5. Dock badges: at least two tiers (actionable vs informational).

## Acceptance criteria

- [ ] COPY button on Ask answers, persona turns, workbench results.
- [ ] COPY button on note/KB/artifact/decision pullout footers.
- [ ] Journal export downloads MD or JSON.
- [ ] All copy actions show "Copied" receipt in SurfaceFooter.
- [ ] Workbench completion: visible transient signal.
- [ ] Workbench saves: "Saved" indicator.
- [ ] Dock badges distinguish severity tiers.

## Files in scope

- `web/src/desk/components/AskPanel.tsx`
- `web/src/desk/components/PersonaChat.tsx`
- `web/src/desk/components/WorkbenchWindow.tsx`
- `web/src/desk/pullouts/NotePullout.tsx` (and other pullouts)
- `web/src/pages/cores/DictationCore.tsx`
- `web/src/desk/components/Dock.tsx`
- `web/src/desk/components/DeskChrome.tsx`
