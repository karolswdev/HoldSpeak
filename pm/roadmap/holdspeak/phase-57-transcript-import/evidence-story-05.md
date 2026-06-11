# Evidence — HS-57-05: Closeout: real-VTT dogfood + final-summary + PR

**Date:** 2026-06-11
**Branch:** `phase-57-transcript-import`

The closeout's full narrative lives in [`final-summary.md`](./final-summary.md)
(this same commit); this file records the story-level proof.

## 1. The real-metal dogfood

`dogfood_story05.py` — real config (the `.43` intel endpoint), temp db,
no mocks, run unsandboxed for LAN reach:

```
model: small · intel endpoint: http://192.168.1.43:8080/v1
PASS  the VTT became a real meeting (5 segments, real cues, both speakers)
PASS  real intel ready on http://192.168.1.43:8080/v1
      summary: The team approved the database migration for Thursday night
      with Marek on call and decided to move two strong backend candidates
      to onsite i…
PASS  the server-side speaker facet filters by a transcript-carried name
PASS  the recording path still works: real Whisper heard 'we agreed to run
      the database migration on thursday night.'
PASS  /history rendered both imports with zero page errors
RESULT: PASS
```

Point by point against the acceptance criteria:
- **VTT speakers/timestamps:** the uploaded multi-speaker VTT landed with
  both file-carried names and the exact cue starts
  `[1.0, 6.5, 14.5, 19.5, 26.5]` — verified through the real detail API.
- **Real intel on `.43`:** the deferred job processed against the
  configured Qwen endpoint; `intel_status=ready`; the summary is an
  accurate digest of the fictional meeting and the snapshot extracted
  2 action items.
- **The facet pass:** `GET /api/meetings?speaker=Sam%20Kowalski` returned
  exactly the imported meeting; a stranger's name returned nothing — the
  speaker facet works on transcript-carried names, server-side.
- **The audio path, same run:** a real spoken WAV (`say` → real MLX
  Whisper) imported through the same route and transcribed verbatim.

Screenshot reviewed: `story05-archive.png` — /history with "infra weekly"
(Ready, 5 segments, **2 action items**, `imported` + `transcript` tags)
beside the Whisper-imported "spoken followup" (Queued), zero page errors.

## 2. Gates

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2641 passed, 17 skipped
$ (cd web && npm run build)   # clean, 13 pages
$ git ls-files holdspeak/static/_built/ | wc -l
0
```

BACKLOG: **P → shipped (CLOSED 5/5)**. Project README: phase CLOSED +
index row. PR to `main` merged on green CI (recorded in the project
README's operating cadence).
