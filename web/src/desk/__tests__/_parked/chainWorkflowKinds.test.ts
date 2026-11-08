/* Parked 2026-11-08 with the Sequence and Workflow Desk kinds
 * (src/lib/_parked/chainWorkflowKinds.ts). Kept, not collected. */

// From src/desk/__tests__/capability.test.ts
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

    expect((persona!.capability as any).action_label).toBe("Ask Scout");
    expect((sequence!.capability as any).support).toBe("linear_compatibility");
    expect((workflow!.capability as any).readiness.state).toBe("ready");
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
    expect(workflow!.hasGraph).toBe(true);
    expect((workflow!.capability as any).support).toBe("unsupported_graph");
  });
});


// From src/desk/__tests__/desk.test.ts
  it("workflow graph_json stays an object", () => {
    const w = fromWireWorkflow({
      id: "w",
      name: "W",
      graph_json: { nodes: [] },
    });
    expect(w!.hasGraph).toBe(true);
    expect(typeof w!.graphJson).toBe("object");
  });


// From src/desk/__tests__/wireGuard.test.ts
describe("fromWireChain", () => {
  it("maps valid wire data", () => {
    const c = fromWireChain({
      id: "c1",
      name: "Pipeline",
      steps: ["a1", "a2"],
      capability: { readiness: { state: "ready" } },
    })!;
    expect(c.kind).toBe("chain");
    expect(c.steps).toEqual(["a1", "a2"]);
    expect(c.capability).toBeTruthy();
  });
});

describe("fromWireWorkflow", () => {
  it("maps valid wire data with graph", () => {
    const w = fromWireWorkflow({
      id: "w1",
      name: "Summarize",
      prompt: "Do it",
      graph_json: { id: "g1", name: "g", entry: "n1", nodes: [], exec_edges: [], data_edges: [] },
      capability: null,
    })!;
    expect(w.kind).toBe("workflow");
    expect(w.hasGraph).toBe(true);
    expect(w.graphJson).toBeTruthy();
  });
  it("handles empty graph", () => {
    const spy = vi.spyOn(console, "warn").mockImplementation(() => {});
    const w = fromWireWorkflow({ id: "w2", name: "Empty" })!;
    expect(w.hasGraph).toBe(false);
    expect(w.graphJson).toBeUndefined();
    spy.mockRestore();
  });
});

