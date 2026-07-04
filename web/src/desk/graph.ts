/** HSM-22-03 — the web's linear graph builder.
 *
 * Lowers an ordered step list to the canonical `graph_json` wire — the EXACT
 * shape the iPad's Blueprint encoder emits (HSM-22-01 golden fixtures,
 * `contracts/fixtures/blueprint-*.json`) and the hub's
 * `workflow_graph.linearize()` parses: Swift tagged-union node kinds
 * (`{"summarize": {}}`, `{"extract": {"_0": "decisions"}}`, `{"keep_if": …}`),
 * `exec_edges` chaining named exec-outs, empty `data_edges`.
 *
 * Linear only, honestly: the web authors the faithful subset the hub runs;
 * control flow stays graphed on the iPad's Blueprint canvas. A graph this
 * module cannot parse back (branches, foreign kinds) is presented read-only.
 */

export interface WorkflowGraphWire {
  id: string;
  name: string;
  entry: string;
  nodes: Array<{
    id: string;
    kind: Record<string, Record<string, unknown>>;
    failure_policy?: string | null;
    runs_on?: string;
  }>;
  exec_edges: Array<{ from: { node: string; name: string }; to: string }>;
  data_edges: unknown[];
}

/** One authored step — the faithful-subset vocabulary. */
export type LinearStep =
  | { kind: "summarize" }
  | { kind: "extract"; artifactType: string }
  | { kind: "rewrite"; tone: string }
  | { kind: "keepIf"; keyword: string }
  | { kind: "llm"; prompt: string };

/** The palette the editor offers (label + a fresh default step). */
export const STEP_PALETTE: Array<{ label: string; make: () => LinearStep }> = [
  { label: "Summarize", make: () => ({ kind: "summarize" }) },
  { label: "Decisions", make: () => ({ kind: "extract", artifactType: "decisions" }) },
  { label: "Action items", make: () => ({ kind: "extract", artifactType: "action_items" }) },
  { label: "Rewrite", make: () => ({ kind: "rewrite", tone: "Executive" }) },
  { label: "Keep if", make: () => ({ kind: "keepIf", keyword: "risk" }) },
  { label: "LLM prompt", make: () => ({ kind: "llm", prompt: "" }) },
];

/** A short human label for a step (the pull-out's steps list). */
export function stepLabel(s: LinearStep): string {
  switch (s.kind) {
    case "summarize": return "Summarize";
    case "extract": return `Extract · ${s.artifactType.replace(/_/g, " ")}`;
    case "rewrite": return `Rewrite · ${s.tone}`;
    case "keepIf": return `Keep if · ${s.keyword}`;
    case "llm": return s.prompt ? `LLM · “${s.prompt.slice(0, 40)}${s.prompt.length > 40 ? "…" : ""}”` : "LLM prompt";
  }
}

function nodeKind(s: LinearStep): Record<string, Record<string, unknown>> {
  switch (s.kind) {
    case "summarize": return { summarize: {} };
    case "extract": return { extract: { _0: s.artifactType } };
    case "rewrite": return { rewrite: { tone: s.tone } };
    // Swift's `keepIf` case name reaches the wire snake_cased by the canonical coder.
    case "keepIf": return { keep_if: { keyword: s.keyword } };
    case "llm": return { llm: { name: "LLM call", prompt: s.prompt.trim() || "{input}" } };
  }
}

/** Lower an ordered step list to the canonical wire: entry → source → n1…nk → out. */
export function buildLinearGraph(id: string, name: string, steps: LinearStep[]): WorkflowGraphWire {
  const nodes: WorkflowGraphWire["nodes"] = [
    { id: "entry", kind: { entry: {} } },
    { id: "source", kind: { source: {} } },
  ];
  const execEdges: WorkflowGraphWire["exec_edges"] = [
    { from: { node: "entry", name: "then" }, to: "source" },
  ];
  let prev = "source";
  steps.forEach((s, i) => {
    const nid = `n${i + 1}`;
    nodes.push({ id: nid, kind: nodeKind(s) });
    execEdges.push({ from: { node: prev, name: "then" }, to: nid });
    prev = nid;
  });
  nodes.push({ id: "out", kind: { output: {} } });
  execEdges.push({ from: { node: prev, name: "then" }, to: "out" });
  return { id, name, entry: "entry", nodes, exec_edges: execEdges, data_edges: [] };
}

/** Parse a graph back into an editable step list — null when the graph is
 * anything the web's linear editor cannot faithfully re-emit (control flow,
 * fan-out, unknown kinds): those stay read-only, never silently rewritten. */
export function parseLinearGraph(graph: unknown): LinearStep[] | null {
  const g = graph as WorkflowGraphWire | null;
  if (!g || !Array.isArray(g.nodes) || !Array.isArray(g.exec_edges)) return null;

  const byId = new Map(g.nodes.map((n) => [n.id, n]));
  // Follow the single exec chain from the entry; any fan-out disqualifies.
  const outgoing = new Map<string, string[]>();
  for (const e of g.exec_edges) {
    const from = e?.from?.node;
    if (!from || !e.to) return null;
    outgoing.set(from, [...(outgoing.get(from) || []), e.to]);
  }
  const steps: LinearStep[] = [];
  let cursor: string | undefined = g.entry;
  const seen = new Set<string>();
  while (cursor) {
    if (seen.has(cursor)) return null; // cycle
    seen.add(cursor);
    const node = byId.get(cursor);
    if (!node) return null;
    // Per-node provenance (failure_policy / runs_on) is iPad-authored; this
    // editor cannot re-emit it, so re-saving would silently strip it. Such a
    // graph stays read-only here — never rewritten to less than it was.
    if (node.failure_policy != null || node.runs_on != null) return null;
    const tag = Object.keys(node.kind || {})[0];
    const payload = (node.kind || {})[tag] || {};
    switch (tag) {
      case "entry":
      case "source":
      case "output":
        break;
      case "summarize":
        steps.push({ kind: "summarize" });
        break;
      case "extract":
        steps.push({ kind: "extract", artifactType: String(payload._0 || "decisions") });
        break;
      case "rewrite":
        steps.push({ kind: "rewrite", tone: String(payload.tone || "Executive") });
        break;
      case "keep_if":
        steps.push({ kind: "keepIf", keyword: String(payload.keyword || "") });
        break;
      case "llm":
        steps.push({ kind: "llm", prompt: String(payload.prompt || "") });
        break;
      default:
        return null; // control flow / unknown — read-only
    }
    const nexts = outgoing.get(cursor) || [];
    if (nexts.length > 1) return null; // fan-out — read-only
    cursor = nexts[0];
  }
  return steps;
}
