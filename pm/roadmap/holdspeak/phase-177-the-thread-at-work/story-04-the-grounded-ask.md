# HS-177-04 — The grounded ask

- **Project:** holdspeak
- **Phase:** 177
- **Status:** backlog
- **Depends on:** HS-177-03
- **Unblocks:** HS-177-05
- **Owner:** unassigned

**CONDITIONAL: this story proceeds only if HS-177-01 produces a GO
verdict. If the measured decision is CUT, this story is cancelled.**

## Problem

The ask today (ask.resolve_grounding at mcp/families/ask.py:109)
resolves desk-level grounding refs: notes, meetings, decisions. It
cannot resolve Watch entities or Room data. The arc says: "the ask
grounded on Watches and the Room." When the owner asks "What is Ania
waiting on from me?" the answer should cite Watch entities (PRs,
issues) by ref, not hallucinate from the question alone.

## Scope

- In:
  - ask.resolve_grounding extended to accept and resolve Watch entity
    refs and Room refs (project://room/{id}, watch://entity/{id})
    alongside desk refs; the hydrator from HS-177-03 is the backend.
  - Thread turns that use the ask carry Watch entity citations in the
    response: each cited entity is a ref card (the HS-177-02 artboard)
    linking to the Watch entity's pullout or external URL.
  - The answer's citations carry provenance: the entity source
    (GitHub PR, Jira issue, meeting decision), the field cited
    (assignee, status, updated_at), and the freshness (last evaluated
    at).
  - The grounded ask stays local (Article III): Watch entity data is
    read from the local DB, never fetched live from the remote source
    during the ask; the freshness is honest ("as of last evaluation").
- Out:
  - Live-fetching Watch entity data during the ask (the evaluation
    cadence from Phase 171 is the freshness guarantee).
  - Grounding on data outside the Room (desk-level grounding stays
    as-is; this story adds Room-level, not cross-Room).
  - Vector RAG over Watch entities (FTS over the existing entity
    snapshots is the first approach).

## Acceptance criteria

- [ ] ask.resolve_grounding resolves Watch entity refs and Room refs
      to their data (Article IX.1).
- [ ] A thread turn's answer cites Watch entities by ref; the ref card
      shows the entity source and the field cited.
- [ ] Citations carry freshness ("as of {last_evaluated_at}") -- never
      "live" or "current" (Article VI: honest by construction).
- [ ] The grounded ask stays local: no live fetch to GitHub/Jira
      during the ask (Article III).
- [ ] Zero egress (Article III).

## Test plan

- Unit: `HOME=$(mktemp -d) uv run pytest -q tests/ -k grounded_ask`
  - ask.resolve_grounding resolves Watch entity refs.
  - Citations carry provenance and freshness.
  - No network calls during resolution (mocked Watch data in the DB).
- Integration: a thread turn grounded on a Room resolves Watch
  entities and produces citations.
- Manual: the owner asks a Room-grounded question; the answer cites
  Watch entities with their refs and freshness.

## Notes / open questions

- The freshness disclaimer ("as of last evaluation") is a face
  element. Does it go on every citation, or once per turn? Propose
  once per turn (a footer line), with per-citation freshness only
  when entities have different evaluation timestamps. The owner
  decides on the canvas.
