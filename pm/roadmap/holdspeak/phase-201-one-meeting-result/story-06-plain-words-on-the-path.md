# HS-201-06 - Plain words on the path

- **Project:** holdspeak
- **Phase:** 201
- **Status:** backlog
- **Depends on:** HS-201-04
- **Unblocks:** (optional)
- **Owner:** unassigned

## Problem

Tenet 4 binds every label on this path to ASD-STE100. The walk listed ten that are not (audits/face-walk-opus.md "Labels not in ASD-STE100"): `RETAINED 0 SEG`, `ROUTED ARTIFACTS`, `INTELLIGENCE` for a summary, `7 WAITINGS`, a run-on server sentence, "Develop a thought", the Trust window column heads, and more.

## Scope

- **In:** every label in that table, on the path only (arrival, Desk, Record, Meetings, the record, the refusal, the egress window, Models): fixed to STE100 or justified in evidence; `product-language.json` updated where a term is canonical; the DOCS_STYLE policy applied.
- **Out:** labels off the path; docs.

## Acceptance criteria

- [ ] Each of the ten rows is fixed (file:line) or justified; the evidence table says which.
- [ ] `countToken` cannot pluralise a non-noun state word (fence).
- [ ] The doc-claims and product-language checks stay green.

## Test plan

- **Unit:** the countToken fence; product-language check.
- **Integration:** n/a.
- **Manual / device:** shots of each changed label at 1440.

## Notes / open questions

Lane B (Muad'Dib to Opus). Serves exit criterion 7.
