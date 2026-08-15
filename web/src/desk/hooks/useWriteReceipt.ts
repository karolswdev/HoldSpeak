// HS-132-06 — the ONE write-receipt channel.
//
// The desk's dominant defect was the silent write: a verb fired, the hub
// refused, and the surface said nothing. Every desk write verb now reports
// into this channel. It renders in the surface's existing receipt slot
// (footer receipt bar / in-flow strip) — never over the work — names the
// verb and the cause in label grammar, and offers RETRY when the same call
// can be re-issued. Success stays quiet: a clean write clears the channel
// and draws nothing.
//
// Two doors, one grammar:
//   useWriteReceipt()      — surface-local channel (windows, panels)
//   reportWriteFailure()   — module channel for non-React writers (store)
import {
  createElement,
  useCallback,
  useEffect,
  useState,
  useSyncExternalStore,
  type ReactElement,
} from "react";
import "./write-receipt.css";

export interface WriteFailure {
  /** The verb that failed, in label grammar ("ADD ITEM"). */
  verb: string;
  /** Why it failed, in label grammar ("HUB UNREACHABLE", "HTTP 422"). */
  reason: string;
  /** Re-issues the exact same write, or null when it cannot be replayed. */
  retry: (() => void) | null;
}

export type WriteResult<T> =
  | { ok: true; value: T }
  | { ok: false; reason: string };

/** The one signature every desk write verb reports through. */
export type WriteAttempt = <T>(
  verb: string,
  run: () => Promise<T>,
  opts?: { retry?: boolean },
) => Promise<WriteResult<T>>;

/** Name the cause in label grammar — never prose, never a sentence. */
export function writeFailureReason(cause: unknown): string {
  if (typeof cause === "string" && cause.trim()) return cause.trim().toUpperCase();
  if (typeof Response !== "undefined" && cause instanceof Response)
    return `HTTP ${cause.status}`;
  if (cause && typeof cause === "object") {
    const status = (cause as { status?: unknown }).status;
    if (typeof status === "number" && status > 0) return `HTTP ${status}`;
  }
  if (cause instanceof Error) {
    if (cause.name === "TypeError" || /fetch|network|failed to fetch/i.test(cause.message))
      return "HUB UNREACHABLE";
    if (cause.name === "AbortError") return "ABORTED";
  }
  return "WRITE REFUSED";
}

/** The one label every write refusal wears. */
export function writeFailureLabel(failure: WriteFailure): string {
  return `${failure.verb} FAILED · ${failure.reason}`;
}

/** A resolved Response that the hub refused is a failure too (no throw). */
function refusedResponse(value: unknown): Response | null {
  if (typeof Response !== "undefined" && value instanceof Response)
    return value.ok ? null : value;
  return null;
}

function receiptElement(
  failure: WriteFailure | null,
  onDismiss: () => void,
): ReactElement | null {
  if (!failure) return null;
  return createElement(
    "span",
    { className: "write-receipt", role: "status" },
    createElement("span", { className: "write-receipt-lamp" }),
    createElement(
      "span",
      { className: "write-receipt-label" },
      writeFailureLabel(failure),
    ),
    failure.retry
      ? createElement(
          "button",
          {
            type: "button",
            className: "desk-chip write-receipt-retry",
            onClick: failure.retry,
          },
          "Retry",
        )
      : null,
    createElement(
      "button",
      {
        type: "button",
        className: "desk-chip write-receipt-dismiss",
        onClick: onDismiss,
      },
      "OK",
    ),
  );
}

/**
 * Surface-local write channel.
 *
 * `attempt` runs the write, keeps quiet when it lands, and seats a named
 * failure receipt (with RETRY re-issuing the same call) when it does not.
 */
export function useWriteReceipt() {
  const [failure, setFailure] = useState<WriteFailure | null>(null);

  const clear = useCallback(() => setFailure(null), []);

  const attempt = useCallback(
    async function attemptWrite<T>(
      verb: string,
      run: () => Promise<T>,
      opts: { retry?: boolean } = {},
    ): Promise<WriteResult<T>> {
      const label = verb.toUpperCase();
      const seat = (reason: string) => {
        setFailure({
          verb: label,
          reason,
          retry:
            opts.retry === false
              ? null
              : () => void attemptWrite(verb, run, opts),
        });
      };
      try {
        const value = await run();
        const refused = refusedResponse(value);
        if (refused) {
          const reason = writeFailureReason(refused);
          seat(reason);
          return { ok: false, reason };
        }
        setFailure(null);
        return { ok: true, value };
      } catch (cause) {
        const reason = writeFailureReason(cause);
        seat(reason);
        return { ok: false, reason };
      }
    },
    [],
  );

  /** Report a failure the caller already caught (or a non-throwing refusal). */
  const fail = useCallback(
    (verb: string, cause: unknown, retry?: () => void) => {
      setFailure({
        verb: verb.toUpperCase(),
        reason: writeFailureReason(cause),
        retry: retry ?? null,
      });
    },
    [],
  );

  return {
    attempt,
    fail,
    clear,
    failure,
    receipt: receiptElement(failure, clear),
  };
}

/* ── module channel: writers outside React (store slices) ─────────────── */

let deskFailure: WriteFailure | null = null;
const listeners = new Set<() => void>();

function publish(next: WriteFailure | null) {
  deskFailure = next;
  for (const fn of listeners) fn();
}

/** Report a desk-level write failure from anywhere (store, plain modules). */
export function reportWriteFailure(
  verb: string,
  cause: unknown,
  retry?: () => void,
): WriteFailure {
  const failure: WriteFailure = {
    verb: verb.toUpperCase(),
    reason: writeFailureReason(cause),
    retry: retry ?? null,
  };
  publish(failure);
  return failure;
}

/** A landed write is quiet: it only clears whatever was standing. */
export function clearWriteFailure() {
  if (deskFailure !== null) publish(null);
}

export function subscribeWriteFailure(fn: () => void): () => void {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

export function currentWriteFailure(): WriteFailure | null {
  return deskFailure;
}

/**
 * How many surfaces are standing closer to the verb than the system bar.
 * The chrome's receipt line is the desk's backstop: it speaks whenever no
 * nearer surface has claimed the channel, so one failure is never printed
 * twice.
 */
let nearMounts = 0;

function nearSnapshot(): WriteFailure | null {
  return deskFailure;
}

function fallbackSnapshot(): WriteFailure | null {
  return nearMounts > 0 ? null : deskFailure;
}

/**
 * Render the desk-level channel wherever the desk keeps its receipt line.
 * `fallback: true` marks the backstop mount (the system bar); it yields to
 * any nearer receipt line that is on screen.
 */
export function useDeskWriteReceipt({ fallback = false } = {}) {
  const snapshot = fallback ? fallbackSnapshot : nearSnapshot;
  const failure = useSyncExternalStore(subscribeWriteFailure, snapshot, snapshot);

  useEffect(() => {
    if (fallback) return;
    nearMounts++;
    for (const fn of listeners) fn();
    return () => {
      nearMounts--;
      for (const fn of listeners) fn();
    };
  }, [fallback]);

  return {
    failure,
    clear: clearWriteFailure,
    receipt: receiptElement(failure, clearWriteFailure),
  };
}
