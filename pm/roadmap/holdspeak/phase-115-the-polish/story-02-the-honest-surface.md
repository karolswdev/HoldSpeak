# HS-115-02 - The honest surface

- **Project:** holdspeak
- **Phase:** 115
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-115-07
- **Owner:** unassigned

## The thesis (the bar)

No internal identifier, enum value, API response body, or
implementation token ever appears in product-facing UI. Every value
the user sees must be a human-readable label, a recognized state
word, or hidden behind a RAW disclosure fold. When this ships, a
non-developer user can open every surface on the Desk and never
encounter a hex ID, a JSON blob, or an internal audit label.

**Articles served:** VII (no prose, labels state what), VIII
(native-grade craft).

## Ground (from the audit)

18 C1 violations across 12 components:

| File | What leaks |
|------|------------|
| Pullout.tsx:364 | Raw capture status, failure, provenance |
| Pullout.tsx:623 | Raw model and internal state values |
| Pullout.tsx:853 | Diagnostic target IDs, engine, boundary, fallback reason, invocation ID |
| InfoWindow.tsx:129 | Raw object ID in Identity section |
| InfoWindow.tsx:194 | Raw contract/internal field names as labels |
| AttentionDrawer.tsx:147 | Backend titles/summaries verbatim (audit labels, placeholders) |
| AttentionDrawer.tsx:200 | Raw `source_kind` and `source_id` |
| AttentionDrawer.tsx:242 | Unnormalized projection titles |
| DeskToolInspector.tsx:278 | Raw qualified resource reference |
| SystemShade.tsx:125 | Raw tool names, session keys, argument previews |
| SystemShade.tsx:265 | Raw internal `kind` values |
| InlineEditor.tsx:378 | `{input}` implementation token in placeholder |
| AskPanel.tsx:249 | Raw placement-engine and fallback-reason |
| SessionPullout.tsx:737 | Unrecognized pane status and backend detail verbatim |
| DictationCore.tsx:935 | Complete API result as JSON |
| HistoryCore.tsx:627 | Complete internal row JSON for body-less artifacts |
| HistoryCore.tsx:737 | Raw timeline JSON in routing receipts |
| LiveCore.tsx:315 | Complete API response as raw JSON in route-preview fold |

## Deliverables

1. **Label map.** Create a `humanize(key: string): string` utility
   that maps internal field names and enum values to user-facing
   labels. Unmapped keys fall through as title-cased words (no raw
   snake_case).

2. **Receipt sanitization.** Run receipts, routing receipts, and
   placement receipts show only: target name, model name, latency.
   Everything else goes behind RAW disclosure.

3. **Attention detail.** Normalize projection titles. Replace raw
   `source_kind`/`source_id` with resolved human-readable source
   names. Backend titles pass through the label map.

4. **JSON dumps.** DictationCore raw trace, HistoryCore artifact/
   routing JSON, LiveCore route-preview — all wrapped in a RAW
   disclosure fold. Never primary content.

5. **Placeholder fix.** InlineEditor workflow prompt: `{input}` →
   something like "Prompt (text is substituted at run time)".

6. **Identity section.** InfoWindow: raw object ID hidden behind RAW
   or removed. Properties use the label map.

## Test plan

- `uv run pytest -q` — no backend regressions.
- `npx vitest run` — all frontend tests pass.
- Open every surface that appeared in the audit. No raw hex IDs, no
  snake_case enum values, no JSON blocks in primary content.
