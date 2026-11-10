import { ListView, StringGadget, type ListVerb } from "../surface";

export type RailPerson = { id: string; name: string; role: string; next: string; youOwe: number; owesYou: number };
export type RailSuggestion = { key: string; name: string; source: string };

export function PeopleRail({ people, suggestions, picked, query, onQuery, onPick, verbs }: {
  people: RailPerson[]; suggestions: RailSuggestion[]; picked: string | null;
  query: string; onQuery(next: string): void; onPick(id: string): void; verbs: ListVerb[];
}) {
  return <ListView label="People" rows={[
    ...people.map((row) => ({ id: row.id, kind: "person", name: row.name, nameTestId: "people-row-name", cells: {
      relationship: row.role, next: row.next, open: [row.youOwe ? `${row.youOwe} you owe` : "", row.owesYou ? `${row.owesYou} owed to you` : ""].filter(Boolean).join(" · "),
    } })),
    ...suggestions.map((row) => ({ id: `suggestion:${row.key}`, kind: "suggestion", name: row.name, cells: { relationship: "From meetings", next: "", open: "" } })),
  ]} columns={[
    { key: "name", word: "Name", priority: 100, track: "minmax(0, 1.2fr)" },
    { key: "relationship", word: "Relationship", priority: 10, track: "minmax(0, 1fr)" },
    { key: "next", word: "Next 1:1", priority: 30, track: "minmax(0, 1fr)" },
    { key: "open", word: "Open with them", priority: 20, track: "minmax(0, 1.4fr)" },
  ]} selectedId={picked} onSelect={onPick} verbs={verbs} defaultVerb="open"
    toolbar={{ trailing: <StringGadget label="Find a person" value={query} onChange={onQuery} placeholder="Find a person" /> }}
    rowProps={(row) => ({ "data-testid": row.kind === "suggestion" ? "people-suggestion" : "people-row", "data-person": row.id })} />;
}
