/* Betterment P3, the Now wing: Waiting on and This week
 * (docs/internal/betterment/projects/DESIGN.md, "The project window: Now").
 *
 * Waiting on: other people's owed items, one line per person, no verbs on
 * the row (Nudge comes with P6; "Hand to coder" never sits on someone
 * else's work). This week: Open, Decided (from the decision records, the one
 * store the face shows; a line opens its decision), Risks and Changed (the
 * background pages when they are served; Risks falls back to the risks the
 * hub read from this week's meetings and notes). Each line keeps the source
 * it rests on. A block with nothing to say is not drawn. */
import { Fragment, useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { DotWord, RefTokens, SurfaceLedger, SurfaceLedgerRow, SurfaceSection, type MemoryRefToken } from "../../../desk/surface";
import { openDecisionRecord, openRef } from "../../../desk/openObject";
import type { StandingPageWire } from "../../../desk/standingPages";
import type { RoomHealthNudge, RoomHealthPerson, RoomNeedsYouItem, RoomNowData } from "../model";
import { monogram } from "../RoomPeopleSection";
import { waitingOn } from "./model";
import type { NudgeItem } from "../api";
import { GenericNudgeCard, NudgeCard } from "../NudgeCard";
import "./now.css";

function sameDestination(left: string | null | undefined, right: string | null | undefined): boolean {
  if (!left || !right) return false;
  return left.replace(/\/$/, "") === right.replace(/\/$/, "");
}

function waitingNudge(items: ReturnType<typeof waitingOn>[number]["items"], nudges: NudgeItem[]) {
  return nudges.find((nudge) =>
    Boolean(nudge.pr_url) && items.some((item) => sameDestination(item.url, nudge.pr_url)));
}

function nudgePerson(person: string, nudge: NudgeItem): RoomHealthPerson {
  return {
    relationshipId: `waiting-on:${nudge.step_id}`,
    displayName: person,
    login: nudge.reviewer_login,
    medianDays: nudge.days,
    count: 1,
    prs: [{ number: nudge.pr_number, title: nudge.pr_title, url: nudge.pr_url, days: nudge.days }],
    nudge: {
      stepId: nudge.step_id,
      state: nudge.state as RoomHealthNudge["state"],
      prNumber: nudge.pr_number,
      text: nudge.comment_text,
    },
  };
}

function nudgeItem(person: string, nudge: NudgeItem): RoomNeedsYouItem {
  return {
    source: "github",
    kind: "review_bottleneck",
    title: person,
    why: "REVIEW BOTTLENECK",
    since: "",
    // Keep the item's destination bound to the producer's matched review
    // step. A person can have several owed items in this group.
    url: nudge.pr_url,
    verb: "nudge",
    severity: "warning",
    direction: "theirs",
  };
}

export function WaitingOnSection({
  items,
  nudges = [],
  onReload,
}: {
  items: RoomNeedsYouItem[];
  nudges?: NudgeItem[];
  onReload?: () => void;
}) {
  const people = waitingOn(items);
  const [openNudge, setOpenNudge] = useState<string | null>(null);
  if (!people.length) return null;
  return (
    <SurfaceSection label="Waiting on" data-testid="room-waiting-on">
      <SurfaceLedger count="" cols="room">
        <ul className="surface-ledger-rows">
          {people.map((group) => {
            const nudge = waitingNudge(group.items, nudges);
            const genericNudge = nudge ? undefined : group.items.find((item) => item.nudge)?.nudge;
            const key = `${group.person}:${nudge?.step_id ?? genericNudge?.documentRef ?? ""}`;
            const open = openNudge === key;
            return (
              <Fragment key={key}>
                <SurfaceLedgerRow
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
                  trailing={nudge || genericNudge ? (
                    <Button dense variant="ghost" data-testid="waiting-on-nudge"
                      onClick={() => setOpenNudge(open ? null : key)}>
                      Nudge
                    </Button>
                  ) : undefined}
                />
                {nudge && open ? (
                  <NudgeCard
                    person={nudgePerson(group.person, nudge)}
                    needsYouItem={nudgeItem(group.person, nudge)}
                    nudgeItem={nudge}
                    onReload={() => { setOpenNudge(null); onReload?.(); }}
                    persistedState={nudge.state}
                  />
                ) : null}
                {!nudge && genericNudge && open ? <GenericNudgeCard nudge={genericNudge} /> : null}
              </Fragment>
            );
          })}
        </ul>
      </SurfaceLedger>
    </SurfaceSection>
  );
}

/** `riskRef`: an open risk item of the project. The line opens it, and its
 *  state is a dot and a word (`● At risk`), never a grey `Risk` token under
 *  the Risks caption (W3-B, atlas 2026-10-27). */
type Line = { key: string; text: string; refs: MemoryRefToken[]; decisionId?: string; riskRef?: string };

function pageLines(pages: StandingPageWire[], slug: string): Line[] {
  const page = pages.find((p) => p.slug === slug);
  return (page?.sentences ?? []).map((s, i) => ({ key: `${slug}:${i}`, text: s.text, refs: s.refs }));
}

/** The groups, in the design's order; an empty group is left out. */
export function thisWeekGroups(now: RoomNowData | null, pages: StandingPageWire[]): { title: string; lines: Line[] }[] {
  const decided: Line[] = (now?.decided ?? []).map((d) => ({
    key: `decided:${d.id}`,
    text: d.text,
    refs: d.sourceRef ? [{ ref: d.sourceRef, token: d.source || "MTG", opens: true }] : [],
    decisionId: d.id,
  }));
  const open = pageLines(pages, "what-is-open");
  const pageRisks = pageLines(pages, "risks-and-disputes");
  const risks: Line[] = pageRisks.length ? pageRisks : (now?.risks ?? []).map((r, i) => {
    const item = r.token.toUpperCase() === "RISK" && Boolean(r.ref) && r.opens;
    return {
      key: `risk:${i}`,
      text: r.text,
      refs: r.ref && !item ? [{ ref: r.ref, token: r.token || r.source, opens: r.opens }] : [],
      riskRef: item ? r.ref : undefined,
    };
  });
  const changed = pageLines(pages, "what-changed-this-week");
  return [
    { title: "Open", lines: open },
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
    <SurfaceSection label="This week" data-testid="room-this-week">
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
                    ) : line.riskRef ? (
                      <Button variant="chrome" className="room-now-decided" data-testid="this-week-risk"
                        aria-label={`Open the risk: ${line.text}`}
                        onClick={() => openRef(line.riskRef as string)}>
                        {line.text}
                      </Button>
                    ) : (
                      <span className="room-now-text">{line.text}</span>
                    )}
                    {line.riskRef ? <DotWord tone="warn" className="room-now-state">At risk</DotWord> : null}
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
