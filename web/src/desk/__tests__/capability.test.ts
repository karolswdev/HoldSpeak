import { describe, expect, it } from "vitest";
import { fromWireChain, fromWireRecipe, fromWireWorkflow } from "../api";

const capability = {
  kind: "workflow",
  input_schema: { type: "object" },
  input_help: "Choose material.",
  supported_placements: ["this_machine"],
  effect_classes: ["creates_artifact"],
  readiness: { state: "ready", detail: "" },
  action_label: "Run Release workflow",
  support: "linear_graph",
};

describe("capability presentation adapters", () => {
  it("keeps readiness and contextual actions on every runnable Desk kind", () => {
    const persona = fromWireRecipe({ id: "p1", name: "Scout", capability: {
      ...capability, kind: "persona", action_label: "Ask Scout",
    } });
    const sequence = fromWireChain({ id: "s1", name: "Triage", steps: ["p1"], capability: {
      ...capability, kind: "sequence", support: "linear_compatibility",
    } });
    const workflow = fromWireWorkflow({ id: "w1", name: "Release", graph_json: {}, capability });

    expect((persona.capability as any).action_label).toBe("Ask Scout");
    expect((sequence.capability as any).support).toBe("linear_compatibility");
    expect((workflow.capability as any).readiness.state).toBe("ready");
  });

  it("preserves an unavailable graph instead of pretending it can run", () => {
    const workflow = fromWireWorkflow({
      id: "w2", name: "Branchy", graph_json: { nodes: [{ id: "branch" }] },
      capability: {
        ...capability,
        readiness: { state: "unavailable", detail: "Control flow needs another host." },
        support: "unsupported_graph",
      },
    });
    expect(workflow.hasGraph).toBe(true);
    expect((workflow.capability as any).support).toBe("unsupported_graph");
  });
});
