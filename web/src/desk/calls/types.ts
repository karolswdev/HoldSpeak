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
    /** LINE-3b: the Telnyx credential connection and the number pointed at it. */
    connection_id?: string;
    number?: string;
    codecs: string[];
  };
  secrets?: { sip_password?: SecretPlace; telnyx_api_key?: SecretPlace };
}

/** `GET /api/calls/line/telnyx/status` (LINE-3b): where the key is, the
 *  connection, the number, the balance (one read when a key is there). */
export interface TelnyxStatus {
  key: SecretPlace;
  password: SecretPlace;
  connection: { id: string; user: string; domain: string } | null;
  number: string;
  balance: { balance: string; available: string; currency: string } | null;
  error: string;
}

/** `POST /api/calls/line/telnyx/connect`. */
export interface TelnyxConnected {
  connected: boolean;
  created: boolean;
  connection_id: string;
  user: string;
  domain: string;
}

/** One row of `GET /api/calls/line/telnyx/numbers`: the hub's quote is
 *  what the confirm press sends to buy at that cost. */
export interface TelnyxNumber {
  phone_number: string;
  monthly_cost: string;
  upfront_cost: string;
  currency: string;
  quote: string;
}

/** `POST /api/calls/line/telnyx/buy` (the kernel's receipt beside it). */
export interface TelnyxBought {
  phone_number: string;
  order_id: string;
  order_status: string;
  monthly_cost: string;
  upfront_cost: string;
  currency: string;
  operation_id?: string;
}

/** A refused Telnyx press: what failed (`error`), what is kept, the next action. */
export interface TelnyxRefusal {
  error: string;
  reason: string;
  kept?: string;
  next?: string;
}

export interface CallResult {
  kind: string;
  label: string;
  ref: string;
  effect: "wrote" | "prepared" | "sent" | "started";
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
