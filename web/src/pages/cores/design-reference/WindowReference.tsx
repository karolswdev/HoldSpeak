import { useState } from "react";
import { Button } from "../../../components/signal/Signal";
import {
  FootSlotContext,
  EgressChip,
  ObjectList,
  ReadingDocument,
  StatusBar,
  StringGadget,
  SurfaceState,
  ToolGlyph,
  Toolbar,
  countWords,
  type ObjectListRow,
  type ObjectListSort,
} from "../../../desk/surface";
import { SYSTEM } from "../../../desk/systemSprites";
import { DotWord } from "../../../desk/surface/kit";
import { spriteUrl } from "../../../desk/sprites";
import { PrefSection } from "../settingsWindow";
import { NewDecisionForm } from "../NewDecisionCore";
// The list + inspector shape is the Engines window's own composition.
import "../../../features/runson/runson.css";

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
  { key: "role", word: "Role", track: "minmax(110px, 0.6fr)" },
  { key: "next", word: "Next 1:1", track: "minmax(0, 0.8fr)" },
  { key: "state", word: "State", track: "minmax(120px, 0.6fr)" },
] as const;

function PeopleSpecimen() {
  const [selected, setSelected] = useState<string | null>("p-1");
  const [sort, setSort] = useState<ObjectListSort>({ key: "name", dir: "asc" });
  return (
    <div className="reference-window-frame reference-window-people" data-testid="reference-window-people">
      <ObjectList
        label="Specimen people"
        density="dense"
        rows={PEOPLE}
        columns={PEOPLE_COLUMNS}
        sort={sort}
        onSort={(key: string) => setSort((current) => ({ key, dir: current.key === key && current.dir === "asc" ? "desc" : "asc" }))}
        selectedId={selected}
        onSelect={setSelected}
      />
    </div>
  );
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
  { key: "when", word: "When", track: "88px" },
  { key: "length", word: "Length", track: "80px" },
  { key: "state", word: "Summary", track: "minmax(140px, 0.6fr)" },
] as const;

/** The New decision window (the owner, 2026-10-25): the decision's picture,
 *  the label/control grid, and Cancel · Create in the status bar. Empty:
 *  Create waits for a title. Filled: a title, a Why and the Project in front.
 *  Local presses only; nothing is written. */
