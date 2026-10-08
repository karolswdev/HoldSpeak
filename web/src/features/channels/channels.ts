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
 * never "delivered" (ACCEPTED BY SENDGRID, ACCEPTED BY RESEND).
 */
import { wireDate } from "../../desk/surface/format";
import { apiFetch, ApiError } from "../../lib/api";
import { refusalWord } from "../../desk/surface/egress";

/** PHILO-11-04: Slack is the sixth channel (design section 5; story 02 carries its wire).
 *  The face words live here so the well shows a Slack row the day the hub carries it. */
export type Channel = "file" | "github" | "jira" | "confluence" | "email" | "slack";

export type Destination = {
  id: string;
  name: string;
  channel: Channel;
  /** The concrete identity: GitHub {host, login}; Jira and Confluence
   *  {site, email}; email {provider, from_email, from_name, key_ref}; empty
   *  for a folder. Never a key. */
  account: Record<string, string | boolean>;
  /** Email's To and Cc arrive as arrays (read with `list`). */
  target: Record<string, string | number>;
  synced: boolean;
  /** The built-in "HoldSpeak folder" (Documents/HoldSpeak/Sent): always there; no Edit, no Remove. */
  builtin?: boolean;
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
  /** The built-in folder: the sync provider ("icloud", "dropbox", ... or "synced") at the send's boundary. */
  egress?: string | null;
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
  slack: "SLACK",
};

/* ── the email providers (story 03 SendGrid; story 07 Resend) ─────── */

export type EmailProvider = "sendgrid" | "resend";
/** One row per provider the hub carries (holdspeak/services/channel_email.py EMAIL_PROVIDERS). */
export const EMAIL_PROVIDERS: Record<EmailProvider, { label: string; word: string; host: string; activity: string }> = {
  // PHILO-15 04 (gap 13): Resend first, the default; SendGrid stays selectable.
  resend: { label: "Resend", word: "RESEND", host: "api.resend.com", activity: "https://resend.com/emails" },
  sendgrid: { label: "SendGrid", word: "SENDGRID", host: "api.sendgrid.com", activity: "https://app.sendgrid.com/email_activity" },
};
/** The provider a new email destination takes (the hub's `DEFAULT_EMAIL_PROVIDER`). */
export const DEFAULT_EMAIL_PROVIDER: EmailProvider = "resend";
/** An email account's provider. Every saved account names one; an account
 *  without one is read as SendGrid, the only provider before PHILO-10-07. */
export const emailProvider = (a?: Record<string, unknown> | null) =>
  EMAIL_PROVIDERS[String(a?.provider ?? "sendgrid") as EmailProvider] ?? EMAIL_PROVIDERS.sendgrid;

/** The face word of a SENT row, per channel. */
export const SENT_WORD: Record<Channel | "manual", string> = {
  file: "SAVED",
  github: "POSTED",
  jira: "COMMENTED",
  confluence: "BLOG POSTED",
  email: "ACCEPTED BY SENDGRID",
  slack: "POSTED",
  manual: "DELIVERED",
};
/** Email's word names the provider that accepted it (the proof's provider, else the account's). */
export const sentWord = (channel: string, proof?: Record<string, unknown> | null,
  account?: Record<string, unknown> | null): string =>
  channel === "email" ? `ACCEPTED BY ${emailProvider(proof?.provider ? proof : account).word}`
    : SENT_WORD[channel as Channel] ?? channel.toUpperCase();

/* The words below cover EVERY code the channel services can emit: the fence
 * tests/unit/test_philo10_face_words.py derives the codes from the services'
 * source and declarations (tests/unit/_philo10_codes.py) and fails on any code
 * with no word here (PHILO-10-05, Muad'Dib's ruling on #698: no raw code on the
 * face). A code with a variable part (an errno, an exception, an HTTP status)
 * takes its word by prefix. */

