// HS-132-06 — the ONE write-receipt channel.
//
// The desk's dominant defect was the silent write: a verb fired, the hub
// refused, and the surface said nothing. Every desk write verb now reports
// into this channel. It renders in the surface's existing receipt slot
// (footer receipt bar / in-flow strip) — never over the work — names the
// verb in one plain sentence ("Could not save the note"; the cause is in the
// hover title), and offers Try again when the same call can be re-issued. Success stays quiet: a clean write clears the channel
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
import { Button } from "../../components/signal/Signal";
import "./write-receipt.css";
import { stateWords } from "../surface/words";

export interface WriteFailure {
  /** The verb that failed, upper case ("ADD ITEM"). It is the failure's
   *  identity, a compare key (callers compare it); the face never draws it,
   *  it says the verb's phrase as a sentence. */
  verb: string;
  /** Why it failed, in short words ("Hub unreachable", "HTTP 422"). It is
   *  shown only in the hover title, never on the face. */
  reason: string;
  /** Re-issues the exact same write, or null when it cannot be replayed. */
  retry: (() => void) | null;
  /** The hub's own words for the refusal, when it sent any (shown as the
   *  label's title, never as prose on the face). */
  detail?: string;
  /** What the failed write was about (e.g. "decision:abc"), so a later
   *  landed write clears only its own failure. */
  subject?: string;
  /** PHILO-13-04 — the face's own state when "Could not <verb>" is not the
   *  truth to show (a refused start is "Not recording · <why>"). */
  label?: string;
  /** W6-E words: the face of every write failure is one sans sentence in
   *  sentence case (`Could not save the note · Try again`), a round dot, the
   *  reason in the hover title only. The old mono caps face
   *  (`SAVE FAILED · HTTP 404`) is parked behind this opt-in. */
  mono?: boolean;
  /** Atlas pass 3 (defect 16): the opt-in that #1567 added. The plain face
   *  is the default now, so this changes nothing; it stays for old callers. */
  plain?: boolean;
  /** The retry verb's word when it is not `Try again`. */
  retryLabel?: string;
}

export type WriteResult<T> =
  | { ok: true; value: T }
  | { ok: false; reason: string };

/** The one signature every desk write verb reports through. */
export type WriteAttempt = <T>(
  verb: string,
  run: () => Promise<T>,
  opts?: { retry?: boolean; subject?: string },
) => Promise<WriteResult<T>>;

/** The failure's identity: the verb as a compare key (`add item` → `ADD
 *  ITEM`). Never drawn; the face says `writeFailurePhrase`. */
const verbKey = (verb: string): string => verb.trim().toUpperCase();

/** Name the cause in short words, sentence case — never prose. A caller's
 *  caps cause (`EMPTY PAYLOAD`) reads `Empty payload`. */
export function writeFailureReason(cause: unknown): string {
  if (typeof cause === "string" && cause.trim()) return stateWords(cause.trim());
  if (typeof Response !== "undefined" && cause instanceof Response)
    return `HTTP ${cause.status}`;
  if (cause && typeof cause === "object") {
    const status = (cause as { status?: unknown }).status;
    if (typeof status === "number" && status > 0) return `HTTP ${status}`;
  }
  if (cause instanceof Error) {
    if (cause.name === "TypeError" || /fetch|network|failed to fetch/i.test(cause.message))
      return "Hub unreachable";
    if (cause.name === "AbortError") return "Stopped";
  }
  return "Write refused";
}

/** The hub's own refusal words (an ApiError's message), when it sent any:
 * the generic fallback is not the hub's words and is dropped. */
export function writeFailureDetail(cause: unknown): string | undefined {
  if (!(cause instanceof Error) || cause.name !== "ApiError") return undefined;
  const message = cause.message.trim();
  if (!message || message.startsWith("HoldSpeak could not complete")) return undefined;
  return message;
}

/* W6-E words — the noun a failed write was about, from its subject
   (`note:abc`) or its kind (`kb`), in the owner's words. */
