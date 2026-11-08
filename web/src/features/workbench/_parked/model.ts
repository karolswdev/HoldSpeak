export type StepKind =
  "lens" | "summarize" | "extract" | "rewrite" | "keepIf" | "llmCall";
export type Workflow = {
  id: string;
  name: string;
  source: string;
  steps: Array<{ kind: StepKind; prompt?: string }>;
  output: string;
};
export type Node = {
  id: string;
  title: string;
  subtitle: string;
  role: "source" | "step" | "output";
  x: number;
  y: number;
  type: "text" | "findings" | "signal";
  stepIndex?: number;
};
export type Edge = { id: string; from: string; to: string; type: Node["type"] };

export const STEP_KINDS: Record<
  StepKind,
  { title: string; type: Node["type"] }
> = {
  lens: { title: "Lens", type: "text" },
  summarize: { title: "Summarize", type: "text" },
  extract: { title: "Extract actions", type: "findings" },
  rewrite: { title: "Rewrite", type: "text" },
  keepIf: { title: "Keep if", type: "signal" },
  llmCall: { title: "LLM call", type: "text" },
};
export const PRESETS: Workflow[] = [
  {
    id: "preset-digest",
    name: "Meeting digest",
    source: "full-transcript",
    steps: [{ kind: "summarize" }, { kind: "extract" }],
    output: "artifact",
  },
  {
    id: "preset-followup",
    name: "Follow-up draft",
    source: "full-transcript",
    steps: [
      { kind: "lens", prompt: "decisions and owners" },
      { kind: "summarize" },
      { kind: "rewrite", prompt: "a friendly follow-up email" },
    ],
    output: "draft",
  },
  {
    id: "preset-triage",
    name: "Action triage",
    source: "tacked",
    steps: [
      { kind: "extract" },
      { kind: "keepIf", prompt: "assigned to me" },
      { kind: "llmCall", prompt: "Draft a GitHub issue for each" },
    ],
    output: "issues",
  },
];

export function graphFromWorkflow(
  workflow: Workflow,
  layout: Record<string, { x: number; y: number }> = {},
): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = [];
  const edges: Edge[] = [];
  const pos = (id: string, index: number) =>
    layout[id] ?? { x: 90 + index * 290, y: 190 };
  nodes.push({
    id: "source",
    title: workflow.source.replace(/-/g, " "),
    subtitle: "meeting input",
    role: "source",
    type: "text",
    ...pos("source", 0),
  });
  let previous = nodes[0];
  workflow.steps.forEach((step, index) => {
    const meta = STEP_KINDS[step.kind];
    const id = `step-${index}`;
    const node: Node = {
      id,
      title: meta.title,
      subtitle: step.prompt ?? "",
      role: "step",
      type: meta.type,
      stepIndex: index,
      ...pos(id, index + 1),
    };
    nodes.push(node);
    edges.push({
      id: `${previous.id}-${id}`,
      from: previous.id,
      to: id,
      type: previous.type,
    });
    previous = node;
  });
  const output: Node = {
    id: "output",
    title: "Output",
    subtitle: workflow.output,
    role: "output",
    type: previous.type,
    ...pos("output", workflow.steps.length + 1),
  };
  nodes.push(output);
  edges.push({
    id: `${previous.id}-output`,
    from: previous.id,
    to: "output",
    type: previous.type,
  });
  return { nodes, edges };
}

export function loadLayout(
  id: string,
): Record<string, { x: number; y: number }> {
  try {
    const all = JSON.parse(localStorage.getItem("hs.workflows.v1") ?? "{}");
    return all[id]?.layout ?? {};
  } catch {
    return {};
  }
}
export function saveLayout(
  id: string,
  layout: Record<string, { x: number; y: number }>,
) {
  try {
    const all = JSON.parse(localStorage.getItem("hs.workflows.v1") ?? "{}");
    all[id] = { ...(all[id] ?? {}), layout };
    localStorage.setItem("hs.workflows.v1", JSON.stringify(all));
  } catch {
    /* optional device-local layout */
  }
}