/** Refusals (before the boundary: nothing ran). */
const REFUSED: Record<string, string> = {
  github_identity_changed: "GITHUB ACCOUNT CHANGED",
  github_identity_unverified: "GITHUB ACCOUNT NOT VERIFIED",
  github_not_logged_in: "GITHUB NOT SIGNED IN",
  github_target_invalid: "REPOSITORY NOT VALID",
  github_cli_missing: "GH NOT INSTALLED",
  jira_cli_missing: "ACLI NOT INSTALLED",
  confluence_cli_missing: "ACLI NOT INSTALLED",
  atlassian_not_signed_in: "NOT SIGNED IN",
  atlassian_not_logged_in: "NOT SIGNED IN",
  atlassian_email_invalid: "ADDRESS NOT VALID",
  atlassian_identity_unverified: "ACCOUNT NOT VERIFIED",
  atlassian_switch_failed: "ACCOUNT SWITCH FAILED",
  confluence_space_invalid: "SPACE ID NOT VALID",
  destination_changed: "DESTINATION CHANGED",
  destination_parked: "DESTINATION PARKED",
  destination_not_saved: "DESTINATION NOT SAVED",
  destination_builtin: "BUILT IN FOLDER",
  destination_name_invalid: "NAME MISSING",
  document_unknown: "NO DOCUMENT",
  document_kind_unknown: "DOCUMENT TYPE UNKNOWN",
  document_not_found: "DOCUMENT NOT FOUND",
  artifact_body_missing: "ARTIFACT BODY MISSING",
  artifact_not_text: "ARTIFACT NOT TEXT",
  email_address_invalid: "ADDRESS NOT VALID",
  email_key_invalid: "KEY NOT VALID",
  email_key_missing: "NO KEY",
  slack_webhook_missing: "NO WEBHOOK",
  slack_webhook_invalid: "WEBHOOK NOT VALID",
  slack_channel_label_invalid: "CHANNEL NAME NOT VALID",
  slack_key_ref_invalid: "KEY NAME NOT VALID",
  slack_key_store_locked: "KEY STORE LOCKED",
  slack_key_store_not_native: "NO SAFE KEY STORE",
  email_key_ref_invalid: "KEY NAME NOT VALID",
  email_key_store_locked: "KEY STORE LOCKED",
  email_key_store_not_native: "NO SAFE KEY STORE",
  email_provider_unknown: "PROVIDER NOT KNOWN",
  email_recipient_duplicate: "ADDRESS TWICE",
  email_recipients_missing: "NO RECIPIENT",
  email_recipients_too_many: "TOO MANY RECIPIENTS",
  jira_key_not_single: "ONE KEY ONLY",
  jira_key_invalid: "KEY NOT VALID",
  folder_not_absolute: "FULL FOLDER PATH",
  folder_missing: "NO FOLDER",
  address_invalid: "ADDRESS NOT VALID",
  channel_unknown: "CHANNEL NOT READY",
  invalid_arguments: "NOT VALID",
  no_summary: "NO SUMMARY",
  not_published: "NOT PUBLISHED",
  validation_error: "NOT VALID",
  preview_changed: "PREVIEW CHANGED",
  payload_changed: "PREVIEW CHANGED",
  send_already_settled: "ALREADY DONE",
  operation_ended_before_dispatch: "SEND ENDED",
  path_outside_folder: "PATH NOT IN FOLDER",
  name_exhausted: "NO FREE FILE NAME",
  no_answer: "NO ANSWER",
  lock_timeout: "LOCK TIMEOUT",
  not_found: "NOT FOUND",
  owner_required: "OWNER ONLY",
  authority_in_arguments: "NOT VALID",
  unknown_operation: "NOT VALID",
};
/** A refusal code with a variable part: its word by prefix. */
const REFUSED_PREFIX: [string, string][] = [
  ["payload_too_large:slack", "TOO LARGE FOR SLACK"],
  ["payload_too_large:", "TOO LARGE"],
];