const WRITE_NOUNS: Record<string, string> = {
  note: "note",
  decision: "decision",
  meeting: "meeting",
  artifact: "result",
  kb: "drawer",
  knowledge: "drawer",
  directory: "zone",
  zone: "zone",
  recipe: "mode",
  persona: "mode",
  chain: "workflow",
  sequence: "workflow",
  workflow: "workflow",
  workbench: "automation",
  project: "project",
  thread: "thread",
  roadmap: "roadmap",
  repository: "repository",
  coder: "agent",
  agent: "agent",
  "action-item": "task",
  action_item: "task",
  proposal: "proposal",
  person: "person",
  people: "person",
};

function writeNoun(token: string | undefined): string | null {
  if (!token) return null;
  const kind = token.split(":", 1)[0].trim().toLowerCase();
  return WRITE_NOUNS[kind] ?? null;
}

/* W6-E words — each write verb's own phrase: the face reads
   `Could not <phrase>`. Keys are the verb's compare key (`verbKey`). A verb that is not
   here is said in lower case (`Could not <verb>`). */
const WRITE_PHRASES: Record<string, string | ((noun: string | null) => string)> = {
  SAVE: (noun) => (noun ? `save the ${noun}` : "save it"),
  RENAME: (noun) => (noun ? `rename the ${noun}` : "rename it"),
  DELETE: (noun) => (noun ? `delete the ${noun}` : "delete it"),
  "RENAME ZONE": "rename the zone",
  "SEED DESK": "set up the desk",
  "NEW NOTE": "make the note",
  "SEND TURN": "send it",
  "MARK SEEN": "mark it seen",
  "OPEN THREAD": "open the thread",
  "IMPORT CHATS": "import the chats",
  "START RECORDING": "start the recording",
  "STOP RECORDING": "stop the recording",
  "RECOVER CAPTURE": "recover the recording",
  // Automations (WorkbenchWindow, WorkbenchAutomations, WorkbenchResourceful)
  "SAVE ITEM": "save the item",
  "RE-RUN ITEM": "run the item again",
  "DISMISS ITEM": "dismiss the item",
  "PARK ITEM": "park the item",
  "CLEAR DONE": "clear the done items",
  "ADD ITEM": "add the item",
  KEEP: "keep the result",
  "RETRY MINT": "keep the result",
  "SAVE AUTOMATION": "save the automation",
  "TEST AUTOMATION": "test the automation",
  "ADD AUTOMATION": "add the automation",
  RUN: "start the run",
  "DROP TO WORK": "add it to the work",
  "CLEAR MEMORY": "clear the memory",
  "PROMOTE TO SKILL": "make it a skill",
  "ENABLE RESOURCEFULNESS": "turn on resourcefulness",
  "PAUSE RESOURCEFULNESS": "pause resourcefulness",
  "SAVE POLICY": "save the policy",
  // Needs you (NeedsDrawer)
  "ALLOW HELPER": "allow the helper",
  APPROVE: "approve it",
  DENY: "deny it",
  DROP: "drop it",
  DONE: "mark it done",
  "MARK DONE": "mark it done",
  LATER: "move it to later",
  CONFIRM: "confirm it",
  DEFER: "defer it",
  DECLINE: "decline it",
  ACCEPT: "accept it",
  "NOT NOW": "defer it",
  CHECK: "check it",
  SEND: "send it",
  "TRY AGAIN": "send it",
  DISCARD: "discard it",
  "NAME AN OWNER": "name an owner",
  "SET A DATE": "set the date",
  "WHOSE?": "set the owner",
  NUDGE: "send the nudge",
  UNDO: "undo it",
  ACKNOWLEDGE: "mark it read",
  "RUN SUMMARY": "run the summary",
  // Ask (AskPanel)
  "USE ANOTHER ENGINE": "change the engine",
  "SAVE AS NOTE": "save the answer as a note",
  "ADD TO NOTE": "add it to the note",
  "ALLOW ONCE": "allow it once",
  "MAKE IT A TASK": "make it a task",
  FORGET: "forget the chat",
};

/** The phrase after `Could not` for one failed verb (`save the note`). */
export function writeFailurePhrase(verb: string, subject?: string): string {
  const key = verbKey(verb);
  const known = WRITE_PHRASES[key];
  if (typeof known === "function") return known(writeNoun(subject));
  if (known) return known;
  // A create or a read names its kind in the verb (`CREATE note`, `READ Notes`).
  const create = /^CREATE\s+(.+)$/.exec(key);
  if (create) {
    const noun = writeNoun(create[1]) ?? create[1].toLowerCase();
    return `make the ${noun}`;
  }
  const read = /^READ\s+(.+)$/.exec(key);
  if (read) return `load the ${read[1].toLowerCase()}`;
  return verb.trim().toLowerCase();
}

