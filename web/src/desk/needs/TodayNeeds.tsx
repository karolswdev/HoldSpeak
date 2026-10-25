/** Betterment daily D4: the top of Needs you, in Today.
 *
 *  The same rows as the Needs-you window, from the same read and in the same
 *  rank (`useNeedFaces`), with the same verbs (`NeedRow`): never a second
 *  list. Today shows the first rows only; its toolbar's Needs you opens the
 *  Needs-you window.
 *  What a person owes him shows here only when it is late or due today. */
import { useRef } from "react";
import { Button } from "../../components/signal/Signal";
import { openSurfaceOr } from "../shell";
import { refreshNeedsYou } from "../needsYou";
import { NeedsList } from "../surface/objects";
import { wireDate } from "../surface/format";
import { faceOpener, NeedRow, useRowMarks } from "./NeedsDrawer";
import type { NeedFace } from "./needsFace";
import { PeopleReadFailed } from "../people/PeopleReadFailed";

/** The local day of `d`, `YYYY-MM-DD`. */
function localDay(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

/** True when the row is due today or earlier. */
export function dueByToday(face: Pick<NeedFace, "due">, now: Date): boolean {
  const due = face.due ? wireDate(face.due) : null;
  return Boolean(due && localDay(due) <= localDay(now));
}

/** Today's rows: the one list in its rank, a person's row only when it is
 *  late or due today, at most `limit`. */
export function todayRows(work: readonly NeedFace[], now: Date, limit: number): NeedFace[] {
  return work
    .filter((face) => face.direction !== "theirs" || dueByToday(face, now))
    .slice(0, limit);
}

export function TodayNeeds({ work, count, now, limit, primary, projects, loaded, failed, emptyDesk, calendarLead, next, peopleUnread = false }: {
  /** `useNeedFaces().work`: the rows of the one list, ranked. */
  work: readonly NeedFace[];
  /** The hub's one number (the bell and the Dock say it too). */
  count: number;
  now: Date;
  limit: number;
  /** The first row's verb is the face's one filled verb. */
  primary: boolean;
  projects: boolean;
  /** The first read has ended (no empty line before it). */
  loaded: boolean;
  /** The hub's answer could not be read: one line and Retry, never "Nothing". */
  failed: boolean;
  /** Connect calendar is the face's one filled verb. */
  calendarLead: boolean;
  /** No calendar and no meetings yet: the one line of an empty desk. */
  emptyDesk: boolean;
  /** `1:1 with Mira at 09:30`: the next meeting, for the line when nothing waits. */
  next: string | null;
  /** Betterment D6: the hub could not read People: one line, Today stays. */
  peopleUnread?: boolean;
}) {
  const listRef = useRef<HTMLDivElement>(null);
  const rows = todayRows(work, now, limit);
  const members = new Set(rows.filter((f) => !f.uncounted).map((f) => f.memberRef ?? f.id));
  useRowMarks(listRef, rows, members);
  const onRowPress = (event: React.MouseEvent<HTMLDivElement>) => {
    const target = event.target as HTMLElement;
    if (target.closest("button, a, input, textarea, select, .needs-drawer-well")) return;
    const id = target.closest("li.needs-row")?.getAttribute("data-object-id");
    const face = rows.find((f) => f.id === id);
    if (face) faceOpener(face)?.();
  };
  const firstId = primary ? rows.find((f) => !f.source && f.verbs.kind !== "setup")?.id ?? null : null;
  return (
    <section className="today-needs" aria-label="Needs you" data-testid="today-needs">
      {/* Window grammar: a sentence-case section caption on a hairline. The
          count and the door to the whole list are Today's toolbar verb
          (Needs you N), so this head says no number. */}
      <h3 className="today-section-cap">Needs you</h3>
      {peopleUnread ? <PeopleReadFailed testId="today-people-read-failed" onRetry={() => void refreshNeedsYou(true)} /> : null}
      {rows.length > 0 ? (
        <div ref={listRef} onClick={onRowPress} className="today-needs-list" data-testid="needs-list">
          <NeedsList label="Needs you">
            {rows.map((face) => (
              <NeedRow key={face.id} face={face} primary={face.id === firstId} projects={projects} />
            ))}
          </NeedsList>
        </div>
      ) : !loaded ? null : failed ? (
        <div className="today-failed" data-testid="today-needs-failed" role="status">
          <span className="kit-pill" data-tone="danger">Needs you could not be read. Nothing changed. Press Retry.</span>
          <Button dense variant="ghost" onClick={() => void refreshNeedsYou(true)}>Retry</Button>
        </div>
      ) : emptyDesk ? (
        <p className="today-needs-none" data-testid="today-empty-desk">
          <span>Your meetings and calendar fill this.</span>
          <Button dense variant={calendarLead ? "primary" : "secondary"} onClick={() => openSurfaceOr("configure-settings", "/settings", "integration:calendar")}>
            Connect calendar
          </Button>
        </p>
      ) : (
        <p className="today-needs-none" data-testid="today-needs-none">
          {next ? `Nothing needs you. Next: ${next}.` : "Nothing needs you."}
        </p>
      )}
    </section>
  );
}
