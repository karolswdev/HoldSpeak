// One home for assignments and models. The hub owns every chain and its order.
import { useEffect, useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { DotWord, Spine, type SpineTone } from "../../../desk/surface";
import { stateWord } from "../../../features/runson/stateWord";
import { EngineLibrary } from "../../../features/runson/EngineLibrary";
import { useRunsOn } from "../../../features/runson/useRunsOn";
import { EVERYTHING_ELSE, WHAT_ROWS } from "../../../features/runson/whatRows";
import type { RowEditor } from "../../../features/runson/api";
import { SectionMast, SettingLine, SettingsLedger, SettingsPlate } from "./native";
import "../../../features/runson/engines.css";

type Health = { word: string; tone: SpineTone };
function health(editor: RowEditor | "failed" | undefined): Health {
  if (editor === "failed") return { word: "Not read", tone: "coral" };
  if (!editor) return { word: "Reading", tone: "steel" };
  if (!editor.effectiveEntries.length) return { word: "Not assigned", tone: "brass" };
  if (editor.effectiveEntries.some((entry) => entry.readiness !== "ready")) return { word: "Not ready", tone: "coral" };
  return { word: "Assigned", tone: "moss" };
}

export function EnginesSection() {
  const ctrl = useRunsOn();
  const [picked, pick] = useState<string | null>(null);
  const [library, showLibrary] = useState(false);
  const rosterIn = Boolean(ctrl.roster);
  const engineSet = ctrl.engines.map((e) => `${e.key}:${e.profileRevision}`).join("|");
  useEffect(() => { if (rosterIn) ctrl.what.reload(); }, [rosterIn, engineSet]); // controller owns refresh after a write
  const { editors } = ctrl.what;
  const speech = editors.speech;
  const speechIds = new Set(speech && speech !== "failed" ? speech.candidates.map((c) => c.profileId) : []);
  const rowHealth = (id: string): Health => {
    const editor = editors[id];
    const base = health(editor);
    if (editor && editor !== "failed" && editor.effectiveEntries.some((entry) => {
      const engine = ctrl.engines.find((e) => e.profileId === entry.profile_id);
      return engine && stateWord(engine.state) === "BROKEN";
    })) return { word: "Not answering", tone: "coral" };
    return base;
  };
  const nameOf = (id: string, label: string) => ctrl.engines.find((engine) => engine.profileId === id)?.name || label;
  const chainWords = (editor: RowEditor) => editor.effectiveEntries.map((e) => nameOf(e.profile_id, e.label)).join(", then ");
  const rowWords = (id: string) => {
    const row = WHAT_ROWS.find((r) => r.id === id)!;
    const editor = editors[id];
    return editor && editor !== "failed" && editor.effectiveEntries.length
      ? `${row.name} ${["default", "thread", "memory", "dictation", "speech"].includes(row.id) ? "runs" : "run"} on ${chainWords(editor)}` : row.name;
  };
  const problem = WHAT_ROWS.find((row) => rowHealth(row.id).tone === "coral")
    ?? WHAT_ROWS.find((row) => rowHealth(row.id).tone === "brass");
  const defaultEditor = editors[EVERYTHING_ELSE];
  const facts = defaultEditor && defaultEditor !== "failed" && defaultEditor.effectiveEntries.length
    ? chainWords(defaultEditor) : "What HoldSpeak does, wired to what you have";
  const selected = WHAT_ROWS.find((row) => row.id === picked);
  const editor = picked ? editors[picked] : undefined;
  const reload = () => { ctrl.readAgain(); ctrl.what.reload(); };
  return <>
    <SectionMast id="engines" label="Engines" sprite="models" facts={facts}>
      <Button variant="ghost" disabled={ctrl.busy} onClick={reload}>Check again</Button>
      <Button variant="secondary" aria-pressed={library} data-testid="settings-engines-library-open"
        onClick={() => showLibrary(!library)}>{library ? "Assignments" : "Model library"}</Button>
    </SectionMast>
    <Spine data-testid="settings-engines-spine" segments={WHAT_ROWS.map((row) => ({ tone: rowHealth(row.id).tone, share: 1 }))} />
    {ctrl.error ? <SettingsPlate tone="coral" title="Engines not read" testId="settings-engines-plate"
      verbs={<Button onClick={reload}>Retry</Button>} /> : null}
    {!library && !ctrl.error && problem ? <SettingsPlate tone={rowHealth(problem.id).tone === "coral" ? "coral" : "brass"}
      title={problem.name} facts={rowHealth(problem.id).word} testId="settings-engines-plate"
      verbs={<Button variant="brass" onClick={() => pick(problem.id)}>Set up</Button>} /> : null}
    {!ctrl.roster && !ctrl.error ? <span role="status">Reading engines…</span> : null}
    {ctrl.receipt ? <span className="settings-receipt" role={ctrl.receipt.tone === "danger" ? "alert" : "status"}
      data-tone={ctrl.receipt.tone} data-testid="settings-engines-receipt">{ctrl.receipt.text}</span> : null}
    {ctrl.canUndo ? <div className="engines-verbs"><Button disabled={ctrl.busy} onClick={() => void ctrl.undo()}>Undo</Button></div> : null}
    {library ? <EngineLibrary ctrl={ctrl} /> : <>
      {selected ? <section className="engines-editor" data-testid="settings-engines-editor" aria-label={`${selected.name} engines`}>
        <div className="engines-editor-head"><h3>{selected.name}</h3><Button variant="ghost" onClick={() => pick(null)}>Close editor</Button></div>
        {!editor || editor === "failed" ? <><span>{health(editor).word}</span><Button onClick={reload}>Retry</Button></> : <>
          <span>{rowWords(selected.id)}</span>
          <ol className="engines-chain">{editor.effectiveEntries.map((entry, index, chain) => {
            const ids = chain.map((e) => e.profile_id);
            return <li key={entry.profile_id}><strong>{nameOf(entry.profile_id, entry.label)}</strong><div className="engines-verbs">
              <Button dense disabled={ctrl.busy || index === 0} aria-label={`Move ${entry.label} up`}
                onClick={() => { [ids[index - 1], ids[index]] = [ids[index], ids[index - 1]]; void ctrl.what.set(selected.id, ids); }}>Move up</Button>
              <Button dense disabled={ctrl.busy || index === chain.length - 1} aria-label={`Move ${entry.label} down`}
                onClick={() => { [ids[index], ids[index + 1]] = [ids[index + 1], ids[index]]; void ctrl.what.set(selected.id, ids); }}>Move down</Button>
              <Button dense disabled={ctrl.busy} aria-label={`Remove ${entry.label}`}
                onClick={() => void ctrl.what.set(selected.id, ids.filter((id) => id !== entry.profile_id))}>Remove</Button>
            </div></li>;
          })}</ol>
          {!editor.own && editor.effectiveEntries.length ? <span>Follows the default order</span> : null}
          {selected.id !== EVERYTHING_ELSE && editor.own ? <Button disabled={ctrl.busy}
            onClick={() => void ctrl.what.set(selected.id, null)}>{selected.id === "speech" ? "Clear assignment" : "Use default order"}</Button> : null}
          <div className="engines-verbs" aria-label="Add an engine to the order">
            {editor.candidates.filter((c) => !editor.effectiveEntries.some((e) => e.profile_id === c.profileId) && (selected.id !== EVERYTHING_ELSE || !speechIds.has(c.profileId))).map((c) =>
              <Button key={c.profileId} disabled={ctrl.busy} onClick={() => void ctrl.what.set(selected.id,
                [...editor.effectiveEntries.map((e) => e.profile_id), c.profileId])}>Add {nameOf(c.profileId, c.label)}</Button>)}
            <Button variant="ghost" onClick={() => showLibrary(true)}>Add a model</Button>
          </div>
          {selected.probe && editor.effectiveEntries.length && (selected.id !== EVERYTHING_ELSE || (editors.answers && editors.answers !== "failed" && editors.answers.effective?.inheritedFrom === "global")) ? <Button disabled={ctrl.busy || Boolean(ctrl.trying)}
            title={`Runs a sample on ${chainWords(editor)}`} onClick={() => void ctrl.what.tryRow(selected.id)}>Try it</Button> : null}
          {ctrl.results[`what:${selected.id}`] ? <div role="status" className="engines-result">
            <span>{ctrl.results[`what:${selected.id}`].tokens.join(" · ")}</span>
            <span>{ctrl.results[`what:${selected.id}`].sampleOutput}</span>
          </div> : null}
        </>}
      </section> : null}
      <SettingsLedger label="What HoldSpeak does">{WHAT_ROWS.map((row) => {
        const state = rowHealth(row.id);
        return <SettingLine key={row.id} label={rowWords(row.id)} testId={`settings-job-${row.id}`}
          value={<><DotWord tone={state.tone === "moss" ? "ok" : state.tone === "coral" ? "fail" : state.tone === "brass" ? "warn" : "info"}>{state.word}</DotWord><Spine tone={state.tone} /></>}
          verb={<Button dense variant="secondary" aria-expanded={picked === row.id} aria-label={`Edit ${row.name}`}
            onClick={() => pick(row.id)}>Edit</Button>} />;
      })}</SettingsLedger>
    </>}
  </>;
}
