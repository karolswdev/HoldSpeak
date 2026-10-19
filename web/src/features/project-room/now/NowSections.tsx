/* Betterment P3, the Now wing: Waiting on and This week
 * (docs/internal/betterment/projects/DESIGN.md, "The project window: Now").
 *
 * Waiting on: other people's owed items, one line per person, no verbs on
 * the row (Nudge comes with P6; "Hand to coder" never sits on someone
 * else's work). This week: Decided (from the decision records, the one store
 * the face shows; a line opens its decision), Risks and Changed (the
 * background pages when they are served; Risks falls back to the risks the
 * hub read from this week's meetings and notes). Each line keeps the source
 * it rests on. A block with nothing to say is not drawn. */
import { useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { RefTokens, SurfaceLedger, SurfaceLedgerRow, SurfaceSection, type MemoryRefToken } from "../../../desk/surface";
import { openDecisionRecord, openRef } from "../../../desk/openObject";
import type { StandingPageWire } from "../../../desk/standingPages";
import type { RoomNeedsYouItem, RoomNowData } from "../model";
import { monogram } from "../RoomPeopleSection";
import { waitingOn } from "./model";
import "./now.css";

export function WaitingOnSection({ items }: { items: RoomNeedsYouItem[] }) {
  const people = waitingOn(items);
  if (!people.length) return null;
  return (
    <SurfaceSection label="WAITING ON" data-testid="room-waiting-on">
      <SurfaceLedger count="" cols="room">
        <ul className="surface-ledger-rows">
          {people.map((group) => (
            <SurfaceLedgerRow
              key={group.person}
              data-testid="waiting-on-row"
              lead={<span className="room-now-mono" aria-hidden="true">{monogram(group.person)}</span>}
              primary={<span className="surface-primary room-now-person" data-testid="waiting-on-person">{group.person}</span>}
              wrap
              cells={
                <span className="room-now-owed" data-testid="waiting-on-items">
                  {group.items.map((item, index) => (
                    <span key={`${index}:${item.title}`} className="room-now-owed-item"
                      data-tone={item.late ? "danger" : undefined}>
                      {item.title}{item.due ? <span className="room-now-due">{` · ${item.due}`}</span> : null}
                    </span>
                  ))}
                </span>
              }
            />
          ))}
        </ul>
      </SurfaceLedger>
    </SurfaceSection>
  );
}

type Line = { key: string; text: string; refs: MemoryRefToken[]; decisionId?: string };

function pageLines(pages: StandingPageWire[], slug: string): Line[] {
  const page = pages.find((p) => p.slug === slug);
  return (page?.sentences ?? []).map((s, i) => ({ key: `${slug}:${i}`, text: s.text, refs: s.refs }));
}

/** The three groups, in the design's order; an empty group is left out. */
export function thisWeekGroups(now: RoomNowData | null, pages: StandingPageWire[]): { title: string; lines: Line[] }[] {
  const decided: Line[] = (now?.decided ?? []).map((d) => ({
    key: `decided:${d.id}`,
    text: d.text,
    refs: [],
    decisionId: d.id,
  }));
  const pageRisks = pageLines(pages, "risks-and-disputes");
  const risks: Line[] = pageRisks.length ? pageRisks : (now?.risks ?? []).map((r, i) => ({
    key: `risk:${i}`,
    text: r.text,
    refs: r.ref ? [{ ref: r.ref, token: r.token || r.source, opens: r.opens }] : [],
  }));
  const changed = pageLines(pages, "what-changed-this-week");
  return [
    { title: "Decided", lines: decided },
    { title: "Risks", lines: risks },
    { title: "Changed", lines: changed },
  ].filter((g) => g.lines.length);
}

export function ThisWeekSection({
  now,
  pages,
  compact = false,
}: {
  now: RoomNowData | null;
  pages: StandingPageWire[];
  /** 393: each group shows its first line and "N more". */
  compact?: boolean;
}) {
  const groups = thisWeekGroups(now, pages);
  const [opened, setOpened] = useState<Record<string, boolean>>({});
  if (!groups.length) return null;
  return (
    <SurfaceSection label="THIS WEEK" data-testid="room-this-week">
      <div className="room-now-week">
        {groups.map((group) => {
          const all = !compact || opened[group.title];
          const shown = all ? group.lines : group.lines.slice(0, 1);
          const rest = group.lines.length - shown.length;
          return (
            <section key={group.title} className="room-now-group" data-testid="this-week-group"
              aria-label={group.title}>
              <h4 className="room-now-group-title">{group.title}</h4>
              <ul className="room-now-lines">
                {shown.map((line) => (
                  <li key={line.key} className="room-now-line" data-testid="this-week-line">
                    {line.decisionId ? (
                      <Button variant="chrome" className="room-now-decided" data-testid="this-week-decided"
                        aria-label={`Open the decision: ${line.text}`}
                        onClick={() => openDecisionRecord(line.decisionId as string)}>
                        {line.text}
                      </Button>
                    ) : (
                      <span className="room-now-text">{line.text}</span>
                    )}
                    <RefTokens refs={line.refs} onOpen={openRef} />
                  </li>
                ))}
              </ul>
              {rest > 0 ? (
                <Button dense variant="ghost" data-testid="this-week-more"
                  onClick={() => setOpened((o) => ({ ...o, [group.title]: true }))}>
                  {`${rest} more`}
                </Button>
              ) : null}
            </section>
          );
        })}
      </div>
    </SurfaceSection>
  );
}
