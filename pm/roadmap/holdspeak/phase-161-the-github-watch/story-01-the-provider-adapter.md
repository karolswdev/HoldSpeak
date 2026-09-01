# HS-161-01 - The provider adapter: real auth, real discovery, receipted egress

- **Project:** holdspeak
- **Phase:** 161
- **Status:** backlog
- **Depends on:** -
- **Unblocks:** HS-161-02
- **Owner:** unassigned

## Problem

§3.2's ruling: the fastest truthful V0 GitHub path is the existing
local `gh` connector plus the MISSING auth/repository discovery
capabilities. PROV-001..011 govern; PROV-003 forbids guessing
readiness from binary presence (GitHubWatchSource:67 does exactly
that today — `shutil.which("gh")`). And the arc's first real
egress: every gh call must ride the kernel with a receipt
(NFR-009/DOM-014) — VERIFY how the existing runner integrates with
the kernel before building (it may already be admitted; the
tombstone law and the 156 scar say check, never assume).

## Scope

- **In:** `holdspeak/services/github_provider.py` —
  GitHubProviderAdapter (the §11 protocol subset P2a needs):
  `manifest()` (versioned capabilities: discover/read yes,
  subscribe/effect no — PROV-007's read-never-shown-as-write),
  `connection_status()` (a REAL `gh auth status` probe through the
  admitted runner path: connected/owner_action_required/
  disconnected/unavailable with the PROV-009 typed codes; the
  result persisted to watch_provider_connections — no credential
  material, PROV-004), `discover()` (repos via `gh repo list
  --json`, bounded/paginated/searchable — PROV-006; stable IDs;
  partial pages tolerated), `validate_repo()` (the typed
  owner/repository fallback: one real bounded read proves the repo
  — §8.1's ruling), `snapshot()` (delegates to the EXISTING
  GitHubWatchSource — no forked fetch logic). Egress: every gh
  invocation admitted + receipted per the kernel's existing runner
  discipline (verified first); the connection row records
  last_checked/connected/error.
- **Out:** compilation/templates (02), test/baseline (03), routes
  (04), any UI, any write capability.

## Acceptance criteria

- [ ] PROV-003 dead: readiness comes from the authenticated probe, never `which gh` alone (the :67 fallback stays only as the 'unavailable' detector); installed-but-unauthenticated yields owner_action_required with the provider's own recovery hint.
- [ ] Discovery bounded + paginated + stable-ID'd; a partial/failed page degrades typed, never crashes; the typed-repo fallback validates via ONE real bounded read.
- [ ] The kernel question ANSWERED in the story record: how gh calls are admitted/receipted (existing path verified or minimally extended — no unadmitted egress; a test proves a receipt exists per probe/discovery call IF the kernel seam applies to service-level runners — otherwise the finding is recorded honestly for counsel).
- [ ] No credential/token ever stored or logged (PROV-004 — a test greps the row + logs).
- [ ] Fixture-driven unit tests (a fake runner) + ONE live-marked test (real gh, skipped when unauthenticated) proving the probe against reality.

## Test plan

- **Unit:** `tests/unit/test_github_provider.py` (fake-runner truth tables: auth states, discovery pages, fallback validation, typed errors, no-credential fence).
- **Live-marked:** the real probe (skip-clean without auth).

## Notes / open questions

- The runner seam: GitHubWatchSource takes `runner` — trace what production passes (kernel-admitted executor or raw subprocess?) and DOCUMENT it; the answer decides whether this story extends the kernel path or verifies it.
