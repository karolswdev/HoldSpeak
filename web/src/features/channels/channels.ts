/* PHILO-10-04: the Send face's shared words, types and wire client (the SEND
 * well in the Room, the Destinations group in Settings -> Connections).
 *
 * Built to the owner's ratified canvases ("Ratify as drawn", 2026-09-29):
 * pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-04-send-canvas/
 * and story-04-destinations-canvas/. The wire is story 01's declared contract
 * (holdspeak/channel_operations.py): `channel.*` over /api/channels/*.
 * Story 02 adds the GitHub, Jira and Confluence channels with flat save
 * arguments (host, repo, kind, number; site, email, key; space_id); story 03
 * adds email. The face words below cover every channel; a channel the hub
 * does not carry yet is refused by the hub by name (REFUSED + its word).
 *
 * Words (ASD-STE100): verbs and states, no prose. A provider's acceptance is
 * never "delivered" (ACCEPTED BY SENDGRID).
 */
import { apiFetch, ApiError } from "../../lib/api";
import { refusalWord } from "../../desk/surface/egress";

export type Channel = "file" | "github" | "jira" | "confluence" | "email";

export type Destination = {
  id: string;
  name: string;
  channel: Channel;
  /** The concrete identity: GitHub {host, login}; Jira and Confluence
   *  {site, email}; email {provider, from_email, from_name, key_ref}; empty
   *  for a folder. Never a key. */
  account: Record<string, string | boolean>;
  target: Record<string, string | number>;
  synced: boolean;
  state: "active" | "parked";
  badge?: string;
  created_at: string;
  parked_at: string | null;
  /** Story 02: the Phase 9 connection this destination's account uses. */
  connection?: { id?: string; state?: string; last_checked_at?: string | null } | null;
};

/** The readable preview the hub derives from the frozen bytes. */
export type WirePreview = { text?: string; title?: string; [k: string]: unknown };

export type Send = {
  id: string;
  document_ref: string;
  destination_id: string;
  destination_name: string | null;
  channel: Channel;
  badge?: string;
  account: Record<string, string | boolean>;
  target: Record<string, string | number>;
  payload_digest: string;
  size?: number;
  preview: WirePreview;
  prepared_by: { kind: string; identity: string };
  /** Set only on a send that went through channel.prepare. */
  prepare_operation_id: string | null;
  send_operation_id?: string | null;
  state: "prepared" | "dispatching" | "sent" | "failed" | "unknown" | "discarded";
  reason: string | null;
  proof: Record<string, unknown> | null;
  file_path: string | null;
  created_at: string;
  dispatch_started_at: string | null;
  settled_at: string | null;
  /** The order sends LEFT in, allocated inside the boundary transaction. */
  dispatch_seq?: number | null;
};

export type PreviewField = { label: string; value: string };
export type Preview = { fields: PreviewField[]; body_kind: "markdown" | "text"; body: string };

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
  sending: "SENDING",
  discarded: "DISCARDED",
  check: "Check",
  lost: "NO ANSWER · RESULT UNKNOWN",
  cannotRead: "CANNOT READ",
  noPreview: "NO PREVIEW",
  keyNotSaved: "KEY NOT SAVED",
  nothingSent: "NOTHING SENT",
} as const;

export const CHANNEL_WORD: Record<Channel, string> = {
  file: "FILE",
  github: "GITHUB",
  jira: "JIRA",
  confluence: "CONFLUENCE",
  email: "EMAIL",
};

/** The face word of a SENT row, per channel. */
export const SENT_WORD: Record<Channel | "manual", string> = {
  file: "SAVED",
  github: "POSTED",
  jira: "COMMENTED",
  confluence: "BLOG POSTED",
  email: "ACCEPTED BY SENDGRID",
  manual: "DELIVERED",
};
export const sentWord = (channel: string): string =>
  SENT_WORD[channel as Channel] ?? channel.toUpperCase();

