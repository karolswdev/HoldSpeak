# Evidence - HS-174-06

- **Story:** HS-174-06 - The third connector decision (candidates, CLI-backed, switch-and-verify)
- **Status:** done
- **Date:** 2026-09-05

## Proof

### Captured run — 2026-09-05T20:06:28Z

- **Command:** `bash -c grep -n 'Story 06, the third connector' pm/roadmap/holdspeak/phase-174-reach/assets/settled-design-reach.md | head -2; grep -c 'RECENT BLOGS' pm/roadmap/holdspeak/phase-174-reach/assets/mockups/DoorConfluence.dc.html; grep -n 'Confluence' docs/internal/project-rooms/HANDOVER-MUADDIB.md | head -3`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** adec5f000f6de5f055a8dfdea69f2f7d39862f4b

```text
742:- **Story 06, the third connector — Confluence as the reversible
1
72:(1) Confluence: does your team live in blog posts, or is page search the
80:Confluence is the reversible default, but its CLI cannot list or search
311:- **174's design ground is DRAFTED** (phase-174-reach/assets/settled-design-reach.md). Recon that changes the charter's assumptions: `acli confluence page` exposes only `view --id` — NO page list/search (only `blog list` and `space list` paginate) — so a Confluence WatchSource in V0 watches blog posts, not pages; the .43 is the CLIENT and the Mac the hub (.43 → hub → .43's llama.cpp → hub → receipt); `_web_auth_gate` (web_server.py:561-591) does not yet refuse OWNER derivation off-loopback — new code; AgentCredential has no palette field (principals.py:83-113) and the store is in-memory (dies with the hub); EgressChip has three scopes (`remote` is the fourth). His questions: Confluence still the third connector knowing V0 watches blogs only, or Linear; persist credentials or re-issue after restart; `caffeinate` for the lid-closed night or fail gracefully.
```
