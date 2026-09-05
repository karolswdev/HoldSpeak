// HS-170-04 — Door verb helpers (promoted from parked DoorBoardLane).
// The arrival renders a door item's FIRST lawful verb as a primary dense
// button; the command posts through the same HTTP adapter table.

import { newDeliveryId } from "../../lib/api";

type DoorVerbArguments = Record<string, string | number | null | undefined>;

export interface DoorVerb {
  name: string;
  arguments: DoorVerbArguments;
  required_arguments?: string[];
}

interface Command {
  endpoint: string;
  body?: Record<string, unknown>;
}

function text(value: unknown): string {
  return typeof value === "string" ? value : "";
}

export function labelFor(verb: DoorVerb): string {
  if (verb.name === "follow_through.complete") {
    return text(verb.arguments.verb).replace(/^./, (letter) => letter.toUpperCase());
  }
  if (verb.name === "cadence.set_status") {
    return text(verb.arguments.status) === "killed" ? "Kill" : "Close";
  }
  if (verb.name === "thought.complete") return "Complete";
  if (verb.name === "people.commitment.transition") {
    return text(verb.arguments.verb).replace(/^./, (letter) => letter.toUpperCase());
  }
  return "";
}

export function supportsDoorVerb(verb: DoorVerb): boolean {
  return [
    "follow_through.complete",
    "cadence.set_status",
    "thought.complete",
    "people.commitment.transition",
  ].includes(verb.name);
}

/** Fixed HTTP adapter table. Door descriptors name capabilities, never URLs. */
export function commandForDoorVerb(verb: DoorVerb, payload: { until?: string; to?: string } = {}): Command | null {
  const args = verb.arguments;
  if (verb.name === "follow_through.complete") {
    const cardId = text(args.card_id);
    const action = text(args.verb);
    if (!cardId || !action) return null;
    if (action === "snooze" && !payload.until?.trim()) return null;
    if (action === "delegate" && !payload.to?.trim()) return null;
    const writePayload = action === "snooze"
      ? { until: payload.until?.trim() }
      : action === "delegate"
        ? { to: payload.to?.trim() }
        : {};
    return {
      endpoint: "/api/follow-through/complete",
      body: { card_id: cardId, verb: action, payload: writePayload },
    };
  }
  if (verb.name === "cadence.set_status") {
    const loopId = text(args.loop_id);
    const status = text(args.status);
    if (!loopId || !["closed", "killed"].includes(status)) return null;
    return { endpoint: `/api/cadence/loops/${encodeURIComponent(loopId)}/${status === "closed" ? "close" : "kill"}` };
  }
  if (verb.name === "thought.complete") {
    const thoughtId = text(args.thought_id);
    const aggregateRevision = args.expected_aggregate_revision;
    const lifecycleRevision = args.expected_lifecycle_revision;
    if (!thoughtId || typeof aggregateRevision !== "number" || typeof lifecycleRevision !== "number") return null;
    return {
      endpoint: `/api/thoughts/${encodeURIComponent(thoughtId)}/complete`,
      body: {
        request_id: newDeliveryId(),
        expected_aggregate_revision: aggregateRevision,
        expected_lifecycle_revision: lifecycleRevision,
      },
    };
  }
  if (verb.name === "people.commitment.transition") {
    const commitmentId = text(args.commitment_id);
    const action = text(args.verb);
    if (!commitmentId || !["done", "dismiss"].includes(action)) return null;
    return {
      endpoint: `/api/people/commitments/${encodeURIComponent(commitmentId)}/transition`,
      body: { verb: action },
    };
  }
  return null;
}