/** Failures (a KNOWN non-delivery). */
const FAILED: Record<string, string> = {
  permission_denied: "NO PERMISSION",
  no_space: "NO SPACE",
  name_taken: "NAME TAKEN",
  not_written: "FILE NOT WRITTEN",
  folder_not_created: "FOLDER NOT MADE",
  github_target_not_found: "ISSUE NOT FOUND",
  github_repository_not_found: "REPOSITORY NOT FOUND",
  github_permission_denied: "NO PERMISSION",
  github_not_authenticated: "GITHUB NOT SIGNED IN",
  github_cli_missing: "GH NOT INSTALLED",
  github_cli_not_started: "GH DID NOT START",
  jira_not_found: "WORK ITEM NOT FOUND",
  jira_cannot_be_edited: "CANNOT COMMENT",
  jira_cli_missing: "ACLI NOT INSTALLED",
  jira_cli_not_started: "ACLI DID NOT START",
  confluence_space_not_found: "SPACE NOT FOUND",
  confluence_permission_denied: "NO PERMISSION",
  confluence_cli_missing: "ACLI NOT INSTALLED",
  confluence_cli_not_started: "ACLI DID NOT START",
  atlassian_unauthorized: "NOT SIGNED IN",
  atlassian_not_logged_in: "NOT SIGNED IN",
  atlassian_identity_unverified: "ACCOUNT NOT VERIFIED",
  atlassian_switch_failed: "ACCOUNT SWITCH FAILED",
  sender_not_verified: "SENDER NOT VERIFIED",
  sendgrid_forbidden: "SENDGRID REFUSED",
  api_key_invalid: "SENDGRID KEY NOT VALID",
  resend_key_invalid: "RESEND KEY NOT VALID",
  resend_forbidden: "RESEND REFUSED",
  resend_invalid_request: "REQUEST NOT VALID",
  resend_rate_limited: "RATE LIMITED",
  resend_quota_exceeded: "SEND LIMIT REACHED",
  rate_limited: "RATE LIMITED",
  invalid_request: "REQUEST NOT VALID",
  payload_too_large: "TOO LARGE",
  payload_changed: "PREVIEW CHANGED",
  plan_refused: "COMMAND NOT VALID",
  subprocess_refused: "COMMAND NOT PERMITTED",
  egress_refused: "SEND NOT PERMITTED",
  email_provider_unknown: "PROVIDER NOT KNOWN",
  email_key_missing: "NO KEY",
  email_key_store_locked: "KEY STORE LOCKED",
  email_key_store_not_native: "NO SAFE KEY STORE",
  url_not_admitted: "ADDRESS NOT PERMITTED",
  connect_refused: "CONNECTION REFUSED",
  dns_failed: "HOST NOT FOUND",
  tls_failed: "SECURE CONNECTION FAILED",
  timeout: "TIMED OUT",
  transport_error: "CONNECTION FAILED",
  /* PHILO-11-05: Slack's pinned non-deliveries (design section 5) and its key custody. */
  invalid_payload: "MESSAGE NOT VALID",
  action_prohibited: "SLACK REFUSED",
  channel_not_found: "CHANNEL NOT FOUND",
  channel_is_archived: "CHANNEL ARCHIVED",
  "payload_too_large:slack": "TOO LARGE FOR SLACK",
  slack_webhook_missing: "NO WEBHOOK",
  slack_webhook_invalid: "WEBHOOK NOT VALID",
  slack_key_store_locked: "KEY STORE LOCKED",
  slack_key_store_not_native: "NO SAFE KEY STORE",
};
/** A failure code with a variable part: its word by prefix (none today). */
const FAILED_PREFIX: [string, string][] = [
];

