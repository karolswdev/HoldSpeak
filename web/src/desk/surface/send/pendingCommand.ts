import type { Preview } from "../../../features/channels/channels";

const KEY = "hs.send.pending.v1";

export type HeldCommand = {
  key: string;
  body: { send_id?: string; document_ref?: string; destination_id?: string; preview_digest?: string };
  preview?: Preview;
};
type Pending = { ref: string; target: string; command: HeldCommand };

/** Tab custody only. Reading never dispatches, and an unresolved press never expires. */
export function pendingCommands(): Pending[] {
  const raw = window.sessionStorage.getItem(KEY);
  if (!raw) return [];
  const records: unknown = JSON.parse(raw);
  if (!Array.isArray(records) || records.some((r) => !r || typeof r.ref !== "string"
      || typeof r.target !== "string" || typeof r.command?.key !== "string"
      || !r.command.body || typeof r.command.body !== "object")) {
    throw new Error("pending send storage unreadable");
  }
  return records;
}

/** Must succeed synchronously before the request is allowed to leave the page. */
export function keepPendingCommand(ref: string, target: string, command: HeldCommand): void {
  const records = pendingCommands().filter((r) => r.ref !== ref || r.target !== target);
  window.sessionStorage.setItem(KEY, JSON.stringify([...records, { ref, target, command }]));
}

export function clearPendingCommand(ref: string, target: string, key: string): void {
  const records = pendingCommands().filter((r) => r.ref !== ref || r.target !== target || r.command.key !== key);
  if (records.length) window.sessionStorage.setItem(KEY, JSON.stringify(records));
  else window.sessionStorage.removeItem(KEY);
}

/** Test isolation: ordinary product clearing always names the settled command. */
export function resetPendingCommands(): void {
  window.sessionStorage.removeItem(KEY);
}
