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
