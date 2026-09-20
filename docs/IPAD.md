# iPad companion

The iPad is a typed client of the HoldSpeak hub, not a second hub and not a
remote-control-only surface. This source audit is pinned to
`675401a857b85336d4acaa8c65383dfc9636e4c8`.

## What the client can call

`apple/Sources/Providers/Desktop/HTTPDesktopClient.swift::HTTPDesktopClient`
owns the base URL, optional Bearer token, timeout, health handshake, runtime
WebSocket request, meeting list/start/stop, remote dictation, companion board,
Coder sessions and recipe/chain execution. The extensions add typed calls for:

| User capability | Client function | Hub route |
|---|---|---|
| Dictate from iPad | `sendRemoteDictation` | `POST /api/dictation/remote` |
| Read/start/stop meeting | `listMeetings`, `startMeeting`, `stopMeeting` | `GET /api/meetings`, `POST /api/meeting/start`, `POST /api/meeting/stop` |
| Import recording/transcript | `importMeeting(fileURL:)` | `POST /api/meetings/import` multipart |
| Review meeting proposals | `meetingProposals`, `decideProposal` | `GET /api/meetings/{meeting_id}/proposals`, `POST /api/meetings/{meeting_id}/proposals/{proposal_id}/decision` |
| Coder board | `companionStatus`, `selectCompanionTarget`, `dismissCompanionTarget`, `pinCompanionTarget`, `coderSessions` | `GET /api/coders/status`, `POST /api/coders/select`, `POST /api/coders/dismiss`, `POST /api/coders/pin`, `GET /api/coders/sessions` |
| Reply/steer coder | `steerCoder`, `armCoder`, `disarmCoder`, `coderKeys`, `coderPeek`, `killCoder` | `POST /api/coders/{key}/steer`, `POST /api/coders/{key}/arm`, `POST /api/coders/{key}/disarm`, `POST /api/coders/{key}/keys`, `GET /api/coders/{key}/peek`, `POST /api/coders/{key}/kill` |
| Review activity | `activityNudges`, `selectNudge`, `dismissNudge`, `briefing` | `GET /api/activity/nudges`, `POST /api/activity/nudges/select`, `POST /api/activity/nudges/{nudge_id}/dismiss`, `GET /api/activity/briefing` |
| Execute saved work | `runRecipe`, `runChain` | `POST /api/recipes/{recipe_id}/run`, `POST /api/chains/{chain_id}/run` |

These route paths are taken from the generated route roster, not invented
labels. The iPad client applies the same response status boundary as the Web
client; non-2xx responses throw a typed HTTP error and malformed payloads are
reported as malformed.

## Dictation path

`VoiceNoteComposer` records device audio, transcribes through a supplied
on-device factory, allows an edit, and sends the reviewed text through the
hub's remote dictation path. The state machine is `idle → recording →
transcribing → review → sending → sent/failed` in
`apple/Sources/RuntimeCore/Companion/VoiceNoteComposer.swift::VoiceNoteState`
and methods `startRecording`, `stopAndTranscribe`, `editText`, `send` (lines
15-119). The source comments explicitly avoid a second transcription path:
the live path passes accumulated chunks to the factory.

Remote dictation carries a stable request identity. The hub claims the id and
returns the terminal receipt on retry; a different payload under the same id is
refused. The approval is the owner's explicit Send/release gesture. Audio does
not travel through the final delivery operation.

## Meeting review and import

The client can capture a meeting, read the retained transcript and artifacts,
review confidence/source information and decide a pending proposal. Import is
multipart from a readable local file; the client sends the bytes to the hub,
which enters the ordinary retained-meeting pipeline. Proposal review does not
execute the effect: decision and actuator policy remain hub-side.

## Authentication and local store

The `DesktopPeer`/`HTTPDesktopClient.Config` path accepts a hub URL and an
optional token; URLs are malformed/offline when host or port cannot be parsed.
The bearer stays in an HTTP header. Native stores and sync adapters live under
`apple/Sources/Providers/Storage/` and `apple/Sources/Providers/Sync/`; the
hub remains authoritative for records and receipts. Device-local model keys
stay in the Keychain when mesh serving is enabled.

## Status boundary

`apple/README.md` documents Swift package and native app sources, build/test
commands and physical-device prerequisites. It does not establish a signed
release, App Store distribution, or the owner's first use. Philo therefore
labels these capabilities `built_unreleased`, with `release_availability:
unverified` and `owner_observed: false`. A device walk must still prove auth,
offline/reconnect, import/review, proposal approval, receipt presentation and
the 393/1440-equivalent surfaces before promotion.