/** Refusals (before the boundary: nothing ran). */
const REFUSED: Record<string, string> = {
  github_identity_changed: "GITHUB ACCOUNT CHANGED",
  github_not_logged_in: "GITHUB NOT SIGNED IN",
  github_target_invalid: "REPOSITORY NOT VALID",
  atlassian_not_signed_in: "NOT SIGNED IN",
  atlassian_not_logged_in: "NOT SIGNED IN",
  atlassian_email_invalid: "ADDRESS NOT VALID",
  atlassian_identity_unverified: "ACCOUNT NOT VERIFIED",
  atlassian_switch_failed: "ACCOUNT SWITCH FAILED",
  confluence_space_invalid: "SPACE ID NOT VALID",
  destination_changed: "DESTINATION CHANGED",
  destination_parked: "DESTINATION PARKED",
  destination_not_saved: "DESTINATION NOT SAVED",
  destination_name_invalid: "NAME MISSING",
  email_key_missing: "NO SENDGRID KEY",
  email_key_store_not_native: "NO SAFE KEY STORE",
  email_recipients_too_many: "TOO MANY RECIPIENTS",
  jira_key_not_single: "ONE KEY ONLY",
  jira_key_invalid: "KEY NOT VALID",
  folder_not_absolute: "FULL FOLDER PATH",
  folder_missing: "NO FOLDER",
  address_invalid: "ADDRESS NOT VALID",
  channel_unknown: "CHANNEL NOT READY",
  invalid_arguments: "NOT VALID",
  preview_changed: "PREVIEW CHANGED",
  payload_changed: "PREVIEW CHANGED",
  send_already_settled: "ALREADY DONE",
  path_outside_folder: "PATH NOT IN FOLDER",
  no_answer: "NO ANSWER",
};
/** Failures (a KNOWN non-delivery). */
const FAILED: Record<string, string> = {
  permission_denied: "NO PERMISSION",
  no_space: "NO SPACE",
  name_taken: "NAME TAKEN",
  not_written: "FILE NOT WRITTEN",
  github_issue_not_found: "ISSUE NOT FOUND",
  github_no_permission: "NO PERMISSION",
  jira_not_found: "WORK ITEM NOT FOUND",
  jira_cannot_edit: "CANNOT COMMENT",
  confluence_space_not_found: "SPACE NOT FOUND",
  atlassian_not_logged_in: "NOT SIGNED IN",
  atlassian_identity_unverified: "ACCOUNT NOT VERIFIED",
  atlassian_switch_failed: "ACCOUNT SWITCH FAILED",
  sender_not_verified: "SENDER NOT VERIFIED",
  sendgrid_forbidden: "SENDGRID REFUSED",
  api_key_invalid: "SENDGRID KEY NOT VALID",
  rate_limited: "RATE LIMITED",
};
/** UNKNOWN reasons: HoldSpeak cannot know. */
const UNKNOWN: Record<string, string> = {
  no_answer: "NO ANSWER",
  interrupted: "INTERRUPTED",
  reaped: "TIMED OUT",
  timeout: "TIMED OUT",
  redirect_refused: "REDIRECT",
  partial_acceptance: "PARTIAL",
  read_back_mismatch: "READ BACK NOT EQUAL",
  missing_after_write: "FILE MISSING",
  read_back_failed: "READ BACK FAILED",
};
const word = (table: Record<string, string>, code: string) =>
  table[code] ?? code.toUpperCase().replace(/[_:]/g, " ");
/** A refusal's word: the channel words above, then the library's refusal
 *  words (the Room's one table: `desk/surface/egress.ts`). */
export const refusedWord = (c: string) => REFUSED[c] ?? refusalWord(c);
export const failedWord = (c: string) => word(FAILED, c);
/** The file channel's unpinned OS errors (`create_<errno>`, `write_<errno>`)
 *  and an effect that raised: HoldSpeak cannot confirm the file. */
export const unknownWord = (c: string) =>
  /^(create|write)_/.test(c) ? "FILE NOT CONFIRMED" : /^(dispatch|recover)_/.test(c) ? "NO ANSWER" : word(UNKNOWN, c);

const MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];
export function stamp(iso: string | null | undefined): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return String(iso);
  return `${MONTHS[d.getMonth()]} ${d.getDate()} ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

/** The short target token for a destination row. Literal: keeps its case. */
export function targetToken(channel: Channel, t: Record<string, string | number>): string {
  switch (channel) {
    case "file": return String(t.folder ?? "").replace(/^\/Users\/[^/]+/, "~");
    case "github": return `${t.repo}${t.kind === "pr" ? " PR" : ""} #${t.number}`;
    case "jira": return String(t.key ?? "");
    case "confluence": return `SPACE ${t.space_id ?? ""}`;
    case "email": {
      const to = String(t.to ?? "").split(",").map((a) => a.trim()).filter(Boolean);
      return (to[0] ?? "") + (to.length > 1 ? ` +${to.length - 1}` : "");
    }
    default: return "";
  }
}

