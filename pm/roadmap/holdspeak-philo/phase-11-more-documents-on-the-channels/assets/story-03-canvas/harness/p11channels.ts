/* PHILO-11-03 CANVAS (PROPOSAL): the channel words and the wire client as
 * stories 01, 02 and 04 will change them. harness/vite.config.mjs resolves
 * every import of web/src/features/channels/channels.ts to THIS module (this
 * module alone reads the real one). What it adds, and nothing else:
 *   - Slack: the sixth channel (design section 5): its words, its egress chip
 *     (HOOKS.SLACK.COM), its preview fields, its refusal and failure words.
 *     A POSTED Slack row has NO link (the webhook answers only `ok`).
 *   - The document refusals of design section 1 and 3.
 *   - The generic wire (design section 4): `document_ref` in place of
 *     `update_id`. A caller that still passes an update id (the product
 *     SendWell on the update face) is read as `project_update:<id>`.
 */
import * as real from "@w/features/channels/channels.real";
import { apiFetch, ApiError } from "@w/lib/api";

export * from "@w/features/channels/channels.real";

export type Channel = real.Channel | "slack";

export const CHANNEL_WORD: Record<Channel, string> = { ...real.CHANNEL_WORD, slack: "SLACK" };
export const SENT_WORD: Record<Channel | "manual", string> = { ...real.SENT_WORD, slack: "POSTED" };
export const sentWord = (channel: string, proof?: Record<string, unknown> | null, account?: Record<string, unknown> | null) =>
  channel === "slack" ? "POSTED" : real.sentWord(channel, proof, account);

/** The Slack limit (owner Q1, "Higher limit, still refuse"; Muad'Dib: 39,000). */
export const SLACK_LIMIT = 39_000;

const REFUSED: Record<string, string> = {
  "payload_too_large:slack": "TOO LARGE FOR SLACK",
  slack_webhook_invalid: "WEBHOOK NOT VALID",
  slack_webhook_missing: "NO WEBHOOK",
  document_kind_unknown: "NO SUCH DOCUMENT",
  document_not_found: "DOCUMENT GONE",
  no_summary: "NO SUMMARY",
};
export const refusedWord = (c: string) => REFUSED[c] ?? real.refusedWord(c);
const FAILED: Record<string, string> = {
  invalid_payload: "SLACK REFUSED THE TEXT",
  action_prohibited: "SLACK REFUSED",
  channel_not_found: "SLACK CHANNEL NOT FOUND",
  channel_is_archived: "SLACK CHANNEL ARCHIVED",
};
export const failedWord = (c: string) => FAILED[c] ?? real.failedWord(c);

export function targetToken(channel: Channel, t: Record<string, string | number>): string {
  return channel === "slack" ? String(t.channel_label ?? "") : real.targetToken(channel, t);
}

export function egressOf(d: { channel: Channel; account: Record<string, string | boolean>; synced?: boolean }) {
  return d.channel === "slack"
    ? { label: "HOOKS.SLACK.COM", scope: "cloud" as const, title: "hooks.slack.com" }
    : real.egressOf(d as Parameters<typeof real.egressOf>[0]);
}

/** A webhook has no read call: nowhere to Check a post (design section 5). */
export function farSide(channel: Channel, t: Record<string, string | number>, a: Record<string, string | boolean>) {
  return channel === "slack" ? null : real.farSide(channel, t, a);
}

export function previewOf(channel: Channel, target: Record<string, string | number>, account: Record<string, string | boolean>,
  wire: real.WirePreview, filePath?: string | null): real.Preview {
  if (channel === "slack") {
    return {
      fields: [{ label: "Channel", value: String(target.channel_label ?? "") },
        { label: "Webhook", value: "hooks.slack.com" }],
      body_kind: "text", body: String(wire.text ?? ""),
    };
  }
  return real.previewOf(channel, target, account, wire, filePath);
}

/* ── the generic wire (design section 4) ─────────────────────────────── */

/** One Refusal class for the whole face (the real one); a refusal's answer rides as `detail`. */
export const Refusal = real.Refusal;
export type Refusal = real.Refusal & { detail?: Record<string, unknown> };

async function call<T>(path: string, init: RequestInit & { json?: unknown } = {}): Promise<T> {
  try {
    return await apiFetch<T>(path, init);
  } catch (e) {
    if (e instanceof ApiError) {
      const p = (e.payload ?? {}) as Record<string, unknown>;
      const code = p.error_code ?? p.code;
      const receipt = (p.receipt ?? null) as Record<string, unknown> | null;
      if (code && (receipt?.state === "refused" || (e.status >= 400 && e.status < 500))) throw Object.assign(new real.Refusal(String(code)), { detail: p });
    }
    throw e;
  }
}
const asRef = (refOrUpdate: string) => (refOrUpdate.includes(":") ? refOrUpdate : `project_update:${refOrUpdate}`);
function listOf<T>(r: unknown, key: string): T[] {
  const v = r && typeof r === "object" ? (r as Record<string, unknown>)[key] : undefined;
  if (!Array.isArray(v)) throw new Error(`no ${key} in the answer`);
  return v as T[];
}

export const wire = {
  ...real.wire,
  sends: (ref: string) =>
    call<unknown>(`/api/channels/sends?document_ref=${encodeURIComponent(asRef(ref))}`).then((r) => listOf<real.Send>(r, "sends")),
  preview: (ref: string, destinationId: string) =>
    call<{ payload_digest: string; preview: real.WirePreview; size?: number }>("/api/channels/preview", {
      method: "POST", json: { document_ref: asRef(ref), destination_id: destinationId },
    }),
  send: (body: { command_id: string; send_id?: string; update_id?: string; document_ref?: string; destination_id?: string; preview_digest?: string }) => {
    const { update_id, ...rest } = body;
    const json = update_id ? { ...rest, document_ref: asRef(update_id) } : rest;
    return call<{ send: real.Send }>("/api/channels/send", { method: "POST", json }).then((r) => r.send);
  },
  discard: (sendId: string) =>
    call<{ send: real.Send }>(`/api/channels/sends/${encodeURIComponent(sendId)}/discard`, {
      method: "POST", json: { command_id: real.commandId() },
    }).then((r) => r.send),
  /** Story 02: the webhook URL, typed once, into the OS keychain (the operation's name is story 02's). */
  saveSlackKey: (keyRef: string, url: string) =>
    call<{ key_ref: string; saved?: boolean }>(`/api/channels/slack-keys/${encodeURIComponent(keyRef)}`, {
      method: "PUT", json: { webhook_url: url, command_id: real.commandId() },
    }),
};
