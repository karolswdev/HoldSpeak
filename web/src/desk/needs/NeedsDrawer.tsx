/** PHILO-14 A5 — Needs you as a smart drawer (board A-5; canvas README,
 *  RATIFIED A; PROPOSAL §3 Movement A: "Needs you is a smart drawer over
 *  the same objects").
 *
 *  The head is the number, once (`6 need you`). The body is a NeedsList of
 *  NeedsRows: each row IS the object (its icon by kind, its name, one fact
 *  line, ONE lamp and its word, its own verbs). The data is the hub's one
 *  answer (`useNeedsYou`, #788): the head speaks the same number as the
 *  Dock badge and the bell, and the rows are the members.
 *
 *  No ⚠, no AgentFlight chip, no filter strip, no coverage chip: a question
 *  is the `ask` lamp; an item an agent works names the agent on its fact
 *  line and never reads UNASSIGNED. Hand to coder is not a Needs row verb
 *  (ruling in the PR body): the object's own window and the Object menu
 *  carry it.
 */
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { create } from "zustand";
import { Button } from "../../components/signal/Signal";
import { apiFetch, readableError } from "../../lib/api";
import { useAgentFlights } from "../agentFlights";
import { commandForDoorVerb, labelFor, supportsDoorVerb, type DoorVerb } from "../chair/doorVerbs";
import { useGate } from "../gate";
import { clearWriteFailure, reportWriteFailure } from "../hooks/useWriteReceipt";
import { refreshNeedsYou, useNeedsYou } from "../needsYou";
import { openProjectProposal, refOpener, type Opener } from "../openObject";
import { openCoderSession, openProjectRoom, openSurfaceOr } from "../shell";
import { useDesk } from "../store";
import { AppHead, EgressChip, FilterBar, ScrollHint, StatusStrip, StringGadget, SurfaceFooter, SurfaceSection, SurfaceState } from "../surface";
import { openSourceRef } from "../surface/citations";
import { NeedsList, NeedsRow } from "../surface/objects";
import { spriteUrl } from "../sprites";
import { groupGaps, readCoverage } from "../coverage";
import {
  armingFace,
  coverageGroupFace,
  needFace,
  needFaces,
  needsHead,
  nextWord,
  passesNeedsFilter,
  plateOf,
  urlHost,
  type NeedFace,
  type NeedsFilter,
} from "./needsFace";
import { cancelArming, useArmingOutcome } from "./arming";
import { WorkMenu, type WorkMenuEntry } from "../components/DeskMenu";
import { Disclosure } from "../surface/patterns/Disclosure";
import { AddToProject } from "../AddToProject";
import "./needs.css";

/** Answer: the agent's window with the answer field focused. Lane C2 builds
 *  the agent window and honors the hint; today the session opener opens the
 *  answer well (Conductor F2 K5b). */
/** A Needs row's sprite: an agent row wears its OWN agent (Codex keeps its
 *  face; PHILO-14 A0c r2); any other row takes its kind's sprite. */
export function needsRowSprite(face: { id: string; agent?: string | null }): string | undefined {
  return face.agent ? spriteUrl("agent", face.id, "rest", face.agent) : undefined;
}

export function openAgentAnswer(sessionKey: string): void {
  openCoderSession(sessionKey, { answer: true });
}

/** What a press on the row body opens (A2b): a proposal opens the Room with
 *  THAT proposal selected; every other row its ref in the one open grammar
 *  (a Project's ref opens its drawer). Null: the body opens nothing. */
export function faceOpener(face: NeedFace): Opener | null {
  const proposal = face.proposal;
  if (proposal) return () => openProjectProposal(proposal.projectId, proposal.proposalId);
  return refOpener(face.openRef);
}

type Well = "owner" | "date" | "detail" | "project";

/** PHILO-15 B61: the receipt a source Retry leaves in the drawer. */
type SourceReceipt = { tone: "ok" | "fail"; text: string };
export const useSourceReceipt = create<{ receipt: SourceReceipt | null; set(r: SourceReceipt | null): void }>(
  (setState) => ({ receipt: null, set: (receipt) => setState({ receipt }) }),
);

