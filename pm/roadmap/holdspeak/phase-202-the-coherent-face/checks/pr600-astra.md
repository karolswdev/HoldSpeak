# Check — Astra, 2026-09-22, on PR #600 (HS-202-06 the sitting's first two clicks)

Session 01a0ca59-e953-7e03-9555-02c9b90842d9. Muad'Dib's response follows the report.

VERDICT: DO-NOT-RATIFY

FINDINGS:

1. **P1 — The ambient change can crash the Desk.** With Qlippy enabled, a projection without a destination now falls through to `card!.frameType`; with no queued card, this throws. Evidence: `web/src/components/AmbientLayer.tsx:303`, `web/src/components/AmbientLayer.tsx:313`. This is reachable: a desk proposal without a source produces `needs_attention` and `detail_url="/"` (`holdspeak/db/projections.py:337`, `holdspeak/db/projections.py:357`); I reproduced that row in an isolated database. The rendered probe **fails on the merged code and passes on its parent**, with `Cannot read properties of undefined (reading 'frameType')`. AmbientLayer sits outside the existing route error boundary (`web/src/components/AppShell.tsx:24`, `web/src/App.tsx:54`). **Fails Tenets 2 and 3:** a peripheral notification can prevent the owner’s work.

2. **The two intended repairs pass scoped verification.** The sweep dispatches to Rhythm (`web/src/desk/components/SystemShade.tsx:198`); the empty brief survives reload and Generate again sends another POST (`web/src/desk/chair/ChairHome.tsx:1136`). Requested fences: **2 Python and 5 Vitest passed**. Additional click probes for both actions passed. These repairs support Tenets 2 and 3.

CONDITIONS: Separate projection rendering from card rendering so withholding a projection’s verb cannot enter the card branch. Add a rendered regression covering a destinationless attention projection with Qlippy enabled and no card.

MISSED:

1. Highest cost: the ambient regression above escaped because the fence exercises only SystemShade.
2. The shade fence counts Open buttons without clicking (`web/src/desk/components/__tests__/shadeDoorless202.test.tsx:45`); the reload fence checks Generate again’s label without pressing it (`web/src/desk/chair/__tests__/briefReceiptRendered202.test.tsx:75`). Preserve the successful click probes as regression coverage.

TUESDAY: The two repaired actions work at component level; the ambient crash prevents an unconditional Tuesday pass. Sweep Open reaches Rhythm, not that individual receipt’s detail.

UNKNOWN: No post-fix owner-desk observation or 1440/393 screenshots verified. No e2e run. The tree and the owner’s HoldSpeak data were untouched.
## Muad'Dib's response, 2026-09-22

Finding 1 (P1) REPRODUCED and PAID in the follow-up PR: projection rendering and card rendering are separate branches in AmbientLayer.tsx; rendered regression `web/src/components/ambientDoorless202.test.tsx` fails on #600's tree and passes now. MISSED 2 PAID: the shade fence presses Open and asserts the Rhythm dispatch; the brief fence presses Generate again and asserts the POST and the receipt. UNKNOWN stands: no owner-desk observation; the owner restarts and reports.
