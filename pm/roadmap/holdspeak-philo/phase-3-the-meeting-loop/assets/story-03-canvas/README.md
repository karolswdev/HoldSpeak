# PHILO-3-03 canvas: the BRIEF section

`brief-section.html` is one self-contained page (the shots are inlined; no fetch). `brief-section.png` is the page at 1440, `brief-section-393.png` at 393. The eight shots in `shots/` are the REAL Chair BRIEF section, taken from a rig hub in a fresh HOME. State 1 is the face today. States 2 to 4 are composed in the page from the section's own species: `SurfaceSection`, `.surface-receipt-line` (12 px, `data-tone="danger"` for the fault), and the library `Button` cloned from the live Generate verb. No new species, colour or font. `shots/labels.json` holds the route labels the date caption shows.

## The four states

| # | State | Body | Verbs |
|---|---|---|---|
| 1 | No brief yet (the read answered `null`) | `No brief yet` (unchanged) | egress badge + Generate (unchanged) |
| 2 | Loading (the read has not answered) | `READING…` (`.surface-receipt-line`, muted) | none |
| 3 | Did not load (the read failed) | `BRIEF DID NOT LOAD · HTTP <n>` (`data-tone="danger"`); a fetch with no response shows `BRIEF DID NOT LOAD · NO ANSWER` | Retry (library Button, ghost dense): reads `GET /api/brief/latest` again |
| 4 | Populated, dated | the item rows (unchanged), then `<period_label> · <generated_label>` (for example `SEP 21 – 23 · GENERATED SEP 23 10:57`), then the receipt when the click made it | Ack · Defer (unchanged) |

The date caption also goes on the empty-brief branch (headline, then the caption). The caption uses the route's `period_label` and `generated_label` (`holdspeak/web/routes/monday_brief.py:27-58`); the face computes no date.

Why the date matters (seen in the next-day rig run, `../story-03-shots/*decision_on_the_face-muaddib-393/after.png`): the receipt says `Brief ready · 1 item · 10:55 AM` from the browser clock, while the brief the producer made is dated the next day. Only the caption shows which day's brief is on the face.

## Seams to bind (build after ratification)

- Load: `web/src/desk/chair/ChairHome.tsx:466-472`. The `.catch(() => null)` becomes `briefLoadFailed` (the `ApiError` status or `NO ANSWER`); a Retry sets loading and reads again.
- Branches: `ChairHome.tsx:1080` (`!briefLoading && !brief` also holds after a failed read, which is the defect). The failure branch comes first; `No brief yet` shows only when the read answered `null`. Loading gets its own branch (today it renders nothing).
- Caption: after the ledger (`BriefSection`, `ChairHome.tsx:1847`) and after the headline (`ChairHome.tsx:1163`), before `arrival-brief-receipt`.

## Ratification question

Do you ratify the BRIEF section in these four states: `READING…` while the read is open, `BRIEF DID NOT LOAD · HTTP <n>` with Retry when it fails, `No brief yet` only when there is no brief, and the brief's period and generated date as one 12 px line under the brief?
