# People security boundary

People stores relationship and 1:1 context in a separate encrypted authority.
It is a protected Desk capability, not a second copy of the main database.
People is available to the owner and to the explicitly bounded agent paths
described here.

## What People does

People stores relationships, shared-intent agendas, requests, commitments,
owner aliases, calendar links, and source-preserving 1:1 briefs. It has no
People audio recorder and no People-owned model inference.

The 1:1 brief is computed at read time. It can include shared-intent records,
linked meeting actions, decision records, and a bounded memory projection when
the caller is allowed to read them. The brief itself is not persisted as a new
People record.

## How the data is protected

- Payloads are encrypted with AES-256-GCM before SQLite sees them.
- The production sidecar is `~/.local/share/holdspeak/people.v1.sqlite3`.
- The key is held by the native key store.
- The sidecar and its directory require private file permissions.
- A missing, locked, unsafe, or mismatched key makes the store unavailable.
- The service does not substitute a new empty store for an unavailable one.

The main SQLite database is not encrypted by this boundary. Use operating-system
disk protection for the rest of the Desk.

## MCP access

The effective MCP mode is `off`, `read`, or `write`. The default persisted
mode is `write` for the local owner. Set
`HOLDSPEAK_MCP_PEOPLE_ACCESS=read` or `=off` before the hub starts to restrict
the capability. The environment value overrides the saved setting.

When access is `off`, People tools and resources leave MCP discovery except
for the owner's access-setting tool. When access is enabled, MCP exposes only
shared-intent People material.

A HoldSpeak-launched agent can read the allowed People brief and suggestions
unless access is `off`. It cannot write People through the launched-agent
scope. `services/agent_brief.py` includes People data in the coding-agent brief
under Conductor R7 when its grounded blocks carry People material. The
`people_cut` field is zero when no People content is cut. This is separate from
an agent's MCP read tool scope.

The MCP family includes readiness, relationship list and get, grounding,
1:1 brief, suggestions, and explicit write tools. Leader-private preparation is
never returned over MCP. A guessed private record or unsupported visibility is
refused.

## What People does not do

People excludes individual scoring, ranking, productivity monitoring, sentiment analysis, personality inference, and health or burnout inference.
It also excludes pay, promotion, discipline, and automatic opportunity-allocation recommendations.

It does not provide generic sync, export, global search, recording, scheduled
brief inference, or a model call. A source-cited draft is unsupported unless a
future feature explicitly defines its boundary.

## Where People content must not appear

Private People payloads must not enter:

- the plain main SQLite database;
- generic memory indexes or search projections;
- model prompts that do not carry the People boundary;
- connector payloads, logs, receipts, or browser telemetry;
- generic MCP resources or an unscoped agent tool.

The protected People brief and coding-agent handoff carry the boundary in their
service path. A coding-agent handoff is an egress choice, recorded with the
brief sources and the selected agent route.

## Lose the key

There is no automatic People backup or recovery in the main database backup.
If the native key is unavailable, the sidecar remains unreadable. Do not delete
the sidecar or key while diagnosing. Restore the key-store access first and
read the readiness state again.

## Release checks

A release that changes People must verify:

- AES-GCM encryption occurs before SQLite writes;
- private file permissions are enforced;
- missing or locked keys fail closed;
- private fields do not appear in the main database, logs, receipts, or generic MCP;
- MCP `off`, `read`, and `write` precedence is correct;
- an agent can read the permitted brief but cannot write People;
- prohibited employment uses remain refused.

## See also

- [Security](SECURITY.md)
- [Security model](SECURITY_MODEL.md)
- [Authority](AUTHORITY.md)
- [Storage and migrations](STORAGE_AND_MIGRATIONS.md)
