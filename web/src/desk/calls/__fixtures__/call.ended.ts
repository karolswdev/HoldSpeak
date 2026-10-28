// from CALLS-DESIGN §6; replace with a recording when the hub slice lands.
// GET /api/calls/{id}: the call after it ended; its transcript is a Note.
import type { Call } from "../types";

export const callEnded: Call = {
  id: "c7a2f1",
  direction: "in",
  remote: "sip:+15550100142@agent",
  state: "ended",
  started_at: "2026-10-27T18:40:02Z",
  answered_at: "2026-10-27T18:40:03Z",
  ended_at: "2026-10-27T18:41:15Z",
  duration_sec: 72,
  first_words: "What is on my plate tomorrow?",
  hold: null,
  results: [
    { kind: "note", label: "Tomorrow: three meetings, two reviews", ref: "note:tomorrow-plate", effect: "wrote" },
    { kind: "send", label: "Runbook reminder to Platform channel", ref: "send:runbook-reminder", effect: "sent" },
  ],
  note_ref: "note:call-c7a2f1",
  project_ref: null,
  outcome: "done",
  ended_by: "caller",
  transcript: [
    { who: "holdspeak", text: "Hello. Say your passphrase.", at: "2026-10-27T18:40:04Z", interrupted: false },
    { who: "caller", text: "Blue heron.", at: "2026-10-27T18:40:07Z", interrupted: false },
    { who: "holdspeak", text: "Hello. What can I do?", at: "2026-10-27T18:40:08Z", interrupted: false },
    { who: "caller", text: "What is on my plate tomorrow?", at: "2026-10-27T18:40:12Z", interrupted: false },
    { who: "holdspeak", text: "Three meetings and two reviews. I wrote them in a note.", at: "2026-10-27T18:40:20Z", interrupted: false },
    { who: "caller", text: "Thanks, that's all.", at: "2026-10-27T18:41:10Z", interrupted: false },
    { who: "holdspeak", text: "Goodbye.", at: "2026-10-27T18:41:12Z", interrupted: false },
  ],
};
