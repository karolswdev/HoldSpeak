import { describe, expect, it } from "vitest";
import { fromWireRecipe } from "../api";

const capability = {
  kind: "persona",
  input_schema: { type: "object" },
  input_help: "Choose material.",
  supported_placements: ["this_machine"],
  effect_classes: ["creates_artifact"],
  readiness: { state: "ready", detail: "" },
  action_label: "Ask Scout",
  support: "linear_graph",
};

describe("capability presentation adapters", () => {
  it("keeps readiness and the contextual action on a Mode", () => {
    const persona = fromWireRecipe({ id: "p1", name: "Scout", capability });
    expect((persona!.capability as any).action_label).toBe("Ask Scout");
    expect((persona!.capability as any).readiness.state).toBe("ready");
  });
});
