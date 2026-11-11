/** One Needs-you row (the ledger's and Today's: one row, not two). The row
 *  is the object: its glyph, its name on one line, one mono line of facts,
 *  one verb; its other verbs are its context menu. An agent's ask is the
 *  Agents row. */
import "./today-rows.css";
import { useLayoutEffect, useMemo, useRef, useState } from "react";
import { AgentRow as AgentRowFace } from "../agents/AgentRow";
import { conductorMembers, type ConductorMember } from "../conductor/members";
import { answerMember, openMember } from "../conductor/open";
import { openAgentLane, openProjectRoom } from "../shell";
import { Button } from "../../components/signal/Signal";
import { useAgentFlights } from "../agentFlights";
import { NeedsRow } from "../surface/objects";
import { Token } from "../surface/Token";
import { wireDate } from "../surface/format";
import { WorkMenu } from "../components/DeskMenu";
import { AddToProject } from "../AddToProject";
import { matchWords, plateOf, tierWord, whenWord, type NeedEntry, type NeedFace } from "./needsFace";
import {
  CommitWell, DecideWell, DetailWell, faceOpener, hasRowMenu, NeedVerbsView, needsRowSprite, NudgeWell,
  projectEntries, SendNeedWell, WhoseWell, type RowMenu, type Well,
} from "./NeedVerbs";

/** Betterment AG9: an agent's ask on Needs you is the agent's own row (the
 *  Agents row: the question, its choices, Answer, Allow / Deny inline). One
 *  row per piece of work: when the ask rides an item, this row stands for
 *  the item. Null until the agents read knows the session (the plain row
 *  draws meanwhile). */
export function useAskMember(sessionKey: string | undefined): ConductorMember | null {
  const sessions = useAgentFlights((s) => s.sessions);
  const flights = useAgentFlights((s) => s.flights);
  return useMemo(() => {
    if (!sessionKey) return null;
    const members = conductorMembers({ detect: null, sessions, flights, launchedAt: {} });
    return members.find((m) => m.sessionKey === sessionKey && (m.live === "ask" || m.live === "held")) ?? null;
  }, [sessionKey, sessions, flights]);
}

export function NeedRow({ face, primary, projects, plates = true }: {
  face: NeedFace;
  primary: boolean;
  projects: boolean;
  /** Window grammar: false leads each row with its object glyph and a
   *  DotWord state (the Needs-you window and Today's Needs you); true keeps
   *  the kind plate and the lamp. */
  plates?: boolean;
}) {
  const member = useAskMember(face.askOf);
  if (member) {
    const question = useAgentFlights.getState().sessions.find((row) => row.key === member.sessionKey)?.question ?? "";
    return (
      <li className="needs-agent-row" data-testid="needs-agent-row" data-need-id={face.id}>
        <AgentRowFace
          member={member}
          question={question}
          lead={primary}
          selected={false}
          onSelect={() => { if (member.launchId) openAgentLane(member.launchId); }}
          onTerminal={() => { if (member.launchId) openAgentLane(member.launchId, { sessionKey: member.sessionKey, raw: true }); }}
          onOpenAnswer={() => answerMember(member)}
          onOpen={() => openMember(member)}
        />
      </li>
    );
  }
  return <PlainNeedRow face={face} primary={primary} projects={projects} plates={plates} />;
}

/** The lamp words that say nothing on a row (owner walk 2026-11-08: "the
 *  'Yours' (well, duh, of course it's going to be mine…)"). */
const DEFAULT_STATES = new Set(["yours", "needs you"]);

/** The row's one quiet word, only when it is not the default: nothing on
 *  his own row; the person's name on a row a person owes (`Bea`, `Bea ·
 *  OVERDUE`); any other state as the hub says it. */
export function quietState(face: Pick<NeedFace, "lamp" | "direction" | "personName">): NeedFace["lamp"] | null {
  const label = String(face.lamp.label ?? "").trim();
  if (!label || DEFAULT_STATES.has(label.toLowerCase())) return null;
  if (face.direction === "theirs") {
    // `WAITING ON BEA · OVERDUE` → `Bea · Overdue`; `TO REVIEW` → `Dana · To review`.
    const parts = label.split(" · ");
    const waiting = /^WAITING ON\s+(.+)$/i.exec(parts[0].trim());
    const person = face.personName || waiting?.[1] || "";
    const rest = waiting ? parts.slice(1) : parts;
    if (person) return { label: [person, ...rest].join(" · "), tone: face.lamp.tone };
  }
  return face.lamp;
}

const LONG_PRESS_MS = 500;

/** The row's context menu (owner walk 2026-11-08): a right press, a long
 *  press on touch, the ContextMenu key or Shift+F10 open it. The ledger's
 *  rows and the first plate share it. */