function hhmm(d: Date): string {
  return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

/** PHILO-15 B61: Retry on a source re-checks THAT source (each of its
 *  Watches, through the hub's single-Watch check) and leaves a receipt;
 *  then the one number is read again. */
export async function recheckSource(name: string, watchIds: readonly string[]): Promise<SourceReceipt> {
  try {
    for (const id of watchIds) {
      await apiFetch(`/api/watches/${encodeURIComponent(id)}/evaluate`, { method: "POST" });
    }
    return { tone: "ok", text: `CHECKED · ${name} · ${hhmm(new Date())}` };
  } catch (error) {
    return { tone: "fail", text: `NOT CHECKED · ${name} · ${readableError(error)}` };
  } finally {
    void refreshNeedsYou(true);
  }
}

function NeedVerbsView({ face, primary, onWell, well }: {
  face: NeedFace;
  primary: boolean;
  well: Well | null;
  onWell(next: Well | null): void;
}) {
  const [busy, setBusy] = useState(false);
  const moreRef = useRef<HTMLButtonElement>(null);
  const [more, setMore] = useState(false);
  const projects = useDesk((state) => state.projects);
  const setSourceReceipt = useSourceReceipt((st) => st.set);
  const lead = primary ? "primary" : "secondary";
  const v = face.verbs;
  const named = (verb: string) => `${verb}: ${face.name}`;

  const act = async (label: string, run: () => Promise<unknown>, key: string) => {
    if (busy) return;
    setBusy(true);
    try {
      await run();
      clearWriteFailure(key);
      void refreshNeedsYou(true);
    } catch (error) {
      reportWriteFailure(label, error, () => void act(label, run, key), key);
    } finally {
      setBusy(false);
    }
  };

  switch (v.kind) {
    case "answer":
      return (
        <>
          <Button dense variant="ghost" aria-label={named("Open")} data-testid="needs-row-verb" data-verb="open"
            onClick={() => openCoderSession(v.sessionKey)}>Open session</Button>
          <Button dense variant={lead} aria-label={named("Answer")} data-testid="needs-row-verb" data-verb="answer"
            onClick={() => openAgentAnswer(v.sessionKey)}>Answer</Button>
        </>
      );
    case "gate": {
      const decide = (decision: "approved" | "denied") =>
        act(decision === "approved" ? "Approve" : "Deny",
          () => useGate.getState().decide(v.proposalId, decision), `gate:${v.proposalId}`);
      const deny = () => void decide("denied");
      const approve = () => void decide("approved");
      return (
        <>
          <Button dense variant="ghost" disabled={busy} aria-label={named("Deny")} data-testid="needs-row-verb" data-verb="deny"
            onClick={deny}>Deny</Button>
          <Button dense variant={lead} disabled={busy} aria-label={named("Approve")} data-testid="needs-row-verb" data-verb="approve"
            onClick={approve}>Approve</Button>
        </>
      );
    }
    case "gate-cut": {
      const deny = () => void act("Deny",
        () => useGate.getState().decide(v.proposalId, "denied"), `gate:${v.proposalId}`);
      return (
        <>
          <Button dense variant="ghost" disabled={busy} aria-label={named("Deny")} data-testid="needs-row-verb" data-verb="deny"
            onClick={deny}>Deny</Button>
          {v.sessionKey ? (
            <Button dense variant={lead} aria-label={named("Open the agent's lane on Raw")} data-testid="needs-row-verb" data-verb="open"
              onClick={() => openCoderSession(v.sessionKey, { raw: true })}>Open raw lane</Button>
          ) : null}
        </>
      );
    }
    case "pr":
      return (
        <>
          <EgressChip label={urlHost(v.url) || "GITHUB.COM"} scope="cloud" />
          <Button dense variant={lead} aria-label={named(`Open PR #${v.number ?? ""}`)} data-testid="needs-row-verb" data-verb="open-pr"
            onClick={() => window.open(v.url, "_blank", "noopener")}>Open PR</Button>
        </>
      );
    case "session":
      return (
        <Button dense variant={lead} aria-label={named("Open the agent")} data-testid="needs-row-verb" data-verb="open"
          onClick={() => openCoderSession(v.sessionKey)}>Open session</Button>
      );
    case "review":
      return (
        <Button dense variant={lead} aria-label={named("Review")} data-testid="needs-row-verb" data-verb="review"
          onClick={() => refOpener(v.ref)?.()}>Review</Button>
      );
    case "commitment": {
      if (v.next === "mark_done") {
        return (
          <Button dense variant={lead} disabled={busy} aria-label={named("Done")} data-testid="needs-row-verb" data-verb="done"
            onClick={() => void act("Done", () => apiFetch("/api/follow-through/complete", {
              method: "POST", json: { card_id: v.cardId, verb: "done", payload: {} },
            }), `action-item:${v.cardId}`)}>Done</Button>
        );
      }
      const which: Well = v.next === "name_owner" ? "owner" : "date";
      const label = which === "owner" ? "Name an owner" : "Set a date";
      return (
        <Button dense variant={lead} aria-label={named(label)} aria-expanded={well === which}
          data-testid="needs-row-verb" data-verb={which === "owner" ? "name-owner" : "set-date"}
          onClick={() => onWell(well ? null : which)}>{label}</Button>
      );
    }
    case "name-owner":
      if (!v.cardId && !v.openRef) return null;
      return (
        <Button dense variant={lead} aria-label={named("Name an owner")}
          aria-expanded={v.cardId ? well === "owner" : undefined} data-testid="needs-row-verb" data-verb="name-owner"
          onClick={() => {
            if (v.cardId) onWell(well ? null : "owner");
            else if (v.openRef) useDesk.getState().openPullout(v.openRef);
          }}>Name an owner</Button>
      );
    case "confirm": {
      const opener = faceOpener(face);
      const entries: WorkMenuEntry[] = [
        ...(opener ? [{ type: "item" as const, id: "open", label: "Open", onSelect: opener }] : []),
        ...(!v.projectId && v.meetingId && projects.some((project) => !project.is_archived)
          ? [{ type: "item" as const, id: "project", label: "Add to Project", onSelect: () => onWell("project") }] : []),
        { type: "item", id: "defer", label: "Defer", ghost: busy ? "Busy" : undefined,
          onSelect: () => void act("Defer", () => apiFetch(
            `/api/proposals/${encodeURIComponent(v.proposalId)}/defer`, { method: "POST", json: {} },
          ), `proposal:${v.proposalId}`) },
        { type: "item", id: "decline", label: "Decline", ghost: busy ? "Busy" : undefined,
          onSelect: () => void act("Decline", () => apiFetch(
            `/api/proposals/${encodeURIComponent(v.proposalId)}/dismiss`, { method: "POST" },
          ), `proposal:${v.proposalId}`) },
      ];
      return <>
        <Button dense variant={lead} disabled={busy} aria-label={named("Confirm")} data-testid="needs-row-verb" data-verb="confirm"
          onClick={() => void act("Confirm", () => apiFetch(
            `/api/proposals/${encodeURIComponent(v.proposalId)}/confirm`, { method: "POST" },
          ), `proposal:${v.proposalId}`)}>Confirm</Button>
        <Button ref={moreRef} dense variant="ghost" aria-label={named("More")} aria-haspopup="menu" aria-expanded={more}
          data-testid="needs-row-verb" data-verb="more" onClick={() => setMore((value) => !value)}>More</Button>
        {more && moreRef.current ? <WorkMenu label={named("More")} x={moreRef.current.getBoundingClientRect().left}
          y={moreRef.current.getBoundingClientRect().bottom} entries={entries} autoFocus onClose={() => setMore(false)}
          returnFocus={() => moreRef.current?.focus()} /> : null}
      </>;
    }
    case "door": {
      const verb = (v.card.lawful_verbs ?? []).find((x) => supportsDoorVerb(x as DoorVerb)) as DoorVerb | undefined;
      const cmd = verb ? commandForDoorVerb(verb) : null;
      if (!verb || !cmd) return null;
      const label = labelFor(verb);
      return (
        <Button dense variant={lead} disabled={busy} aria-label={named(label)} data-testid="needs-row-verb" data-verb="door-verb"
          onClick={() => void act(label, () => apiFetch(cmd.endpoint, { method: "POST", json: cmd.body }),
            `door:${cmd.endpoint}`)}>{label}</Button>
      );
    }
    case "link":
      return (
        <>
          <EgressChip label={urlHost(v.url) || "NOT SET"} scope="cloud" />
          <Button dense variant={lead} aria-label={named("Open")} data-testid="needs-row-verb" data-verb="open"
            onClick={() => window.open(v.url, "_blank", "noopener")}>Open link</Button>
        </>
      );
    case "summarize":
      // The summary route (where the text goes) is disclosed on the meeting,
      // before the run: Summarize opens it there.
      return (
        <>
          <AddToProject meetingId={v.meetingId} />
          <Button dense variant={lead} aria-label={named("Summarize")} data-testid="needs-row-verb" data-verb="summarize"
            onClick={() => openSourceRef(`meeting:${v.meetingId}`)}>Summarize</Button>
        </>
      );
    case "setup":
      return (
        <Button dense variant={lead} aria-label={named(v.verb)} data-testid="needs-row-verb" data-verb="setup"
          onClick={() => (v.key === "unknown"
            ? void refreshNeedsYou(true)
            : openSurfaceOr("open-concierge", "/models", v.key))}>{v.verb}</Button>
      );
    case "repair":
      return (
        <>
        {face.detail?.length ? (
          <Button dense variant="ghost" aria-label={named("Details")} aria-expanded={well === "detail"}
            data-testid="needs-row-verb" data-verb="details"
            onClick={() => onWell(well === "detail" ? null : "detail")}>Details</Button>
        ) : null}
        {/* Astra r1 P2-6: a Retry that re-checks a remote source names where it goes. */}
        {v.verb === "Retry" && v.watchIds?.length && v.host ? (
          <EgressChip label={v.host.toUpperCase()} scope="cloud" />
        ) : null}
        <Button dense variant="secondary" disabled={busy} aria-label={named(v.verb)} data-testid="needs-row-verb" data-verb="repair"
          onClick={() => {
            if (v.verb === "Retry" && v.watchIds?.length) {
              const ids = v.watchIds;
              setBusy(true);
              void recheckSource(face.name, ids).then((r) => { setSourceReceipt(r); setBusy(false); });
            } else if (v.verb === "Retry") void refreshNeedsYou(true);
            // PHILO-17 (needsyou): Settings · Connections, the provider focused.
            else if (v.href.startsWith("/settings")) openSurfaceOr("configure-settings", "/settings", `integration:${v.provider ?? "connections"}`);
            else openProjectRoom(v.projectId);
          }}>{v.verb}</Button>
        </>
      );
    case "arming":
      return (
        <>
          <Button dense variant="danger" aria-label={named(v.refused ? "Retry cancel" : "Cancel")}
            data-testid="needs-row-verb" data-verb={v.refused ? "retry" : "cancel"}
            onClick={() => void cancelArming(v.scheduleId)}>{v.refused ? "Retry" : "Cancel"}</Button>
          <Button dense variant="ghost" aria-label={named("Open")} data-testid="needs-row-verb" data-verb="open"
            onClick={() => openSurfaceOr("review-meetings", "/history")}>Open meetings</Button>
        </>
      );
    case "calendar":
      return (
        <Button dense variant="secondary" aria-label="Connect calendar" data-testid="needs-row-verb" data-verb="connect-calendar"
          onClick={() => openSurfaceOr("configure-settings", "/settings", "meetings")}>Connect calendar</Button>
      );
    case "open": {
      const open = refOpener(v.ref);
      if (!open) return null;
      return (
        <Button dense variant={lead} aria-label={named("Open")} data-testid="needs-row-verb" data-verb="open"
          onClick={() => open()}>Open item</Button>
      );
    }
    default:
      return null;
  }
}

function CommitWell({ face, which, onDone }: { face: NeedFace; which: Well; onDone(): void }) {
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const v = face.verbs;
  const cardId = v.kind === "commitment" || v.kind === "name-owner" ? v.cardId : null;
  const save = async () => {
    const value = draft.trim();
    if (!value || !cardId || busy) return;
    setBusy(true);
    const verb = which === "owner" ? "delegate" : "due";
    const label = which === "owner" ? "Name an owner" : "Set a date";
    try {
      await apiFetch("/api/follow-through/complete", {
        method: "POST",
        json: { card_id: cardId, verb, payload: verb === "delegate" ? { to: value } : { due_at: value } },
      });
      clearWriteFailure(`action-item:${cardId}`);
      onDone();
      void refreshNeedsYou(true);
    } catch (error) {
      reportWriteFailure(label, error, () => void save(), `action-item:${cardId}`);
    } finally {
      setBusy(false);
    }
  };
  return (
    <li
      className="needs-drawer-well"
      role="region"
      aria-label={`${which === "owner" ? "Owner" : "Due"}: ${face.name}`}
      data-testid="needs-well"
      onKeyDown={(event) => {
        if (event.key === "Escape") { event.stopPropagation(); onDone(); }
      }}
    >
      <StringGadget
        label={which === "owner" ? "Owner" : "Due"}
        type={which === "owner" ? "text" : "date"}
        value={draft}
        onChange={setDraft}
        autoFocus
        onKeyDown={(event) => { if (event.key === "Enter") void save(); }}
      />
      <Button dense variant="secondary" disabled={!draft.trim() || busy}
        aria-label={`Save ${which === "owner" ? "owner" : "date"}: ${face.name}`}
        data-testid="needs-well-save" onClick={() => void save()}>Save</Button>
    </li>
  );
}

/** PHILO-17 (needsyou): a source row's detail: each source and the hub's
 *  own reason, one line each. */
function DetailWell({ face }: { face: NeedFace }) {
  return (
    <li className="needs-drawer-well needs-drawer-detail" role="region" aria-label={`Details: ${face.name}`}
      data-testid="needs-detail">
      <ul>
        {(face.detail ?? []).map((line, i) => (
          <li key={`${line.name}:${i}`}>
            <span className="needs-detail-name">{line.name}</span>
            <span className="needs-detail-reason">{line.reason}</span>
          </li>
        ))}
      </ul>
    </li>
  );
}

function NeedRow({ face, primary, projects }: { face: NeedFace; primary: boolean; projects: boolean }) {
  const [well, setWell] = useState<Well | null>(null);
  const project = projects && face.project ? face.project : null;
  return (
    <>
      <NeedsRow
        id={face.id}
        kind={face.kind}
        name={face.name}
        fact={face.fact || undefined}
        factCode={face.factCode}
        factWords={face.factWords}
        lamp={face.lamp}
        sprite={needsRowSprite(face)}
        plate={plateOf(face)}
        // A2b: the Project button is a generic open: the Project's drawer.
        project={project ? { name: project.name, onOpen: () => openProjectRoom(project.id) } : undefined}
        verbs={(
          <>
            {face.moreAsks ? (
              <span className="surface-token" data-testid="needs-more-asks">{`+${face.moreAsks} MORE`}</span>
            ) : null}
            <NeedVerbsView face={face} primary={primary} well={well} onWell={setWell} />
          </>
        )}
      />
      {well === "project" && face.verbs.kind === "confirm" ? <li className="needs-drawer-well"><AddToProject meetingId={face.verbs.meetingId} /></li> : well === "detail" ? <DetailWell face={face} /> : well === "owner" || well === "date" ? <CommitWell face={face} which={well} onDone={() => setWell(null)} /> : null}
    </>
  );
}

interface DoorRead {
  upcoming?: Array<{ title?: string; starts_at?: string; source?: string }>;
  calendar_configured?: boolean;
}

/** Stamp the stable testids and the row-open mark on the species' rows
 *  (NeedsRow takes no testid prop; B1 owns it): `needs-row` on a member,
 *  `needs-source-row` on a source row, `data-opens` where the body opens. */
function useRowMarks(
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
      if (face.verbs.kind === "confirm") li.setAttribute("data-proposal", "true");
      if (faceOpener(face)) li.setAttribute("data-opens", "true");
      else li.removeAttribute("data-opens");
    }
  });
}

