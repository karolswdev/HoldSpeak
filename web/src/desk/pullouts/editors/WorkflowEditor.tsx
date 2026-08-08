/** Workflow inline editor content (HS-117-15). */
import { useMemo, useState } from "react";
import { useDesk } from "../../store";
import { StringGadget } from "../../surface/gadgets";
import {
  buildLinearGraph,
  parseLinearGraph,
  stepLabel,
  STEP_PALETTE,
  type LinearStep,
} from "../../graph";
import type { Workflow } from "../../../lib/primitives";
import { useDebouncedSave } from "./useDebouncedSave";
import type { InlineEditorContentProps } from "./types";

export function WorkflowEditor({ object: o }: InlineEditorContentProps) {
  const items = useDesk((s) => s.items);
  const save = useDebouncedSave("workflow", o.id);

  const live = useMemo(
    () => (items.workflow || []).find((x) => x.id === o.id) || o.ref as Workflow,
    [items, o.id],
  );
  const [f, setF] = useState<Record<string, string>>(() => ({
    name: String(live.name || ""),
  }));

  const [steps, setSteps] = useState<LinearStep[] | null>(() =>
    parseLinearGraph(live.graphJson),
  );

  const commitGraph = (next: LinearStep[], name?: string) => {
    setSteps(next);
    save({
      graph_json: buildLinearGraph(o.id, name ?? (f.name || "Workflow"), next),
    });
  };
  const setStepParam = (i: number, patch: Partial<LinearStep>) => {
    if (!steps) return;
    const next = steps.map((s, j) =>
      j === i ? ({ ...s, ...patch } as LinearStep) : s,
    );
    commitGraph(next);
  };

  return (
    <>
      <StringGadget
        label="Workflow name"
        value={f.name}
        placeholder="Name"
        onChange={(value) => {
          setF((prev) => ({ ...prev, name: value }));
          if (steps) {
            save({
              name: value,
              graph_json: buildLinearGraph(o.id, value || "Workflow", steps),
            });
          } else {
            save({ name: value });
          }
        }}
      />
      {steps ? (
        <div className="desk-wf-steps">
          {steps.map((s, i) => (
            <div key={i} className="desk-wf-step">
              <span className="desk-wf-step-label">{stepLabel(s)}</span>
              {s.kind === "rewrite" && (
                <StringGadget
                  label="Tone"
                  value={s.tone}
                  placeholder="Tone"
                  onChange={(tone) => setStepParam(i, { tone })}
                />
              )}
              {s.kind === "keepIf" && (
                <StringGadget
                  label="Keyword"
                  value={s.keyword}
                  placeholder="Keyword"
                  onChange={(keyword) => setStepParam(i, { keyword })}
                />
              )}
              {s.kind === "llm" && (
                <StringGadget
                  label="Prompt"
                  value={s.prompt}
                  placeholder="Prompt (selected text is substituted at run time)"
                  onChange={(prompt) => setStepParam(i, { prompt })}
                />
              )}
              <button
                type="button"
                className="desk-chip quiet"
                aria-label="Move step up"
                disabled={i === 0}
                onClick={() => {
                  const next = [...steps];
                  [next[i - 1], next[i]] = [next[i], next[i - 1]];
                  commitGraph(next);
                }}
              >
                ↑
              </button>
              <button
                type="button"
                className="desk-chip quiet"
                aria-label="Remove step"
                onClick={() =>
                  commitGraph(steps.filter((_, j) => j !== i))
                }
              >
                ✕
              </button>
            </div>
          ))}
          <div className="desk-wf-palette">
            {STEP_PALETTE.map((p) => (
              <button
                key={p.label}
                type="button"
                className="desk-chip quiet"
                onClick={() => commitGraph([...steps, p.make()])}
              >
                + {p.label}
              </button>
            ))}
          </div>
        </div>
      ) : (
        <p className="quiet">Graphed on iPad</p>
      )}
    </>
  );
}
