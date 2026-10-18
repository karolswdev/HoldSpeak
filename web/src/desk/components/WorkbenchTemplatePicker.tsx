/** Betterment A7 — New automation: the starters, plus Start from scratch
 * (docs/internal/betterment/workbench/DESIGN.md §4, "Starters").
 *
 * Each starter is one automation's sentence: what it does, when it runs and
 * where the result goes. A press makes exactly one automation with that
 * sentence (no agent is copied) and opens its window; a blank the starter
 * cannot guess ("About: which people?") is shown here and in the window.
 * Start from scratch makes one empty automation.
 *
 * HS-130-09 still holds: one press, one record, no orphan. The HS-116-05
 * template cards are parked (`_parked/WorkbenchTemplatePicker.tsx`). */
import "./automation/automation-home.css";
import { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch, readableError } from "../../lib/api";
import { Button } from "../../components/signal/Signal";
import { useDesk } from "../store";
import { SurfaceState } from "../surface/Surface";
import { useRovingRows } from "../surface/roving";
import { putWords, scheduleWords } from "./automation/model";

/** One starter (`holdspeak/workbench_templates.py` STARTERS). */
export interface AutomationStarter {
  id: string;
  name: string;
  description: string;
  instruction: string;
  sources: string[];
  when: { kind: string };
  /** The schedule as cron (shown in words); null when it is not scheduled. */
  schedule: string | null;
  output_target: string;
  /** The lines it cannot guess, in words: `{ about: "which people?" }`. */
  blanks: Record<string, string>;
}

function starterWhen(starter: AutomationStarter): string {
  return scheduleWords(starter.schedule) ?? "Only when I press Run now";
}

export function WorkbenchTemplatePicker({
  onCreated,
}: {
  onCreated?: (workbenchId: string) => void;
}) {
  const [starters, setStarters] = useState<AutomationStarter[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [busy, setBusy] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);
  const [createError, setCreateError] = useState("");
  const [created, setCreated] = useState<string | null>(null);
  const gridRef = useRef<HTMLDivElement>(null);
  useRovingRows(gridRef, { selector: ".automation-starter" });

  const loadStarters = useCallback(() => {
    setError(false);
    setLoading(true);
    return apiFetch<{ templates?: AutomationStarter[] }>("/api/workbench-templates")
      .then((answer) => setStarters(answer.templates || []))
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { void loadStarters(); }, [loadStarters]);

  const create = async (starter: AutomationStarter | null) => {
    if (busy || created) return;
    const name = starter?.name ?? "New automation";
    setSelected(starter?.id ?? "scratch");
    setBusy(true);
    setCreateError("");
    try {
      const answer = await apiFetch<{ workbench?: { id?: string } }>(
        starter ? `/api/workbench-templates/${encodeURIComponent(starter.id)}/instantiate` : "/api/workbenches",
        { method: "POST", json: starter ? {} : { name } },
      );
      const id = answer.workbench?.id;
      if (!id) {
        setCreateError(`${name} was not made. Try again.`);
        return;
      }
      // The POST saved it; its window reads it by id, so open it now. The
      // desk read after it only refreshes the lists.
      setCreated(id);
      useDesk.getState().openWorkbenchWindow(id);
      onCreated?.(id);
      void useDesk.getState().refresh();
    } catch (failure) {
      setCreateError(`${name} was not made: ${readableError(failure)}`);
    } finally {
      setBusy(false);
    }
  };

  if (error) {
    return <SurfaceState error="The starters did not load. Retry." onRetry={() => void loadStarters()} />;
  }
  if (loading) return <SurfaceState loading />;

  return (
    <div className="automation-starters" data-testid="automation-starters">
      {createError ? <SurfaceState error={createError} /> : null}
      <div ref={gridRef} className="automation-starter-grid">
        {starters.map((starter) => (
          <Button
            key={starter.id}
            variant="chrome"
            className="automation-starter"
            aria-pressed={selected === starter.id}
            disabled={busy || Boolean(created)}
            onClick={() => void create(starter)}
            data-testid={`automation-starter-${starter.id}`}
          >
            <span className="automation-starter-name">{starter.name}</span>
            <span className="automation-starter-words">{starter.description}</span>
            <span className="automation-starter-facts">
              {starterWhen(starter)} · {putWords(starter.output_target)}
            </span>
            {starter.blanks.about ? (
              <span className="automation-starter-blank">About: {starter.blanks.about}</span>
            ) : null}
          </Button>
        ))}
        <Button
          variant="chrome"
          className="automation-starter automation-starter-scratch"
          aria-pressed={selected === "scratch"}
          disabled={busy || Boolean(created)}
          onClick={() => void create(null)}
          data-testid="automation-starter-scratch"
        >
          <span className="automation-starter-name">Start from scratch</span>
          <span className="automation-starter-words">Say what it does, when, and with which engine.</span>
        </Button>
      </div>
    </div>
  );
}
