/* Calls (CALLS-DESIGN-2026-10-28 §6): the hub's shapes, as the faces read
 * them. `/api/calls/status`, `/api/calls`, `/api/calls/{id}`, the
 * `call_state` frame and the `calls` section of `/api/settings`. */

export type CallStepId = "install" | "daemon" | "line" | "engine" | "passphrase" | "enable";

export interface CallStep {
  id: CallStepId;
  done: boolean;
  words: string;
}

export interface CallsStatus {
  enabled: boolean;
  aiphone: { state: "not_found" | "not_running" | "running"; words: string };
  lines: { id: string; kind: "trunk" | "sip"; state: string; words: string }[];
  engine: { profile_id: string | null; model: string | null; state: "ready" | "no_tools" | "none"; words: string };
  passphrase_set: boolean;
  listening: boolean;
  active: CallSummary | null;
  steps: CallStep[];
}

export interface CallResult {
  kind: string;
  label: string;
  ref: string;
  effect: "wrote" | "prepared" | "sent";
}

export interface CallSummary {
  id: string;
  direction: "in" | "out";
  remote: string;
  state: "ringing" | "gate" | "live" | "ended";
  started_at: string | null;
  answered_at: string | null;
  ended_at: string | null;
  duration_sec: number | null;
  first_words: string | null;
  hold: { tool: string; words: string } | null;
  results: CallResult[];
  note_ref: string | null;
  project_ref: string | null;
  outcome: string | null;
  ended_by: string | null;
}

export interface CallLine {
  who: "caller" | "holdspeak";
  text: string;
  at: string;
  interrupted: boolean;
}

export interface Call extends CallSummary {
  transcript: CallLine[];
}

export interface CallStateFrame {
  reason: "incoming" | "heard" | "said" | "hold" | "decided" | "result" | "ended" | "status";
  call: Call;
}

/** The `calls` section of GET /api/settings: the passphrase is write only
 *  (the read says `passphrase_set`, never the value). */
export interface CallsSettings {
  enabled: boolean;
  aiphone_dir: string;
  greeting: string;
  allowed_numbers: string[];
  passphrase_set: boolean;
}
