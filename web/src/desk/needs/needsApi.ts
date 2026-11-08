/** The Needs-you writes that close a promise (2026-11-08: one Done).
 *
 *  Done on a row had three client copies: `followThrough()` for a work row,
 *  an inline POST for a Room commitment, and the Door verb's POST for a
 *  People promise. `markDone(verbs)` is the one: it knows the row's route by
 *  its verbs and reads one receipt (the row's id, its status, `done_at`),
 *  which `/api/follow-through/complete` and People's transition both answer.
 *  No other module in `desk/needs` posts to these routes (fenced by
 *  `__tests__/NeedsDrawer.test.tsx`).
 */
import { apiFetch } from "../../lib/api";
import type { NeedVerbs } from "./needsFace";

const FOLLOW_THROUGH = "/api/follow-through/complete";

/** One follow-through verb on an action item (the hub's one write path for
 *  Done, Drop, Later, Undo, Set a date and Name an owner). */
export function followThrough(cardId: string, verb: string, payload: Record<string, unknown> = {}) {
  return apiFetch(FOLLOW_THROUGH, { method: "POST", json: { card_id: cardId, verb, payload } });
}

/** Later: the row comes back tomorrow (the follow-through snooze is by day). */
export function tomorrowDay(now: Date = new Date()): string {
  const d = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

/** The one receipt a Done answers, whichever route took it. */
export type DoneReceipt = { id: string; status: string; doneAt: string | null };

export function readDoneReceipt(answer: unknown): DoneReceipt {
  const a = (answer ?? {}) as { card_id?: unknown; status?: unknown; done_at?: unknown };
  return {
    id: String(a.card_id ?? ""),
    status: String(a.status ?? ""),
    doneAt: typeof a.done_at === "string" && a.done_at ? a.done_at : null,
  };
}

type DoneRoute = { endpoint: string; body: Record<string, unknown> };

/** Where Done goes for a row, by its verbs: a work row (a Door action item
 *  or a Room commitment, by its action item) is the follow-through
 *  complete; a People promise (a Door card) is People's transition. A row
 *  with no Done has no route. */
export function doneRoute(v: NeedVerbs): DoneRoute | null {
  if (v.kind === "work") {
    return { endpoint: FOLLOW_THROUGH, body: { card_id: v.cardId, verb: "done", payload: {} } };
  }
  if (v.kind === "door") {
    for (const verb of v.card.lawful_verbs ?? []) {
      const args = verb.arguments ?? {};
      if (args.verb !== "done") continue;
      if (verb.name === "people.commitment.transition" && args.commitment_id) {
        return {
          endpoint: `/api/people/commitments/${encodeURIComponent(String(args.commitment_id))}/transition`,
          body: { verb: "done" },
        };
      }
      if (verb.name === "follow_through.complete" && args.card_id) {
        return { endpoint: FOLLOW_THROUGH, body: { card_id: String(args.card_id), verb: "done", payload: {} } };
      }
    }
  }
  return null;
}

/** Done on a Needs-you row: its one route, its one receipt. */
export async function markDone(v: NeedVerbs): Promise<DoneReceipt> {
  const route = doneRoute(v);
  if (!route) throw new Error("This row has no Done.");
  return readDoneReceipt(await apiFetch(route.endpoint, { method: "POST", json: route.body }));
}
