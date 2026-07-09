# Directory — Meetings

> **Auto-derived** by the 8-agent inventory sweep (Opus 4.8, 2026-07-08) from the
> phase record, then to be **verified on real glass** by the sweep story. This is the
> *starting map*, not the final ledger: the ✅/❓/— marks are the record's claim, and
> every ❓ (and every contested ✅) is exactly what the human checks on the device.

capture (hub and on-device), import, the 14 plugins, artifacts, aftercare, proposals, the archive. Feeds sweep story **HSU-2-03**.

**42 capabilities** — 17 must-test, 14 should-test, 11 spot-check.

Surfaces: ✅ record says present · ❓ unknown, verify on device · — record says not on this surface.

| P | web | iPad | iPhone | Capability | Key | Phases | State recipe(s) |
|---|---|---|---|---|---|---|---|
| 🔴 | ✅ | ✅ | ❓ | An accepted action item becomes a human-approved filed issue | `meetings.aftercare.action-to-issue` | HS-49 | `meeting-just-ended-open-actions`, `proposal-pending-approval` |
| 🔴 | ✅ | ❓ | ❓ | 'Your next move' aftercare digest on the meeting detail | `meetings.aftercare.digest` | HS-49 | `meeting-just-ended-open-actions` |
| 🔴 | ✅ | ❓ | ❓ | File an accepted meeting action as a GitHub issue (via proposal) | `meetings.aftercare.file_as_issue` | HS-49 | `meeting-just-ended-open-actions`, `proposal-pending-approval` |
| 🔴 | ✅ | ❓ | ❓ | Record a live meeting | `meetings.capture.live` | HS-2,HS-6 | `fresh-desk` |
| 🔴 | ✅ | ❓ | ❓ | Capture mic and system audio live with speaker labels | `meetings.capture.live-mic-system-audio` | HS-36,HS-55 | `fresh-desk` |
| 🔴 | ✅ | ❓ | ❓ | Import an audio recording as a meeting | `meetings.import.audio` | HS-55 | `seeded-desk`, `intel-endpoint-dead`, `recording-file-on-disk` |
| 🔴 | ✅ | ✅ | ❓ | Import a recording or transcript file into the full intelligence pipeline | `meetings.import.recording-and-transcript` | HS-55,HS-57 | `fresh-desk` |
| 🔴 | ✅ | ❓ | ❓ | Import a .vtt/.srt/.txt transcript as a meeting | `meetings.import.transcript` | HS-57 | `seeded-desk`, `transcript-file-on-disk`, `intel-endpoint-dead` |
| 🔴 | ✅ | ❓ | ❓ | Run meeting intelligence on a cloud/homelab endpoint | `meetings.intel.cloud_endpoint` | HS-2,HS-16 | `meeting-just-ended-open-actions`, `intel-endpoint-dead` |
| 🔴 | ✅ | ✅ | ❓ | Multi-intent routing over meeting windows | `meetings.intel.multi_intent_routing` | HS-2,HS-27,HS-36 | `meeting-just-ended-open-actions` |
| 🔴 | ✅ | ✅ | ❓ | 14 built-in LLM-backed plugins extract typed artifacts from a transcript | `meetings.plugins.14-typed-artifacts` | HS-36,PLUGIN_AUTHORING | `meeting-just-ended-open-actions` |
| 🔴 | ✅ | ✅ | ❓ | 14 built-in LLM meeting synthesizer plugins | `meetings.plugins.fourteen_synthesizers` | HS-16,HS-27,HS-28,HS-29 | `meeting-just-ended-open-actions` |
| 🔴 | ✅ | ✅ | ❓ | Review every pending proposal for a meeting wherever it was created | `meetings.proposals.review-anywhere` | HS-49,HS-61 | `proposal-pending-approval` |
| 🔴 | — | ❓ | ❓ | Run the full meeting notetaker fully offline (airplane mode) | `mobile.capture.airgapped_notetaker` | HSM-8-05,HSM-11-02,HSM-5-02 | `first-run-no-model`, `model-installed-on-device`, `airplane-mode-on` |
| 🔴 | — | ✅ | ❓ | Record a meeting on the iPad with a live transcript | `mobile.capture.meeting_record` | HSM-8-01,HSM-2-01,HSM-3-02,HSM-14-02 | `fresh-desk`, `mic-permission-granted` |
| 🔴 | ✅ | ✅ | ❓ | File a meeting action item as a GitHub issue from the iPad | `mobile.meeting.aftercare.file_issue` | HSM-19-01 | `meeting-just-ended-open-actions`, `seeded-desk` |
| 🔴 | ✅ | ✅ | ❓ | Approve or reject actuator proposals in the iPad review queue | `mobile.meeting.proposals.review` | HSM-19-05 | `proposal-pending-approval`, `meeting-just-ended-open-actions` |
| 🟡 | ✅ | ❓ | ❓ | Review and edit accepted action items | `meetings.actions.review_edit` | HS-6 | `meeting-just-ended-open-actions` |
| 🟡 | ✅ | ✅ | ❓ | Meeting aftercare shows what is open, decided, and changed since last time | `meetings.aftercare.close-the-loop` | HS-49 | `meeting-just-ended-open-actions` |
| 🟡 | ✅ | ❓ | ❓ | 'Show me the moment' — jump to the transcript segment behind a result | `meetings.aftercare.show_the_moment` | HS-49 | `meeting-just-ended-open-actions` |
| 🟡 | ✅ | ✅ | ❓ | The archive is searchable and filterable by date, speaker, tag, and open actions | `meetings.archive.facet-search` | HS-55 | `seeded-desk` |
| 🟡 | ✅ | ❓ | ❓ | Filter the meeting archive by date/speaker/tag/open-actions | `meetings.archive.faceted_search` | HS-55 | `seeded-desk-many-meetings` |
| 🟡 | ✅ | ✅ | ❓ | View meeting artifacts as elevated cards | `meetings.artifacts.cards` | HS-6,HS-36 | `meeting-just-ended-open-actions` |
| 🟡 | ✅ | ❓ | ❓ | Export a meeting as local Markdown/JSON | `meetings.export.local_handoff` | HS-7 | `meeting-just-ended-open-actions` |
| 🟡 | ✅ | ❓ | ❓ | The transcript is intent-scored and a chain of plugins runs per meeting | `meetings.intel.intent-scored-chain` | MIR-01,HS-36 | `meeting-just-ended-open-actions` |
| 🟡 | — | ✅ | — | Turn handwritten ink into intelligence (the magic pencil) | `mobile.capture.ink_into_intelligence` | HSM-8-06 | `seeded-desk`, `meeting-with-ink-notes` |
| 🟡 | ❓ | ✅ | ❓ | Watch utterances float as bubbles and tack them to a spatial board | `mobile.capture.live_capture_canvas` | HSM-14-11,HSM-14-13 | `seeded-desk`, `recording-in-progress` |
| 🟡 | — | ✅ | ❓ | Mark a moment during recording and jump back to it | `mobile.capture.mark_moment` | HSM-8-03 | `seeded-desk`, `recording-in-progress` |
| 🟡 | — | ✅ | — | Take Apple Pencil handwritten notes in a per-meeting notebook | `mobile.capture.pencil_notebook` | HSM-8-02 | `seeded-desk`, `meeting-open` |
| 🟡 | ✅ | ✅ | ❓ | Search and facet the meeting archive on the iPad | `mobile.meeting.archive.facets` | HSM-19-02 | `seeded-desk` |
| 🟡 | ✅ | ✅ | ❓ | Import a meeting recording or transcript from the iPad | `mobile.meeting.import.picker` | HSM-19-03 | `seeded-desk`, `mesh-node-alive` |
| ⚪ | ✅ | ❓ | ❓ | Draft a local follow-up summary from a meeting (preview + copy) | `meetings.aftercare.followup_draft` | HS-49 | `meeting-just-ended-open-actions` |
| ⚪ | ✅ | ❓ | ❓ | Jump to the transcript moment that justifies any result | `meetings.aftercare.transcript-moment-jump` | HS-49 | `meeting-just-ended-open-actions` |
| ⚪ | ✅ | ❓ | ❓ | Delete a meeting from the archive | `meetings.archive.delete` | HS-55 | `seeded-desk` |
| ⚪ | — | ✅ | ❓ | Dock, float, or minimize the recorder as an OS-like widget | `mobile.capture.floating_recorder` | HSM-14-13,HSM-14-02 | `seeded-desk`, `recording-in-progress` |
| ⚪ | — | ❓ | ❓ | See who's talking (on-device speaker diarization) | `mobile.capture.on_device_diarization` | HSM-14-17 | `seeded-desk`, `two-speaker-recording` |
| ⚪ | — | ❓ | — | Sketch a diagram with the Pencil and get a Mermaid diagram | `mobile.capture.pencil_to_mermaid` | HSM-14-08 | `seeded-desk` |
| ⚪ | ❓ | ❓ | ❓ | Get live intelligence markers during a meeting | `mobile.capture.realtime_mir` | HSM-14-18,HSM-14 | `seeded-desk`, `recording-in-progress`, `model-installed-on-device` |
| ⚪ | ❓ | ❓ | ❓ | Reject an artifact by voice and have the local model re-route | `mobile.capture.voice_correction` | HSM-14-07 | `meeting-just-ended-open-actions`, `model-installed-on-device` |
| ⚪ | ✅ | ✅ | ❓ | Artifact provenance ring and sources on iPad meeting artifacts | `mobile.meeting.artifact.provenance` | HSM-19-04 | `meeting-just-ended-open-actions`, `seeded-desk` |
| ⚪ | ✅ | ✅ | ❓ | Read the learning-loop digest on the iPad Dictate tab | `mobile.meeting.learning.reader` | HSM-19-06 | `seeded-desk` |
| ⚪ | ✅ | — | — | Write your own meeting plugin or connector against a documented contract | `plugins.authoring.write-your-own` | PLUGIN_AUTHORING,HS-38 | `seeded-desk` |

Priority: 🔴 must-test · 🟡 should-test · ⚪ spot-check · ⬛ skip.