/** `Checked just now`, `Checked 4 min ago`, `Checked 09:14`. */
export function checkedWord(at: string | null | undefined, now: Date = new Date()): string | null {
  const d = at ? new Date(at) : null;
  if (!d || Number.isNaN(d.getTime())) return null;
  const minutes = Math.floor((now.getTime() - d.getTime()) / 60000);
  if (minutes < 1) return "Checked just now";
  if (minutes < 60) return `Checked ${minutes} min ago`;
  return `Checked ${hhmm(d)}`;
}

const FILTERS: Array<{ value: NeedsFilter; label: string }> = [
  { value: "ranked", label: "All" },
  { value: "overdue", label: "Overdue" },
  { value: "today", label: "Due today" },
  { value: "not-run", label: "Not run" },
  { value: "no-due", label: "No due date" },
  { value: "waiting", label: "Waiting" },
  { value: "muted", label: "Muted" },
];

/** The Needs-you window body. Phase 16 (the interior kit; the canvas window
 *  "Needs you"): AppHead (`N need you` + the status strip) → FilterBar →
 *  Section `Actions · n` over the Ledger of kind-plated rows → the Foot
 *  (`Ranked hh:mm`). Every row is drawn (HS-200-15: no cap; B11: the head
 *  number is the rows drawn); the Ledger scrolls inside the window and
 *  ScrollHint says so (UX-CANON §B). */