function NewDecisionWindow({ filled }: { filled: boolean }) {
  const [title, setTitle] = useState(filled ? "Keep the ledger on SQLite" : "");
  const [why, setWhy] = useState(filled ? "One writer, one file. Postgres waits until we need a second host." : "");
  const [pressed, setPressed] = useState<string | null>(null);
  return (
    <section className="reference-example reference-window" data-testid="reference-window" aria-label="Window pattern">
      <div className="reference-window-frame reference-window-new-decision" data-preset={filled ? "decision-filled" : "decision-new"}>
        <NewDecisionForm
          title={title}
          why={why}
          about={filled ? { id: "specimen-project", name: "Payments ledger cutover" } : null}
          onTitle={setTitle}
          onWhy={setWhy}
          onCreate={() => setPressed("Create")}
          onCancel={() => setPressed("Cancel")}
          inline
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

/* The list + inspector shape (window grammar, the Engines window): a dense
 * list, and under it the selected object's label/control grid. Fixture
 * engines and jobs only; a choice changes this specimen and nothing else. */
const SPEC_ENGINES = [
  { id: "e-1", name: "qwen3.8 27B", where: { word: "LAN", tone: "idle" as const }, state: { label: "Ready", tone: "ok" as const }, egress: "studio.local · LAN" },
  { id: "e-2", name: "Claude Code", where: { word: "Cloud", tone: "ask" as const }, state: { label: "Ready", tone: "ok" as const }, egress: "Anthropic" },
  { id: "e-3", name: "whisper-base-mlx", where: { word: "This Mac", tone: "ok" as const }, state: { label: "Downloading 43 %", tone: "info" as const }, egress: "" },
];
const SPEC_JOBS = ["Everything else", "Meeting summaries", "Answers (Ask)", "Automations"];
const NOT_SET = "Not assigned";

function InspectorWindow() {
  const [selected, setSelected] = useState("e-1");
  const [did, setDid] = useState<string | null>(null);
  const [sort, setSort] = useState<ObjectListSort>({ key: "order", dir: "asc" });
  const [runs, setRuns] = useState<Record<string, string>>({ "Everything else": "e-1", "Meeting summaries": "e-1", "Answers (Ask)": "e-2" });
  const nameOf = (id: string | undefined) => SPEC_ENGINES.find((engine) => engine.id === id)?.name ?? NOT_SET;
  const rows: ObjectListRow[] = SPEC_ENGINES.map((engine, index) => {
    const used = SPEC_JOBS.filter((job) => runs[job] === engine.id);
    return {
      id: engine.id,
      kind: "model",
      name: engine.name,
      sprite: spriteUrl("model", engine.id, "rest", null, 20),
      state: engine.state,
      cells: {
        where: <DotWord tone={engine.where.tone}>{engine.where.word}</DotWord>,
        used: used.length ? <span className="runson-used">{used.join(", ")}</span> : <DotWord>{NOT_SET}</DotWord>,
      },
      sortValues: { order: index, used: used.join(", ") },
    };
  });
  const pick = SPEC_ENGINES.find((engine) => engine.id === selected) ?? SPEC_ENGINES[0];
  const cycle = (job: string) => {
    const order = [undefined, ...SPEC_ENGINES.map((engine) => engine.id)];
    const next = order[(order.indexOf(runs[job]) + 1) % order.length];
    setRuns((current) => {
      const copy = { ...current };
      if (next) copy[job] = next;
      else delete copy[job];
      return copy;
    });
  };
  return (
    <section className="reference-example reference-window" data-testid="reference-window" aria-label="Window pattern">
      <div className="reference-window-frame runson-root" data-preset="inspector">
        <Toolbar label="Specimen engines">
          <Button dense variant="primary" onClick={() => setDid("Add an engine")}>
            <ToolGlyph kind="new" />
            Add an engine
          </Button>
          <Button dense variant="secondary" onClick={() => setDid("Check all")}>
            <ToolGlyph kind="retry" />
            Check all
          </Button>
        </Toolbar>
        <div className="runson-body">
          <div className="runson-list">
            <ObjectList
              label="Specimen engines"
              density="dense"
              rows={rows}
              columns={[
                { key: "name", word: "Engine" },
                { key: "where", word: "Where", track: "112px" },
                { key: "used", word: "Used for", track: "minmax(0, 1fr)" },
                { key: "state", word: "State", track: "152px" },
              ]}
              sort={sort}
              onSort={(key: string) => setSort((current) => ({ key, dir: current.key === key && current.dir === "asc" ? "desc" : "asc" }))}
              selectedId={selected}
              onSelect={setSelected}
            />
          </div>
          <div className="runson-inspector">
            <PrefSection id="reference-inspector" label="What runs where">
              <ul className="runson-what-list">
                {SPEC_JOBS.map((job) => (
                  <li key={job} className="runson-what-row" data-runs-selected={runs[job] === pick.id ? "" : undefined}>
                    <span className="runson-what-job">{job}</span>
                    <span className="runson-what-engine">
                      <Button dense variant="secondary" className="runson-what-pick" aria-label={`${job}: ${nameOf(runs[job])}`} onClick={() => cycle(job)}>
                        {runs[job] ? <span className="runson-what-name">{nameOf(runs[job])}</span> : <DotWord className="runson-what-name">{NOT_SET}</DotWord>}
                        <span className="runson-what-caret" aria-hidden="true">▾</span>
                      </Button>
                    </span>
                  </li>
                ))}
              </ul>
            </PrefSection>
          </div>
        </div>
        <FootSlotContext.Provider value={null}>
          <StatusBar
            items={[
              { key: "count", lamp: "ok", text: countWords(SPEC_ENGINES.length, "engine") },
              { key: "checked", text: "Checked 23:11" },
              did ? { key: "did", text: <span data-testid="reference-window-opened">Pressed locally · {did}</span> } : null,
            ]}
            verbs={<Button dense variant="secondary" onClick={() => setDid(`Check ${pick.name}`)}><ToolGlyph kind="retry" />Check</Button>}
            egress={pick.egress ? <EgressChip label={pick.egress} scope={pick.where.word === "Cloud" ? "cloud" : "local"} /> : undefined}
          />
        </FootSlotContext.Provider>
      </div>
    </section>
  );
}

function ListWindow({ preset }: { preset: Exclude<WindowPreset, "reader" | "inspector" | "decision-new" | "decision-filled"> }) {
  const [selected, setSelected] = useState<string | null>(preset === "populated" ? "w-2" : null);
  const [opened, setOpened] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState<ObjectListSort>({ key: "when", dir: "desc" });
  const rows = preset === "populated"
    ? FIXTURE.filter((row) => row.name.toLowerCase().includes(query.toLowerCase()))
    : [];
  const failed = rows.filter((row) => row.state?.tone === "fail").length;
  const review = rows.some((row) => row.state?.tone === "ask");
  const selectedRow = rows.find((row) => row.id === selected);
  return (
    <section className="reference-example reference-window" data-testid="reference-window" aria-label="Window pattern">
      <div className="reference-window-frame" data-preset={preset}>
        <Toolbar
          label="Specimen meetings"
          trailing={<StringGadget label="Search specimen meetings" value={query} onChange={setQuery} placeholder="Search meetings" />}
        >
          <Button dense variant={selectedRow?.state?.tone === "fail" ? "secondary" : "primary"} onClick={() => setOpened("record")}>
            <ToolGlyph kind="record" />
            Record meeting
          </Button>
          <Button dense variant="secondary" onClick={() => setOpened("import")}>
            <ToolGlyph kind="import" />
            Import
          </Button>
        </Toolbar>
        <div className="reference-window-content">
          {preset === "busy" ? (
            <SurfaceState loading />
          ) : preset === "failed" ? (
            <SurfaceState error="Meetings not read" onRetry={() => setOpened("retry read")} />
          ) : rows.length ? (
            <ObjectList
              label="Specimen meetings"
              density="dense"
              rows={rows}
              columns={COLUMNS}
              sort={sort}
              onSort={(key: string) => setSort((current) => ({ key, dir: current.key === key && current.dir === "desc" ? "asc" : "desc" }))}
              selectedId={selected}
              onSelect={setSelected}
              onOpen={(id) => setOpened(rows.find((row) => row.id === id)?.name ?? id)}
            />
          ) : (
            <SurfaceState empty emptyImage={SYSTEM.dockMeetings} emptyLabel={preset === "empty" ? "Record or import a meeting" : "No meeting matches"} />
          )}
        </div>
        <FootSlotContext.Provider value={null}>
          <StatusBar
            verbs={selectedRow ? (
              <>
                <Button dense variant="secondary" onClick={() => setOpened(selectedRow.name)}>
                  <ToolGlyph kind="open" />
                  Open
                </Button>
                {selectedRow.state?.tone === "fail" ? (
                  <Button dense variant="primary" onClick={() => setOpened(`retry ${selectedRow.name}`)}>
                    <ToolGlyph kind="retry" />
                    Retry
                  </Button>
                ) : null}
              </>
            ) : null}
            items={[
              { key: "count", text: countWords(rows.length, "meeting") },
              review ? { key: "review", lamp: "ask", text: "2 to review" } : null,
              { key: "failed", lamp: "fail", text: countWords(failed, "failed", "failed") },
              opened ? { key: "opened", text: <span data-testid="reference-window-opened">Opened locally · {opened}</span> } : null,
            ]}
          />
        </FootSlotContext.Provider>
      </div>
      {preset === "populated" ? <PeopleSpecimen /> : null}
    </section>
  );
}
