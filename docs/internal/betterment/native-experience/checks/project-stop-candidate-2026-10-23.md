# Project-update Stop candidate — parked draft

**NOT SHIP-READY. Not merged or deployed.** Owner correction, 2026-10-23:
finish current work and refine strategy before further implementation. This
branch preserves the candidate bytes; it is not a delivered repair.

The draft binds a project-update job to its Workbench parent, attempts to
fence producer writes and preserve already-written results, and changes the
Stop consumer. It crosses run/credential, transaction and editor ownership.
Those boundaries need a settled design and focused proof before delivery.

Root found that result writes could discard automation identity, and that
a stopped result could overwrite a newer owner draft. The worker patched
those locally before the final hold; neither patch is verified. Early reuse
of an existing result may also suppress legitimate later tool text.

Seven modified Python product files and the new regression file compile.
Earlier selected checks passed 11 backend and 29 frontend cases, but are
stale relative to the last edits. The four new backend regressions and the
updated frontend Stop test have not run. The new backend draft includes an
unremoved no-op placeholder. No behavior or readiness claim follows from
these tests existing. No owner DB, provider or external delivery was used.

The remaining project-update finding stays open. Resolve exact parent/job
identity, Stop-versus-commit outcome, retained owner draft, late read authority
and real HTTP/CLI producer proof in the strategy before resuming this draft.
No schema or general UI framework was adopted.
