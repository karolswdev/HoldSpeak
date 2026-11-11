import { useCallback, useState } from "react";
import { Button } from "../../../components/signal/Signal";
import {
  PreferencePane, PaneGroup, CycleGadget, ListPane, PaneInspector, ListApp, useListApp, InspectorFacts,
  FootSlotContext,
  ReadingDocument,
  StatusBar,
  ToolGlyph,
  Toolbar,
  countWords,
  type ObjectListRow,
  type ObjectListSort,
} from "../../../desk/surface";
import { ListView } from "../../../desk/surface/objects/ListView";
import { DecisionComposer } from "../../../desk/decisions/Composer";

export type WindowPreset = "populated" | "empty" | "busy" | "failed" | "reader" | "inspector" | "decision-new" | "decision-filled";

/** Fixture rows only: the same Toolbar, dense ObjectList and StatusBar the
 * Meetings and Projects windows compose, fed by a local adapter. No hub
 * read, no engine, no egress. */
const FIXTURE: ObjectListRow[] = [
  { id: "w-1", kind: "meeting", name: "Ledger cutover sync", when: "Oct 24", whenSort: 4, cells: { length: "30 min" }, sortValues: { length: 30 }, state: { label: "Summary stored", tone: "ok" } },
  { id: "w-2", kind: "meeting", name: "Vendor sync", when: "Oct 24", whenSort: 3, cells: { length: "25 min" }, sortValues: { length: 25 }, state: { label: "Failed", tone: "fail" } },
  { id: "w-3", kind: "meeting", name: "Architecture review: tracing", when: "Oct 23", whenSort: 2, cells: { length: "45 min" }, sortValues: { length: 45 }, state: { label: "2 to review", tone: "ask" } },
  { id: "w-4", kind: "meeting", name: "1:1 Avery", when: "Oct 22", whenSort: 1, cells: { length: "30 min" }, sortValues: { length: 30 }, state: { label: "Summary stored", tone: "ok" } },
];

/** An avatar-led list (People's roster): the 24 px initials disc in the
 * person's hue leads each row; an idle state is the plain grey dot. */
const PEOPLE: ObjectListRow[] = [
  { id: "p-1", kind: "person", name: "Avery Chen", avatar: { initials: "AC", hue: 1 }, cells: { role: "Direct report", next: "1:1 Today 16:00" }, state: { label: "Prep ready", tone: "ok" } },
  { id: "p-2", kind: "person", name: "Priya Nair", avatar: { initials: "PN", hue: 3 }, cells: { role: "Peer", next: "" }, state: { label: "Waiting on you", tone: "ask" } },
  { id: "p-3", kind: "person", name: "Sam Rivera", avatar: { initials: "SR", hue: 2 }, cells: { role: "", next: "1:1 Fri 10:30" }, state: { label: "Quiet", tone: "idle" } },
];

const PEOPLE_COLUMNS = [
  { key: "role", word: "Role", priority: 20, track: "minmax(110px, 0.6fr)" },
  { key: "next", word: "Next 1:1", priority: 30, track: "minmax(0, 0.8fr)" },
  { key: "state", word: "State", priority: 30, track: "minmax(120px, 0.6fr)" },
] as const;

const readPeople = async () => ({rows:PEOPLE});
function PeopleSpecimen() {
  const app = useListApp({initialPicked:"p-1",initialPage:{rows:PEOPLE},read:readPeople,keyOf:row => row.id,search:(row,query) => row.name.toLowerCase().includes(query)});
  const [opened, setOpened] = useState("");
  return <div className="reference-window-frame reference-window-people" data-testid="reference-window-people">
    <ListApp app={app} label="Specimen people" ids={{windowTestId:"specimen-people",listTestId:"specimen-people-list",paneTestId:"specimen-person",toolbarTestId:"specimen-people-toolbar",statusTestId:"specimen-people-status"}}
      words={{find:"Find a person",empty:"No people",noMatch:"No people match",select:"Select a person"}} row={row => row}
      list={{columns:[{key:"name",word:"Name",priority:100},...PEOPLE_COLUMNS],defaultVerb:"open",
        verbs:[{id:"open",label:"Open",key:"Enter",enabled:row => Boolean(row),run:row => setOpened(row!.name)}]}}
      pane={row => opened ? `Opened locally · ${opened}` : row?.name ?? null} />
  </div>;
}

/** A meeting summary, read in its window: the one place a document
 *  heading is allowed. Fixture words only. */
const READER_SUMMARY = `Dual-write is stable. The team agreed to freeze the old ledger on Nov 5.

- Jordan owns the rollback plan.
- Mira reviews the cutover checklist by Thursday.

The vendor sync moves to next week.`;

/** Window grammar ▸ Reader: toolbar → a compact head → the summary as a
 *  ReadingDocument → the status bar with its state. No egress chip on a
 *  working window (owner ruling 2026-10-25); the Engines specimen below is
 *  where the address shows. Local presses only; no hub read, no engine. */
