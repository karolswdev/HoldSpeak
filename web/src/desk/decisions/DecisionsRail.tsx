import { ListView, StringGadget, type ListVerb } from "../surface";

export type RailDecision = { key: string; title: string; day: string; state: string };

/** The collection's only list. The kit owns selection, keys and all menus. */
export function DecisionsRail({ rows, picked, query, onQuery, current, onCurrent, onPick, verbs }: {
  rows: RailDecision[]; picked: string | null; query: string; onQuery(next: string): void;
  current: boolean; onCurrent(next: boolean): void; onPick(key: string): void; verbs: ListVerb[];
}) {
  return <ListView label="Decisions" rows={rows.map((row) => ({
    id: row.key, kind: "decision", name: row.title, when: row.day,
    cells: { project: "" },
    state: row.state ? { label: row.state, tone: row.state === "Disputed" ? "fail" as const : row.state === "Proposed" ? "ask" as const : "idle" as const } : undefined,
  }))} columns={[
    { key: "name", word: "Decision", priority: 100, track: "minmax(0, 3fr)", minWidth: 200 },
    { key: "project", word: "Project", priority: 10, track: "minmax(0, 1fr)" },
    { key: "when", word: "Decided", priority: 20, track: "112px" },
    { key: "state", word: "State", priority: 30, track: "112px" },
  ]} selectedId={picked} onSelect={onPick} verbs={verbs} defaultVerb="open" ordered
    toolbar={{ testId: "decisions-toolbar", scopes: [{id:"current",kind:"tick",label:"Current only",checked:current,onChange:onCurrent}], trailing: <StringGadget label="Find a decision" type="search" value={query} onChange={onQuery} placeholder="Find" /> }}
    rowProps={() => ({ "data-testid": "decisions-row", "data-kind": "decision" })} />;
}
