/**
 * The pure document binding used by Floor send affordances.
 *
 * The Floor owns only the icon and its stable identity. Meeting summary
 * presence and a project's latest published update arrive as explicit facts
 * from the bounded reads owned by the menu/drop lane. This module performs no
 * reads and never turns an unresolved fact into a refusal.
 */

export type PendingState = "unread" | "loading" | "failed";

export type Fact<T> =
  | { state: "unread" }
  | { state: "loading" }
  | { state: "failed" }
  | { state: "known"; value: T };

export type MeetingForm = "summary" | "digest" | "followup";

export type FloorDestination = {
  id: string;
  state: "active" | "parked";
};

export type FloorDocumentInput =
  | { kind: "decision"; id: string }
  | { kind: "artifact"; id: string }
  | {
      kind: "meeting";
      id: string;
      summary: Fact<boolean>;
      form?: MeetingForm;
    }
  | {
      kind: "project";
      id: string;
      latestPublishedUpdateId: Fact<string | null>;
    }
  | { kind: "brief"; briefId: string };

export type FloorBindingInput = FloorDocumentInput & {
  destination: FloorDestination;
};

export type DocumentRef =
  | `desk_decision:${string}`
  | `artifact:${string}`
  | `meeting_summary:${string}`
  | `meeting_digest:${string}`
  | `meeting_followup:${string}`
  | `project_update:${string}`
  | `monday_brief:${string}`;

export type FloorRefusal =
  "no_summary" | "not_published" | "destination_parked";

export type FloorBinding =
  { ref: DocumentRef } | { refusal: FloorRefusal } | { pending: PendingState };

/** Resolve one Floor icon to the exact document the send well must preview. */
export function resolve(input: FloorBindingInput): FloorBinding {
  if (input.destination.state === "parked") {
    return { refusal: "destination_parked" };
  }

  switch (input.kind) {
    case "decision":
      return { ref: `desk_decision:${input.id}` };
    case "artifact":
      return { ref: `artifact:${input.id}` };
    case "brief":
      return { ref: `monday_brief:${input.briefId}` };
    case "meeting": {
      const summary = factResult(input.summary);
      if (summary !== null) return summary;
      const form = input.form ?? "summary";
      return { ref: `meeting_${form}:${input.id}` };
    }
    case "project": {
      const update = input.latestPublishedUpdateId;
      if (update.state !== "known") return { pending: update.state };
      if (update.value === null) return { refusal: "not_published" };
      return { ref: `project_update:${update.value}` };
    }
  }
}

/** Convert a fact into its unresolved/refusal result, or null when usable. */
function factResult(
  fact: Fact<boolean>,
): Exclude<FloorBinding, { ref: DocumentRef }> | null {
  if (fact.state !== "known") return { pending: fact.state };
  if (!fact.value) return { refusal: "no_summary" };
  return null;
}

/** Data-only projection for a saved destination icon. */
export type FloorDestinationProjection = {
  projection: "destination";
  /** Stable per-browser layout identity, distinct from the API destination id. */
  id: `destination:${string}`;
  destinationId: string;
  name: string;
  channel: string;
  state: FloorDestination["state"];
};

/** Data-only projection for the single latest brief icon/row. */
export type FloorBriefProjection = {
  projection: "brief";
  id: "intelligence:brief";
  briefId: string;
  label: string;
  capabilities: readonly ["send"];
};

/** Explicit non-primitive Floor icons; neither variant is a PrimitiveKind. */
export type FloorProjection = FloorDestinationProjection | FloorBriefProjection;

export function destinationProjection(
  input: Omit<FloorDestinationProjection, "projection" | "id">,
): FloorDestinationProjection {
  return {
    projection: "destination",
    id: `destination:${input.destinationId}`,
    ...input,
  };
}

export function briefProjection(
  input: Pick<FloorBriefProjection, "briefId" | "label">,
): FloorBriefProjection {
  return {
    projection: "brief",
    id: "intelligence:brief",
    ...input,
    capabilities: ["send"],
  };
}