function ReaderWindow() {
  const [opened, setOpened] = useState<string | null>(null);
  return (
    <section className="reference-example reference-window" data-testid="reference-window" aria-label="Window pattern">
      <div className="reference-window-frame" data-preset="reader">
        <Toolbar label="Specimen meeting">
          <Button dense variant="primary" onClick={() => setOpened("Send")}>
            <ToolGlyph kind="open" />
            Send…
          </Button>
          <Button dense variant="secondary" onClick={() => setOpened("Export")}>
            <ToolGlyph kind="import" />
            Export
          </Button>
        </Toolbar>
        <div className="reference-window-content reference-window-reader" data-testid="reference-window-reader">
          <div className="reference-reader-head">
            <span className="reference-reader-facts">Oct 24 · 30 min · 2 people</span>
          </div>
          <h2 className="reference-reader-heading">Summary</h2>
          <ReadingDocument className="reference-reader-document">{READER_SUMMARY}</ReadingDocument>
        </div>
        <FootSlotContext.Provider value={null}>
          <StatusBar
            items={[
              { key: "state", lamp: "ok", text: "Summary stored" },
              opened ? { key: "opened", text: <span data-testid="reference-window-opened">Opened locally · {opened}</span> } : null,
            ]}
          />
        </FootSlotContext.Provider>
      </div>
    </section>
  );
}

const COLUMNS = [
  { key: "when", word: "When", priority: 20, track: "88px" },
  { key: "length", word: "Length", priority: 20, track: "80px" },
  { key: "state", word: "Summary", priority: 30, track: "minmax(140px, 0.6fr)" },
] as const;

/** New decision, the Decisions window's composer plate (the native app,
 *  2026-11-08). Empty: Create waits for a title. Filled: a title, a Why and
 *  the Project in front. Local presses only; nothing is written. */
function NewDecisionWindow({ filled }: { filled: boolean }) {
  const [title, setTitle] = useState(filled ? "Keep the ledger on SQLite" : "");
  const [why, setWhy] = useState(filled ? "One writer, one file. Postgres waits until we need a second host." : "");
  const [pressed, setPressed] = useState<string | null>(null);
  return (
    <section className="reference-example reference-window" data-testid="reference-window" aria-label="Window pattern">
      <div className="reference-window-frame reference-window-new-decision" data-preset={filled ? "decision-filled" : "decision-new"}>
        <DecisionComposer
          title={title}
          why={why}
          about={filled ? { id: "specimen-project", name: "Payments ledger cutover" } : null}
          onTitle={setTitle}
          onWhy={setWhy}
          onCreate={() => setPressed("Create")}
          onCancel={() => setPressed("Cancel")}
        />
        {pressed ? <span className="reference-window-pressed" data-testid="reference-window-opened">Pressed locally · {pressed}</span> : null}
      </div>
    </section>
  );
}

export function WindowReference({ preset }: { preset: WindowPreset }) {
  if (preset === "decision-new") return <NewDecisionWindow filled={false} />;
  if (preset === "decision-filled") return <NewDecisionWindow filled />;
  if (preset === "reader") return <ReaderWindow />;
  if (preset === "inspector") return <InspectorWindow />;
  return <ListWindow preset={preset} />;
}

/* The two-lists shape (Engines grammar, 2026-10-30, canvas direction B):
 * the jobs beside the engines; a row names its partner and a selection
 * lights its partners in the other list; an engine opens its facts in
 * place. Fixture engines and jobs only; a choice changes this specimen and
 * nothing else. */
const SPEC_ENGINES = [
  { id: "e-1", name: "qwen3.8 27B", where: "Your network", state: { word: "Ready", tone: "ok" as const }, address: "http://studio.local:8080/v1" },
  { id: "e-2", name: "Claude Code", where: "Agent on this Mac · Anthropic", state: { word: "Ready", tone: "ok" as const }, address: "" },
  { id: "e-3", name: "whisper-base-mlx", where: "This Mac", state: { word: "Downloading 43 %", tone: "info" as const, live: true }, address: "", progress: 43 },
];
const SPEC_JOBS = ["Everything else", "Meeting summaries", "Answers (Ask)", "Automations"];