/** UNKNOWN reasons: HoldSpeak cannot know. */
const UNKNOWN: Record<string, string> = {
  no_answer: "NO ANSWER",
  interrupted: "INTERRUPTED",
  github_interrupted: "INTERRUPTED",
  jira_interrupted: "INTERRUPTED",
  confluence_interrupted: "INTERRUPTED",
  reaped: "TIMED OUT",
  timeout: "TIMED OUT",
  redirect_refused: "REDIRECT",
  partial_acceptance: "PARTIAL",
  read_back_mismatch: "READ BACK NOT EQUAL",
  missing_after_write: "FILE MISSING",
  read_back_failed: "READ BACK FAILED",
  accepted_without_message_id: "NO MESSAGE ID",
  github_no_proof: "NO PROOF",
  jira_no_proof: "NO PROOF",
  confluence_no_proof: "NO PROOF",
  email_key_missing: "NO KEY",
  email_key_store_locked: "KEY STORE LOCKED",
  email_key_store_not_native: "NO SAFE KEY STORE",
  url_not_admitted: "ADDRESS NOT PERMITTED",
  connect_refused: "CONNECTION REFUSED",
  dns_failed: "HOST NOT FOUND",
  tls_failed: "SECURE CONNECTION FAILED",
  transport_error: "CONNECTION FAILED",
  /* PHILO-11-05: Slack answered, but not with its exact `ok` (design section 5). */
  ack_missing: "NO OK FROM SLACK",
  rollup_error: "SLACK ERROR",
  plan_refused: "COMMAND NOT VALID",
  slack_webhook_missing: "NO WEBHOOK",
  slack_webhook_invalid: "WEBHOOK NOT VALID",
  slack_key_store_locked: "KEY STORE LOCKED",
  slack_key_store_not_native: "NO SAFE KEY STORE",
};
/** An UNKNOWN code with a variable part: the file channel's unpinned OS
 *  errors (`create_<errno>`, `write_<errno>`), an effect that raised, a CLI's
 *  unpinned exit, an unpinned HTTP status. */
const UNKNOWN_PREFIX: [string, string][] = [
  ["create_", "FILE NOT CONFIRMED"],
  ["write_", "FILE NOT CONFIRMED"],
  ["dispatch_", "NO ANSWER"],
  ["recover_", "NO ANSWER"],
  ["github_exit_", "NO CLEAR ANSWER"],
  ["jira_exit_", "NO CLEAR ANSWER"],
  ["confluence_exit_", "NO CLEAR ANSWER"],
  ["unpinned_", "NO CLEAR ANSWER"],
];

const byPrefix = (table: [string, string][], code: string) => table.find(([p]) => code.startsWith(p))?.[1];
const word = (table: Record<string, string>, prefixes: [string, string][], code: string) =>
  table[code] ?? byPrefix(prefixes, code) ?? code.toUpperCase().replace(/[_:]/g, " ");
/** A refusal's word: the channel words above, then the library's refusal
 *  words (the Room's one table: `desk/surface/egress.ts`). */
export const refusedWord = (c: string) => REFUSED[c] ?? byPrefix(REFUSED_PREFIX, c) ?? refusalWord(c);
export const failedWord = (c: string) => word(FAILED, FAILED_PREFIX, c);
export const unknownWord = (c: string) => word(UNKNOWN, UNKNOWN_PREFIX, c);

const MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];
export function stamp(iso: string | null | undefined): string {
  if (!iso) return "";
  const d = wireDate(iso);
  if (!d) return String(iso);
  return `${MONTHS[d.getMonth()]} ${d.getDate()} ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

/** The short target token for a destination row. Literal: keeps its case. */
/** PHILO-15 lane 12 (B23): what a SEND well row and its preview call the
 *  target. A folder reads by its NAME, the last two folder names
 *  (`HoldSpeak/Sent`), never a path; the `~` token stays on hover
 *  (`targetToken`) and in Settings ▸ Destinations. Other channels read their
 *  token. */
export function targetName(channel: Channel, t: Record<string, string | number>): string {
  if (channel !== "file") return targetToken(channel, t);
  const path = String(t.display || t.folder || "");
  const names = path.split("/").filter((n) => n && n !== "~");
  return names.slice(-2).join("/") || path;
}

export function targetToken(channel: Channel, t: Record<string, string | number>): string {
  switch (channel) {
    // The hub's short token (home_paths.py, the known HOME as ~); never a
    // guess from a /Users/<name> pattern (Astra, #869).
    case "file": return t.display ? String(t.display) : String(t.folder ?? "");
    case "github": return `${t.repo}${t.kind === "pr" ? " PR" : ""} #${t.number}`;
    case "jira": return String(t.key ?? "");
    case "confluence": return `SPACE ${t.space_id ?? ""}`;
    case "email": {
      const raw = t.to as unknown;
      const to = (Array.isArray(raw) ? raw.map(String) : String(raw ?? "").split(",")).map((a) => a.trim()).filter(Boolean);
      return (to[0] ?? "") + (to.length > 1 ? ` +${to.length - 1}` : "");
    }
    case "slack": return String(t.channel_label ?? "");
    default: return "";
  }
}