export function useRowMenu(face: NeedFace, projects: boolean) {
  const [well, setWell] = useState<Well | null>(null);
  const [menu, setMenu] = useState<RowMenu | null>(null);
  const press = useRef<{ timer: number; held: boolean } | null>(null);
  const project = projects && face.project ? face.project : null;
  // The row's own menu (work, confirm), or for any other row that opens or
  // names its Project: Open and Open the Project.
  const extra = projectEntries(project);
  const own = hasRowMenu(face);
  const opener = faceOpener(face);
  const menuable = own || extra.length > 0 || opener !== null;
  const clearPress = () => { if (press.current) window.clearTimeout(press.current.timer); };
  const rowProps: React.LiHTMLAttributes<HTMLLIElement> | undefined = menuable ? {
    onContextMenu: (event) => {
      event.preventDefault();
      setMenu({ x: event.clientX, y: event.clientY, row: event.currentTarget });
    },
    onKeyDown: (event) => {
      if (event.key !== "ContextMenu" && !(event.shiftKey && event.key === "F10")) return;
      event.preventDefault();
      const box = event.currentTarget.getBoundingClientRect();
      setMenu({ x: box.left + 32, y: box.bottom, row: event.currentTarget });
    },
    onPointerDown: (event) => {
      if (event.pointerType !== "touch") return;
      const row = event.currentTarget;
      const { clientX: x, clientY: y } = event;
      clearPress();
      press.current = { held: false, timer: window.setTimeout(() => {
        if (press.current) press.current.held = true;
        setMenu({ x, y, row });
      }, LONG_PRESS_MS) };
    },
    onPointerUp: clearPress,
    onPointerCancel: clearPress,
    onPointerLeave: clearPress,
    // A long press is not also a press on the row (it would open the item).
    onClickCapture: (event) => {
      if (!press.current?.held) return;
      press.current = null;
      event.stopPropagation();
      event.preventDefault();
    },
  } : undefined;
  return { well, setWell, menu, setMenu, rowProps, own, extra, opener, project };
}

/** The row's verbs and, for a row with no menu of its own, its Open menu. */
export function RowVerbs({ face, primary, brass, ctl }: {
  face: NeedFace;
  primary: boolean;
  brass?: boolean;
  ctl: ReturnType<typeof useRowMenu>;
}) {
  const { well, setWell, menu, setMenu, own, extra, opener } = ctl;
  return (
    <>
      {face.moreAsks ? (
        <Token className="surface-token" data-testid="needs-more-asks">{`+${face.moreAsks} MORE`}</Token>
      ) : null}
      <NeedVerbsView face={face} primary={primary} brass={brass} well={well} onWell={setWell} menu={own ? menu : null} onMenu={setMenu} extra={extra} />
      {!own && menu ? <WorkMenu label={face.name} x={menu.x} y={menu.y} autoFocus onClose={() => setMenu(null)}
        returnFocus={() => menu.row?.querySelector<HTMLElement>("[data-testid=needs-row-verb]")?.focus()}
        entries={[...(opener ? [{ type: "item" as const, id: "open", label: "Open", onSelect: opener }] : []), ...extra]} /> : null}
    </>
  );
}

/** The well a row's verb opened, under the row. */
export function RowWells({ face, well, setWell }: { face: NeedFace; well: Well | null; setWell(next: Well | null): void }) {
  return well === "project" && face.verbs.kind === "confirm" ? <li className="needs-drawer-well"><AddToProject meetingId={face.verbs.meetingId} /></li>
    : well === "detail" ? <DetailWell face={face} />
      : well === "nudge" ? <NudgeWell face={face} />
        : well === "decide" ? <DecideWell face={face} onDone={() => setWell(null)} />
          : well === "whose" ? <WhoseWell face={face} onDone={() => setWell(null)} />
            : well === "send" ? <SendNeedWell face={face} onDone={() => setWell(null)} />
              : well === "owner" || well === "date" ? <CommitWell face={face} which={well} onDone={() => setWell(null)} /> : null;
}

/** The bold row's facts (2026-11-08), one mono line: the fact, since when,
 *  where it came from. Only the facts there are; none said twice. */
export function ledgerFact(face: Pick<NeedFace, "fact" | "since" | "origin">, now: Date = new Date()): string {
  const since = face.since ? wireDate(face.since) : null;
  const parts = [face.fact, since ? whenWord(since, now) : "", face.origin ?? ""].map((p) => (p ?? "").trim()).filter(Boolean);
  return parts.filter((part, index) => !parts.slice(0, index).some((was) => was.toLowerCase().includes(part.toLowerCase()))).join(" · ");
}

