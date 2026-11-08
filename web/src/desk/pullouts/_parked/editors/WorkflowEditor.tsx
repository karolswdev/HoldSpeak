/** Workflow inline editor content (HS-117-15). */
import { useMemo, useState } from "react";
import { useDesk } from "../../store";
import { PadGadget, StringGadget } from "../../surface/gadgets";
import { Button } from "../../../components/signal/Signal";
import {
  buildLinearGraph,
  parseLinearGraph,
  stepLabel,
  STEP_PALETTE,
  type LinearStep,
} from "../../graph";
import type { Workflow } from "../../../lib/primitives";
import { useDebouncedSave } from "./useDebouncedSave";
import { keptEditorPatch, keptField } from "./editorDraft";
import type { InlineEditorContentProps } from "./types";

export function WorkflowEditor({ object: o, autoFocusName, onWriter }: InlineEditorContentProps) {
  const items = useDesk((s) => s.items);
  const save = useDebouncedSave("workflow", o.id, onWriter);

  const live = useMemo(
    () => (items.workflow || []).find((x) => x.id === o.id) || o.ref as Workflow,
    [items, o.id],
  );
  // PHILO-13-07 (B2): an edit the hub has not kept returns after a reload.
  const [kept] = useState(() => keptEditorPatch("workflow", o.id));
  const [f, setF] = useState<Record<string, string>>(() => ({
    name: keptField(kept, "name", String(live.name || "")),
    prompt: keptField(kept, "prompt", String(live.prompt || "")),
  }));
  const graph = kept.graph_json ?? live.graphJson;
  const promptOnly = !graph || (typeof graph === "object" && !Object.keys(graph).length);

  const [steps, setSteps] = useState<LinearStep[] | null>(() =>
    parseLinearGraph(kept.graph_json ?? live.graphJson),
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
        autoFocus={autoFocusName}
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
      {promptOnly ? <PadGadget label="Prompt" value={f.prompt} rows={5} onChange={(prompt) => {
        setF((prev) => ({ ...prev, prompt })); save({ prompt });
      }} /> : steps ? (
        <div className="desk-wf-steps">
          {steps.map((s, i) => (
            <div key={i} className="desk-wf-step">
              <div className="desk-wf-step-head">
              <span className="desk-wf-step-label">{s.kind === "llm" ? "AI prompt" : stepLabel(s)}</span>
              <Button dense variant="ghost" aria-label="Move step up" disabled={i === 0} onClick={() => {
                const next = [...steps]; [next[i - 1], next[i]] = [next[i], next[i - 1]]; commitGraph(next);
              }}>Move up</Button>
              <Button dense variant="ghost" aria-label="Remove step" onClick={() => commitGraph(steps.filter((_, j) => j !== i))}>Remove</Button>
              </div>
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
                <PadGadget
                  label="Prompt"
                  value={s.prompt}
                  placeholder="Prompt (selected text is substituted at run time)"
                  onChange={(prompt) => setStepParam(i, { prompt })}
                />
              )}
            </div>
          ))}
          <div className="desk-wf-palette">
            {STEP_PALETTE.map((p) => (
              <Button
                key={p.label}
                dense variant="ghost"
                onClick={() => commitGraph([...steps, p.make()])}
              >
                + {p.label === "LLM prompt" ? "AI prompt" : p.label}
              </Button>
            ))}
          </div>
        </div>
      ) : (
        <span className="quiet">Graph editing · iPad</span>
      )}
    </>
  );
}