/** iCloud Drive syncs the folder: the file leaves this device. */
export const ICLOUD_EGRESS = { label: "ICLOUD", scope: "cloud" as const, title: "iCloud Drive syncs this folder: the file leaves this device." };

/** The sync service that takes the built-in folder's files off this device
 *  (the hub's `target.cloud` and a send's `egress`). Any provider the hub
 *  does not name reads SYNCED: "not iCloud" is never "this device". */
const SYNC_EGRESS: Record<string, { label: string; scope: "cloud"; title: string }> = {
  icloud: ICLOUD_EGRESS,
  dropbox: { label: "DROPBOX", scope: "cloud", title: "Dropbox syncs this folder: the file leaves this device." },
  googledrive: { label: "GOOGLE DRIVE", scope: "cloud", title: "Google Drive syncs this folder: the file leaves this device." },
  onedrive: { label: "ONEDRIVE", scope: "cloud", title: "OneDrive syncs this folder: the file leaves this device." },
};
const SYNCED_EGRESS = { label: "SYNCED", scope: "cloud" as const, title: "A sync app syncs this folder: the file leaves this device." };
export function syncEgress(provider: unknown): { label: string; scope: "cloud"; title: string } | null {
  if (!provider) return null;
  return SYNC_EGRESS[String(provider)] ?? SYNCED_EGRESS;
}

/** The egress chip of a destination (UX-CANON: where egress happens). */
export function egressOf(d: {
  channel: Channel; account: Record<string, string | boolean>; synced?: boolean; target?: Record<string, string | number>;
}): {
  label: string; scope: "local" | "cloud"; title: string;
} {
  switch (d.channel) {
    case "file":
      // The built-in HoldSpeak folder in an iCloud Drive Documents folder (the hub reads it now).
      { const sync = syncEgress(d.target?.cloud); if (sync) return sync; }
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
    case "email": {
      const host = emailProvider(d.account).host;
      return { label: host.toUpperCase(), scope: "cloud", title: host };
    }
    case "slack": return { label: "HOOKS.SLACK.COM", scope: "cloud", title: "hooks.slack.com" };
    default: return { label: "", scope: "local", title: "" };
  }
}

/** Where "Check" goes for an UNKNOWN row: the far side. Null for a folder. */
export function farSide(channel: Channel, t: Record<string, string | number>, a: Record<string, string | boolean>): string | null {
  switch (channel) {
    case "github": return `https://${a.host ?? "github.com"}/${t.repo}/${t.kind === "pr" ? "pull" : "issues"}/${t.number}`;
    case "jira": return `https://${a.site}/browse/${t.key}`;
    case "confluence": return `https://${a.site}/wiki/spaces/${t.space_id}/blog`;
    case "email": return emailProvider(a).activity;
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
        // B23: the folder by its name, never the raw path (`/private/var/...`).
        fields: [{ label: "Folder", value: targetName("file", t) },
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
      // Parsed back from the frozen provider request (story 03): From, To, Cc, Subject, the text.
      const list = (v: unknown) => (Array.isArray(v) ? v.map(String).join(", ") : String(v ?? ""));
      const f: PreviewField[] = [
        { label: "From", value: String(wire.from ?? `${a.from_name ?? ""} <${a.from_email ?? ""}>`) },
        { label: "To", value: list(wire.to ?? t.to) },
      ];
      const cc = list(wire.cc ?? t.cc);
      if (cc) f.push({ label: "Cc", value: cc });
      if (wire.subject) f.push({ label: "Subject", value: String(wire.subject) });
      return { fields: f, body_kind: "text", body: String(wire.text ?? body) };
    }
    case "slack":
      // A webhook has no read call: the fields are the channel label and the one host.
      return {
        fields: [{ label: "Channel", value: String(t.channel_label ?? "") }, { label: "Webhook", value: "hooks.slack.com" }],
        body_kind: "text", body,
      };
    default:
      return { fields: [], body_kind: "text", body };
  }
}

