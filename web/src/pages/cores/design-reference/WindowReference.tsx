import { useState } from "react";
import { Button } from "../../../components/signal/Signal";
import {
  FootSlotContext,
  ObjectList,
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

export type WindowPreset = "populated" | "empty" | "busy" | "failed";

/** Fixture rows only: the same Toolbar, dense ObjectList and StatusBar the
 * Meetings and Projects windows compose, fed by a local adapter. No hub
 * read, no engine, no egress. */
const FIXTURE: ObjectListRow[] = [
  { id: "w-1", kind: "meeting", name: "Ledger cutover sync", when: "Oct 24", whenSort: 4, cells: { length: "30 min" }, sortValues: { length: 30 }, state: { label: "Summary stored", tone: "ok" } },
  { id: "w-2", kind: "meeting", name: "Vendor sync", when: "Oct 24", whenSort: 3, cells: { length: "25 min" }, sortValues: { length: 25 }, state: { label: "Failed", tone: "fail" } },
  { id: "w-3", kind: "meeting", name: "Architecture review: tracing", when: "Oct 23", whenSort: 2, cells: { length: "45 min" }, sortValues: { length: 45 }, state: { label: "2 to review", tone: "ask" } },
  { id: "w-4", kind: "meeting", name: "1:1 Avery", when: "Oct 22", whenSort: 1, cells: { length: "30 min" }, sortValues: { length: 30 }, state: { label: "Summary stored", tone: "ok" } },
];

const COLUMNS = [
  { key: "when", word: "When", track: "88px" },
  { key: "length", word: "Length", track: "80px" },
  { key: "state", word: "Summary", track: "minmax(140px, 0.6fr)" },
] as const;

export function WindowReference({ preset }: { preset: WindowPreset }) {
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
    </section>
  );
}
