// Betterment E5 — What runs where: the rows (DESIGN §4 "The words").
//
// One row for each job, named as he says it. A row writes its own scope:
// `global` (Everything else), `capability:<cap>` (one job everywhere), or
// `group:<id>` where the job is a whole group (memory, dictation, speech).
// `probe` is the capability Try it runs (the hub's fixed samples,
// services/route_probe.py); a row without one has no Try it. Three rows
// have none, by the hub's reasons (route_probe.py): Thoughts and Drafts and
// updates do not run through the shared sample path, and speech needs audio.

import type { AssignmentScope } from "./api";

export interface WhatRow {
  id: string;
  name: string;
  scope: AssignmentScope;
  /** The capability the editor reads for this row (a group or global row
   *  takes the roster's editor capability when this is empty). */
  capability: string;
  probe?: string;
  /** Shown without "more". */
  lead?: boolean;
}

export const EVERYTHING_ELSE = "default";

export const WHAT_ROWS: readonly WhatRow[] = [
  { id: EVERYTHING_ELSE, name: "Everything else", scope: { kind: "global" }, capability: "", probe: "ask.answer", lead: true },
  { id: "summaries", name: "Meeting summaries", scope: { kind: "capability", capability_id: "meeting.deferred_analysis" }, capability: "meeting.deferred_analysis", probe: "meeting.deferred_analysis", lead: true },
  { id: "answers", name: "Answers (Ask)", scope: { kind: "capability", capability_id: "ask.answer" }, capability: "ask.answer", probe: "ask.answer", lead: true },
  { id: "automations", name: "Automations", scope: { kind: "capability", capability_id: "workbench.item" }, capability: "workbench.item", probe: "workbench.item", lead: true },
  { id: "live", name: "Live meeting notes", scope: { kind: "capability", capability_id: "meeting.live_analysis" }, capability: "meeting.live_analysis", probe: "meeting.live_analysis" },
  { id: "thread", name: "Thread", scope: { kind: "capability", capability_id: "chat.turn" }, capability: "chat.turn", probe: "chat.turn" },
  { id: "thoughts", name: "Thoughts", scope: { kind: "capability", capability_id: "thought.interview" }, capability: "thought.interview" },
  { id: "drafts", name: "Drafts and updates", scope: { kind: "capability", capability_id: "project.update_draft" }, capability: "project.update_draft" },
  { id: "memory", name: "Background memory", scope: { kind: "group", group_id: "background" }, capability: "", probe: "background.rails_summary" },
  { id: "dictation", name: "Dictation clean-up", scope: { kind: "group", group_id: "writing_dictation" }, capability: "", probe: "speech.rewrite" },
  { id: "speech", name: "Speech to text", scope: { kind: "group", group_id: "speech_recognition" }, capability: "" },
];

/** The roster row id a group or global row reads its editor capability from. */
export function rosterIdOf(row: WhatRow): string | null {
  if (row.scope.kind === "global") return "global";
  if (row.scope.kind === "group") return row.scope.group_id;
  return null;
}
