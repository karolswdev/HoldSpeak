import { apiFetch } from "../lib/api";
import type { DictationFailure } from "../lib/dictationRecovery";

export type FirstValueEvent =
  | "capture_started"
  | "capture_released"
  | "transcript_received"
  | "draft_edited"
  | "copy_selected"
  | "keep_selected"
  | "setup_selected"
  | "alternate_target_selected"
  | "continue_later_selected";

type Fetcher = typeof apiFetch;

const KEEP_NOTE_ID_KEY = "hs.first-value.keep-note-id";
const PENDING_NOTE_OPEN_KEY = "hs.first-value.pending-note-open";
let memoryKeepNoteId = "";
let memoryPendingNoteRef = "";

function local(): Storage | null {
  try {
    return typeof window === "undefined" ? null : window.localStorage;
  } catch {
    return null;
  }
}

function session(): Storage | null {
  try {
    return typeof window === "undefined" ? null : window.sessionStorage;
  } catch {
    return null;
  }
}

/** One note claim survives an ambiguous response and a local relaunch. */
export function firstValueKeepNoteId(): string {
  const stored = local()?.getItem(KEEP_NOTE_ID_KEY) || memoryKeepNoteId;
  if (stored) return stored;
  const entropy =
    typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
      ? crypto.randomUUID().replaceAll("-", "")
      : Math.random().toString(36).slice(2);
  const noteId = `note_${entropy}`;
  memoryKeepNoteId = noteId;
  try {
    local()?.setItem(KEEP_NOTE_ID_KEY, noteId);
  } catch {
    // The in-memory claim still protects retries in this live page.
  }
  return noteId;
}

export function clearFirstValueKeepNoteId(): void {
  memoryKeepNoteId = "";
  try {
    local()?.removeItem(KEEP_NOTE_ID_KEY);
  } catch {
    // Nothing else is needed once the confirmed note has been staged.
  }
}

/** Queue the normal-Desk handoff without leaking a pullout into arrival. */
export function stageFirstValueNoteOpen(ref: string): void {
  memoryPendingNoteRef = ref;
  try {
    session()?.setItem(PENDING_NOTE_OPEN_KEY, ref);
  } catch {
    // Memory keeps the current page's handoff intact.
  }
}

/** Consume the one queued open only after the normal Desk is revealed. */
export function takeFirstValueNoteOpen(): string | null {
  const ref = session()?.getItem(PENDING_NOTE_OPEN_KEY) || memoryPendingNoteRef;
  memoryPendingNoteRef = "";
  try {
    session()?.removeItem(PENDING_NOTE_OPEN_KEY);
  } catch {
    // The in-memory queue has already been consumed.
  }
  return ref || null;
}

/** Content-free journey instrumentation. Phrase text is not accepted anywhere. */
export class FirstValueTracker {
  private attemptId = "";
  private destination: "this_machine" | "paired_desktop" = "this_machine";
  private sequence = 0;
  private queue: Promise<unknown> = Promise.resolve();

  constructor(private readonly fetcher: Fetcher = apiFetch) {}

  async start(destination: "this_machine" | "paired_desktop") {
    const result = await this.fetcher<{ attempt?: { id?: string } }>(
      "/api/setup/first-value/start",
      { method: "POST", json: { destination } },
    );
    this.attemptId = String(result.attempt?.id ?? "");
    this.destination = destination;
    this.sequence = 0;
  }

  event(kind: FirstValueEvent): Promise<unknown> {
    const attemptId = this.attemptId;
    if (!attemptId) return Promise.resolve();
    this.sequence += 1;
    const eventId = `${attemptId}:${this.sequence}:${kind}`;
    this.queue = this.queue
      .catch(() => undefined)
      .then(() =>
        this.fetcher(
          `/api/setup/first-value/${encodeURIComponent(attemptId)}/event`,
          { method: "POST", json: { event_id: eventId, kind } },
        ),
      );
    return this.queue;
  }

  async finish(
    outcome: "success" | "failure",
    failureCategory?: DictationFailure,
  ) {
    const attemptId = this.attemptId;
    if (!attemptId) return;
    await this.queue.catch(() => undefined);
    await this.fetcher(
      `/api/setup/first-value/${encodeURIComponent(attemptId)}/finish`,
      {
        method: "POST",
        json: {
          outcome,
          destination: this.destination,
          ...(failureCategory ? { failure_category: failureCategory } : {}),
        },
      },
    );
    this.attemptId = "";
  }
}
