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

export type WindowPreset = "populated" | "empty" | "busy" | "failed" | "reader";

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
 *  ReadingDocument → the status bar with its state and the egress chip of
 *  the engine that ran it. Local presses only; no hub read, no engine. */
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
            egress={<EgressChip label="studio.local · LAN" scope="local" title="Where the specimen summary ran." />}
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

export function WindowReference({ preset }: { preset: WindowPreset }) {
  if (preset === "reader") return <ReaderWindow />;
  return <ListWindow preset={preset} />;
}

function ListWindow({ preset }: { preset: Exclude<WindowPreset, "reader"> }) {
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
