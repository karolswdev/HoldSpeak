import type { ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import { Rail, StringGadget } from "../surface";

export type RailPerson = { id: string; name: string; role: string; next: string; youOwe: number; owesYou: number; overdue: number; done: number };
export type RailSuggestion = { key: string; name: string; source: string };

export function PeopleRail({ people, suggestions, picked, query, onQuery, onPick, onAdd, onBack, adding, head, searchable }: {
  people: RailPerson[]; suggestions: RailSuggestion[]; picked: string | null;
  query: string; onQuery(next: string): void; onPick(id: string): void; onAdd(): void; onBack(): void;
  adding: boolean; head?: ReactNode; searchable: boolean;
}) {
  return <Rail label="People" data-testid="people-rail" picked={picked} onPick={onPick} onBack={onBack}
    paneOpen={Boolean(picked)}
    head={<>
      <Button dense variant="primary" aria-expanded={adding} onClick={onAdd} data-testid="people-add">Add person</Button>
      {searchable ? <StringGadget label="Search people" value={query} onChange={onQuery} placeholder="Search people" /> : null}
      {head}
    </>}
    groups={[
      { id: "people", items: people.map((row) => ({
        id: row.id, label: <span data-testid="people-row-name">{row.name}</span>,
        rowData: { "data-testid": "people-row", "data-person": row.id, "data-next-one-on-one": row.next ? "" : undefined },
        facts: <>{row.role}{row.next ? <> · <span data-testid="people-row-next">{row.next}</span></> : null}</>,
        spine: row.owesYou + row.youOwe + row.overdue + row.done ? {
          label: [row.owesYou ? `${row.owesYou} owed to you` : "", row.youOwe ? `${row.youOwe} you owe` : "",
            row.overdue ? `${row.overdue} overdue` : "", row.done ? `${row.done} done` : ""].filter(Boolean).join(", "),
          segments: [{ tone: "brass", share: row.owesYou }, { tone: "steel", share: row.youOwe }, { tone: "coral", share: row.overdue }, { tone: "moss", share: row.done }],
        } : undefined,
      })) },
      { id: "suggestions", label: "From your meetings", items: suggestions.map((row) => ({
        id: `suggestion:${row.key}`, label: row.name, facts: row.source,
        rowData: { "data-testid": "people-suggestion", "data-suggested": "" },
      })) },
    ]} />;
}
