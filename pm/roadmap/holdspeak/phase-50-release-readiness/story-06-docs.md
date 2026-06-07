# HS-50-06 — Docs: release + upgrade/backup policy

- **Project:** holdspeak
- **Phase:** 50
- **Status:** done
- **Depends on:** HS-50-01, HS-50-02, HS-50-03, HS-50-04, HS-50-05
- **Owner:** unassigned

## Problem
Once the gate is built, a release needs a written policy: what versions are
supported, what happens to a user's data on upgrade, how to back up first, and what
`doctor` reports on unexpected state. There is no such doc, and the standing rule
gives every phase its own dedicated docs story.

## Scope
- **In:**
  - A release + upgrade/backup policy doc (e.g. `docs/RELEASING.md` or a section in
    an existing guide): supported config/DB versions, the safe-upgrade behavior
    (refuse-newer, backup-then-apply-older, no-op-equal, create-fresh), the
    backup-before-upgrade step (`holdspeak backup`), and what `doctor` says on
    unexpected/newer schema.
  - A maintainer release checklist (bump version in one place, run the suite,
    verify the clean install, tag, what to publish).
  - Reconcile README + `docs/GETTING_STARTED.md`: honest status, the pinned install
    command, the upgrade/backup note. The README is already fairly honest ("early /
    pre-release ... isn't on PyPI yet") — keep it honest and sync any version string.
- **Out:** new feature docs; the meeting/dictation guides (unchanged).

## Acceptance criteria
- [x] A release + upgrade/backup policy doc exists and matches the shipped behavior
      (HS-50-02/03/04); a maintainer release checklist is written.
      (`docs/RELEASING.md`)
- [x] README + GETTING_STARTED reconciled: honest status, pinned install, backup
      note; terms consistent with `DOCS_STYLE.md`. ("Upgrading and your data" in
      README; backup pointer in GETTING_STARTED; status line already honest)
- [x] Doc-drift + dangling-link/image-ref guards green; every claim grounded in
      `db/core.py` / `commands/doctor.py` / `config.py` / the backup path.
      (`test_doc_drift_guard.py` 5 passed; humanizer voice, no em/en dashes)

## Test plan
- `uv run pytest -q -k "doc_drift or link or doc_guard or doc"`.
- Manual: read the upgrade/backup section as a user about to upgrade; it is clear
  what happens to their data and how to be safe.

## Notes / open questions
- Voice: humanizer rule (no em/en dashes, no rule-of-three, plain and direct).
- Keep the policy forward-looking (from this release on); do not document a
  historical migration ladder that never existed.