/** The egress chip of a destination (UX-CANON: where egress happens). */
export function egressOf(d: { channel: Channel; account: Record<string, string | boolean>; synced?: boolean }): {
  label: string; scope: "local" | "cloud"; title: string;
} {
  switch (d.channel) {
    case "file":
      return d.synced
        ? { label: "SYNCED FOLDER", scope: "cloud", title: "Synced folder: it leaves this device." }
        : { label: "THIS DEVICE", scope: "local", title: "A folder on this device." };
    case "github": {
      const host = String(d.account.host ?? "github.com");
      return { label: host.toUpperCase(), scope: "cloud", title: host };
    }
    case "jira":
    case "confluence": {
      const site = String(d.account.site ?? "");
      return { label: site.toUpperCase(), scope: "cloud", title: site };
    }
    case "email": return { label: "API.SENDGRID.COM", scope: "cloud", title: "api.sendgrid.com" };
    default: return { label: "", scope: "local", title: "" };
  }
}

/** Where "Check" goes for an UNKNOWN row: the far side. Null for a folder. */
export function farSide(channel: Channel, t: Record<string, string | number>, a: Record<string, string | boolean>): string | null {
  switch (channel) {
    case "github": return `https://${a.host ?? "github.com"}/${t.repo}/${t.kind === "pr" ? "pull" : "issues"}/${t.number}`;
    case "jira": return `https://${a.site}/browse/${t.key}`;
    case "confluence": return `https://${a.site}/wiki/spaces/${t.space_id}/blog`;
    case "email": return "https://app.sendgrid.com/email_activity";
    default: return null;
  }
}

const baseName = (p: string) => p.split("/").filter(Boolean).pop() ?? p;

/** The readable preview: the fields from the destination (or the frozen
 *  send), and the body the hub derived from the frozen bytes. Never raw
 *  JSON or XHTML: the hub's preview is text. */
export function previewOf(
  channel: Channel,
  target: Record<string, string | number>,
  account: Record<string, string | boolean>,
  wire: WirePreview,
  filePath?: string | null,
): Preview {
  const a = account, t = target;
  const body = String(wire.text ?? "");
  switch (channel) {
    case "file":
      return {
        fields: [{ label: "Folder", value: String(t.folder ?? "") },
          ...(filePath ? [{ label: "File", value: baseName(filePath) }] : [])],
        body_kind: "markdown", body,
      };
    case "github":
      return {
        fields: [{ label: "Repository", value: String(t.repo ?? "") },
          { label: t.kind === "pr" ? "Pull request" : "Issue", value: `#${t.number}` },
          { label: "Account", value: `${a.login ?? ""} · ${a.host ?? "github.com"}` }],
        body_kind: "markdown", body,
      };
    case "jira":
      return {
        fields: [{ label: "Work item", value: String(t.key ?? "") },
          { label: "Account", value: `${a.email ?? ""} · ${a.site ?? ""}` }],
        body_kind: "text", body,
      };
    case "confluence":
      return {
        fields: [{ label: "Space", value: String(t.space_id ?? "") },
          { label: "Title", value: String(wire.title ?? "") },
          { label: "Account", value: `${a.email ?? ""} · ${a.site ?? ""}` }],
        body_kind: "text", body,
      };
    case "email": {
      const f: PreviewField[] = [
        { label: "From", value: `${a.from_name ?? ""} <${a.from_email ?? ""}>` },
        { label: "To", value: String(t.to ?? "") },
      ];
      if (t.cc) f.push({ label: "Cc", value: String(t.cc) });
      if (wire.subject) f.push({ label: "Subject", value: String(wire.subject) });
      return { fields: f, body_kind: "text", body };
    }
    default:
      return { fields: [], body_kind: "text", body };
  }
}

/* ── the wire client ───────────────────────────────────────────────── */