/** The one label every write refusal wears: `Could not save the note`. The
 *  parked mono face says `SAVE FAILED · HTTP 404`. */
export function writeFailureLabel(failure: WriteFailure): string {
  if (failure.mono) return failure.label ?? `${failure.verb} FAILED · ${failure.reason}`;
  return failure.label ?? `Could not ${writeFailurePhrase(failure.verb, failure.subject)}`;
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
  // The reason (HTTP code, hub words) is in the hover title only.
  const title = [writeFailureLabel(failure), failure.mono ? "" : failure.reason, failure.detail ?? ""]
    .filter(Boolean)
    .join(" · ");
  return createElement(
    "span",
    { className: failure.mono ? "write-receipt write-receipt-mono" : "write-receipt write-receipt-plain", role: "status" },
    createElement("span", { className: "write-receipt-lamp" }),
    createElement(
      "span",
      // PHILO-3-01: the whole label stays readable where the strip clips it.
      { className: "write-receipt-label", title },
      writeFailureLabel(failure),
    ),
    failure.retry
      ? createElement(
          Button,
          {
            variant: "ghost",
            dense: true,
            className: "write-receipt-retry",
            onClick: failure.retry,
          },
          failure.retryLabel ?? (failure.mono ? "Retry" : "Try again"),
        )
      : null,
    createElement(
      Button,
      {
        variant: "ghost",
        dense: true,
        className: "write-receipt-dismiss",
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
      opts: { retry?: boolean; subject?: string } = {},
    ): Promise<WriteResult<T>> {
      const label = verbKey(verb);
      const seat = (reason: string, detail?: string) => {
        setFailure({
          verb: label,
          reason,
          detail,
          subject: opts.subject,
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
        // PHILO-8-02 round six — one rule in both channels: a failure about a
        // subject (an item, an object) is cleared only by a landed write
        // about that same subject; another item's success never erases it.
        setFailure((standing) =>
          standing?.subject !== undefined && standing.subject !== opts.subject ? standing : null,
        );
        return { ok: true, value };
      } catch (cause) {
        const reason = writeFailureReason(cause);
        seat(reason, writeFailureDetail(cause));
        return { ok: false, reason };
      }
    },
    [],
  );

  /** Report a failure the caller already caught (or a non-throwing refusal). */
  const fail = useCallback(
    (verb: string, cause: unknown, retry?: () => void) => {
      setFailure({
        verb: verbKey(verb),
        reason: writeFailureReason(cause),
        retry: retry ?? null,
        detail: writeFailureDetail(cause),
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
  subject?: string,
  label?: string,
  face?: { plain?: boolean; mono?: boolean; retryLabel?: string },
): WriteFailure {
  const failure: WriteFailure = {
    verb: verbKey(verb),
    reason: writeFailureReason(cause),
    retry: retry ?? null,
    detail: writeFailureDetail(cause),
    subject,
    ...(label ? { label } : {}),
    ...(face?.plain ? { plain: true } : {}),
    ...(face?.mono ? { mono: true } : {}),
    ...(face?.retryLabel ? { retryLabel: face.retryLabel } : {}),
  };
  publish(failure);
  return failure;
}

/** A landed write is quiet: it clears the standing failure it answers.
 *
 * PHILO-8-02 round seven — one rule for the whole desk channel, by
 * construction: a clear carries the landed write's subject (or none). A
 * standing failure about a subject is removed only by a clear with that same
 * subject; a standing failure with no subject is removed by any clear. So no
 * other object's success (a create, an update, a delete, a seed) can erase
 * an unresolved refusal and its Retry. The owner's own dismissal (OK) is
 * `dismissWriteFailure`. */
export function clearWriteFailure(subject?: string) {
  if (deskFailure === null) return;
  if (deskFailure.subject !== undefined && deskFailure.subject !== subject) return;
  publish(null);
}

/** The owner dismissed the receipt (OK): it goes, whatever it was about. */
export function dismissWriteFailure() {
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
    clear: dismissWriteFailure,
    receipt: receiptElement(failure, dismissWriteFailure),
  };
}
