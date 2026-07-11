/** HSM-22-03 — the web builder emits the canonical graph_json wire.
 *
 * The expectations mirror the HSM-22-01 golden fixtures
 * (`contracts/fixtures/blueprint-*.json`, encoded by Swift) and the hub's
 * `workflow_graph.linearize()` vocabulary — the same shape on all three
 * surfaces, or nothing travels.
 */
import { describe, expect, it } from "vitest";
import {
  buildLinearGraph,
  parseLinearGraph,
  stepLabel,
  STEP_PALETTE,
} from "../graph";

describe("buildLinearGraph", () => {
  it("emits the canonical tagged-union wire the hub linearizes", () => {
    const g = buildLinearGraph("wf-1", "Web workflow", [
      { kind: "summarize" },
      { kind: "extract", artifactType: "decisions" },
      { kind: "rewrite", tone: "Executive" },
      { kind: "keepIf", keyword: "risk" },
      { kind: "llm", prompt: "From {input}, list risks." },
    ]);

    expect(g.entry).toBe("entry");
    expect(g.data_edges).toEqual([]);
    // The chain: entry → source → n1…n5 → out, one exec edge per hop.
    expect(g.nodes.map((n) => n.id)).toEqual([
      "entry",
      "source",
      "n1",
      "n2",
      "n3",
      "n4",
      "n5",
      "out",
    ]);
    expect(g.exec_edges).toEqual([
      { from: { node: "entry", name: "then" }, to: "source" },
      { from: { node: "source", name: "then" }, to: "n1" },
      { from: { node: "n1", name: "then" }, to: "n2" },
      { from: { node: "n2", name: "then" }, to: "n3" },
      { from: { node: "n3", name: "then" }, to: "n4" },
      { from: { node: "n4", name: "then" }, to: "n5" },
      { from: { node: "n5", name: "then" }, to: "out" },
    ]);
    // The Swift-Codable kind shapes, exactly (incl. extract's `_0` and the
    // snake_cased `keep_if` case name).
    expect(g.nodes.map((n) => n.kind)).toEqual([
      { entry: {} },
      { source: {} },
      { summarize: {} },
      { extract: { _0: "decisions" } },
      { rewrite: { tone: "Executive" } },
      { keep_if: { keyword: "risk" } },
      { llm: { name: "LLM call", prompt: "From {input}, list risks." } },
      { output: {} },
    ]);
  });

  it("an empty llm prompt still runs (the {input} passthrough)", () => {
    const g = buildLinearGraph("wf-2", "W", [{ kind: "llm", prompt: "   " }]);
    expect(g.nodes[2].kind).toEqual({
      llm: { name: "LLM call", prompt: "{input}" },
    });
  });
});

describe("parseLinearGraph", () => {
  it("round-trips what the builder emits", () => {
    const steps = [
      { kind: "summarize" },
      { kind: "extract", artifactType: "action_items" },
      { kind: "keepIf", keyword: "blocker" },
    ] as const;
    const g = buildLinearGraph("wf-3", "RT", [...steps]);
    expect(parseLinearGraph(g)).toEqual([...steps]);
  });

  it("refuses control flow (read-only, like the hub refuses to run it)", () => {
    const g = {
      id: "x",
      name: "Branchy",
      entry: "e1",
      nodes: [
        { id: "e1", kind: { entry: {} } },
        {
          id: "br",
          kind: { branch: { condition: { contains: { keyword: "x" } } } },
        },
      ],
      exec_edges: [{ from: { node: "e1", name: "then" }, to: "br" }],
      data_edges: [],
    };
    expect(parseLinearGraph(g)).toBeNull();
  });

  it("refuses fan-out and cycles", () => {
    const fanOut = buildLinearGraph("wf-4", "F", [{ kind: "summarize" }]);
    fanOut.exec_edges.push({
      from: { node: "source", name: "then" },
      to: "out",
    });
    expect(parseLinearGraph(fanOut)).toBeNull();

    const cycle = buildLinearGraph("wf-5", "C", [{ kind: "summarize" }]);
    cycle.exec_edges[cycle.exec_edges.length - 1] = {
      from: { node: "n1", name: "then" },
      to: "entry",
    };
    expect(parseLinearGraph(cycle)).toBeNull();
  });

  it("refuses iPad provenance (failure_policy/runs_on must never be stripped)", () => {
    const g = buildLinearGraph("wf-6", "P", [{ kind: "summarize" }]);
    g.nodes[2].runs_on = "endpoint";
    expect(parseLinearGraph(g)).toBeNull();

    const g2 = buildLinearGraph("wf-7", "P2", [{ kind: "summarize" }]);
    g2.nodes[2].failure_policy = "skip";
    expect(parseLinearGraph(g2)).toBeNull();
  });

  it("tolerates explicit null provenance (the Swift-absent = hub-None rule)", () => {
    const g = buildLinearGraph("wf-8", "N", [{ kind: "summarize" }]);
    (g.nodes[2] as any).failure_policy = null;
    expect(parseLinearGraph(g)).toEqual([{ kind: "summarize" }]);
  });

  it("refuses junk", () => {
    expect(parseLinearGraph(null)).toBeNull();
    expect(parseLinearGraph({})).toBeNull();
    expect(parseLinearGraph({ nodes: [], exec_edges: "nope" })).toBeNull();
  });
});

describe("the palette + labels", () => {
  it("every palette entry builds and labels", () => {
    for (const p of STEP_PALETTE) {
      const s = p.make();
      expect(stepLabel(s).length).toBeGreaterThan(0);
      const g = buildLinearGraph("wf-p", "P", [s]);
      // A fresh empty llm prompt lowers to the {input} passthrough by design.
      const expected =
        s.kind === "llm" && !s.prompt.trim() ? { ...s, prompt: "{input}" } : s;
      expect(parseLinearGraph(g)).toEqual([expected]);
    }
  });
});
