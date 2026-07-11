import {
  type PointerEvent as ReactPointerEvent,
  useEffect,
  useMemo,
  useState,
} from "react";
import { Button, Field, Panel, TextArea } from "../components/signal/Signal";
import { apiFetch, readableError } from "../lib/api";
import { buildLinearGraph, parseLinearGraph, type LinearStep } from "../desk/graph";
import { PageHero } from "./pageSupport";
import {
  PRESETS,
  STEP_KINDS,
  graphFromWorkflow,
  loadLayout,
  saveLayout,
  type Node,
  type StepKind,
  type Workflow,
} from "../features/workbench/model";

function toWorkbench(id: string, name: string, graph: unknown): Workflow | null {
  const steps = parseLinearGraph(graph);
  if (!steps) return null;
  return {
    id,
    name,
    source: "selected-material",
    steps: steps.map((step) => {
      switch (step.kind) {
        case "summarize": return { kind: "summarize" as const };
        case "extract": return { kind: "extract" as const, prompt: step.artifactType.replace(/_/g, " ") };
        case "rewrite": return { kind: "rewrite" as const, prompt: step.tone };
        case "keepIf": return { kind: "keepIf" as const, prompt: step.keyword };
        case "llm": return { kind: "llmCall" as const, prompt: step.prompt };
      }
    }),
    output: "kept Artifact",
  };
}

function toLinear(workflow: Workflow): LinearStep[] {
  return workflow.steps.map((step) => {
    switch (step.kind) {
      case "summarize": return { kind: "summarize" };
      case "extract": return { kind: "extract", artifactType: step.prompt?.replace(/ /g, "_") || "action_items" };
      case "rewrite": return { kind: "rewrite", tone: step.prompt || "Executive" };
      case "keepIf": return { kind: "keepIf", keyword: step.prompt || "risk" };
      case "lens":
      case "llmCall": return { kind: "llm", prompt: step.prompt || "{input}" };
    }
  });
}

