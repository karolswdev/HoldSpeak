/* Phone (PHONE-DESIGN-2026-10-28 §9, §10): the faces' reads and writes.
 *
 * One hook holds the Phone wing's copy: the status (paired phones, the
 * line, quiet hours, Reach you), the thread (messages in seq order) and the
 * calls the desk made. A `phone_changed` frame reads the thread again from
 * the last `seq` it holds (the event log's replay, §4), so no reply is lost.
 * A hub without the Phone slice answers 404: the faces then draw "No phone
 * yet" and read nothing more. */
import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, apiFetch, readableError } from "../../lib/api";
import { useOptionalRuntimeBus } from "../../runtime/RuntimeBus";
import { writeCallsSetting } from "./api";
import type {
  PhoneCall, PhoneChangedFrame, PhoneDevice, PhoneMessage, PhonePairing, PhonePushKey, PhonePushTest, PhoneStatus, ReachChannel,
} from "./phoneTypes";

function notFound(error: unknown): boolean {
  return error instanceof ApiError && error.status === 404;
}

/** The hub's phone is on: the `calls` section of the settings says so
 *  (`phone_on`). With it off the hub mounts no /api/phone route, so the
 *  faces read nothing there (no 404 on the console). */
export async function phoneIsOn(): Promise<boolean> {
  try {
    const body = await apiFetch<{ calls?: { phone_on?: boolean } }>("/api/settings");
    return Boolean(body?.calls?.phone_on);
  } catch {
    return false;
  }
}

/** The status; null on a hub without the Phone slice or with Phone off. */
export async function readPhoneStatus(): Promise<PhoneStatus | null> {
  if (!(await phoneIsOn())) return null;
  try {
    const status = await apiFetch<PhoneStatus>("/api/phone/status");
    return status && typeof status === "object" && status.on !== false ? { ...status, devices: status.devices ?? [] } : null;
  } catch (error) {
    if (notFound(error)) return null;
    throw error;
  }
}

export async function readPhoneMessages(afterSeq = 0): Promise<PhoneMessage[]> {
  const body = await apiFetch<{ messages?: PhoneMessage[] }>(`/api/phone/messages?after_seq=${afterSeq}`);
  return Array.isArray(body?.messages) ? body.messages : [];
}

export async function readPhoneCalls(): Promise<PhoneCall[]> {
  const body = await apiFetch<{ calls?: PhoneCall[] }>("/api/phone/calls");
  return Array.isArray(body?.calls) ? body.calls : [];
}

export function sendPhoneMessage(text: string, replyTo?: string | null): Promise<unknown> {
  return apiFetch("/api/phone/messages", { method: "POST", json: replyTo ? { text, reply_to: replyTo } : { text } });
}

export function markPhoneMessageRead(id: string): Promise<unknown> {
  return apiFetch(`/api/phone/messages/${encodeURIComponent(id)}/read`, { method: "POST", json: {} });
}

/** One verb on a desk call: `again` (a missed call), `ring` (a held call). */
export function phoneCallVerb(id: string, verb: "again" | "ring" | "decline"): Promise<unknown> {
  return apiFetch(`/api/phone/calls/${encodeURIComponent(id)}/${verb}`, { method: "POST", json: {} });
}

export function startPairing(): Promise<PhonePairing> {
  return apiFetch<PhonePairing>("/api/phone/pair", { method: "POST", json: {} });
}

export function removePhoneDevice(id: string): Promise<unknown> {
  return apiFetch(`/api/phone/devices/${encodeURIComponent(id)}`, { method: "DELETE" });
}

/** His Apple push key: where each part is (never the key). */
export function readPushKey(): Promise<PhonePushKey> {
  return apiFetch<PhonePushKey>("/api/phone/push");
}

/** Keep one part of his Apple push key in the hub's keystore. */
export function savePushKey(part: Partial<{ p8: string; key_id: string; team_id: string; bundle_id: string; host: string }>): Promise<PhonePushKey> {
  return apiFetch<PhonePushKey>("/api/phone/push", { method: "PUT", json: part });
}

/** One silent push to the paired phone; Apple's answer. */
export function testPush(): Promise<PhonePushTest> {
  return apiFetch<PhonePushTest>("/api/phone/push/test", { method: "POST", json: {} });
}

/** Reach you writes his own words (`calls.phone_reach`, the whole map: a
 *  kind not named follows the level), through the one writer of the
 *  `calls` subtree (desk/calls/api.ts). */
export async function writeReach(own: Record<string, ReachChannel>): Promise<void> {
  await writeCallsSetting("phone_reach", own);
}

/** The paired phone (the newest paired), or none. */
export function pairedPhone(status: PhoneStatus | null): PhoneDevice | null {
  const paired = (status?.devices ?? []).filter((device) => device.state === "paired");
  return [...paired].sort((a, b) => String(b.paired_at ?? "").localeCompare(String(a.paired_at ?? "")))[0] ?? null;
}

