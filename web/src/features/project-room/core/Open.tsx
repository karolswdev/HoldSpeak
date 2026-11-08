// R1 "the brief" (owner 2026-11-08): What is open. Three object rows, each
// opens its thing: Programs (the Programs window scoped to this Project),
// People (what others owe, opened in place: Waiting on and the Project's
// people), Decisions (the latest decision). A row with nothing to say is not
// drawn; a failed Programs read says so, never a zero.
import { useEffect, useState } from "react";
import { ListRow, ListView, SurfaceSection } from "../../../desk/surface";
import { spriteUrl } from "../../../desk/sprites";
import { openDecisionRecord } from "../../../desk/openObject";
import { useDesk } from "../../../desk/store";
import { Button } from "../../../components/signal/Signal";
import type { RoomNowData, RoomProgramRow, RoomSnapshot } from "../model";
import { dayWords, waitingOn } from "../now/model";
import { WaitingOnSection } from "../now/NowSections";
import { RoomPeopleSection } from "../RoomPeopleSection";
import { fetchRoomPeoplePreparation, type NudgeItem, type RoomPeoplePreparation } from "../api";
import { useRoomRead } from "../roomReads";

/** `2 running · 1 waits on you`; the count of Programs when neither. */
export function programsWords(rows: readonly RoomProgramRow[]): string {
  // A waiting Program is running: its agent works or it waits on a step.
  const running = rows.filter((row) => row.state === "running" || row.state === "waiting").length;
  const waits = rows.reduce((sum, row) => sum + (row.your_turn > 0 ? 1 : 0), 0);
  const parts: string[] = [];
  if (running) parts.push(`${running} running`);
  if (waits) parts.push(`${waits} ${waits === 1 ? "waits" : "wait"} on you`);
  return parts.join(" · ") || `${rows.length} ${rows.length === 1 ? "Program" : "Programs"}`;
}

/** `Bea owes a review · Dana owes 2`: what others owe, one part per person. */
export function peopleWords(room: RoomSnapshot): string {
  if (room.needsYou.state !== "ok") return "";
  return waitingOn(room.needsYou.items).map((group) => group.items.length === 1
    ? `${group.person} owes ${group.items[0].title}`
    : `${group.person} owes ${group.items.length}`).join(" · ");
}

/** The People row's words when no one owes him: the Project's people by
 *  name (`Ana Kowalska · Marek Nowak`), or the owners still to link. */
export function namedPeopleWords(prep: RoomPeoplePreparation | null): string {
  if (!prep) return "";
  const names = prep.people.map((person) => String(person.display_name ?? "").trim()).filter(Boolean);
  if (names.length) return names.length > 3 ? `${names.slice(0, 3).join(" · ")} · ${names.length - 3} more` : names.join(" · ");
  return prep.unresolved.length ? `${prep.unresolved.length} ${prep.unresolved.length === 1 ? "owner" : "owners"} to link` : "";
}

/** The newest decision this week, or null. */
export function latestDecision(room: RoomSnapshot): RoomNowData["decided"][number] | null {
  const now = room.now?.state === "ok" ? (room.now as RoomNowData & { state: "ok" }) : null;
  const decided = [...(now?.decided ?? [])].sort((a, b) => String(b.at).localeCompare(String(a.at)));
  return decided[0] ?? null;
}

export function OpenSection({ room, projectId, nudges, onReload, onRefresh }: {
  room: RoomSnapshot;
  projectId: string;
  nudges: NudgeItem[];
  onReload: () => void;
  onRefresh: () => void;
}) {
  const [peopleOpen, setPeopleOpen] = useState(false);
  // The Project's people (the People section's own read): the row is drawn
  // when someone owes him or the Project names people.
  const [prep, setPrep] = useState<{ id: string; prep: RoomPeoplePreparation | null } | null>(null);
  useRoomRead("people-row", prep?.id === projectId);
  useEffect(() => {
    let live = true;
    fetchRoomPeoplePreparation(projectId)
      .then((next) => { if (live) setPrep({ id: projectId, prep: next }); })
      .catch(() => { if (live) setPrep({ id: projectId, prep: null }); });
    return () => { live = false; };
  }, [projectId, room.revision]);
  const programs = room.programs;
  const openPrograms = () => useDesk.getState().openSurfaceWindow("open-programs", `project:${projectId}`);
  const people = peopleWords(room) || namedPeopleWords(prep?.id === projectId ? prep.prep : null);
  const decision = latestDecision(room);
  const rows = programs?.state === "ok" ? programs.programs : [];
  const programRow = programs?.state === "ok" ? (
    <ListRow data-testid="room-open-programs" openTestId="room-open-programs-open"
      glyph={spriteUrl("program", projectId, "rest", null, 20)} name="Programs"
      meta={rows.length ? programsWords(rows) : "No Programs yet"}
      onOpen={openPrograms} openLabel="Open the Programs of this project"
      verbs={rows.length ? undefined : (
        <Button dense variant="secondary" onClick={openPrograms} data-testid="room-programs-new">New program</Button>
      )} />
  ) : programs?.state === "degraded" ? (
    <ListRow data-testid="room-open-programs" glyph={spriteUrl("program", projectId, "rest", null, 20)}
      name="Programs" state={{ word: "Not read", tone: "warn", testId: "room-programs-unavailable" }}
      verbs={<Button dense variant="secondary" onClick={onRefresh} data-testid="room-programs-refresh">Refresh</Button>} />
  ) : null;
  if (!programRow && !people && !decision) return null;
  return (
    <SurfaceSection label="What is open" className="room-open" data-testid="room-what-is-open">
      <ListView label="What is open" className="room-open-rows">
        <ul className="kit-listrows">
          {programRow}
          {people ? (
            <ListRow data-testid="room-open-people" openTestId="room-open-people-open"
              glyph={spriteUrl("people", projectId, "rest", null, 20)} name="People" meta={people}
              onOpen={() => setPeopleOpen((open) => !open)} expanded={peopleOpen}
              openLabel={peopleOpen ? "Hide the people" : "Show the people"}
              fold={peopleOpen ? (
                <div className="room-open-people" data-testid="room-open-people-fold">
                  {room.needsYou.state === "ok" ? (
                    <WaitingOnSection items={room.needsYou.items} nudges={nudges} onReload={onReload} />
                  ) : null}
                  <RoomPeopleSection projectId={projectId} />
                </div>
              ) : undefined} />
          ) : null}
          {decision ? (
            <ListRow data-testid="room-open-decisions" openTestId="room-open-decisions-open"
              glyph={spriteUrl("decision", decision.id, "rest", null, 20)} name="Decisions"
              meta={[decision.text, dayWords(decision.at)].filter(Boolean).join(" · ")}
              onOpen={() => openDecisionRecord(decision.id)} openLabel={`Open the decision: ${decision.text}`} />
          ) : null}
        </ul>
      </ListView>
    </SurfaceSection>
  );
}