export default function WorkbenchPage() {
  const [workflow, setWorkflow] = useState<Workflow>(PRESETS[0]);
  const [layout, setLayout] = useState(() => loadLayout(PRESETS[0].id));
  const [selected, setSelected] = useState<Node | null>(null);
  const [drag, setDrag] = useState<{
    id: string;
    dx: number;
    dy: number;
  } | null>(null);
  const [linked, setLinked] = useState(false);
  const [support, setSupport] = useState("supported");
  const [status, setStatus] = useState("");
  const [runInput, setRunInput] = useState("");
  const [runOutput, setRunOutput] = useState("");
  const [artifactId, setArtifactId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const id = new URLSearchParams(window.location.search).get("workflow");
    if (!id) return;
    setBusy(true);
    apiFetch<any>(`/api/workflows/${encodeURIComponent(id)}`)
      .then(({ workflow: row }) => {
        const loaded = toWorkbench(row.id, row.name, row.graph_json);
        setLinked(true);
        setSupport(String(row.capability?.support || (loaded ? "supported" : "unsupported_graph")));
        if (loaded) {
          setWorkflow(loaded);
          setLayout(loadLayout(loaded.id));
        } else {
          setWorkflow({ id: row.id, name: row.name, source: "selected-material", steps: [], output: "kept Artifact" });
          setStatus(row.capability?.readiness?.detail || "This graph is read-only on this Workbench host.");
        }
      })
      .catch((error) => setStatus(readableError(error)))
      .finally(() => setBusy(false));
  }, []);

  const save = async () => {
    if (support === "unsupported_graph") return false;
    setBusy(true); setStatus("");
    try {
      const graph = buildLinearGraph(workflow.id, workflow.name, toLinear(workflow));
      await apiFetch(`/api/workflows/${encodeURIComponent(workflow.id)}`, {
        method: "PUT", json: { name: workflow.name, graph_json: graph },
      });
      setStatus("Saved to this Workflow.");
      return true;
    } catch (error) {
      setStatus(readableError(error));
      return false;
    } finally { setBusy(false); }
  };

  const run = async () => {
    if (!(await save())) return;
    setBusy(true); setRunOutput(""); setArtifactId(null);
    try {
      const result = await apiFetch<any>(`/api/workflows/${encodeURIComponent(workflow.id)}/run`, {
        method: "POST", json: { input: runInput },
      });
      setRunOutput(String(result.output || ""));
      setArtifactId(result.artifact_id ? String(result.artifact_id) : null);
      setStatus(`Receipt · ${result.invocation_id}`);
    } catch (error) {
      setStatus(readableError(error));
    } finally { setBusy(false); }
  };
  const graph = useMemo(
    () => graphFromWorkflow(workflow, layout),
    [workflow, layout],
  );
  const nodeById = (id: string) => graph.nodes.find((node) => node.id === id)!;
  const selectPreset = (next: Workflow) => {
    setWorkflow(structuredClone(next));
    setLayout(loadLayout(next.id));
    setSelected(null);
  };
  const startDrag = (event: ReactPointerEvent, node: Node) => {
    (event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);
    const rect = (
      event.currentTarget.parentElement as HTMLElement
    ).getBoundingClientRect();
    setDrag({
      id: node.id,
      dx: event.clientX - rect.left - node.x,
      dy: event.clientY - rect.top - node.y,
    });
  };
  const move = (event: ReactPointerEvent) => {
    if (!drag) return;
    const rect = event.currentTarget.getBoundingClientRect();
    const next = {
      ...layout,
      [drag.id]: {
        x: event.clientX - rect.left - drag.dx,
        y: event.clientY - rect.top - drag.dy,
      },
    };
    setLayout(next);
  };
  const stop = () => {
    if (drag) saveLayout(workflow.id, layout);
    setDrag(null);
  };
  const add = (kind: StepKind) =>
    setWorkflow((current) => ({
      ...current,
      steps: [...current.steps, { kind }],
    }));
  const prompt = (value: string) => {
    if (selected?.stepIndex === undefined) return;
    setWorkflow((current) => ({
      ...current,
      steps: current.steps.map((step, index) =>
        index === selected.stepIndex ? { ...step, prompt: value } : step,
      ),
    }));
    setSelected((current) =>
      current ? { ...current, subtitle: value } : current,
    );
  };

  return (
    <div className="page-wrap workbench-page">
      <PageHero
        eyebrow="Build"
        title="Workbench"
        actions={
          <div className="button-row">
            {linked && (
              <a className="button secondary dense" href={`/?open=${encodeURIComponent(`workflow:${workflow.id}`)}`}>
                Back to this Workflow
              </a>
            )}
            {PRESETS.map((preset) => (
              <Button
                dense
                key={preset.id}
                variant={workflow.id === preset.id ? "primary" : "secondary"}
                onClick={() => selectPreset(preset)}
              >
                {preset.name}
              </Button>
            ))}
          </div>
        }
      >
        {linked ? `Editing the exact “${workflow.name}” definition from your Desk.` : "Wire primitives into a run."}
        {" "}Drag to arrange; the graph remains the canonical linear Workflow shape.
      </PageHero>
      {status && <p className={support === "unsupported_graph" ? "notice error" : "notice"}>{status}</p>}
      <div
        className="workbench-canvas"
        tabIndex={0}
        aria-label="Workflow canvas"
        onPointerMove={move}
        onPointerUp={stop}
        onPointerCancel={stop}
      >
        <svg className="workbench-cables" aria-hidden="true">
          {graph.edges.map((edge) => {
            const from = nodeById(edge.from);
            const to = nodeById(edge.to);
            const x1 = from.x + 210;
            const y1 = from.y + 50;
            const x2 = to.x;
            const y2 = to.y + 50;
            return (
              <path
                key={edge.id}
                className={`is-${edge.type}`}
                d={`M${x1},${y1} C${x1 + 70},${y1} ${x2 - 70},${y2} ${x2},${y2}`}
              />
            );
          })}
        </svg>
        {graph.nodes.map((node) => (
          <button
            key={node.id}
            type="button"
            className={`workbench-node is-${node.role} is-${node.type}${selected?.id === node.id ? " selected" : ""}`}
            style={{ transform: `translate(${node.x}px, ${node.y}px)` }}
            onPointerDown={(event) => startDrag(event, node)}
            onClick={() => setSelected(node)}
          >
            <span>{node.role}</span>
            <strong>{node.title}</strong>
            <small>{node.subtitle}</small>
            <i aria-hidden="true" />
          </button>
        ))}
        <div className="workbench-palette" role="group" aria-label="Add a node">
          <span>Add</span>
          {(Object.keys(STEP_KINDS) as StepKind[]).map((kind) => (
            <Button dense key={kind} disabled={support === "unsupported_graph"} onClick={() => add(kind)}>
              {STEP_KINDS[kind].title}
            </Button>
          ))}
        </div>
        {selected ? (
          <Panel
            className="workbench-inspector"
            title={selected.title}
            eyebrow={`${selected.role} · ${selected.type}`}
            actions={
              <Button dense variant="ghost" onClick={() => setSelected(null)}>
                Close
              </Button>
            }
          >
            <Field
              label="Prompt"
              description={
                selected.role === "step"
                  ? "What this step should do."
                  : "Source and output nodes are structural."
              }
            >
              {({ id, describedBy }) => (
                <TextArea
                  id={id}
                  aria-describedby={describedBy}
                  value={selected.subtitle}
                  disabled={selected.role !== "step"}
                  onChange={(event) => prompt(event.target.value)}
                />
              )}
            </Field>
          </Panel>
        ) : null}
      </div>
      <Panel title="Run and return" eyebrow="Workflow result">
        <Field label="Material" description="The input stays here if the run fails, ready to retry.">
          {({ id, describedBy }) => (
            <TextArea id={id} aria-describedby={describedBy} value={runInput}
              onChange={(event) => setRunInput(event.target.value)} />
          )}
        </Field>
        <div className="button-row">
          <Button disabled={busy || support === "unsupported_graph"} onClick={() => void save()}>Save Workflow</Button>
          <Button variant="primary" disabled={busy || support === "unsupported_graph"} onClick={() => void run()}>
            Run {workflow.name}
          </Button>
          {artifactId && <a className="button secondary" href={`/?open=${encodeURIComponent(`artifact:${artifactId}`)}`}>Return to kept Artifact</a>}
        </div>
        {runOutput && <pre>{runOutput}</pre>}
      </Panel>
    </div>
  );
}
