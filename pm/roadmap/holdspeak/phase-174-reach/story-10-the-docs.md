# HS-174-10 — The docs

- **Project:** holdspeak
- **Phase:** 174
- **Status:** backlog
- **Depends on:** HS-174-08, HS-174-09 (if not deferred)
- **Unblocks:** HS-174-11
- **Owner:** unassigned

## Problem

Reach adds a remote transport, a third connector, and (conditionally)
LAN notifications. Every new surface must be documented: MCP_SIDECAR.md
(the generated doc — extend the generator, never hand-edit counts), the
user guide's companions section, the architecture's remote chapter, and
the README's prerequisites (the third connector's CLI).

## Scope

- In:
  - MCP_SIDECAR.md extended: the Streamable HTTP transport, the scoped
    credential section, the egress badge vocabulary, the long-running
    contract over HTTP, the protocol version bump.
  - The user guide's companions section: the .43 runner, the remote
    credential lifecycle, the overnight scenario.
  - The README's prerequisites: the third connector's CLI (alongside
    `gh` and `acli`).
  - The architecture doc: the remote transport in the MCP layer, the
    credential flow, the egress badge path.
  - "Ecosystem publication" named honestly as self-hosted
    discoverability (the no-hosted-relay law).
- Out:
  - Marketing copy.
  - Remote/ecosystem docs beyond what ships in this phase.

## Acceptance criteria

- [ ] MCP_SIDECAR.md reflects the Streamable HTTP transport, scoped
      credentials, egress badges, and the protocol version (the
      generator is extended, not hand-edited).
- [ ] The user guide documents the .43 runner scenario and the remote
      credential lifecycle.
- [ ] The README's prerequisites name the third connector's CLI.
- [ ] Every new face is re-shot in the guide at both widths.
- [ ] "Ecosystem publication" is documented as self-hosted
      discoverability, not a hosted relay.

## Test plan

- Unit: n/a (docs story).
- Integration: n/a.
- Manual: the MCP_SIDECAR.md generator runs cleanly; the guide's
  screenshots match the current faces.

## Notes / open questions

- MCP_SIDECAR.md is partially generated (the tool count, family list,
  and per-tool reference). The generator must be extended for the
  remote transport section, not hand-edited.