function PlainNeedRow({ face, primary, projects, plates }: { face: NeedFace; primary: boolean; projects: boolean; plates: boolean }) {
  const ctl = useRowMenu(face, projects);
  const { project } = ctl;
  return (
    <>
      <NeedsRow
        id={face.id}
        // The row takes the keyboard: on a pointer its verb shows on hover or
        // focus (the bold row), so Tab reaches the row first, then its verb.
        rowProps={{ tabIndex: 0, ...ctl.rowProps }}
        kind={face.kind}
        name={face.name}
        fact={(plates ? face.fact : ledgerFact(face)) || undefined}
        factTitle={face.factTitle}
        factCode={face.factCode}
        factWords={face.factWords}
        lamp={plates ? face.lamp : quietState(face)}
        sprite={needsRowSprite(face)}
        plate={plates ? plateOf(face) : undefined}
        glyphLabel={plates ? undefined : face.tier ? tierWord(face.tier) : glyphWord(face)}
        dotState={!plates}
        // A2b: the Project button is a generic open: the Project's drawer.
        project={project ? { name: project.name, onOpen: () => openProjectRoom(project.id) } : undefined}
        verbs={<RowVerbs face={face} primary={primary} ctl={ctl} />}
      />
      <RowWells face={face} well={ctl.well} setWell={ctl.setWell} />
    </>
  );
}

/** Window Program W4 (the words): the meetings that say one Project's word
 *  are one row (`13 mentions of cutover`); Show lists each meeting under it
 *  by its own title, Hide folds them again. */
export function MatchRows({ entry, firstId, projects }: {
  entry: Extract<NeedEntry, { kind: "match" }>;
  firstId: string | null;
  projects: boolean;
}) {
  const [open, setOpen] = useState(false);
  const name = matchWords(entry.faces.length, entry.word);
  const project = projects && entry.project ? entry.project : null;
  return (
    <>
      <NeedsRow
        id={`match:${entry.key}`}
        kind="meeting"
        name={name}
        lamp={{ label: "Not in the Project", tone: entry.faces[0]?.lamp.tone ?? "info" }}
        sprite={needsRowSprite(entry.faces[0])}
        glyphLabel="Meetings"
        dotState
        project={project ? { name: project.name, onOpen: () => openProjectRoom(project.id) } : undefined}
        verbs={(
          <Button dense variant="secondary" aria-label={`${open ? "Hide" : "Show"}: ${name}`} aria-expanded={open}
            data-testid="needs-match-toggle" onClick={() => setOpen((was) => !was)}>
            {open ? "Hide" : "Show"}
          </Button>
        )}
      />
      {open ? entry.faces.map((face) => (
        <NeedRow key={face.id} face={face} primary={face.id === firstId} projects={projects} plates={false} />
      )) : null}
    </>
  );
}

/** PHILO-15-09 (B12): every row says what it is. With the glyph leading
 *  (window grammar) the word is the glyph's name: its alt and its title. */
const GLYPH_WORDS: Record<string, string> = {
  CC: "Claude Code", CX: "Codex", PI: "pi", AGT: "Agent", PR: "Pull request",
  DEC: "Decision", ACT: "Action", MTG: "Meeting", SRC: "Source", REC: "Recording",
};
export function glyphWord(face: NeedFace): string | undefined {
  const plate = plateOf(face);
  if (!plate) return undefined;
  return GLYPH_WORDS[plate] ?? plate.charAt(0) + plate.slice(1).toLowerCase();
}

interface DoorRead {
  upcoming?: Array<{ title?: string; starts_at?: string; source?: string }>;
  calendar_configured?: boolean;
}

/** Stamp the stable testids and the row-open mark on the species' rows
 *  (NeedsRow takes no testid prop; B1 owns it): `needs-row` on a member,
 *  `needs-source-row` on a source row, `data-opens` where the body opens. */
export function useRowMarks(
  ref: React.RefObject<HTMLDivElement | null>,
  faces: readonly NeedFace[],
  members: ReadonlySet<string>,
) {
  useLayoutEffect(() => {
    const byId = new Map(faces.map((f) => [f.id, f]));
    for (const li of ref.current?.querySelectorAll<HTMLElement>("li.needs-row") ?? []) {
      const face = byId.get(li.getAttribute("data-object-id") ?? "");
      if (!face) continue;
      li.setAttribute("data-testid", face.source ? "needs-source-row" : "needs-row");
      // A row the hub counts (one member): the head, the Dock and the notch
      // say the number of these rows.
      li.setAttribute("data-counted", members.has(face.memberRef ?? face.id) ? "true" : "false");
      if (face.verbs.kind === "confirm" || face.verbs.kind === "decide" || face.verbs.kind === "whose") li.setAttribute("data-proposal", "true");
      if (face.arrival) li.setAttribute("data-new", "true");
      else li.removeAttribute("data-new");
      if (face.direction) li.setAttribute("data-direction", face.direction);
      if (face.tier) li.setAttribute("data-tier", face.tier);
      else li.removeAttribute("data-tier");
      if (faceOpener(face)) li.setAttribute("data-opens", "true");
      else li.removeAttribute("data-opens");
    }
  });
}
