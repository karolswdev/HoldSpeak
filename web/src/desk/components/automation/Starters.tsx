/** New automation uses the same inspector form as its saved setup. */
import { useEffect, useRef, useState } from "react";
import { apiFetch, readableError } from "../../../lib/api";
import { CycleGadget, InspectorForm, SurfaceState } from "../../surface";
import { putWords, scheduleWords } from "./model";

export interface AutomationStarter {
  id: string; name: string; description: string; instruction: string;
  sources: string[]; when: { kind: string }; schedule: string | null;
  output_target: string; blanks: Record<string, string>;
}

export function AutomationStarters({ onCreated, onCancel = () => undefined }: {
  onCreated(id: string): void; onCancel?(): void;
}) {
  const [starters, setStarters] = useState<AutomationStarter[]>([]);
  const [loading, setLoading] = useState(true);
  const [readError, setReadError] = useState("");
  const [choice, setChoice] = useState("scratch");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const inFlight = useRef(false);
  const load = async () => {
    setLoading(true); setReadError("");
    try { const answer = await apiFetch<{ templates: AutomationStarter[] }>("/api/workbench-templates"); setStarters(answer.templates); }
    catch (failure) { setReadError(readableError(failure)); }
    finally { setLoading(false); }
  };
  useEffect(() => { void load(); }, []);
  const starter = starters.find((row) => row.id === choice);
  const create = async () => {
    if (inFlight.current) return;
    inFlight.current = true; setBusy(true); setError("");
    try {
      const answer = await apiFetch<{ workbench?: { id?: string } }>(starter
        ? `/api/workbench-templates/${encodeURIComponent(starter.id)}/instantiate` : "/api/workbenches",
      { method: "POST", json: starter ? {} : { name: "New automation" } });
      if (!answer.workbench?.id) throw new Error("No automation was returned");
      onCreated(answer.workbench.id);
    } catch (failure) { setError(`${starter?.name ?? "New automation"} was not made: ${readableError(failure)}`); inFlight.current = false; setBusy(false); }
  };
  return <InspectorForm testId="automation-starters" rows={[
    { label: "Start from", control: <CycleGadget label="Automation starter" value={choice} disabled={busy || loading} onChange={setChoice}
      options={[{value:"scratch",label:"Start from scratch"}, ...starters.map((row) => ({value:row.id,label:row.name}))]} /> },
    { label: "Runs", control: starter ? scheduleWords(starter.schedule) ?? "On request" : "On request" },
    { label: "Do", control: starter?.instruction || "Choose what to do" },
    ...(starter?.blanks.about ? [{ label: "About", control: starter.blanks.about }] : []),
    { label: "Put it in", control: putWords(starter?.output_target) },
  ]} notice={loading || readError || error ? <SurfaceState loading={loading} error={readError || error || undefined} onRetry={readError ? () => void load() : undefined} /> : undefined}
    completion={{cancel:onCancel,cancelDisabled:busy,primary:{label:"Create",run:() => void create(),disabled:loading || Boolean(readError),busy,testId:"automation-create"}}} />;
}
