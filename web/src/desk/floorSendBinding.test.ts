import { describe, expect, it } from "vitest";
import {
  briefProjection,
  destinationProjection,
  resolve,
  type Fact,
  type FloorBindingInput,
  type FloorDocumentInput,
} from "./floorSendBinding";
import { primitiveCan } from "../lib/primitives";

const known = <T>(value: T): Fact<T> => ({ state: "known", value });

const destination = { id: "dest-1", state: "active" as const };

function input(document: FloorDocumentInput): FloorBindingInput {
  return { ...document, destination };
}

describe("Floor send binding", () => {
  it("exposes send only for the four primitive document kinds", () => {
    for (const kind of [
      "decision",
      "meeting",
      "project",
      "artifact",
    ] as const) {
      expect(primitiveCan(kind, "send")).toBe(true);
    }
    for (const kind of ["note", "directory", "recipe"] as const) {
      expect(primitiveCan(kind, "send")).toBe(false);
    }
  });

  it.each([
    [
      "decision",
      input({ kind: "decision", id: "dec-1" }),
      "desk_decision:dec-1",
    ],
    ["artifact", input({ kind: "artifact", id: "art-1" }), "artifact:art-1"],
    [
      "meeting summary",
      input({
        kind: "meeting",
        id: "meet-1",
        summary: known(true),
        form: "summary",
      }),
      "meeting_summary:meet-1",
    ],
    [
      "meeting digest",
      input({
        kind: "meeting",
        id: "meet-1",
        summary: known(true),
        form: "digest",
      }),
      "meeting_digest:meet-1",
    ],
    [
      "meeting followup",
      input({
        kind: "meeting",
        id: "meet-1",
        summary: known(true),
        form: "followup",
      }),
      "meeting_followup:meet-1",
    ],
    [
      "project latest published update",
      input({
        kind: "project",
        id: "project-1",
        latestPublishedUpdateId: known("update-9"),
      }),
      "project_update:update-9",
    ],
    [
      "brief exact stored id",
      input({ kind: "brief", briefId: "brief-7" }),
      "monday_brief:brief-7",
    ],
  ])("binds %s to its exact document reference", (_label, value, ref) => {
    expect(resolve(value)).toEqual({ ref });
  });

  it("defaults a meeting to Summary", () => {
    expect(
      resolve(input({ kind: "meeting", id: "meet-1", summary: known(true) })),
    ).toEqual({ ref: "meeting_summary:meet-1" });
  });

  it.each([
    [
      "meeting without a summary",
      input({ kind: "meeting", id: "meet-1", summary: known(false) }),
      "no_summary",
    ],
    [
      "project without a published update",
      input({
        kind: "project",
        id: "project-1",
        latestPublishedUpdateId: known(null),
      }),
      "not_published",
    ],
    [
      "parked destination",
      {
        ...input({ kind: "decision", id: "dec-1" }),
        destination: { id: "dest-1", state: "parked" as const },
      },
      "destination_parked",
    ],
  ])("names the known absence for %s", (_label, value, refusal) => {
    expect(resolve(value)).toEqual({ refusal });
  });

  it.each(["unread", "loading", "failed"] as const)(
    "keeps a %s fact pending instead of refusing",
    (state) => {
      expect(
        resolve(
          input({
            kind: "meeting",
            id: "meet-1",
            summary: { state },
          }),
        ),
      ).toEqual({ pending: state });
      expect(
        resolve(
          input({
            kind: "project",
            id: "project-1",
            latestPublishedUpdateId: { state },
          }),
        ),
      ).toEqual({ pending: state });
    },
  );

  it("keeps destination and brief as explicit nonprimitive projection data", () => {
    expect(
      destinationProjection({
        destinationId: "dest-1",
        name: "Slack #leads",
        channel: "slack",
        state: "active",
      }),
    ).toEqual({
      projection: "destination",
      id: "destination:dest-1",
      destinationId: "dest-1",
      name: "Slack #leads",
      channel: "slack",
      state: "active",
    });
    expect(
      briefProjection({ briefId: "brief-7", label: "BRIEF SEP 29" }),
    ).toEqual({
      projection: "brief",
      id: "intelligence:brief",
      briefId: "brief-7",
      label: "BRIEF SEP 29",
      capabilities: ["send"],
    });
  });
});