/** The drawer is drawn after this long even when a read is still out (the
 *  Room's cap, roomReads.ts ROOM_READS_CAP_MS). */
const NEEDS_READS_CAP_MS = 8000;

export function NeedsDrawer() {
  const needs = useNeedsYou();
  const flights = useAgentFlights((s) => s.flights);
  const sessions = useAgentFlights((s) => s.sessions);
  const arming = useDesk((s) => s.scheduledArming);
  const [, tick] = useState(0);
  const [door, setDoor] = useState<DoorRead | null>(null);
  const [filter, setFilter] = useState<NeedsFilter>("ranked");
  const listRef = useRef<HTMLDivElement>(null);

  // The countdown ticks while a recording arms.
  const live = Boolean(arming && !arming.outcome);
  useEffect(() => {
    if (!live) return;
    const t = window.setInterval(() => tick((n) => n + 1), 250);
    return () => window.clearInterval(t);
  }, [live]);
  // The Door read: the next event and whether a calendar is connected.
  const computedAt = needs.room?.computedAt ?? null;
  const [doorRead, setDoorRead] = useState(false);
  useEffect(() => {
    let alive = true;
    void apiFetch<DoorRead>("/api/door")
      .then((body) => { if (alive) setDoor(body ?? null); })
      .catch(() => undefined)
      .finally(() => { if (alive) setDoorRead(true); });
    return () => { alive = false; };
  }, [computedAt, needs.count]);
  // PHILO-17 (the desk sweep, sweepreds r2): the drawer is drawn once its
  // first reads end (the hub's answer and the Door read), or at the cap: the
  // strip, the filter and the rows never move under his eye (UX-CANON D; the
  // Room's pattern). Once drawn it stays drawn.
  const needsRead = needs.room !== null || Object.keys(needs.errors).length > 0;
  const [capped, setCapped] = useState(false);
  useEffect(() => {
    const timer = window.setTimeout(() => setCapped(true), NEEDS_READS_CAP_MS);
    return () => window.clearTimeout(timer);
  }, []);
  const [drawn, setDrawn] = useState(false);
  const ready = capped || (needsRead && doorRead);
  useLayoutEffect(() => { if (ready && !drawn) setDrawn(true); }, [ready, drawn]);
  const settling = !(drawn || ready);

  const now = new Date();
  // The rows name their Project when two or more Projects need him (the
  // Chair's rule, HS-200-15: one Project on every row says nothing).
  const multipleProjects = (needs.room?.projects?.length ?? 0) > 1;
  const ctx = { flights, sessions, now, multipleProjects };
  const coverage = readCoverage(
    needs.room?.coverage, needs.room?.complete ?? undefined, Boolean(needs.errors.room),
  );
  // PHILO-15-09 (B11): the calendar is an offer, never a row: the head's
  // number is the number of rows below it. The offer is in the strip.
  // PHILO-15 B60: a source held by quiet hours is drawn after the gaps and
  // is not counted.
  // PHILO-17 (needsyou): the sources of one cause are ONE row (the hub
  // counts the cause once); each source stays in the row's detail.
  const sources = [...groupGaps(coverage.gaps), ...groupGaps(coverage.quiet)].map((rows) => coverageGroupFace(rows, now));
  const noCalendar = Boolean(door && door.calendar_configured === false);
  const outcome = useArmingOutcome();
  const liveArming = arming && !arming.outcome ? arming : null;
  // PHILO-15-09 (B11): the hub counts a recording that arms; the desk draws
  // it with the live countdown when the bus has it, else from the hub's row.
  // A countdown the bus has ended (cancelled, refused) is not drawn again.
  const hubArming = (needs.arming ?? []).filter((row) => row.scheduleId !== arming?.scheduleId);
  const armed = [
    ...(liveArming
      ? [armingFace(
        liveArming, (liveArming.fireAt - now.getTime()) / 1000,
        outcome.refusal?.scheduleId === liveArming.scheduleId ? outcome.refusal.reason : null,
      )]
      : []),
    ...hubArming.map((row) => ({
      ...armingFace({ scheduleId: row.scheduleId, title: row.title }, 0),
      fact: "Arms now",
      lamp: { label: "ARMS", tone: "ask" as const },
    })),
  ];
  // The bus and the hub disagree on a countdown (one started, or ended):
  // read the one number again.
  const hubLists = (id: string) => (needs.arming ?? []).some((row) => row.scheduleId === id);
  const armingStale = liveArming
    ? !hubLists(liveArming.scheduleId)
    : Boolean(arming?.outcome && hubLists(arming.scheduleId));
  useEffect(() => {
    if (armingStale) void refreshNeedsYou(true);
  }, [armingStale]);
  // Board A-5: one list, no group heads. A recording that arms, then the
  // agents (one object, one row), then the rest in the hub's rank order.
  // PHILO-17 (needsyou, walker BLOCKS): the work leads; the sources that
  // could not be read (plumbing) come last.
  // The asks the hub folded into an item are listed, not members: they ride
  // in so their item's row carries them (one object, one row, one count).
  const foldedAsks = needs.unmutedItems
    .filter((item) => item.foldedInto && !item.waiting)
    .map((item) => ({ ref: String(item.ref ?? item.id ?? ""), kind: "attention" as const, item }));
  const faces = [...armed, ...needFaces([...needs.members, ...foldedAsks], ctx), ...sources];
  const asFace = (item: (typeof needs.mutedItems)[number]) =>
    needFace({ ref: String(item.id ?? item.ref ?? ""), kind: "attention", item }, ctx);
  // Listed, never counted: what he waits on someone else for, and the muted.
  const waiting = needs.waitingItems.map(asFace);
  const muted = needs.mutedItems.map(asFace);
  // PHILO-15-09 (B11, the A5 ruling): the head is the hub's one number, the
  // number the Dock badge and the bell say, and it counts every row under
  // it: a member, a source the hub could not read, a recording that arms.
  const head = needsHead(needs.count, needs.complete && coverage.complete);
  // One filled primary on a face with work; a SETUP, repair or offer verb is
  // never filled (the quiet face has none: HS-201-01 ruling 2).
  const primaryId = faces.find((f) => !f.source && f.verbs.kind !== "setup")?.id ?? null;

  // The FilterBar: a filter that matches nothing is not drawn (HS-201-11),
  // except the one that is on (the way back) and Ranked (all).
  const listOf = (f: NeedsFilter) => (f === "waiting" ? waiting : f === "muted" ? muted : faces);
  const matching = (f: NeedsFilter) => listOf(f).filter((face) => passesNeedsFilter(face, f, now));
  const options = FILTERS.filter((o) => o.value === "ranked" || o.value === filter || matching(o.value).length > 0);
  const shown = matching(filter);
  const all = [...faces, ...waiting, ...muted];
  const memberRefs = new Set(faces.filter((f) => !f.uncounted).map((f) => f.memberRef ?? f.id));
  const sourceReceipt = useSourceReceipt((st) => st.receipt);
  useRowMarks(listRef, all, memberRefs);

  const upcoming = door?.upcoming?.[0];
  const next = nextWord(upcoming
    ? { label: upcoming.title, at: upcoming.starts_at }
    : (needs.room?.next as { label?: string; at?: string } | null | undefined));
  const ranked = computedAt ? new Date(computedAt) : null;
  const checked = ranked && !Number.isNaN(ranked.getTime()) ? `Checked ${hhmm(ranked)}` : null;

  // The row body is the Open (the verb Open stays for the keyboard and 393).
  const onRowPress = (event: React.MouseEvent<HTMLDivElement>) => {
    const target = event.target as HTMLElement;
    if (target.closest("button, a, input, textarea, select, .needs-drawer-well")) return;
    const id = target.closest("li.needs-row")?.getAttribute("data-object-id");
    const face = all.find((f) => f.id === id);
    if (face) faceOpener(face)?.();
  };

  const caption = filter === "waiting" ? "Waiting" : filter === "muted" ? "Muted" : "Work";
  const sectionTestId = filter === "waiting" ? "needs-waiting" : filter === "muted" ? "needs-muted" : undefined;
  const listed = filter === "waiting" || filter === "muted";

  return (
    <div className="needs-drawer kit-face" data-testid="needs-drawer"
      data-settling={settling ? "true" : undefined} aria-busy={settling ? true : undefined}>
      {settling ? <div className="needs-drawer-settling"><SurfaceState loading /></div> : null}
      {/* The Chair's head keeps its testids (the Chair-ready signal of the
          glass rigs): the drawer's head IS the Chair's display. */}
      <AppHead fact={head} data-testid="arrival-headline" factTestId="arrival-display">
        <StatusStrip
          items={[
            next ? { key: "next", text: <span data-testid="needs-next">{next}</span> } : null,
            // The offer is ONE token: its word and its verb (PHILO-15-09 B11:
            // an offer, never a row).
            noCalendar
              ? {
                key: "no-calendar",
                verb: (
                  <span className="needs-calendar-offer" data-testid="needs-no-calendar">
                    NO CALENDAR
                    <Button dense variant="ghost" aria-label="Connect calendar" data-testid="needs-row-verb" data-verb="connect-calendar"
                      onClick={() => openSurfaceOr("configure-settings", "/settings", "meetings")}>Connect calendar</Button>
                  </span>
                ),
              }
              : null,
          ]}
        />
      </AppHead>
      {coverage.expected > 0 ? <Disclosure label={`${coverage.available} of ${coverage.expected} available`} ariaLabel="Coverage">
        <StatusStrip items={[{ lamp: coverage.complete ? "ok" : "warn", text: coverage.complete ? "All sources checked" : "Sources need a check" }]} />
        {coverage.gaps.length + coverage.quiet.length > 0 ? <ul className="needs-coverage-details">
          {[...coverage.gaps, ...coverage.quiet].map((source, index) => <li key={index}>{source.label || source.source_id}</li>)}
        </ul> : null}
      </Disclosure> : null}
      {faces.length + waiting.length + muted.length > 0 ? (
        <FilterBar
          label="Needs you filter"
          data-testid="needs-filter"
          options={options}
          value={filter}
          onChange={(next) => setFilter(next as NeedsFilter)}
        />
      ) : null}
      {/* A press on a row body opens it; each row's verbs carry the keyboard. */}
      <div ref={listRef} onClick={onRowPress} data-testid="needs-list" className="needs-drawer-list">
        <ScrollHint axis="y" scrollRef={listRef}>
          {shown.length > 0 ? (
            <SurfaceSection label={caption} count={shown.length || null} data-testid={sectionTestId}
            className={filter === "muted" ? "needs-drawer-muted" : undefined}>
              <NeedsList label={listed ? caption : "Needs you"}>
                {shown.map((face) => (
                  <NeedRow key={face.id} face={face} primary={!listed && face.id === primaryId} projects={multipleProjects} />
                ))}
              </NeedsList>
            </SurfaceSection>
          ) : null}
        </ScrollHint>
      </div>
      <SurfaceFooter
        receipt={
          outcome.receipt ? (
            <span className="surface-footer-receipt-line" role="status" data-testid="needs-receipt">
              {outcome.receipt}
            </span>
          ) : sourceReceipt ? (
            <span className="surface-footer-receipt-line" role="status" data-testid="needs-source-receipt"
              data-tone={sourceReceipt.tone === "fail" ? "danger" : undefined}>
              {sourceReceipt.text}
            </span>
          ) : checked ? (
            <span className="surface-footer-receipt-line" data-testid="needs-checked">{checked}</span>
          ) : null
        }
      />
    </div>
  );
}
