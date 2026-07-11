import {
  type PointerEvent as ReactPointerEvent,
  useMemo,
  useState,
} from "react";
import { Button, Field, Panel, TextArea } from "../components/signal/Signal";
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

export default function WorkbenchPage() {
  const [workflow, setWorkflow] = useState<Workflow>(PRESETS[0]);
  const [layout, setLayout] = useState(() => loadLayout(PRESETS[0].id));
  const [selected, setSelected] = useState<Node | null>(null);
  const [drag, setDrag] = useState<{
    id: string;
    dx: number;
    dy: number;
  } | null>(null);
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
        Wire primitives into a run. Drag to arrange; the graph remains the
        canonical linear Workflow shape.
      </PageHero>
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
            <Button dense key={kind} onClick={() => add(kind)}>
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
    </div>
  );
}
