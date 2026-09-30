# PHILO-11-02 - The Slack channel and the aftercare rewrite

- **Project:** holdspeak-philo
- **Phase:** 11
- **Status:** backlog
- **Depends on:** the owner's ratification and his answer to Q1; PHILO-11-01 for the aftercare rewrite (the channel module runs in parallel with 01)
- **Unblocks:** PHILO-11-05 (Destinations with Slack), PHILO-11-06, PHILO-11-07
- **Owner:** Astra's lane (Luna, xhigh); Muad'Dib checks
- **Closure finding:** `docs/internal/philo/phase-11/grounding/backend.md` F1, F5, F7; `faces.md` F2; rulings R6, R7
- **Design:** `design/document-sources.md` sections 5–6 (binding); `../phase-10-the-channels/design/send-lifecycle.md` sections 3, 4, 6, 8 (binding, unchanged)
- **Canvas:** none (canvas D, story 03, owns the Destinations face)

## Problem

Slack is not a channel. The meeting's Slack export is a second send path: a mutable Settings webhook read at execution (`holdspeak/web/routes/actuator_shared.py:265`; `holdspeak/services/meeting_aftercare_service.py:106`), a URL validator that accepts any HTTPS host (`holdspeak/slack_export.py:49`), redirects followed (`holdspeak/plugins/builtin/webhook_post_actuator.py:125`), any 2xx taken as success (`:147`), and a posture path that approves and posts in one call (`holdspeak/services/meeting_aftercare_service.py:170`). Its face row says Send but only proposes (faces.md §4).

## Scope

- **In:** the Slack channel (design section 5): the destination (`{key_ref}`, `{channel_label}`), the webhook URL saved once into the native keyring under `slack:<key_ref>` through an HTTP-only held-secret operation (its name in this story's first commit, checked by Muad'Dib), the host rule at save, the Markdown-to-Slack-text serializer and the frozen `{"text": ...}` body, the size refusal as Q1 rules, the `external.egress` child to exactly `hooks.slack.com:443` with parent, principal, broker and digest, redirects refused, exceptions sanitized, the pinned outcome table (POSTED with no link), Check without a post. The aftercare rewrite (design section 6): every reader of `meeting.slack_webhook_url` removed from the send path (the census in section 6), the config field kept as an ignored value and explicitly dropped from Settings reads and writes (design section 6; Astra r1 finding 2: removing the credential registration alone makes `SECRET_PATHS` stop redacting it), the aftercare Slack proposal and executor and `build_slack_connector` removed, the posture path unable to post, the desk actuator's Slack endpoint parked (`slack_moved_to_channel`, stated default D1, a deliberate capability deferral; story 05 parks its face affordance), historical proposals kept readable; the BACKLOG row "Slack as a Send channel" closed and a row for the parked free-text Slack send.
- **Out:** a bot token, a message link (R6); a split or truncated post (Q1); the face (story 05 removes the aftercare rows and the Settings row, and draws Destinations with Slack); the generic webhook actuator's redirect defect (its BACKLOG row stands).

## Acceptance criteria

- [ ] Each pinned outcome through a recording HTTPS edge: `200 ok` → SENT (face word POSTED) with no link in the proof; each FAILED pair; UNKNOWN on a timeout after send, `500 rollup_error`, another `5xx`, a `3xx` (never followed), `200` without the exact `ok`, an unlisted answer. No repost after UNKNOWN or `429`.
- [ ] The bytes on the wire equal the frozen payload; the preview is parsed from those bytes.
- [ ] A URL with another scheme, host or port is refused at save (`slack_webhook_invalid`). A new webhook is a new destination; a send prepared on the old one refuses `destination_parked`.
- [ ] The URL never appears in a row, a payload, a receipt, a log, an API answer or an error (a sentinel fence over every one).
- [ ] Above the Q1 limit, `payload_too_large:slack` before any byte leaves, and the refusal answer carries `size` and `limit` (39,000); fenced through the real refusal producer and the HTTP route, red before the fix (Astra canvas check r2, condition 1). **The contract (Muad'Dib's ruling on PHILO-11-04, Astra built-check r1 F2):** top-level integer `size` and `limit` in the answer, alongside `code` / `error_code: "payload_too_large:slack"` (the existing receipt envelope kept where it applies); `size` is the character count of the final Slack text, `limit` is `39000`. No nested `context` form: the face (`refusalSize`, `web/src/features/channels/channels.ts`) reads the top level only. Today the producer (`holdspeak/services/channel_service.py:344`) sends neither and the route (`holdspeak/web/routes/channels.py:68`) does not serialize exception context: both seams are this story's.
- [ ] The egress child carries the parent, the authenticated owner principal, the broker and the frozen digest; an agent's Slack send is refused `owner_principal_required`.
- [ ] No code posts to Slack except `channel.send`. The posture path is red on main (it posts) and green here (it prepares at most). The desk actuator's Slack target refuses `slack_moved_to_channel`. An old `config.json` with `slack_webhook_url` still loads.
- [ ] A Settings read with a sentinel URL in `config.json` never returns it; a Settings write with the field never sets it (red with only the credential registration removed).

## Effort (not a promise)

PROVISIONAL: 1.5–2 engineering days.

## Test plan

- **Integration:** fences through the real hub on an isolated HOME; the recording HTTPS edge and the in-memory key store of Phase 10 story 03.
- **Rig:** `op` steps for save, preview, prepare and the Slack outcomes.

## Notes

- 2026-09-29 — round two: amended on Astra r1 RATIFY-WITH-CONDITIONS (`checks/charter-astra-r1.md`).
- 2026-09-29 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
