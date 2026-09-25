# Check — Muad'Dib, 2026-09-24

Session: `58de5cc9-af32-46e6-9dc1-df2b55435f85`. Read-only check; full result follows.

Reads are done. Writing the check now.

**VERDICT: RATIFY-WITH-CONDITIONS**

**FINDINGS**

1. **The diagnosis is correct.** `web/src/desk/chair/ChairHome.tsx:523-531` reads the latest brief and sets only `brief`; `briefKept` is declared null at line 679 and set only inside the Generate handler at line 709. A brief Codex made through MCP arrives in rows with no receipt. The source agrees with the seam as proposed.

2. **The latest payload carries everything the receipt reads.** The receipt helper (`briefEgress.tsx`, `briefReceipt`) needs only `sections` and `generated_at`. Both `/latest` and `/generate` return the service dict through the same `_compose_overlay` (`holdspeak/web/routes/monday_brief.py:112-129`), and the route's own `_generated_label` already reads `generated_at` from that dict at line 48. So hydrating from the returned brief is the same producer shape the Generate path uses today. The TS `MondayBrief` type at `ChairHome.tsx:140-150` omits `generated_at`, which is why the Generate path casts; the fresh-read path will need the same cast or a one-field type addition. Neither is a face change.

3. **The slots are already in every branch.** Three receipt spans, same testid, at lines 1339, 1369 and 1405 (empty, populated, handled). No new layout is needed for the hydrated value to render at 1440 or 393.

4. **This is a semantic broadening, not a new face.** The HS-202-02 receipt was ratified as "the receipt after the press" (comment at lines 675-678, Article III). After the seam it also reads as "the latest brief's receipt" on arrival. Same words, same slot, wider meaning. That is exactly the amendment the owner's brief demands, and it is lawful, but the record must say so rather than call it hydration only.

5. **One existing fence goes soft.** `briefReceiptRendered202.test.tsx:70-91` seeds `latest` with a brief that has `generated_at`, presses Generate, and asserts the receipt matches `Brief ready`. After the seam that receipt is already present before the press, so the assertion passes without the POST proving anything. Not a break, but a loss of teeth that the new fence must restore.

6. **Order of declarations matters for lint, not runtime.** `readBrief` at line 523 is a `useCallback` whose body runs in an effect, so referencing `setBriefKept` before line 679 is not a temporal dead zone at runtime. The repo's lint will likely refuse use-before-define. Moving the declaration next to `brief` is required, not optional.

**CONDITIONS**

- C1. The AMENDMENTS entry names finding 4: the Article III receipt now also shows on a fresh read for the latest durable brief, quoting the owner's demand as the authority. No claim that the face is unchanged.
- C2. The new rendered fence asserts three things from the retained real producer payload: the receipt appears on arrival without any press, its count and time derive from that payload, and a subsequent Generate replaces it with the new payload's receipt (different count or time). Prove the first assertion red on the pre-fix tree.
- C3. Read failure leaves `briefKept` untouched and the fence says so; only a null answer clears it. A failed read is not an absent brief (PHILO-3-03, line 515).
- C4. The 393 shot is taken after the receipt testid renders, same predicate law as my earlier C2 for the pullout.
- C5. The Codex/glass before shots stay in the evidence with the missing receipt named as the defect the seam paid, next to the after shots.

**MISSED**

1. The `MondayBrief` TS type omission of `generated_at` (finding 2). Cheap, but a bare cast repeated twice is the kind of thing Astra's own counsel caught once on PR #595.
2. Finding 5, the softened 202 fence.
3. The receipt time is `period_end`, not the wall clock of the run (`monday_brief_service.py:296`). Already true on the Generate path, so not this seam's debt, but the evidence should not describe the time as "when Codex ran it".

**TUESDAY:** Yes. He opens Arrival, sees tomorrow's decision in the rows and `Brief ready · N items · time` under them, and does not press Generate a second time to earn a receipt for a brief that already exists.

**UNKNOWN:** I ran no hub, no vitest, no lint, by role. Whether the repo's ESLint enforces use-before-define is unverified. Whether the retained Codex payload carries a timezone-bearing `generated_at` that renders the same at 1440 and 393 is what the shots will show. My closing check on the built evidence remains owed.

## Astra ruling

Accepted all conditions. No dissent. The existing Article III receipt now also identifies the latest durable brief on a fresh read. The owner's explicit `Brief ready …` requirement authorizes this narrow semantic amendment. No product edit before the real missing-receipt red; no claim of already-open brief refresh. The generated timestamp is the producer's period end, not the observed Codex execution time.
