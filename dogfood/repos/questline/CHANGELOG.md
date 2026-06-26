# Changelog

All notable changes to questline. Format follows
[Keep a Changelog](https://keepachangelog.com/). Versions are SemVer.

## [Unreleased]
### Added
- Draft Guilds PRD (`docs/prd/guilds.md`) — social accountability bet,
  in discovery (QL-310).

### Fixed
- (in progress) Streak resets on timezone boundary for non-UTC users
  and across DST (QL-322), behind the `streakEngineTzFix` flag.

## [1.4.0] — 2026-04-22
### Added
- Analytics event pipeline (`track()`) and dashboards for WAQC,
  activation, and the onboarding funnel (Stage 4).
- `freemium_gate_hit` event on the active-quest cap.

## [1.3.0] — 2026-03-20
### Added
- Streak engine with XP and streak multipliers (Stage 3).
- 🔥 streak indicator on the quests page.

## [1.2.0] — 2026-02-12
### Added
- Quest CRUD: create, edit, archive, complete; daily/weekly/N-per-week
  cadence (Stage 2).
- Freemium gate at 3 active quests for the free plan.

## [1.1.0] — 2026-01-15
### Added
- Email auth, session cookies, and the 4-step onboarding wizard
  (Stage 1).
