import { describe, expect, it } from "vitest";
import { EMPTY_ITEMS, type Items } from "../api";
import {
  contextualCapabilityActions,
  contextualCoderSessions,
  contextualIntegrationActions,
  selectedMaterials,
} from "../contextual";
import type { TrustDestination } from "../setup";

const destinations: TrustDestination[] = [
  {
    id: "slack",
    name: "Slack",
    operation: "Send approved text",
    enabled: true,
    destination: "Workspace",
    boundary: "External service",
    data_class: "Selected text",
    authority_basis: "Per-action approval",
    background_ability: "No",
    revoke_action: "Clear the credential",
  },
  {
    id: "github",
    name: "GitHub issues",
    operation: "Create approved issue",
    enabled: false,
    destination: "owner/repo",
    boundary: "External service",
    data_class: "Issue title and body",
    authority_basis: "Per-action approval",
    background_ability: "No",
    revoke_action: "Clear the repository",
  },
];

function fixture(): Items {
  return {
    ...EMPTY_ITEMS,
    note: [
      {
        kind: "note",
        id: "same",
        title: "Release checklist",
        bodyMarkdown: "Ship after checks pass.",
      },
    ],
    artifact: [
      {
        kind: "artifact",
        id: "same",
        title: "Risk report",
        bodyMarkdown: "One open risk.",
      },
    ],
    recipe: [
      {
        kind: "recipe",
        id: "scout",
        name: "Scout",
        capability: {
          readiness: { state: "ready" },
          input_schema: { required: ["input"] },
          effect_classes: ["creates_artifact"],
        },
      },
      {
        kind: "recipe",
        id: "offline",
        name: "Offline",
        capability: {
          readiness: { state: "unavailable" },
          input_schema: { required: ["input"] },
          effect_classes: ["creates_artifact"],
        },
      },
      {
        kind: "recipe",
        id: "unscoped",
        name: "Unscoped",
        capability: {
          readiness: { state: "ready" },
          input_schema: { required: ["input"] },
          effect_classes: [],
        },
      },
    ],
    workflow: [
      {
        kind: "workflow",
        id: "release",
        name: "Release workflow",
        capability: {
          readiness: { state: "ready" },
          input_schema: { required: ["input"] },
          effect_classes: ["creates_artifact"],
        },
      },
    ],
    coder: [
      { kind: "coder", id: "waiting", title: "App", state: "waiting" },
      { kind: "coder", id: "busy", title: "Docs", state: "running" },
    ],
  };
}

describe("HS-93-04 contextual Desk action eligibility", () => {
  it("requires selected material and ready capabilities", () => {
    const items = fixture();
    expect(contextualCapabilityActions(items, [])).toEqual([]);
    expect(
      contextualCapabilityActions(items, ["note:same"]).map(
        (action) => action.label,
      ),
    ).toEqual([
      "Ask Scout about Release checklist",
      "Run Release workflow on Release checklist",
    ]);
  });

  it("uses qualified selection identity when primitive ids collide", () => {
    const selected = selectedMaterials(fixture(), ["artifact:same"]);
    expect(selected).toHaveLength(1);
    expect(selected[0].title).toBe("Risk report");
    expect(selected[0].ref).toBe("artifact:same");
  });

  it("offers only configured Integrations for one compatible source", () => {
    expect(
      contextualIntegrationActions(destinations, fixture(), ["note:same"]).map(
        (action) => action.label,
      ),
    ).toEqual(["Send Release checklist to Slack"]);
    expect(
      contextualIntegrationActions(destinations, fixture(), [
        "note:same",
        "artifact:same",
      ]),
    ).toEqual([]);
  });

  it("offers selected-material handoff only to waiting Coder sessions", () => {
    expect(
      contextualCoderSessions(fixture(), ["note:same"]).map((action) => [
        action.id,
        action.label,
      ]),
    ).toEqual([["waiting", "Send Release checklist to App Coder session"]]);
  });
});
