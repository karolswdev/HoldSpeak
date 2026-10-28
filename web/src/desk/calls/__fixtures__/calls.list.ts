// from CALLS-DESIGN §6; replace with a recording when the hub slice lands.
// GET /api/calls: the past calls, newest first.
import type { CallSummary } from "../types";

export const callsList: { calls: CallSummary[] } = {
  calls: [
    {
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
      results: [],
      note_ref: "note:call-c7a2f1",
      project_ref: null,
      outcome: "done",
      ended_by: "caller",
    },
    {
      id: "c5d0e9",
      direction: "out",
      remote: "+15550100142",
      state: "ended",
      started_at: "2026-10-26T08:05:10Z",
      answered_at: null,
      ended_at: "2026-10-26T08:05:40Z",
      duration_sec: 0,
      first_words: null,
      hold: null,
      results: [],
      note_ref: null,
      project_ref: null,
      outcome: "no_answer",
      ended_by: "holdspeak",
    },
  ],
};