export class Refusal extends Error {
  constructor(readonly code: string) { super(code); }
}

/** A read whose answer lacks its list is unreadable, never empty. */
function listOf<T>(r: unknown, key: string): T[] {
  const v = r && typeof r === "object" ? (r as Record<string, unknown>)[key] : undefined;
  if (!Array.isArray(v)) throw new Error(`no ${key} in the answer`);
  return v as T[];
}

async function call<T>(path: string, init: RequestInit & { json?: unknown } = {}): Promise<T> {
  try {
    return await apiFetch<T>(path, init);
  } catch (e) {
    if (e instanceof ApiError && e.status >= 400 && e.status < 500) {
      const p = (e.payload ?? {}) as Record<string, unknown>;
      const code = p.error_code ?? p.code;
      if (code) throw new Refusal(String(code));
    }
    throw e;
  }
}

/* ── the face's own change signal ─────────────────────────────────────
 * Settings and the Room are two windows of one page. A save or a remove in
 * the Destinations group tells every open SEND well to read again, so the
 * Room shows the new destination when he comes back (no reload). The wells
 * also read again on window focus. */
export const DEST_CHANGED = "holdspeak:destinations-changed";
const destChanged = () => window.dispatchEvent(new Event(DEST_CHANGED));

/* The Room's "Add destination" asks Settings to arrive AT the group: the
 * intent is read once by the group when it mounts, or by the event when
 * Settings is already open. */
export const DEST_FOCUS = "holdspeak:destinations-focus";
let focusIntent = false;
export function requestDestinationsFocus() { focusIntent = true; window.dispatchEvent(new Event(DEST_FOCUS)); }
export function takeDestinationsFocus(): boolean { const f = focusIntent; focusIntent = false; return f; }

export type SaveBody = {
  name: string;
  channel: Channel;
  replaces?: string;
  folder?: string; synced?: boolean;
  host?: string; repo?: string; kind?: "issue" | "pr"; number?: number;
  site?: string; email?: string; key?: string; space_id?: string;
  provider?: string; from_email?: string; from_name?: string; to?: string; cc?: string;
};

const commandId = () =>
  (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
    ? crypto.randomUUID() : `cmd-${Date.now()}-${Math.random().toString(36).slice(2)}`);
export { commandId };

export const wire = {
  destinations: (all = false) =>
    call<unknown>(`/api/channels/destinations${all ? "?include_parked=true" : ""}`).then((r) => listOf<Destination>(r, "destinations")),
  save: (body: SaveBody) =>
    call<{ destination: Destination }>("/api/channels/destinations", {
      method: "POST", json: { ...body, command_id: commandId() },
    }).then((r) => { destChanged(); return r.destination; }),
  park: (id: string) =>
    call<{ destination: Destination }>(`/api/channels/destinations/${encodeURIComponent(id)}`, {
      method: "DELETE", json: { command_id: commandId() },
    }).then((r) => { destChanged(); return r.destination; }),
  check: (id: string) =>
    call<{ destination: Destination; check: { state: string } }>(
      `/api/channels/destinations/${encodeURIComponent(id)}/check`, { method: "POST", json: {} }),
  /** Story 03: the SendGrid key, typed once, into the OS keychain. */
  saveKey: (keyRef: string, value: string) =>
    call<{ key_present: boolean }>("/api/channels/keys", { method: "POST", json: { key_ref: keyRef, value } }),
  sends: (updateId: string) =>
    call<unknown>(`/api/channels/sends?update_id=${encodeURIComponent(updateId)}`).then((r) => listOf<Send>(r, "sends")),
  preview: (updateId: string, destinationId: string) =>
    call<{ payload_digest: string; preview: WirePreview }>("/api/channels/preview", {
      method: "POST", json: { update_id: updateId, destination_id: destinationId },
    }),
  send: (body: { command_id: string; send_id?: string; update_id?: string; destination_id?: string; preview_digest?: string }) =>
    call<{ send: Send }>("/api/channels/send", { method: "POST", json: body }).then((r) => r.send),
  discard: (sendId: string) =>
    call<{ send: Send }>(`/api/channels/sends/${encodeURIComponent(sendId)}/discard`, {
      method: "POST", json: { command_id: commandId() },
    }).then((r) => r.send),
};
