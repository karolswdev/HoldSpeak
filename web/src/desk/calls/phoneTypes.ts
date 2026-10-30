/* Phone (PHONE-DESIGN-2026-10-28 §3, §4, §10): the hub's shapes, as the
 * faces read them (recorded in desk/calls/__fixtures__/phone.*.json through
 * the real routes, holdspeak/web/routes/phone.py). `/api/phone/status`,
 * `/api/phone/messages`, `/api/phone/devices`, `/api/phone/calls`,
 * `/api/phone/pair` and the `phone_changed` frame. A field the hub leaves
 * out draws as absent, never as a guess. */

export type PhoneDeviceState = "pairing" | "paired" | "revoked";

export type PhonePushState = "ready" | "no_key" | "http2_unavailable" | "unregistered";

export interface PhoneDevice {
  id: string;
  name: string;
  platform: string;
  state: PhoneDeviceState;
  has_push?: boolean;
  push_kind?: string | null;
  /** Why a push will or will not go (RECIPE PH13, `device_wire`). */
  push_state?: PhonePushState | null;
  paired_at: string;
  last_seen_at?: string | null;
  revoked_at?: string | null;
}

export type PhoneMessageDirection = "to_phone" | "from_phone";

export interface PhoneMessage {
  id: string;
  seq: number;
  direction: PhoneMessageDirection;
  text: string;
  reply_to?: string | null;
  created_at: string;
  delivered_at?: string | null;
  read_at?: string | null;
  /** Where the line came from: `program:<id>:<kind>`,
   *  `program_step:<id>:<kind>`, `agent:<lane>:<n>`, `phone_call:<id>`. */
  origin_ref?: string | null;
  program_step_id?: string | null;
}

export type PhoneCallState = "held" | "ringing" | "answered" | "missed" | "declined" | "ended";

export interface PhoneCall {
  id: string;
  seq: number;
  direction: "to_phone" | "from_phone";
  reason: string;
  urgent: boolean;
  state: PhoneCallState;
  transport: "number" | "app";
  created_at: string;
  answered_at?: string | null;
  ended_at?: string | null;
  end_reason?: string | null;
  duration_s?: number | null;
  /** `call:<Calls call id>` (the number transport) or a note ref. */
  transcript_ref?: string | null;
  decision?: unknown;
}

export type ReachChannel = "message" | "call" | "nothing";

/** One kind that may reach him (§6): his word, whether it is his own, and
 *  the level's word under it. */
export interface ReachChoice {
  word: ReachChannel;
  own: boolean;
  level_word: ReachChannel;
}

export interface PhoneStatus {
  /** The Phone switch (`HOLDSPEAK_PHONE`). */
  on: boolean;
  devices: PhoneDevice[];
  /** The number transport (Settings ▸ Calls). */
  line: { number_set: boolean; ready: boolean; words: string };
  /** The desk's Rhythm quiet hours, as hours of the day (22, 8). */
  quiet_hours: { start: number; end: number; now: boolean };
  urgent_dnd: boolean;
  level: string;
  reach: Record<string, ReachChoice>;
  last_reach: { seq: number; type: string; ts: string; data: Record<string, unknown> } | null;
  /** The last 24 hours. */
  today: { reaches: number; calls: number; answered: number };
  last_seq: number;
}

export interface PhonePairing {
  token: string;
  /** What the QR encodes: the hub's id, the address the press came in on,
   *  the pair token and its end (JSON text). */
  qr_payload: string;
  qr_png_base64: string | null;
  expires_at: string;
}

export interface PhoneChangedFrame {
  kind: "message" | "call" | "device";
  id: string;
  state?: string;
}

/** `GET|PUT /api/phone/push` (PHONE-APNS-KEY): where each part of his Apple
 *  push key is. The key itself never comes back: only `present`. */
export interface PhonePushKey {
  present: { p8: boolean; key_id: boolean; team_id: boolean };
  bundle_id: string;
  push_state: PhonePushState;
}

/** `POST /api/phone/push/test`: Apple's answer to one silent push. */
export interface PhonePushTest {
  answer: "accepted" | "stale" | "refused" | "failed";
  status: number;
  reason: string;
  device_id: string;
}