function InspectorWindow() {
  const [selected, setSelected] = useState<string | null>(null);
  const [did, setDid] = useState<string | null>(null);
  const [runs, setRuns] = useState<Record<string, string>>({ "Everything else": "e-1", "Meeting summaries": "e-1", "Answers (Ask)": "e-2" });
  return <section className="reference-example reference-window" data-testid="reference-window" aria-label="Window pattern">
    <div className="reference-window-frame" data-preset="inspector">
      <div className="reference-window-content">
        <PreferencePane label="Specimen preferences">
          <PaneGroup label="Each job runs on"><ListView label="Specimen jobs" ordered rows={SPEC_JOBS.map((name) => ({ id: name, kind: "job", name, cells: {
            engine: <CycleGadget label={`${name} engine`} value={runs[name] ?? ""} options={[{ value: "", label: "Same as Everything" }, ...SPEC_ENGINES.map((engine) => ({ value: engine.id, label: engine.name }))]} onChange={(id) => setRuns((now) => ({ ...now, [name]: id }))} />,
          } }))} columns={[{ key: "name", word: "Job", priority: 100, track: "minmax(0, 1fr)" }, { key: "engine", word: "Engine", priority: 30, track: "minmax(0, 1fr)" }]} /></PaneGroup>
          <PaneGroup label="Engines on this desk"><ListPane label="Engine facts" list={<ListView label="Specimen engines" rows={SPEC_ENGINES.map((engine) => ({ id: engine.id, kind: "engine", name: engine.name,
            cells: { where: engine.where }, state: { label: engine.state.word, tone: engine.state.tone },
          }))} columns={[{ key: "name", word: "Engine", priority: 100 }, { key: "where", word: "Where", priority: 20, track: "minmax(0, 1fr)" }, { key: "state", word: "State", priority: 30, track: "150px" }]}
            selectedId={selected} onSelect={setSelected} defaultVerb="open" verbs={[
              { id: "add", label: "Model library", symbol: "+", run: () => setDid("Model library") },
              { id: "open", label: "Open", key: "Enter", enabled: (row) => Boolean(row), run: (row) => setDid(row?.name ?? null) },
            ]} />} >{did && SPEC_ENGINES.some((engine) => engine.name === did) ? <PaneInspector label={did} onClose={() => setDid(null)} rows={[
              { label: "Where", control: SPEC_ENGINES.find((engine) => engine.name === did)?.where },
              { label: "State", control: SPEC_ENGINES.find((engine) => engine.name === did)?.state.word },
            ]} /> : null}</ListPane></PaneGroup>
        </PreferencePane>
      </div>
      <FootSlotContext.Provider value={null}><StatusBar items={did ? [{ text: <span data-testid="reference-window-opened">Opened locally · {did}</span> }] : []} /></FootSlotContext.Provider>
    </div>
  </section>;
}

function ListWindow({ preset }: { preset: Exclude<WindowPreset, "reader" | "inspector" | "decision-new" | "decision-filled"> }) {
  const [opened, setOpened] = useState<string | null>(null);
  const [sort, setSort] = useState<ObjectListSort>({ key: "when", dir: "desc" });
  const read = useCallback(async () => {
    if (preset === "busy") return new Promise<{rows:ObjectListRow[]}>(() => undefined);
    if (preset === "failed") throw new Error("Meetings not read");
    return {rows:preset === "populated" ? FIXTURE : []};
  }, [preset]);
  const app = useListApp({initialPicked:preset === "populated" ? "w-2" : null,initialPage:{rows:preset === "populated" ? FIXTURE : []},read,keyOf:row => row.id,search:(row,query) => row.name.toLowerCase().includes(query)});
  return <section className="reference-example reference-window" data-testid="reference-window" aria-label="Window pattern">
    <div className="reference-window-frame" data-preset={preset}>
      <FootSlotContext.Provider value={null}><ListApp app={app} label="Specimen meetings"
        ids={{windowTestId:"specimen-list-app",listTestId:"specimen-list",paneTestId:"specimen-preview",toolbarTestId:"specimen-toolbar",statusTestId:"specimen-status"}}
        words={{find:"Search specimen meetings",empty:"Select a meeting to read its summary.",noMatch:"No meetings match",select:"Select a meeting to read its summary."}}
        row={row => row} list={{columns:COLUMNS,ordered:false,sort,onSort:(key:string) => setSort(current => ({key,dir:current.key === key && current.dir === "desc" ? "asc" : "desc"})),defaultVerb:"open",verbs:[
          {id:"record",label:"Record",run:() => setOpened("record")},
          {id:"import",label:"Import",run:() => setOpened("import")},
          {id:"open",label:"Open",key:"Enter",enabled:row => Boolean(row),run:row => setOpened(row?.name ?? null)},
        ]}} pane={row => row ? <InspectorFacts name={row.name} rows={[{label:"Summary",value:READER_SUMMARY}]} /> : null}
        status={[{text:countWords(app.rows.length,"meeting")},{lamp:"ask",text:app.rows.some(row => row.state?.tone === "ask") ? "2 to review" : null},{lamp:"fail",text:countWords(app.rows.filter(row => row.state?.tone === "fail").length,"failed","failed")},opened ? {text:<span data-testid="reference-window-opened">Opened locally · {opened}</span>} : null]} /></FootSlotContext.Provider>
    </div>
    {preset === "populated" ? <PeopleSpecimen /> : null}
  </section>;
}