/* ── the wire client ───────────────────────────────────────────────── */

/** A named refusal. `detail` is the hub's whole answer: a size refusal
 *  carries `size` and `limit` there (design section 5, canvas T1). */
export class Refusal extends Error {
  constructor(readonly code: string, readonly detail: Record<string, unknown> = {}) { super(code); }
}

/** The size and the limit a size refusal names, when the answer carries them:
 *  top-level integers beside `code` / `error_code` (story 02's contract for
 *  `payload_too_large:slack`: `size` the final Slack text's characters,
 *  `limit` 39000). The word is CHARACTERS: a byte-limited channel that reuses
 *  this must carry its unit (BACKLOG). */
export function refusalSize(r: { detail?: Record<string, unknown> } | null | undefined): { size: number; limit: number } | null {
  const d = r?.detail ?? {};
  return Number.isInteger(d.size) && Number.isInteger(d.limit) ? { size: d.size as number, limit: d.limit as number } : null;
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
    if (e instanceof ApiError) {
      // The named refusal wins over the HTTP class (Codex Astra r2 on #697): an answer that carries a
      // terminal REFUSED receipt is a known refusal whatever its status; a 4xx that names its code is one.
      const p = (e.payload ?? {}) as Record<string, unknown>;
      const code = p.error_code ?? p.code;
      const receipt = (p.receipt ?? null) as Record<string, unknown> | null;
      if (code && (receipt?.state === "refused" || (e.status >= 400 && e.status < 500))) throw new Refusal(String(code), p);
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
  provider?: string; from_email?: string; from_name?: string; key_ref?: string; to?: string[]; cc?: string[];
  channel_label?: string;
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
    call<{ destination: Destination; check: { state: string; answered_at?: string | null } }>(
      `/api/channels/destinations/${encodeURIComponent(id)}/check`, { method: "POST", json: {} }),
  /** Story 03/07: the provider's key, typed once, into the OS keychain (the key is the body, never shown again). */
  saveKey: (keyRef: string, value: string, provider: EmailProvider = DEFAULT_EMAIL_PROVIDER) =>
    call<{ key_ref: string; saved?: boolean }>(`/api/channels/email-keys/${encodeURIComponent(keyRef)}`, {
      method: "PUT", json: { api_key: value, provider, command_id: commandId() },
    }),
  /** PHILO-11-05: a Slack webhook, typed once, into the OS keychain (design section 5). The URL is the
   *  credential: HTTP only, never shown again. The hub mints the key_ref the destination save then names. */
  saveSlackWebhook: (webhookUrl: string) =>
    call<{ key_ref: string; saved?: boolean }>("/api/channels/slack-webhooks", {
      method: "POST", json: { webhook_url: webhookUrl, command_id: commandId() },
    }),
  sends: (documentRef: string) =>
    call<unknown>(`/api/channels/sends?document_ref=${encodeURIComponent(documentRef)}`).then((r) => listOf<Send>(r, "sends")),
  preview: (documentRef: string, destinationId: string) =>
    call<{ payload_digest: string; preview: WirePreview }>("/api/channels/preview", {
      method: "POST", json: { document_ref: documentRef, destination_id: destinationId },
    }),
  send: (body: { command_id: string; send_id?: string; document_ref?: string; destination_id?: string; preview_digest?: string }) =>
    call<{ send: Send }>("/api/channels/send", { method: "POST", json: body }).then((r) => r.send),
  discard: (sendId: string) =>
    call<{ send: Send }>(`/api/channels/sends/${encodeURIComponent(sendId)}/discard`, {
      method: "POST", json: { command_id: commandId() },
    }).then((r) => r.send),
};
