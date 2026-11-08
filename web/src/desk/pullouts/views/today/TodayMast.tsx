/** Today's mast (the language, 2026-11-08): the Dock's lamp, the part of
 *  the day as the title, one mono facts line (the meetings ahead, the one
 *  number of Needs you, the next 1:1) and the verbs Record now and Prepare
 *  now. Under it the spine: steel is the day's meetings held, brass what
 *  waits on him now (meetings to finish, decisions to make), idle the rest. */
import { Button } from "../../../../components/signal/Signal";
import { Mast } from "../../../surface/patterns/Mast";
import { Spine, type SpineSegment } from "../../../surface/patterns/Spine";
import { DotWord, TickNumber } from "../../../surface/kit";
import { SYSTEM_48 } from "../../../systemSprites";
import { openChairWindow } from "../../../chair/chairWindows";
import { dayGreeting, SHORT_DAYS, SHORT_MONTHS } from "./time";

/** The spine's parts: steel held, brass waits on him, idle ahead. */
export function daySpine(held: number, waits: number, ahead: number): SpineSegment[] {
  const total = held + waits + ahead;
  if (total <= 0) return [];
  return [
    { tone: "steel", share: held / total },
    { tone: "brass", share: waits / total },
    { tone: "idle", share: ahead / total },
  ];
}

export function TodayMast({ now, ahead, needsCount, nextWords, held, waits, recordLead, onRecord, prepare, prepareBusy, prepareError, onPrepare }: {
  now: Date;
  ahead: number;
  needsCount: number;
  /** `next 1:1 in 50 min`, or null. */
  nextWords: string | null;
  held: number;
  waits: number;
  recordLead: boolean;
  onRecord(): void;
  /** Prepare now shows only when Morning prep is set up. */
  prepare: boolean;
  prepareBusy: boolean;
  prepareError: string | null;
  onPrepare(): void;
}) {
  const segments = daySpine(held, waits, ahead);
  const facts = [
    ahead > 0 ? <span key="ahead">{ahead === 1 ? "1 meeting ahead" : `${ahead} meetings ahead`}</span> : null,
    needsCount > 0 ? (
      <Button key="needs" variant="chrome" className="today-mast-needs" data-testid="today-needs-all"
        onClick={() => openChairWindow("chair:needs")}>
        <b className="today-needs-count" data-testid="today-needs-count"><TickNumber value={needsCount} /></b>
        {needsCount === 1 ? " needs you" : " need you"}
      </Button>
    ) : null,
    nextWords ? <span key="next">{nextWords}</span> : null,
  ].filter(Boolean);
  return (
    <div className="today-mast-band">
      <Mast
        kind="today"
        glyph={SYSTEM_48.dockIntelligence}
        className="today-mast"
        data-testid="today-toolbar"
        title={(
          <span className="today-mast-day" data-testid="today-day" title={`${SHORT_DAYS[now.getDay()]} ${now.getDate()} ${SHORT_MONTHS[now.getMonth()]}`}>
            <span data-testid="today-greeting">{dayGreeting(now)}</span>
          </span>
        )}
        facts={facts.length ? facts.flatMap((fact, index) => (index ? [<span key={`dot${index}`} className="today-mast-sep" aria-hidden="true">·</span>, fact] : [fact])) : undefined}
      >
        <Button dense variant={recordLead ? "primary" : "secondary"} onClick={onRecord} data-testid="today-record-now">Record now</Button>
        {prepare ? (
          <Button dense variant="secondary" loading={prepareBusy} data-testid="today-prepare-now" onClick={onPrepare}>Prepare now</Button>
        ) : null}
        {prepareError ? <span role="status"><DotWord tone="fail">{prepareError}</DotWord></span> : null}
      </Mast>
      {segments.length ? (
        <Spine className="today-mast-spine" segments={segments} data-testid="today-spine"
          label={[held ? `${held} held` : "", waits ? `${waits} wait on you` : "", ahead ? `${ahead} ahead` : ""].filter(Boolean).join(", ")} />
      ) : null}
    </div>
  );
}
