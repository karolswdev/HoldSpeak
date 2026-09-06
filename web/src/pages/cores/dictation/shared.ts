// Shared types and utilities used across dictation sub-components.
import { createContext, useContext } from "react";
import { ApiError, newDeliveryId } from "../../../lib/api";
import type { MicPhase } from "../../../lib/micSession";

export function readableValue(value: unknown): string {
  if (value && typeof value === "object") {
    const row = value as Record<string, unknown>;
    for (const key of ["message", "detail", "warning", "error", "label"]) {
      if (typeof row[key] === "string" && row[key]) return row[key];
    }
    return JSON.stringify(value);
  }
  return String(value ?? "");
}

/* HS-111-02 — the ONE receipt channel: every outcome (save whisper,
   refusal, verdict, recovery note) lands as a token in the footer bar
   (the Prefs receipt/refusal pattern). The toast-banner species is
   dead in this program. */
export type ReceiptTone = "ok" | "warn";
export type Receipt = { text: string; tone: ReceiptTone };

export const ReceiptContext = createContext<(text: string, tone?: ReceiptTone) => void>(
  () => undefined,
);

export function useAnnounce() {
  return useContext(ReceiptContext);
}

export function clockNow(): string {
  return new Date().toLocaleTimeString([], { hour12: false });
}

/* HS-112-02 — the delivery half of the deck. */
export const STATE_TOKENS: { id: string; label: string }[] = [
  { id: "idle", label: "Idle" },
  { id: "listening", label: "Listening" },
  { id: "busy", label: "Busy" },
  { id: "landed", label: "Landed" },
  { id: "refused", label: "Refused" },
];

/* HS-112-02 — the AIM: where a released TALK sends the words. FOCUSED
   APP and AGENT go through the real delivery contract; THIS FIELD is
   the old speak-to-fill (the transcript lands in the well, nothing is
   delivered). The pick is the owner's, and it is remembered. */
export const AIM_KEY = "holdspeak.speakAim";
export const AIM_OPTIONS = [
  { value: "focused", label: "Focused app" },
  { value: "agent", label: "Agent" },
  { value: "field", label: "This field" },
];
export const AIM_FACT: Record<string, string> = {
  focused: "FOCUSED APP",
  agent: "AGENT",
  field: "THIS FIELD",
};

/* HS-112-06 — the mic session's own truth, one word each. CLOSED means
   the tracks are stopped; SUSPENDED means the grant is kept and nothing
   is captured; HELD means a push-to-talk hold owns the floor. */
export const MIC_PHASE_FACT: Record<MicPhase, string> = {
  closed: "CLOSED",
  suspended: "SUSPENDED",
  open: "OPEN",
  segmenting: "SEGMENTING",
  held: "HELD",
};
export const MIC_PHASE_LIVE: MicPhase[] = ["open", "segmenting", "held"];

/* The kernel's own refusal vocabulary, rendered as WHAT in the fewest
   words. An unknown code rides through verbatim — never swallowed. */
export const REFUSAL_LABELS: Record<string, string> = {
  no_awaiting_agent: "NO AGENT AWAITING",
  desktop_focus_unresolved: "NO FOCUSED APP",
  desktop_type_driver_unavailable: "NO TYPING DRIVER",
  desktop_type_claim_refused: "KERNEL CLAIM REFUSED",
  desktop_type_refused: "KERNEL REFUSED",
  delivery_pending: "OUTCOME UNKNOWN",
  delivery_conflict: "DELIVERY CONFLICT",
  no_delivery_target: "NO DELIVERY TARGET",
};

export function refusalLabel(code: string): string {
  return REFUSAL_LABELS[code] ?? code.replace(/_/g, " ").toUpperCase();
}

/** The named refusal behind a failed delivery, or "" when it is not one. */
export function refusalCode(reason: unknown): string {
  if (!(reason instanceof ApiError)) return "";
  const payload =
    reason.payload && typeof reason.payload === "object"
      ? (reason.payload as Record<string, unknown>)
      : {};
  for (const key of ["refusal", "error_code", "failure_category"]) {
    const value = payload[key];
    if (typeof value === "string" && value) return value;
  }
  return "";
}

export { newDeliveryId };

/* ── HS-176-02 — the teach loop's vocabulary ──────────────────────────
   FIELD is a three-way cycle. TEXT is the default: the Tuesday mistake
   is a WORDS mistake ("postgress" for PostgreSQL), and the routing
   kinds are a pick over the real enum, never free text. The tokens are
   uppercase because the face's caption step is 11 mono uppercase. */
export const CORRECTION_FIELDS = [
  { value: "text", label: "TEXT" },
  { value: "intent", label: "INTENT" },
  { value: "target", label: "TARGET" },
];

/** One teach outcome, as tokens. Never a sentence (rule A.3). */
export type TeachReceipt = {
  token: string;
  tone?: "ok" | "danger";
  tail?: string;
};

/* The store's own refusal names (`corrections.py`) rendered as the
   receipt the owner reads. `no_change` wrote nothing and is not a
   refusal — it is the honest "you changed nothing". */
export const TEACH_REFUSALS: Record<string, TeachReceipt> = {
  no_change: { token: "NO CHANGE" },
  secret: { token: "REFUSED · SECRET", tone: "danger", tail: "nothing written" },
  one_word: { token: "REFUSED · ONE WORD", tone: "danger", tail: "nothing written" },
  empty: { token: "REFUSED · EMPTY", tone: "danger", tail: "nothing written" },
  kind: { token: "REFUSED · KIND", tone: "danger", tail: "nothing written" },
};

/** A named refusal, or the reason verbatim as a token — never swallowed. */
export function teachReceiptFor(reason: string): TeachReceipt {
  const known = TEACH_REFUSALS[reason];
  if (known) return known;
  const named = reason.trim()
    ? `REFUSED · ${reason.replace(/_/g, " ").toUpperCase()}`
    : "REFUSED";
  return { token: named, tone: "danger", tail: "nothing written" };
}

/** The receipt's spans are truncated at 40 characters (the design's cap). */
export function truncateSpan(text: string, cap = 40): string {
  const clean = text.trim();
  return clean.length > cap ? `${clean.slice(0, cap)}…` : clean;
}
