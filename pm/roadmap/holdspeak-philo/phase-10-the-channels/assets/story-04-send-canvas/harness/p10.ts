/* PHILO-10-04 canvas: the shared words, types and wire client of the two
 * proposals (the Send well and the Destinations group). The WIRE these call
 * is unbuilt (stories 01-03); shim.ts stands in for it and says how.
 *
 * Every word here is a proposal for the owner's ratification (ASD-STE100:
 * verbs and states, no prose). The per-channel outcome words are the
 * charter's (design/send-lifecycle.md sections 4 and 8).
 */
import { apiFetch, ApiError } from "@w/lib/api";

export type Channel = "file" | "github" | "jira" | "confluence" | "email";

export type Destination = {
  id: string;
  name: string;
  channel: Channel;
  /** The CONCRETE identity (design section 1): GitHub {host, login}; Jira
   *  and Confluence {site, email}; email {provider, from_email, from_name,
   *  key_ref, key_present}; empty for a folder. Never a key. */
  account: Record<string, string | boolean>;
  target: Record<string, string | number>;
  synced: boolean;
  state: "active" | "parked";
  created_at: string;
  parked_at: string | null;
  checked_at: string | null;
};

export type PreviewField = { label: string; value: string };
export type Preview = {
  fields: PreviewField[];
  /** "markdown" renders through the library Material; "text" as plain lines. */
  body_kind: "markdown" | "text";
  body: string;
};

export type Send = {
  id: string;
  update_id: string;
  destination_id: string;
  destination_name: string;
  channel: Channel;
  target: Record<string, string | number>;
  account: Record<string, string | boolean>;
  draft_revision: number;
  payload_digest: string;
  preview: Preview;
  prepared_by_kind: "owner" | "steward" | "agent";
  prepared_by_identity: string;
  state: "prepared" | "dispatching" | "sent" | "failed" | "unknown" | "discarded";
  proof: Record<string, string | number> | null;
  reason: string | null;
  created_at: string;
  settled_at: string | null;
};

/* ── words ─────────────────────────────────────────────────────────── */

export const SEND_WORDS = {
  section: "SEND",
  send: "Send",
  sendAgain: "Send again",
  retry: "Retry",
  discard: "Discard",
  discardArmed: "Discard?",
  addDestination: "Add destination",
  noDestination: "NO DESTINATION",
  prepared: "PREPARED",
  history: "DELIVERY",
  unknownChip: "RESULT UNKNOWN",
  lastUnknown: "LAST SEND UNKNOWN",
  lastFailed: "LAST SEND FAILED",
  discarded: "DISCARDED",
  check: "Check",
  lost: "NO ANSWER · RESULT UNKNOWN",
  cannotRead: "CANNOT READ",
  noPreview: "NO PREVIEW",
  keyNotSaved: "KEY NOT SAVED",
} as const;

export const CHANNEL_WORD: Record<Channel, string> = {
  file: "FILE",
  github: "GITHUB",
  jira: "JIRA",
  confluence: "CONFLUENCE",
  email: "EMAIL",
};

/** The face word of a SENT row, per channel (the charter's words). */
export const SENT_WORD: Record<Channel | "manual", string> = {
  file: "SAVED",
  github: "POSTED",
  jira: "COMMENTED",
  confluence: "BLOG POSTED",
  email: "ACCEPTED BY SENDGRID",
  manual: "DELIVERED",
};

