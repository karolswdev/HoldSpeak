# HSM-18-02 — Voice command macros fire on the remote relay + the iPad CommandsBoard

- **Project:** holdspeak-mobile
- **Phase:** 18
- **Status:** todo — **the highest-value single fix in the phase** (a one-function hub hole
  that switches the whole macro feature on for the iPad).
- **Depends on:** the remote relay (`/api/dictation/remote`, `holdspeak/.../pipeline.py`);
  the macro dispatcher (`dispatch_voice_command`); the settings route (`PUT /api/settings`).
- **Unblocks:** macro parity for every companion that dictates through the Mac.
- **Owner:** unassigned

## Problem

Voice command macros silently never fire when triggered from the iPad. `api_dictation_remote`
(`holdspeak/.../pipeline.py:299-369`) routes straight to `_run_dictation_dry_run_text` and
**never calls `dispatch_voice_command`** — the exact dispatch the local dictation path runs.
So a macro keyword spoken into the iPad relay is silently rewritten as prose instead of
firing. The iPad also has no authoring board; the web `/commands` board has no Apple twin.

## The design

1. **The hub fix (the real contract hole).** In `api_dictation_remote`, gate on
   `config.dictation.macros.enabled` and call `dispatch_voice_command` on the recognized text
   **before** the dry-run, exactly as the local path does. Return `{fired: <kind>}` when a
   macro matched so the caller can show the honest "ran a command" result. Add a remote-path
   test that proves a keyword fires over the relay (the local-path test does not cover this
   seam — that is why it shipped broken).
2. **The iPad CommandsBoard.** A `CommandsBoard` screen reading/writing
   `settings.dictation.macros` via `PUT /api/settings`, mirroring the web `/commands` board:
   the four macro kinds (open_url / launch_app / shell / type_text), a **Test** action via
   `/api/commands/test`, the honest "runs code on your Mac" mark, the egress badge, and a
   speak-to-fill mic on every field.

## Scope

- **In:** the `api_dictation_remote` macro-dispatch fix + its remote-path test; the iPad
  `CommandsBoard` (read/write macros, Test, the honesty mark).
- **Out:** the dictation preview screen (18-01); on-device macro execution (macros run on the
  Mac by design — the iPad authors and triggers, never executes).
