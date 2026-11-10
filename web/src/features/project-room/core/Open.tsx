// What is open (the language, 2026-11-08; the bold canvas RoomBold): three
// object plates, each an opener with its own Spine. Programs (the Programs
// window scoped to this Project; brass for what waits on you, steel for what
// runs), People (what others owe, opened in place: Waiting on and the
// Project's people), Decisions (moss for the committed share; the latest
// decision opens). A plate with nothing to say is not drawn; a failed
// Programs read says so, never a zero.
import { useEffect, useState, type ReactNode } from "react";
import { DotWord, SurfaceSection } from "../../../desk/surface";
import { Spine, type SpineSegment } from "../../../desk/surface/patterns/Spine";
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
  if (waits) {
    // One waits: name the step it waits on (`1 waits on you: Merge`).
    const step = waits === 1
      ? rows.find((row) => row.your_turn > 0)?.track.find((mark) => mark.mark === "here")?.title ?? ""
      : "";
    parts.push(`${waits} ${waits === 1 ? "waits" : "wait"} on you${step ? `: ${step}` : ""}`);
  }
  return parts.join(" · ") || `${rows.length} ${rows.length === 1 ? "Program" : "Programs"}`;
}

/** The Programs plate's spine: brass waits on you, steel runs, idle rests. */
export function programsSpine(rows: readonly RoomProgramRow[]): SpineSegment[] {
  const waits = rows.filter((row) => row.your_turn > 0).length;
  const running = rows.filter((row) => (row.state === "running" || row.state === "waiting") && row.your_turn <= 0).length;
  return [
    { tone: "brass", share: waits },
    { tone: "steel", share: running },
    { tone: "idle", share: Math.max(0, rows.length - waits - running) },
  ];
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

/** One object plate (the kit plate material): the opener holds the glyph,
 *  the name in the display face, the mono right word, the spine and one line
 *  of words; verbs and the plate's own fold sit under it. */
function OpenPlate({ testId, openTestId, glyph, name, word, wordTone, spine, line, onOpen, openLabel,
  expanded, verbs, fold }: {
  testId: string;
  openTestId?: string;
  glyph: string;
  name: string;
  word?: ReactNode;
  wordTone?: "brass";
  spine: ReactNode;
  line: ReactNode;
  onOpen?: () => void;
  openLabel?: string;
  expanded?: boolean;
  verbs?: ReactNode;
  fold?: ReactNode;
}) {
  const body = (
    <>
      <span className="room-plate-head">
        <img className="room-plate-glyph" src={glyph} alt="" width={24} height={24} draggable={false} />
        <span className="room-plate-name" data-control-label>{name}</span>
        {word ? <span className="room-plate-word" data-tone={wordTone}>{word}</span> : null}
      </span>
      {spine}
      <span className="room-plate-line">{line}</span>
    </>
  );
  return (
    <li className="room-plate" data-testid={testId}>
      {onOpen ? (
        <Button variant="chrome" className="room-plate-open" onClick={onOpen} aria-label={openLabel}
          aria-expanded={expanded} data-testid={openTestId}>
          {body}
        </Button>
      ) : <div className="room-plate-open">{body}</div>}
      {verbs ? <div className="room-plate-verbs">{verbs}</div> : null}
      {fold}
    </li>
  );
}

export function OpenSection({ room, projectId, nudges, onReload, onRefresh }: {
  room: RoomSnapshot;
  projectId: string;
  nudges: NudgeItem[];
  onReload: () => void;
  onRefresh: () => void;
}) {
  const [peopleOpen, setPeopleOpen] = useState(false);
  // The Project's people (the People section's own read): the plate is drawn
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
  const named = prep?.id === projectId ? prep.prep : null;
  const people = peopleWords(room) || namedPeopleWords(named);
  const owing = room.needsYou.state === "ok" ? waitingOn(room.needsYou.items).length : 0;
  const peopleCount = Math.max(owing, named?.people.length ?? 0);
  const decision = latestDecision(room);
  const now = room.now?.state === "ok" ? (room.now as RoomNowData & { state: "ok" }) : null;
  const decided = now?.decided ?? [];
  const committed = decided.filter((d) => d.committedTo).length;
  const rows = programs?.state === "ok" ? programs.programs : [];
  const waits = rows.filter((row) => row.your_turn > 0).length;
  const programGlyph = spriteUrl("program", projectId, "rest", null, 32);
  const programPlate = programs?.state === "ok" ? (
    <OpenPlate testId="room-open-programs" openTestId="room-open-programs-open" glyph={programGlyph}
      name="Programs" word={waits ? `${waits} waits` : rows.length || undefined} wordTone={waits ? "brass" : undefined}
      spine={<Spine segments={programsSpine(rows)} className="room-plate-spine" />}
      line={rows.length ? programsWords(rows) : "No Programs yet"}
      onOpen={openPrograms} openLabel="Open the Programs of this project"
      verbs={rows.length ? undefined : (
        <Button dense variant="secondary" onClick={openPrograms} data-testid="room-programs-new">New program</Button>
      )} />
  ) : programs?.state === "degraded" ? (
    <OpenPlate testId="room-open-programs" glyph={programGlyph} name="Programs"
      spine={<Spine tone="graphite" fill={0} className="room-plate-spine" />}
      line={<DotWord tone="warn" data-testid="room-programs-unavailable">Not read</DotWord>}
      verbs={<Button dense variant="secondary" onClick={onRefresh} data-testid="room-programs-refresh">Refresh</Button>} />
  ) : null;
  if (!programPlate && !people && !decision) return null;
  return (
    <SurfaceSection label="What is open" className="room-open" data-testid="room-what-is-open">
      <ul className="room-plates" aria-label="What is open">
        {programPlate}
        {people ? (
          <OpenPlate testId="room-open-people" openTestId="room-open-people-open"
            glyph={spriteUrl("person", projectId, "rest", null, 32)} name="People" word={peopleCount || undefined}
            spine={<Spine tone="person" fill={peopleCount ? owing / peopleCount : 0} className="room-plate-spine" />}
            line={people}
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
          <OpenPlate testId="room-open-decisions" openTestId="room-open-decisions-open"
            glyph={spriteUrl("decision", decision.id, "rest", null, 32)} name="Decisions" word={decided.length}
            spine={<Spine tone="moss" fill={decided.length ? committed / decided.length : 0} className="room-plate-spine" />}
            line={[decision.text, dayWords(decision.at)].filter(Boolean).join(" · ")}
            onOpen={() => openDecisionRecord(decision.id)} openLabel={`Open the decision: ${decision.text}`} />
        ) : null}
      </ul>
    </SurfaceSection>
  );
}
