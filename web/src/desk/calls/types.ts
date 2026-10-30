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
  /** The Line (2026-10-29): HoldSpeak's own phone line; `state: "off"`
   *  when ai-phone is the phone (or `HOLDSPEAK_LINE=off`). */
  line?: LineStatus;
}

/** The Line's place word (the Engines vocabulary; `calls/service.py` LINE_WORDS). */
export type LineState = "ready" | "starting" | "not_running" | "not_installed" | "not_set_up" | "offline" | "off";
/** Where a secret is: never its value (`holdspeak/line/secrets.py`). */
export type SecretPlace = "keystore" | "environment" | "missing";

/** `GET /api/calls/line/status` and the `line` block of `/api/calls/status`. */
export interface LineStatus {
  node: string;
  state: LineState;
  words: string;
  address: string;
  secrets: { sip_password?: SecretPlace; telnyx_api_key?: SecretPlace };
  machine?: LineMachine;
}

/** A machine's own word of itself, from its last hello (`line/hub.py` _machine). */
export interface LineMachine {
  name?: string;
  platform?: string;
  baresip?: string;
  models?: Array<{ id: string; name: string; state: string }>;
}

/** One row of `GET /api/calls/line/nodes`: an enrolled Line node, the word
 *  from its last hello (stale after 2 minutes: Not running). Never a token. */
export interface LineNode {
  node: string;
  enrolled_at: string;
  state: LineState;
  words: string;
  machine: LineMachine;
}

/** `POST /api/calls/line/codes`: the one-time code (10 minutes, once) and
 *  the whole command to run on that machine. */
export interface LineCode {
  node: string;
  code: string;
  expires_in: number;
  hub: string;
  command: string;
}

/** `POST /api/calls/line/test` (200): the result word, and who was called. */
export interface LineTestResult {
  result: string;
  to: string;
}

/** `calls.line` of GET /api/settings: the secrets are write only (the
 *  read says where each one is). */
export interface LineSettings {
  adapter: "" | "line" | "ai-phone";
  where: string;
  account: {
    kind: "sip" | "telnyx";
    user: string;
    domain: string;
    outbound: string;
    password_ref: string;
    codecs: string[];
  };
  secrets?: { sip_password?: SecretPlace; telnyx_api_key?: SecretPlace };
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
  /** Phone (2026-10-28): the hub's phone is on (`HOLDSPEAK_PHONE`); read only. */
  phone_on?: boolean;
  /** The Line (2026-10-29): the most calls HoldSpeak places in a day (0: no limit). */
  daily_limit?: number;
  line?: LineSettings;
}
