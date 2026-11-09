/* The rail of people (the native People app, 2026-11-08; the language of
 * Programs and the Room): the left edge of the People window. Add person
 * and the search at the head, then one row per person: the name, the role
 * and the next 1:1 in the person's teal, and a spine of what stands
 * between you (brass: owed to you; steel: you owe). Under them, the names
 * his work carries that People does not hold yet. A press picks the row;
 * the right pane is that person. ↑ and ↓ walk the rows. At 393 the rail
 * is the whole window until a person is picked (people.css). */
import { useRef, type ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import { Spine, StringGadget, useRovingRows } from "../surface";

export type RailPerson = { id: string; name: string; role: string; next: string; youOwe: number; owesYou: number };
export type RailSuggestion = { key: string; name: string; source: string };

function owedWords(row: RailPerson): string {
  return [row.owesYou ? `${row.owesYou} owed to you` : "", row.youOwe ? `${row.youOwe} you owe` : ""].filter(Boolean).join(", ");
}

export function PeopleRail({ people, suggestions, picked, query, onQuery, onPick, onAdd, adding, head, searchable }: {
  people: RailPerson[]; suggestions: RailSuggestion[]; picked: string | null;
  query: string; onQuery(next: string): void; onPick(id: string): void; onAdd(): void;
  /** The add row is open: Add person shows it is pressed. */
  adding: boolean;
  /** The add row, the name row and the scope verb, under the head. */
  head?: ReactNode;
  searchable: boolean;
}) {
  // The library's roving focus: one Tab stop, ↑ and ↓ walk the rows.
  const ref = useRef<HTMLElement | null>(null);
  useRovingRows(ref, { selector: ".people-rail-row" });
  return (
    <nav ref={ref} className="people-rail" aria-label="People" data-testid="people-rail">
      <div className="people-rail-head">
        <Button dense variant="primary" aria-expanded={adding} onClick={onAdd} data-testid="people-add">Add person</Button>
        {searchable ? <StringGadget label="Search people" value={query} onChange={onQuery} placeholder="Search people" /> : null}
      </div>
      {head}
      <ul className="people-rail-list">
        {people.map((row) => {
          const owed = owedWords(row);
          return <li key={row.id} data-testid="people-row" data-person={row.id} data-next-one-on-one={row.next ? "" : undefined}>
            <Button variant="chrome" className="people-rail-row" aria-current={row.id === picked ? "true" : undefined} onClick={() => onPick(row.id)}>
              <span className="people-rail-name" data-testid="people-row-name">{row.name}</span>
              <span className="people-rail-facts">
                <span>{row.role}</span>
                {row.next ? <span className="people-rail-next" data-testid="people-row-next">{row.next}</span> : null}
              </span>
              {owed ? <Spine className="people-rail-spine" label={owed}
                segments={[{ tone: "brass", share: row.owesYou }, { tone: "steel", share: row.youOwe }]} /> : null}
            </Button>
          </li>;
        })}
      </ul>
      {suggestions.length ? <>
        <span className="people-rail-cap">From your meetings</span>
        <ul className="people-rail-list">
          {suggestions.map((row) => (
            <li key={row.key} data-testid="people-suggestion" data-suggested="">
              <Button variant="chrome" className="people-rail-row people-rail-suggestion" aria-current={`suggestion:${row.key}` === picked ? "true" : undefined}
                onClick={() => onPick(`suggestion:${row.key}`)}>
                <span className="people-rail-name">{row.name}</span>
                {row.source ? <span className="people-rail-facts"><span>{row.source}</span></span> : null}
              </Button>
            </li>
          ))}
        </ul>
      </> : null}
    </nav>
  );
}
