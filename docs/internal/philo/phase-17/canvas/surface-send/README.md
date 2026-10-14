# Send refinement canvas

DRAFT — BUILD approved by root after reading both widths. Static design states;
synthetic content; no dispatch.

Settled direction: `docs/internal/SEND-REFINEMENT-2026-10-14.md`.
This canvas uses the production surface, ledger, well, Button, StateChip and
EgressChip species in the current native material. Its local CSS shows the
proposed full width preview and single outer scroll. The desktop shell retains
the Note's 520 px width and the settled Send-only 520 px minimum height; the
phone shell uses the available height. Back sits in the host footer.
The parent lane owns the final Note frame, Back and save receipt.

Run the existing Vite executable with `--config
docs/internal/philo/phase-17/canvas/surface-send/vite.config.mjs` on port 24183.
Query states: `?state=ready`, `email`, `loading`, `sent`. These are artboards,
not working destinations or operations.

## Shared Send lane — HOLD FOR SHIP

The shared species now keeps Add destination visible, labels the Preview,
shows read/preview/chunk loading, gives the expanded preview its content
width, and places dispatch and receipts outside the uncapped payload well.
Only a closed destination repeats its short target; channel, account, egress
and receipt facts remain. Operation, digest, held-key and retry logic is
unchanged. The Note host/frame/footer are the sibling lane's work.

- `.tmp/send-refinement/send-focused-fixed.log`: four scoped Vitest files,
  **70 passed**, with isolated HOME, the machine test lock and two workers.
  Includes Add destination's existing Settings door, held reads/preview,
  frozen fields/body, dispatch order and retained channel/account/egress.
  The first run's two failures were old built-in target assertions; the
  target is now checked on the exact preview field.
- `.tmp/send-refinement/canvas-final.log`: fourteen canvas shots, 1440/393,
  browser errors `[]`; `.tmp/evidence-shots/send-refinement/canvas-adjusted/`.
  The adjusted 520 px artboard was captured before product edits; this final
  pass also retains the selected row's channel/account facts.
- Product integration shots and the combined quick check belong to root.
  No external Send, owner hub/DB/mic/state, staging or commit was used.
