# Relationship-aware memory evidence

These screenshots were captured from the real assembled HoldSpeak web runtime
against a disposable local SQLite database. The fixture contains one Project,
one Meeting transcript, one extracted Decision, one durable Decision Record,
one Artifact, one Action, two Notes (one deliberately outside the Project), and
one Thread with a frozen source reference.

Run from the repository root:

```bash
uv run python scripts/capture_relationship_memory.py
```

The script uses the production database repositories, web server, auth URL,
Desk launcher, Project Room, HTTP search route, and React components. It does
not mock the memory search response. The temporary database is discarded after
capture.

| File | Evidence |
| --- | --- |
| `desk-memory-launcher.png` | Owner-facing Desk Memory shade and attention state. |
| `desk-memory-global.png` | Whole-Desk search in the assembled application. |
| `desk-memory-results.png` | Close-up of lexical and relationship-expanded results. |
| `project-memory-scoped.png` | The same query opened through Project Orion. |
| `project-memory-results.png` | The unscoped scratchpad is absent while Project members and relationship neighbours remain. |