/** The desk can reach him: a paired phone or a ready number. */
export function canReach(status: PhoneStatus | null): boolean {
  return Boolean(pairedPhone(status) || status?.line?.ready);
}

/** A desk line waits for his reply: it asks (an agent's or a Program's
 *  question, a missed call's follow-up) and no reply came. The twin of the
 *  hub's `needs_you_items` asks. */
export function waitsForReply(message: PhoneMessage, messages: readonly PhoneMessage[]): boolean {
  if (message.direction !== "to_phone") return false;
  const origin = String(message.origin_ref ?? "");
  const asks = origin.startsWith("agent:") || origin.startsWith("phone_call:")
    || /:(core_question|agent_question)$/.test(origin);
  return asks && !messages.some((other) => other.reply_to === message.id && other.direction === "from_phone");
}

export interface PhoneState {
  loading: boolean;
  error: string;
  /** null: the hub has no Phone slice (or Phone is off). */
  status: PhoneStatus | null;
  messages: PhoneMessage[];
  calls: PhoneCall[];
}

function mergeMessages(now: PhoneMessage[], next: PhoneMessage[]): PhoneMessage[] {
  const byId = new Map(now.map((message) => [message.id, message]));
  for (const message of next) byId.set(message.id, { ...byId.get(message.id), ...message });
  return [...byId.values()].sort((a, b) => a.seq - b.seq);
}

export function usePhone(enabled = true, thread = true) {
  const [state, setState] = useState<PhoneState>({ loading: true, error: "", status: null, messages: [], calls: [] });
  const alive = useRef(true);
  const seq = useRef(0);
  useEffect(() => () => { alive.current = false; }, []);

  const load = useCallback(async () => {
    try {
      const status = await readPhoneStatus();
      if (!status) {
        if (alive.current) setState({ loading: false, error: "", status: null, messages: [], calls: [] });
        return;
      }
      const [messages, calls] = thread ? await Promise.all([readPhoneMessages(0), readPhoneCalls()]) : [[], []];
      seq.current = messages.reduce((max, message) => Math.max(max, message.seq), 0);
      if (alive.current) setState({ loading: false, error: "", status, messages: mergeMessages([], messages), calls });
    } catch (error) {
      if (alive.current) setState((now) => ({ ...now, loading: false, error: readableError(error) }));
    }
  }, [thread]);

  useEffect(() => { if (enabled) void load(); }, [enabled, load]);

  /** Read what came after the last line held (a reply, a new line). A
   *  receipt on a line already held reads the whole thread. */
  const catchUp = useCallback(async () => {
    try {
      const next = await readPhoneMessages(seq.current);
      const all = next.length ? next : await readPhoneMessages(0);
      seq.current = all.reduce((max, message) => Math.max(max, message.seq), seq.current);
      if (alive.current) setState((now) => ({ ...now, messages: mergeMessages(now.messages, all) }));
    } catch { /* the next frame or the next open reads again */ }
  }, []);

  const subscribe = useOptionalRuntimeBus()?.subscribe;
  useEffect(() => {
    if (!subscribe || !enabled) return;
    return subscribe("phone_changed", (frame) => {
      const data = frame.data as PhoneChangedFrame | null;
      if (data?.kind === "message" && thread) void catchUp();
      else void load();
    });
  }, [subscribe, enabled, thread, catchUp, load]);

  return { ...state, reload: load, catchUp };
}

/** Today (§9): "Reached you 3 times: 1 answered" from the status's last
 *  24 hours, or "" when the desk did not reach him (never "0 times"). */
export function phoneTodayLine(status: PhoneStatus | null): string {
  const today = status?.today;
  const reaches = Math.max(today?.reaches ?? 0, today?.calls ?? 0);
  if (!reaches) return "";
  const times = reaches === 1 ? "1 time" : `${reaches} times`;
  return today?.answered ? `Reached you ${times}: ${today.answered} answered` : `Reached you ${times}`;
}

/** The Today line, read once (and again on a `phone_changed` frame). */
export function usePhoneToday(enabled = true): string {
  const [status, setStatus] = useState<PhoneStatus | null>(null);
  const alive = useRef(true);
  useEffect(() => () => { alive.current = false; }, []);
  const load = useCallback(() => {
    void readPhoneStatus().then((next) => { if (alive.current) setStatus(next); }).catch(() => undefined);
  }, []);
  useEffect(() => { if (enabled) load(); }, [enabled, load]);
  const subscribe = useOptionalRuntimeBus()?.subscribe;
  useEffect(() => (subscribe && enabled ? subscribe("phone_changed", () => load()) : undefined), [subscribe, enabled, load]);
  return phoneTodayLine(status);
}
