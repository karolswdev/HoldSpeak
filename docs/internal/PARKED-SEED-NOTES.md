# Parked seed notes

PHILO-15 11 (bounce B20, owner ruling 2026-10-07). The fresh desk seed
(`holdspeak/seeds/fresh-desk.yaml`) carries only the notes a Senior Architect
wants on day one: Start here, About me, 1:1 prep, Current priorities and
Weekly update. The five notes below were in the seed before. They are parked
here as text, not deleted.

- **How I like help**, **People & vocabulary**, **Meeting preferences**:
  starter questions. A person can make the same note on the desk at any time.
- **Effect guard**, **Egress guard**: thread guardrails for developers. A
  guardrail is a note with the tag `guardrail` and YAML front matter
  (`instruction`, `trigger_tools`, `n_messages`); see
  `holdspeak/services/thread_modes.py` (`_parse_guardrail_note`).
  `thread_modes.seed_guardrails(db)` still creates these two notes when a
  developer calls it; the desk seed no longer calls it.

Desks seeded before this change keep these notes (the seed never removes an
object it made).

To get a starter-question note back on a new desk, make a note with the same
title and body. Nothing reads these three by id.

The guard notes are different: the built-in Desk and Chase modes find them
by their fixed ids (`hs-seed-guardrail-effect-guard`,
`hs-seed-guardrail-egress-guard`; `holdspeak/services/thread_modes.py`
`MODE_SEEDS` and `guardrails_for_thread`). A new note with the same title,
tags and body gets a new id, and those modes do not load it. To get the
guards back:

- **The original ids.** A developer calls `thread_modes.seed_guardrails(db)`
  (it makes both notes with their ids). Alternatively, `POST /api/notes`
  with `"id": "hs-seed-guardrail-effect-guard"` (or the egress id) and the
  title, tags and body below. This works only while the id has never
  existed on that desk; a deleted note keeps its id as a tombstone.
- **A replacement note on a mode.** `PATCH /api/threads/{id}` with
  `toggle_guardrail` enables any guardrail note on the thread's mode
  (`toggle_guardrail_on_mode`). This works only for a custom mode: the
  built-in Desk and Chase modes keep their fixed lists and ignore it.

Open (recorded in the PR #986 body): no desk verb and no face restores the
guard notes or enables one on Desk or Chase today. The way back is the API or
code above.

The notes, as they were in the seed manifest:

```yaml
  - id: hs-seed-how-i-like-help
    title: How I like help
    body_markdown: |
      How should help be shaped when you explicitly attach this context?

      - Tone: [example: direct, warm, concise]
      - Useful format: [example: bullets, draft, checklist]
      - Avoid: [example: ]
  - id: hs-seed-people-vocabulary
    title: People & vocabulary
    body_markdown: |
      Which names, terms, or abbreviations would be useful to explain?

      - Name or team: [example: ]
      - Term or abbreviation: [example: ]
      - Meaning: [example: ]
  - id: hs-seed-meeting-preferences
    title: Meeting preferences
    body_markdown: |
      What would make a meeting record useful?

      - Capture: [example: decisions, actions, open questions]
      - Follow-up format: [example: ]
      - People to include: [example: ]
  - id: hs-seed-guardrail-effect-guard
    title: Effect guard
    tags: [guardrail]
    body_markdown: |
      ---
      instruction: >
        Flag any tool call that writes to a person's ledger
        (people.commitment.transition, people.agenda.add,
        people.note.create) without naming a specific source
        (meeting, decision record, or owner directive) in its
        arguments. A call with no source is a violation.
      trigger_tools:
        - "people.*"
      n_messages: 6
      ---
  - id: hs-seed-guardrail-egress-guard
    title: Egress guard
    tags: [guardrail]
    body_markdown: |
      ---
      instruction: >
        Flag any pending tool call whose result would carry
        people-sourced data (a people.* read) to a cloud
        egress boundary. Reading people data on a local
        boundary is fine; sending it over a cloud route is a
        violation.
      trigger_tools:
        - "people.*"
      n_messages: 4
      ---
```
