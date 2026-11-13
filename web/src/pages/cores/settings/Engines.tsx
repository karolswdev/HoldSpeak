// The hub owns all chains. Choices write only on an owner press.
import { useCallback, useEffect, useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { PreferencePane, ListPane, PaneGroup, PaneInspector, InspectorForm, InspectorQuestion, GadgetRow, PaneActions, SegmentedTabs, ListView, CycleGadget, type ListVerb } from "../../../desk/surface";
import { wireDayClock } from "../../../desk/surface/format";
import { stateWord } from "../../../features/runson/stateWord";
import { EngineLibrary } from "../../../features/runson/EngineLibrary";
import { conciergeProbe } from "../../../features/concierge/api";
import { useRunsOn } from "../../../features/runson/useRunsOn";
import { EVERYTHING_ELSE, WHAT_ROWS } from "../../../features/runson/whatRows";
import type { RowEditor } from "../../../features/runson/api";

export function EnginesSection({ onCount, onStatus, onBackChange, lastRead, onRead }: { onCount?: (count: number) => void; onStatus?: (words: string) => void; lastRead?: Date | null; onRead?: (at: Date) => void; onBackChange?: (back: (() => void) | null) => void } = {}) {
  const ctrl = useRunsOn();
  const [library, showLibrary] = useState(false);
  const closeLibrary = useCallback(() => showLibrary(false), []);
  useEffect(() => { if (ctrl.lastRead) onRead?.(ctrl.lastRead); }, [ctrl.lastRead, onRead]);
  const readAt = ctrl.lastRead ?? lastRead;
  const readStatus = ctrl.error ? `Engines not read · ${readAt ? `Last read ${wireDayClock(readAt)}` : "Not read yet"}` : "";
  useEffect(() => { onStatus?.(readStatus); return () => onStatus?.(""); }, [readStatus, onStatus]);
  const [tab, setTab] = useState("jobs");
  const [picked, pick] = useState<string | null>(null);
  const [editing, edit] = useState<string | null>(null);
  const [jobPicked, pickJob] = useState<string | null>(null);
  const [chainPicked, pickChain] = useState<string | null>(null);
  const [test, setTest] = useState("");
  const [testing, setTesting] = useState(false);
  const [removing, setRemoving] = useState<string | null>(null);
  const rosterIn = Boolean(ctrl.roster);
  const engineSet = ctrl.engines.map((e) => `${e.key}:${e.profileRevision}`).join("|");
  useEffect(() => { if (rosterIn) ctrl.what.reload(); }, [rosterIn, engineSet]);
  const name = (id: string, label: string) => ctrl.engines.find((engine) => engine.profileId === id)?.name || label;
  const words = (editor: RowEditor) => editor.effectiveEntries.map((entry) => name(entry.profile_id, entry.label)).join(", then ");
  const reload = () => { ctrl.readAgain(); ctrl.what.reload(); };
  const job = WHAT_ROWS.find((row) => row.id === editing);
  const editor = editing ? ctrl.what.editors[editing] : undefined;
  const chain = editor && editor !== "failed" ? editor.effectiveEntries : [];
  const chainRevision = JSON.stringify([editing, editor && editor !== "failed" ? editor.baseRevision : null, chain]);
  useEffect(() => setRemoving(null), [chainRevision, chainPicked]);
  const candidates = editor && editor !== "failed" ? editor.candidates.filter(candidate => !chain.some(entry => entry.profile_id === candidate.profileId)) : [];
  const chainVerbs: ListVerb[] = [
    { id: "add", label: "Add engine", symbol: "+", run: () => {}, enabled: () => !ctrl.busy && candidates.length > 0, items: candidates.map((candidate) => ({
      id: candidate.profileId, label: name(candidate.profileId, candidate.label), enabled: () => !ctrl.busy, run: () => { if (editing) void ctrl.what.set(editing, [...chain.map((entry) => entry.profile_id), candidate.profileId]); },
    })) },
    { id: "remove", label: "Remove from order", symbol: "−", key: "Delete", enabled: (row) => Boolean(row) && !ctrl.busy, run: (row) => setRemoving(row!.id) },
    ...(["up", "down"] as const).map((direction): ListVerb => ({ id: direction, label: direction === "up" ? "Move up" : "Move down", enabled: (row) => {
      const at = chain.findIndex((entry) => entry.profile_id === row?.id);
      return !ctrl.busy && at >= 0 && (direction === "up" ? at > 0 : at < chain.length - 1);
    }, run: (row) => { const ids = chain.map((entry) => entry.profile_id); const at = ids.indexOf(row!.id); const next = at + (direction === "up" ? -1 : 1); [ids[at], ids[next]] = [ids[next], ids[at]]; if (editing) void ctrl.what.set(editing, ids); } })),
  ];
  const installed = ctrl.engines.filter((engine) => engine.profileId && !engine.found && engine.kind !== "preset");
  useEffect(() => { onCount?.(rosterIn && !ctrl.error && !library ? installed.length : 0); }, [rosterIn, ctrl.error, installed.length, library, onCount]);
  const engineVerbs: ListVerb[] = [
    { enabled: () => true, id: "add", label: "Model library", symbol: "+", run: () => showLibrary(true) },
    { id: "test", label: "Test", enabled: (row) => Boolean(row) && !testing && Boolean(installed.find((engine) => engine.key === row?.id)?.detectId), run: (row) => {
      const engine = installed.find((engine) => engine.key === row?.id); if (!engine?.detectId || testing) return;
      setTesting(true); setTest("Testing…");
      void conciergeProbe(engine.detectId).then((answer) => setTest(`${engine.name} · ${answer.plainReason || (answer.state === "READY" ? "Ready" : "Not ready")}`))
        .catch(() => setTest(`${engine.name} · Test failed`)).finally(() => setTesting(false));
    } },
    { id: "open", label: "Open", key: "Enter", enabled: (row) => Boolean(row), run: () => showLibrary(true) },
  ];
  return <PreferencePane label="Engines" testId="settings-engines">
    {ctrl.error ? <PaneActions><span role="alert">Engines not read</span><Button onClick={reload}>Retry</Button></PaneActions> : null}
    {ctrl.receipt ? <PaneActions><span role={ctrl.receipt.tone === "danger" ? "alert" : "status"} data-testid="settings-engines-receipt">{ctrl.receipt.text}</span>{ctrl.canUndo ? <Button dense disabled={ctrl.busy} onClick={() => void ctrl.undo()}>Undo</Button> : null}</PaneActions> : null}
    <SegmentedTabs label="Engines" value={tab} onChange={next => { setTab(next); showLibrary(false); ctrl.add.close(); }} tabs={[{ id: "jobs", label: "Jobs" }, { id: "engines", label: "Engines" }]}>
    {library ? <EngineLibrary ctrl={ctrl} onClose={closeLibrary} onBackChange={onBackChange} /> : <ListPane label="Engine inspector" list={<>

      <div className="surface-tab-panel" hidden={tab !== "jobs"} data-testid="settings-jobs">
      <PaneGroup label="Each job runs on">
        <ListView label="Jobs" ordered rows={WHAT_ROWS.map((row) => {
          const value = ctrl.what.editors[row.id];
          const current = value && value !== "failed" ? JSON.stringify(value.effectiveEntries.map((entry) => entry.profile_id)) : "";
          const inherited = value && value !== "failed" && !value.own && row.id !== EVERYTHING_ELSE;
          const ownValue = inherited ? "inherit" : current;
          return { id: row.id, kind: "job", name: row.id === EVERYTHING_ELSE ? "Everything" : row.name, cells: {
            chain: <CycleGadget roster label={`${row.name} engines`} value={ownValue}
              disabled={!value || value === "failed" || ctrl.busy}
              options={value && value !== "failed" ? [
                ...(row.id !== EVERYTHING_ELSE ? [{ value: "inherit", label: "Same as Everything" }] : []),
                { value: current, label: words(value) || "No engine" },
                ...value.candidates.filter((candidate) => JSON.stringify([candidate.profileId]) !== current).map((candidate) => ({ value: JSON.stringify([candidate.profileId]), label: name(candidate.profileId, candidate.label) })),
                { value: "order", label: "Set order…" },
              ] : [{ value: "", label: value === "failed" ? "Not read" : "Reading…" }]}
              onChange={(next) => { pickJob(row.id); if (next === "order") { edit(row.id); pickChain(null); } else if (next !== ownValue) void ctrl.what.set(row.id, next === "inherit" ? null : JSON.parse(next)); }} />,
          } };
        })} columns={[{ key: "name", word: "Job", priority: 100, track: "minmax(0, 1fr)" }, { key: "chain", word: "Engines, in order", priority: 30, track: "minmax(0, 1.4fr)" }]}
          selectedId={jobPicked} onSelect={pickJob} rowProps={(row) => ({ "data-testid": `settings-job-${row.id}` })} />
      </PaneGroup>
      </div>
      <div className="surface-tab-panel" hidden={tab !== "engines"}>
      <PaneGroup label="Engines on this desk">
        <ListView label="Engines on this desk" ordered rows={installed.map((engine) => ({ id: engine.key, kind: "engine", name: engine.name,
          cells: { where: engine.kind === "agent" || engine.kind === "local" ? "This Mac" : engine.host },
          state: stateWord(engine.state) === "READY" ? undefined : { label: stateWord(engine.state) === "BROKEN" ? "Not answering" : "Not ready", tone: "warn" as const },
        }))} columns={[{ key: "name", word: "Engine", priority: 100, track: "minmax(0, 1.5fr)" }, { key: "where", word: "Where", priority: 20, track: "minmax(0, 1fr)" }, { key: "state", word: "State", priority: 30, track: "130px" }]}
          selectedId={picked} onSelect={pick} verbs={engineVerbs} defaultVerb="open" />
      </PaneGroup>
      {test ? <output>{test}</output> : null}
      </div>
    </>}>

    {removing && job && editor && editor !== "failed" ? <InspectorQuestion actionId="remove-engine-order" targetId={`${chainRevision}:${removing}`} question={`Remove ${name(removing, "engine")} from ${job.name}?`} keeps={["The engine"]} cancel={() => setRemoving(null)}
      verb={{label:"Remove", busy:ctrl.busy, run:() => { void ctrl.what.set(job.id, chain.filter(entry => entry.profile_id !== removing).map(entry => entry.profile_id)); }}} />
    : job && editor && editor !== "failed" ? <PaneInspector label={`${job.name}: engine order`} onClose={() => edit(null)}>
      <InspectorForm><GadgetRow label="Order"><ListView label="Engine order" headerless ordered rows={chain.map((entry) => ({ id: entry.profile_id, kind: "engine", name: name(entry.profile_id, entry.label) }))} columns={[{ key: "name", word: "Engine, in order", priority: 100 }]}
        selectedId={chainPicked} onSelect={pickChain} verbs={chainVerbs} /></GadgetRow>
      <GadgetRow label="Check"><PaneActions>{job.probe ? <Button dense disabled={ctrl.busy || Boolean(ctrl.trying) || !chain.length} title={`Runs a sample on ${words(editor)}`} onClick={() => void ctrl.what.tryRow(job.id)}>Try it</Button> : null}
        {job.id !== EVERYTHING_ELSE && editor.own ? <Button dense disabled={ctrl.busy} onClick={() => void ctrl.what.set(job.id, null)}>Same as Everything</Button> : null}</PaneActions></GadgetRow>
      {ctrl.results[`what:${job.id}`] ? <GadgetRow label="Result"><output>{ctrl.results[`what:${job.id}`].tokens.join(" · ")} {ctrl.results[`what:${job.id}`].sampleOutput}</output></GadgetRow> : null}</InspectorForm>
    </PaneInspector> : null}
    </ListPane>}
    </SegmentedTabs>
  </PreferencePane>;
}
