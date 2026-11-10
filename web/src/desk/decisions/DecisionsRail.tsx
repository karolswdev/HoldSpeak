import type { ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import { CheckGadget, Rail, StringGadget, ToolGlyph, type SpineTone } from "../surface";

export type RailDecision = { key: string; title: string; day: string; where: string; tone: SpineTone; word: string };

export function DecisionsRail({ rows, picked, query, onQuery, current, onCurrent, onPick, onNew, composing, head, more }: {
  rows: RailDecision[]; picked: string | null; query: string; onQuery(next: string): void;
  current: boolean; onCurrent(next: boolean): void; onPick(key: string): void; onNew(): void;
  composing: boolean; head?: ReactNode; more?: ReactNode;
}) {
  return <Rail label="Decisions" data-testid="decisions-rail" picked={picked} onPick={onPick}
    paneOpen={Boolean(picked) || composing} hostBack foot={more}
    head={<>
      <Button dense variant="primary" aria-expanded={composing} onClick={onNew} data-testid="decisions-new"><ToolGlyph kind="new" />New decision</Button>
      <StringGadget label="Search decisions" type="search" value={query} onChange={onQuery} placeholder="Search decisions" />
      <CheckGadget label="Current only" variant="token" checked={current} onChange={onCurrent} />
      {head}
    </>}
    items={rows.map((row) => ({
      id: row.key, label: row.title, accessibleLabel: `${row.title}, ${row.word}`,
      facts: [row.day, row.where].filter(Boolean).join(" · "),
      state: <span data-tone={row.tone} data-testid="decisions-state">{row.word}</span>, spine: { tone: row.tone },
      rowData: { "data-testid": "decisions-row", "data-kind": "decision", "data-state": row.tone },
    }))} />;
}
