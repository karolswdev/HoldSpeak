// HS-69-10: the Workbench model — a plain JS object that is the EXACT shape of
// the engine `Workflow` JSON (apple/.../Workflow.swift:102), so a web-built
// workflow and an iPad-built one are the same artifact:
//
//   { id, name, source, steps: [ {kind, ...} ], output }
//
// The free node-graph is visual sugar over this linear pipeline (the Phase-68
// finding): the canvas lays the source → steps → output out as a chain. This
// module owns the model + presets + the node/edge derivation the canvas renders.
// Framework-free.

// Port/data types → the web-wins status palette (Phase-69 decision):
//   text → --accent · findings → --ok · signal → --info
export const PORT_TYPE = {
  text: { color: "var(--accent)", label: "text" },
  findings: { color: "var(--ok)", label: "findings" },
  signal: { color: "var(--info)", label: "signal" },
};

// Step kind → display + the data type it OUTPUTS (drives the cable color).
export const STEP_KINDS = {
  lens: { title: "Lens", glyph: "eye", out: "text" },
  summarize: { title: "Summarize", glyph: "doc", out: "text" },
  extract: { title: "Extract actions", glyph: "check", out: "findings" },
  rewrite: { title: "Rewrite", glyph: "pen", out: "text" },
  keepIf: { title: "Keep if", glyph: "filter", out: "signal" },
  llmCall: { title: "LLM call", glyph: "spark", out: "text" },
};

export const SOURCE_KINDS = {
  "full-transcript": { title: "Full transcript", glyph: "transcript" },
  tacked: { title: "Tacked moments", glyph: "pin" },
  selection: { title: "Selection", glyph: "select" },
};

// A small library of preset workflows (port of WorkflowPresets.all).
export const PRESETS = [
  {
    id: "preset-digest",
    name: "Meeting digest",
    source: "full-transcript",
    steps: [
      { kind: "summarize" },
      { kind: "extract" },
    ],
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

const STEP_W = 210; // node card width (world px)
const STEP_GAP = 96; // horizontal gap between nodes
const ROW_Y = 200; // the chain's baseline y

/**
 * Derive the renderable nodes + edges from a Workflow. Linear chain:
 * source → step0 → step1 → … → output. Positions auto-laid left-to-right
 * (then the canvas may override x/y from a saved layout / a drag).
 * @returns {{nodes: object[], edges: object[]}}
 */
export function graphFromWorkflow(wf, layout) {
  const nodes = [];
  const edges = [];
  let i = 0;
  const place = (id) => {
    const saved = layout && layout[id];
    return {
      x: saved ? saved.x : 80 + i * (STEP_W + STEP_GAP),
      y: saved ? saved.y : ROW_Y,
    };
  };

  // source node
  const src = SOURCE_KINDS[wf.source] || { title: wf.source, glyph: "transcript" };
  nodes.push({ id: "source", role: "source", title: src.title, glyph: src.glyph,
               outType: "text", ...place("source") });
  i++;

  let prevId = "source";
  (wf.steps || []).forEach((step, idx) => {
    const meta = STEP_KINDS[step.kind] || { title: step.kind, glyph: "spark", out: "text" };
    const id = `step-${idx}`;
    nodes.push({
      id, role: "step", kind: step.kind, title: meta.title, glyph: meta.glyph,
      subtitle: step.prompt || "", inType: "text", outType: meta.out, ...place(id),
    });
    edges.push({ id: `e-${prevId}-${id}`, from: prevId, to: id,
                 type: nodes.find((n) => n.id === prevId).outType });
    prevId = id;
    i++;
  });

  // output node
  const outMeta = STEP_KINDS[prevId === "source" ? "summarize" : null];
  nodes.push({ id: "output", role: "output", title: "Output", subtitle: wf.output || "",
               glyph: "out", inType: nodes[nodes.length - 1].outType, ...place("output") });
  edges.push({ id: `e-${prevId}-output`, from: prevId, to: "output",
               type: nodes.find((n) => n.id === prevId).outType });
  void outMeta;

  return { nodes, edges };
}

const LS_KEY = "hs.workflows.v1"; // the iPad's exact key

// The per-workflow persisted state: { layout: {id:{x,y}}, edges: [...],
// prompts: {nodeId: text} }. One read/merge/write keeps node positions, any
// re-wired cables (HS-69-11), and inspector prompt edits together.
export function loadState(workflowId) {
  try {
    const all = JSON.parse(window.localStorage.getItem(LS_KEY) || "{}");
    return all[workflowId] || {};
  } catch (_e) {
    return {};
  }
}

export function saveState(workflowId, partial) {
  try {
    const all = JSON.parse(window.localStorage.getItem(LS_KEY) || "{}");
    all[workflowId] = { ...(all[workflowId] || {}), ...partial };
    window.localStorage.setItem(LS_KEY, JSON.stringify(all));
  } catch (_e) {
    /* localStorage may be unavailable; persistence is non-critical */
  }
}

// back-compat thin wrappers (canvas.js layout path)
export function loadLayout(workflowId) {
  return loadState(workflowId).layout || null;
}
export function saveLayout(workflowId, layout) {
  saveState(workflowId, { layout });
}

// Two ports are compatible when their data types match (the iPad PortType rule).
export function portsCompatible(outType, inType) {
  return String(outType) === String(inType);
}
