# Concierge UX Evidence Log

Date: 2026-08-31
Desk: http://127.0.0.1:62119 (owner token auth)

## Evidence Items

### 1. "Connect a LAN llama.cpp server" is not a front-door action

The 24-model catalog shows cloud (OpenRouter) presets, local GGUF
downloads, and detected files. There is no catalog entry, wizard, or
first-class action for "connect to an existing LAN llama.cpp server
at a URL." The owner must know to call POST /api/inference/model-library/define-endpoint
with a JSON body whose exact field set (request_id, profile_id,
expected_profile_revision, label, provider_family, model, endpoint,
requires_key) was only discoverable by reading `_provider_draft` at
model_library_service.py:275. The provider_family must be
"openai_compatible" -- the user-facing label "LAN llama.cpp" never
appears.

### 2. define-endpoint creates v1 deployments with context_ceiling=0, making the profile unusable

`DeploymentRevision.from_identity()` (deployment_revisions.py:37)
defaults `context_ceiling` to 0. The model library service's
`_ensure_provider_deployment` (model_library_service.py:455) uses this
method, storing `revision.context_ceiling` (= 0) into the
`deployment_revisions` table. Meanwhile `inference_deployments` gets
`context_ceiling=16384` (line 501) but this value is never consulted
by the assignment compatibility checker.

The compatibility checker in `_incompatibility`
(inference_assignment_service.py:1882-1886) reads context_ceiling from
the deployment_revisions table via `_deployment_from_row`, which for
schema_version=1 reconstructs via `from_identity()` returning 0. The
check `int(deployment.context_ceiling or 0) < req.minimum_context_tokens`
thus evaluates to `0 < 2048` for every capability, producing
`context_unsupported` for all.

Net effect: every `define-endpoint` profile passes readiness probing
(shows "ready" in the Model Library) but is rejected by the assignment
editor and `set_assignment` as incompatible with ALL capabilities.
The owner sees "ready" and has no path to "assigned."

### 3. Legacy profile assignment succeeds but chat.turn FK-errors at route freeze

Legacy profiles (profile_id prefix "legacy-") bypass the v2
compatibility check at `set_assignment` time because their
context_limit comes from the profiles table, not deployment_revisions.
The assignment is persisted successfully. However, when chat.turn
calls `admit` which calls `_freeze_one_shot_in_transaction`, the
process fails with a raw SQLite `FOREIGN KEY constraint failed`
(HTTP 500). This error occurs consistently with every tested legacy
profile (legacy-legacy-intel, legacy-target_a46b5f675a5f).

The exact failing INSERT could not be identified without DB access,
but the error occurs within the `admit` transaction which spans
`evidence.stage`, `_freeze_one_shot_in_transaction`,
and `start_execution_in_transaction`.

### 4. Downloaded catalog models do not create assignable profiles

POST /api/inference/model-library/download successfully downloads a
model (verified in ~30s for the 532MB Tiny Qwen). The acquisition
reaches status "ready", an installed artifact appears in the model
library, and the setup endpoint reports it as verified. However, no
v2 profile or binding is created. The model never appears in the
assignment editor's candidates list. There is no documented follow-up
API call to "promote" an installed artifact into an assignable profile.

### 5. The assignment editor shows zero candidates for text capabilities

Despite having two "ready" provider profiles (LAN Qwen3.6, LAN
Qwythos) and four "ready" installed artifacts, the assignment editor
returns zero candidates for chat.turn, ask.answer, and all other text
capabilities. The only candidate ever shown is the Whisper MLX model
(audio-only, unavailable because MLX is not installed), visible in the
global scope because it is compatible with speech.transcribe (the one
non-text capability).

### 6. 24-model catalog with no guidance for self-hosted users

The catalog presents 24 rows mixing cloud-hosted (OpenRouter), local
downloads, and detected files without any indication of which are
relevant to a user who has their own LAN server. The "Connect" actions
lead to OpenRouter API key setup; the "Download" actions download from
HuggingFace. There is no "Point to your own server" action. The user
who already has a working llama.cpp server must independently discover
the define-endpoint API.

### 7. Legacy config routes are not surfaced in the Model Library assignment flow

The setup endpoint shows working legacy routes
(dictation.target_id = "legacy-intel", meetings.target_id = "legacy-intel")
pointing to the .43 LAN server. These legacy targets are shown as
"Migrated intel endpoint" in the model library with repair="Add this
legacy model to the library." But clicking "Add model" (the legacy
adapter) leads nowhere useful -- the legacy profile gets assigned but
then FK-errors at runtime (item 3).

### 8. Speech recognition works independently but the assignment UI shows it broken

The built-in whisper transcriber at POST /api/dictation/transcribe
works correctly (returns "The quick brown fox jumps over the lazy dog."
for the test fixture). But the assignment UI shows speech_recognition
as "no_compatible_assignment" and the only candidate (Whisper MLX base)
is unavailable. The built-in transcriber and the Model Library
assignment system are disconnected -- a user looking at the Models
screen would think speech is broken.

### 9. "no_compatible_assignment" is unexplained jargon

When the global assignment is a legacy profile that cannot serve
structured_output capabilities, the group rows show
"no_compatible_assignment" with no explanation of what is incompatible
or what would fix it. The label should say something like "This model
cannot produce structured output needed for Agents & Tools" and offer
a path to a compatible model.

### 10. Request shapes require source-reading to discover

Every API call required reading Python source to construct:
- define-endpoint: outer envelope {"draft": {...}, "secret": null}
  plus the exact field set for the draft
- assignments/editor: {"scope": {"kind": "global"}, "capability_id": "agent.code"}
  -- the valid scope shapes and capability_id values are not documented
- assignments/set: command_id, expected_revision, scope, entries --
  the entries shape [{profile_id, profile_revision}] was only
  discoverable by reading _validate_entries
- The profile_id naming convention for legacy profiles
  ("legacy-<profiles.id>") is entirely internal

### 11. The "ready" indicator on provider profiles is misleading

Both LAN endpoints show status "ready" in the Model Library, implying
they are functional. But they cannot be used for any capability
because of the context_ceiling=0 deployment bug (item 2). The user
sees "Ready" and reasonably expects the model to be assignable, but
the editor shows zero candidates.

### 12. Broken acquisitions accumulate without cleanup

The model library shows three "broken" acquisitions from previous
attempts (two with "acquisition_failed" and one with
"model_download_integrity"). These dead rows clutter the library with
no automatic cleanup, no batch retry, and no "dismiss" action.
