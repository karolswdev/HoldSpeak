// from CALLS-DESIGN §6; replace with a recording when the hub slice lands.
// GET /api/calls/{id} (and the call of a call_state frame): a live call with
// a held send waiting for his yes and one thing already done.
import type { Call } from "../types";

export const callLive: Call = {
  id: "c9b1e0",
  direction: "in",
  remote: "sip:+15550100142@agent",
  state: "live",
  started_at: "2026-10-28T09:12:00Z",
  answered_at: "2026-10-28T09:12:01Z",
  ended_at: null,
  duration_sec: null,
  first_words: "Prepare the 1:1 with Priya and nudge Tomás about the runbook.",
  hold: { tool: "channel.send", words: "Send Runbook reminder to Platform channel" },
  results: [
    { kind: "note", label: "Priya 1:1 prep: agenda, open items, her promotion packet", ref: "note:priya-prep", effect: "wrote" },
    { kind: "action", label: "Nudge Tomás about the runbook", ref: "action:nudge-tomas", effect: "wrote" },
  ],
  note_ref: null,
  project_ref: null,
  outcome: null,
  ended_by: null,
  transcript: [
    { who: "holdspeak", text: "Hello. Say your passphrase.", at: "2026-10-28T09:12:03Z", interrupted: false },
    { who: "caller", text: "Blue heron.", at: "2026-10-28T09:12:06Z", interrupted: false },
    { who: "holdspeak", text: "Hello. What can I do?", at: "2026-10-28T09:12:07Z", interrupted: false },
    { who: "caller", text: "Prepare the 1:1 with Priya and nudge Tomás about the runbook.", at: "2026-10-28T09:12:10Z", interrupted: false },
    { who: "holdspeak", text: "I added a task: Nudge Tomás. I want to send Runbook reminder to Platform channel. Say yes or no.", at: "2026-10-28T09:12:14Z", interrupted: false },
  ],
};
