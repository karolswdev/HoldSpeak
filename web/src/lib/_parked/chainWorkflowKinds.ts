/* Parked 2026-11-08: the Sequence (chain) and Workflow Desk kinds.
 *
 * The Desk read no chain or workflow since #1979, and the iPad runs a crew as
 * one Mode run per step (#2002). The hub keeps the synced rows (CRUD + sync)
 * for the iPad. Kept verbatim; not compiled (tsconfig excludes _parked).
 */

// From web/src/lib/primitives.ts
export interface Chain {
  kind: "chain";
  id: string;
  name: string;
  steps: string[]; // agentId[]
  capability?: unknown | null;
}

/** The canonical `graph_json` wire (HSM-22-01 golden fixtures): Swift
 * tagged-union node kinds + the two edge sets, snake_case keys. An OBJECT on
 * the wire — never a string (the HSM-22-03 type fix; the old
 * `graphJson?: string` drifted from every producer and parser). */
export interface WorkflowGraphJson {
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

export interface Workflow {
  kind: "workflow";
  id: string;
  name: string;
  prompt?: string;
  graphJson?: WorkflowGraphJson;
  hasGraph?: boolean;
  capability?: unknown | null;
}


// From PRIMITIVE_DESCRIPTORS in web/src/lib/primitives.ts
export const PARKED_DESCRIPTORS = {
  chain: {
    kind: "chain",
    label: productLabel("sequence"),
    plural: productLabel("sequence", true),
    syncClass: "capability",
    blurb:
      "An advanced linear Workflow whose output flows through ordered steps.",
    icon: "M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1",
    authorable: true,
    capabilities: ["delete"],
    surface: { type: "pullout" },
  },
  workflow: {
    kind: "workflow",
    label: "Workflow",
    plural: "Workflows",
    syncClass: "capability",
    blurb: "Saved multi-step behavior that runs on selected material.",
    icon: "M6 3v12M18 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6zM6 21a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM6 15a9 9 0 0 0 9 9",
    authorable: true,
    capabilities: ["ask", "edit", "rename", "duplicate", "delete"],
    surface: { type: "pullout" },
  },
};

// From web/src/desk/api.ts
export const fromWireChain = (c: unknown): Chain | null => {
  const id = wireString(c, "id");
  if (!id) { warnMissingId("chain", c, "id"); return null; }
  return {
    kind: "chain",
    id,
    name: wireString(c, "name"),
    steps: wireArray(c, "steps").filter((s): s is string => typeof s === "string"),
    capability: wireRaw(c, "capability") ?? null,
  };
};

export const fromWireWorkflow = (w: unknown): Workflow | null => {
  const id = wireString(w, "id");
  if (!id) { warnMissingId("workflow", w, "id"); return null; }
  const graph = wireRaw(w, "graph_json");
  const hasGraph =
    graph != null && typeof graph === "object" && Object.keys(graph as Record<string, unknown>).length > 0;
  return {
    kind: "workflow",
    id,
    name: wireString(w, "name"),
    prompt: wireString(w, "prompt"),
    hasGraph: Boolean(hasGraph),
    graphJson: hasGraph ? (graph as Workflow["graphJson"]) : undefined,
    capability: wireRaw(w, "capability") ?? null,
  };
};