/** Refusals (before the boundary: nothing ran). */
const REFUSED: Record<string, string> = {
  github_identity_changed: "GITHUB ACCOUNT CHANGED",
  github_not_logged_in: "GITHUB NOT SIGNED IN",
  atlassian_not_signed_in: "NOT SIGNED IN",
  destination_changed: "DESTINATION CHANGED",
  destination_parked: "DESTINATION PARKED",
  email_key_missing: "NO SENDGRID KEY",
  email_key_store_not_native: "NO SAFE KEY STORE",
  email_recipients_too_many: "TOO MANY RECIPIENTS",
  jira_key_not_single: "ONE KEY ONLY",
  github_repo_invalid: "REPOSITORY NOT VALID",
  number_invalid: "NUMBER NOT VALID",
  folder_not_absolute: "FULL FOLDER PATH",
  address_invalid: "ADDRESS NOT VALID",
  name_missing: "NAME MISSING",
  preview_changed: "PREVIEW CHANGED",
  owner_principal_required: "OWNER ONLY",
  payload_too_large: "TOO LARGE",
  send_already_settled: "ALREADY DONE",
  update_not_published: "NOT PUBLISHED",
};
/** Failures (a KNOWN non-delivery). */
const FAILED: Record<string, string> = {
  github_issue_not_found: "ISSUE NOT FOUND",
  github_no_permission: "NO PERMISSION",
  jira_not_found: "WORK ITEM NOT FOUND",
  jira_cannot_edit: "CANNOT COMMENT",
  confluence_space_not_found: "SPACE NOT FOUND",
  sender_not_verified: "SENDER NOT VERIFIED",
  sendgrid_forbidden: "SENDGRID REFUSED",
  api_key_invalid: "SENDGRID KEY NOT VALID",
  rate_limited: "RATE LIMITED",
  not_written: "FILE NOT WRITTEN",
};
/** UNKNOWN reasons: HoldSpeak cannot know. */
const UNKNOWN: Record<string, string> = {
  no_answer: "NO ANSWER",
  interrupted: "INTERRUPTED",
  reaped: "TIMED OUT",
  redirect_refused: "REDIRECT",
  partial_acceptance: "PARTIAL",
};
const word = (table: Record<string, string>, code: string) =>
  table[code] ?? code.toUpperCase().replace(/[_:]/g, " ");
export const refusedWord = (c: string) => word(REFUSED, c);
export const failedWord = (c: string) => word(FAILED, c);
export const unknownWord = (c: string) => word(UNKNOWN, c);

const MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];
export function stamp(iso: string | null | undefined): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return String(iso);
  return `${MONTHS[d.getMonth()]} ${d.getDate()} ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

/** The short target token for a destination row. */
export function targetToken(channel: Channel, t: Record<string, string | number>): string {
  switch (channel) {
    case "file": return String(t.folder ?? "").replace(/^\/Users\/[^/]+/, "~");
    case "github": return `${t.repo}${t.kind === "pr" ? " PR" : ""} #${t.number}`;
    case "jira": return String(t.key ?? "");
    case "confluence": return `SPACE ${t.space}`;
    case "email": {
      const to = String(t.to ?? "").split(",").map((a) => a.trim()).filter(Boolean);
      return to[0] + (to.length > 1 ? ` +${to.length - 1}` : "");   // the first To address and the count of the others
    }
  }
}

/** The egress chip of a destination (UX-CANON §A.9: where egress happens). */
export function egressOf(d: { channel: Channel; account: Record<string, string | boolean>; synced?: boolean }): {
  label: string; scope: "local" | "cloud"; title: string;
} {
  switch (d.channel) {
    case "file":
      return d.synced
        ? { label: "SYNCED FOLDER", scope: "cloud", title: "The owner marked this folder synced: it leaves this device." }
        : { label: "THIS DEVICE", scope: "local", title: "A folder on this device." };
    case "github": return { label: String(d.account.host ?? "github.com").toUpperCase(), scope: "cloud", title: String(d.account.host ?? "github.com") };
    case "jira":
    case "confluence": return { label: String(d.account.site ?? "").toUpperCase(), scope: "cloud", title: String(d.account.site ?? "") };
    case "email": return { label: "API.SENDGRID.COM", scope: "cloud", title: "api.sendgrid.com" };
  }
}

/** Where "Check" goes for an UNKNOWN or a SENT row: the far side. */
export function farSide(channel: Channel, t: Record<string, string | number>, a: Record<string, string | boolean>): string | null {
  switch (channel) {
    case "github": return `https://github.com/${t.repo}/${t.kind === "pr" ? "pull" : "issues"}/${t.number}`;
    case "jira": return `https://${a.site}/browse/${t.key}`;
    case "confluence": return `https://${a.site}/wiki/spaces/${t.space}/blog`;
    case "email": return "https://app.sendgrid.com/email_activity";
    case "file": return null;
  }
}

/* ── the wire client (shim-served) ─────────────────────────────────── */

export class Refusal extends Error {
  constructor(readonly kind: "refused" | "failed", readonly code: string) { super(code); }
}

async function call<T>(path: string, init: RequestInit & { json?: unknown } = {}): Promise<T> {
  try {
    return await apiFetch<T>(path, init);
  } catch (e) {
    if (e instanceof ApiError && e.status >= 400 && e.status < 500) {
      const p = (e.payload ?? {}) as Record<string, unknown>;
      if (p.error_code) throw new Refusal(p.outcome === "failed" ? "failed" : "refused", String(p.error_code));
    }
    throw e;
  }
}

/* ── the face's own change signal ─────────────────────────────────────
 * Settings and the Room are two windows of one page. A save or a remove in
 * the Destinations group tells every open SEND well to read again, so the
 * Room shows the new destination when he comes back (no reload). The wells
 * also read again on window focus. */
export const DEST_CHANGED = "p10:destinations-changed";
const destChanged = () => window.dispatchEvent(new Event(DEST_CHANGED));

/* The Room's "Add destination" asks Settings to arrive AT the group: the
 * intent is read once by the group when it mounts, or by the event when
 * Settings is already open. */
export const DEST_FOCUS = "p10:destinations-focus";
let focusIntent = false;
export function requestDestinationsFocus() { focusIntent = true; window.dispatchEvent(new Event(DEST_FOCUS)); }
export function takeDestinationsFocus(): boolean { const f = focusIntent; focusIntent = false; return f; }

export const wire = {
  destinations: (all = false) =>
    call<{ destinations: Destination[] }>(`/api/channels/destinations${all ? "?include_parked=true" : ""}`).then((r) => r.destinations),
  addDestination: (body: Partial<Destination> & { replaces?: string }) =>
    call<{ destination: Destination }>("/api/channels/destinations", { method: "POST", json: body }).then((r) => { destChanged(); return r.destination; }),
  park: (id: string) =>
    call<{ destination: Destination }>(`/api/channels/destinations/${id}`, { method: "DELETE" }).then((r) => { destChanged(); return r; }),
  check: (id: string) => call<{ destination: Destination; state: string }>(`/api/channels/destinations/${id}/check`, { method: "POST", json: {} }),
  saveKey: (keyRef: string, value: string) =>
    call<{ key_present: boolean }>("/api/channels/keys", { method: "POST", json: { key_ref: keyRef, value } }),
  // Argument names as story 01 built them (holdspeak/channel_operations.py).
  sends: (updateId: string) =>
    call<{ sends: Send[] }>(`/api/channels/sends?update_id=${encodeURIComponent(updateId)}`).then((r) => r.sends),
  preview: (updateId: string, destinationId: string) =>
    call<{ payload_digest: string; preview: Preview; draft_revision: number }>("/api/channels/preview", {
      method: "POST", json: { update_id: updateId, destination_id: destinationId },
    }),
  send: (body: { command_id: string; send_id?: string; update_id?: string; destination_id?: string; preview_digest?: string }) =>
    call<{ send: Send; replayed?: boolean }>("/api/channels/send", { method: "POST", json: body }).then((r) => r.send),
  discard: (sendId: string, commandId: string) =>
    call<{ send: Send }>(`/api/channels/sends/${sendId}/discard`, { method: "POST", json: { command_id: commandId } }),
};
