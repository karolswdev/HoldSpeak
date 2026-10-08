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
 *  line and never reads UNASSIGNED. Hand to agent is not a Needs row verb
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
import { openDrawer } from "../drawer/store";
import { openCoderSession, openProjectRoom, openSurfaceOr } from "../shell";
import { useDesk } from "../store";
import { EgressChip, StringGadget } from "../surface";
import { openSourceRef } from "../surface/citations";
import { NeedsList, NeedsRow } from "../surface/objects";
import { spriteUrl } from "../sprites";
import { readCoverage } from "../coverage";
import {
  armingFace,
  coverageFace,
  needFace,
  needFaces,
  needsHead,
  nextWord,
  urlHost,
  type NeedFace,
} from "./needsFace";
import { cancelArming, useArmingOutcome } from "./arming";
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

type Well = "owner" | "date";

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
            onClick={() => openCoderSession(v.sessionKey)}>Open</Button>
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
            <Button dense variant={lead} aria-label={named("Open the agent's lane")} data-testid="needs-row-verb" data-verb="open"
              onClick={() => openCoderSession(v.sessionKey)}>Open</Button>
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
          onClick={() => openCoderSession(v.sessionKey)}>Open</Button>
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
    case "confirm":
      return (
        <>
          {/* A2b: the explicit Room path, with this proposal selected (the
              row body opens the same; the verb carries the keyboard). */}
          {v.projectId ? (
            <Button dense variant="ghost" aria-label={named("Room")} data-testid="needs-row-verb" data-verb="room"
              onClick={() => openProjectProposal(v.projectId, v.proposalId)}>Room</Button>
          ) : null}
          {/* PHILO-15 16 (B37): a meeting in no Project joins one here. */}
          {!v.projectId && v.meetingId ? <AddToProject meetingId={v.meetingId} /> : null}
          {/* PHILO-15 08 (B03): three verbs with words, Project or not. */}
          <Button dense variant="ghost" disabled={busy} aria-label={named("Decline")} data-testid="needs-row-verb" data-verb="decline"
            onClick={() => void act("Decline", () => apiFetch(
              `/api/proposals/${encodeURIComponent(v.proposalId)}/dismiss`, { method: "POST" },
            ), `proposal:${v.proposalId}`)}>Decline</Button>
          <Button dense variant="ghost" disabled={busy} aria-label={named("Defer")} data-testid="needs-row-verb" data-verb="defer"
            onClick={() => void act("Defer", () => apiFetch(
              `/api/proposals/${encodeURIComponent(v.proposalId)}/defer`, { method: "POST", json: {} },
            ), `proposal:${v.proposalId}`)}>Defer</Button>
          <Button dense variant={lead} disabled={busy} aria-label={named("Confirm")} data-testid="needs-row-verb" data-verb="confirm"
            onClick={() => void act("Confirm", () => apiFetch(
              `/api/proposals/${encodeURIComponent(v.proposalId)}/confirm`, { method: "POST" },
            ), `proposal:${v.proposalId}`)}>Confirm</Button>
        </>
      );
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
            onClick={() => window.open(v.url, "_blank", "noopener")}>Open</Button>
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
            : openSurfaceOr("open-concierge", "/models"))}>{v.verb}</Button>
      );
    case "repair":
      return (
        <Button dense variant="secondary" disabled={busy} aria-label={named(v.verb)} data-testid="needs-row-verb" data-verb="repair"
          onClick={() => {
            if (v.verb === "Retry" && v.watchIds?.length) {
              const ids = v.watchIds;
              setBusy(true);
              void recheckSource(face.name, ids).then((r) => { setSourceReceipt(r); setBusy(false); });
            } else if (v.verb === "Retry") void refreshNeedsYou(true);
            else if (v.href.startsWith("/settings")) openSurfaceOr("configure-settings", "/settings", "connections");
            else openProjectRoom(v.projectId);
          }}>{v.verb}</Button>
      );
    case "arming":
      return (
        <>
          <Button dense variant="danger" aria-label={named(v.refused ? "Retry cancel" : "Cancel")}
            data-testid="needs-row-verb" data-verb={v.refused ? "retry" : "cancel"}
            onClick={() => void cancelArming(v.scheduleId)}>{v.refused ? "Retry" : "Cancel"}</Button>
          <Button dense variant="ghost" aria-label={named("Open")} data-testid="needs-row-verb" data-verb="open"
            onClick={() => openSurfaceOr("review-meetings", "/history")}>Open</Button>
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
          onClick={() => open()}>Open</Button>
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
        lamp={face.lamp}
        sprite={needsRowSprite(face)}
        kindWord={face.kindWord}
        // A2b: the Project button is a generic open: the Project's drawer.
        project={project ? { name: project.name, onOpen: () => openDrawer(project.id) } : undefined}
        verbs={(
          <>
            {face.moreAsks ? (
              <span className="surface-token" data-testid="needs-more-asks">{`+${face.moreAsks} MORE`}</span>
            ) : null}
            <NeedVerbsView face={face} primary={primary} well={well} onWell={setWell} />
          </>
        )}
      />
      {well ? <CommitWell face={face} which={well} onDone={() => setWell(null)} /> : null}
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
      if (faceOpener(face)) li.setAttribute("data-opens", "true");
      else li.removeAttribute("data-opens");
    }
  });
}

/** The Needs-you window body. */
export function NeedsDrawer() {
  const needs = useNeedsYou();
  const flights = useAgentFlights((s) => s.flights);
  const sessions = useAgentFlights((s) => s.sessions);
  const arming = useDesk((s) => s.scheduledArming);
  const [, tick] = useState(0);
  const [door, setDoor] = useState<DoorRead | null>(null);
  const [showMuted, setShowMuted] = useState(false);
  const [showWaiting, setShowWaiting] = useState(false);
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
  useEffect(() => {
    let alive = true;
    void apiFetch<DoorRead>("/api/door")
      .then((body) => { if (alive) setDoor(body ?? null); })
      .catch(() => undefined);
    return () => { alive = false; };
  }, [computedAt, needs.count]);

  const now = new Date();
  // The rows name their Project when two or more Projects need him (the
  // Chair's rule, HS-200-15: one Project on every row says nothing).
  const multipleProjects = (needs.room?.projects?.length ?? 0) > 1;
  const ctx = { flights, sessions, now, multipleProjects };
  const coverage = readCoverage(
    needs.room?.coverage, needs.room?.complete ?? undefined, Boolean(needs.errors.room),
  );
  // PHILO-15-09 (B11): the calendar is an offer, never a row: the head's
  // number is the number of rows below it. The offer is in the foot.
  // PHILO-15 B60: a source held by quiet hours is drawn after the gaps and
  // is not counted.
  const sources = [...coverage.gaps, ...coverage.quiet].map((gap) => coverageFace(gap, now));
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
  // Board A-5: one list, no group heads. The sources lead (HS-200-15:
  // coverage above the answer), then a recording that arms, then the agents
  // (one object, one row), then the rest in the hub's rank order.
  // The asks the hub folded into an item are listed, not members: they ride
  // in so their item's row carries them (one object, one row, one count).
  const foldedAsks = needs.unmutedItems
    .filter((item) => item.foldedInto && !item.waiting)
    .map((item) => ({ ref: String(item.ref ?? item.id ?? ""), kind: "attention" as const, item }));
  const faces = [...sources, ...armed, ...needFaces([...needs.members, ...foldedAsks], ctx)];
  const asFace = (item: (typeof needs.mutedItems)[number]) =>
    needFace({ ref: String(item.id ?? item.ref ?? ""), kind: "attention", item }, ctx);
  // Listed, never counted: what he waits on someone else for, and the muted.
  const waiting = needs.waitingItems.map(asFace);
  const muted = needs.mutedItems.map(asFace);
  // PHILO-15-09 (B11, the A5 ruling): the head is the hub's one number, the
  // number the Dock badge and the bell say, and it counts every row under
  // it: a member, a source the hub could not read, a recording that arms.
  // The calendar offer is in the foot.
  const head = needsHead(needs.count, needs.complete && coverage.complete);
  // One filled primary on a face with work; a SETUP, repair or offer verb is
  // never filled (the quiet face has none: HS-201-01 ruling 2).
  const primaryId = faces.find((f) => !f.source && f.verbs.kind !== "setup")?.id ?? null;
  const all = [...faces, ...(showWaiting ? waiting : []), ...(showMuted ? muted : [])];
  const memberRefs = new Set(faces.filter((f) => !f.uncounted).map((f) => f.memberRef ?? f.id));
  const sourceReceipt = useSourceReceipt((st) => st.receipt);
  useRowMarks(listRef, all, memberRefs);

  const upcoming = door?.upcoming?.[0];
  const next = nextWord(upcoming
    ? { label: upcoming.title, at: upcoming.starts_at }
    : (needs.room?.next as { label?: string; at?: string } | null | undefined));

  // The footer tokens are drawn only over a list that holds rows (A.8).
  const waitingRows = waiting.length;
  const mutedRows = muted.length;
  const waitingWord = waitingRows > 0 ? `Waiting · ${waitingRows}` : null;
  const mutedWord = mutedRows > 0 ? `Muted · ${mutedRows}` : null;

  // The row body is the Open (the verb Open stays for the keyboard and 393).
  const onRowPress = (event: React.MouseEvent<HTMLDivElement>) => {
    const target = event.target as HTMLElement;
    if (target.closest("button, a, input, textarea, select, .needs-drawer-well")) return;
    const id = target.closest("li.needs-row")?.getAttribute("data-object-id");
    const face = all.find((f) => f.id === id);
    if (face) faceOpener(face)?.();
  };

  return (
    <div className="needs-drawer" data-testid="needs-drawer">
      {/* The Chair's head keeps its testids (the Chair-ready signal of the
          glass rigs): the drawer's head IS the Chair's display. */}
      <div className="needs-drawer-headline" data-testid="arrival-headline">
        <h2 className="surface-display needs-drawer-head" data-testid="arrival-display">{head}</h2>
      </div>
      {outcome.receipt ? (
        <p className="surface-receipt-line needs-drawer-receipt" role="status" data-testid="needs-receipt">
          {outcome.receipt}
        </p>
      ) : null}
      {sourceReceipt ? (
        <p className="surface-receipt-line needs-drawer-receipt" role="status" data-testid="needs-source-receipt"
          data-tone={sourceReceipt.tone}>
          {sourceReceipt.text}
        </p>
      ) : null}
      {/* A press on a row body opens it; each row's verbs carry the keyboard. */}
      <div ref={listRef} onClick={onRowPress} data-testid="needs-list">
        {faces.length > 0 ? (
          <NeedsList label="Needs you">
            {faces.map((face) => (
              <NeedRow key={face.id} face={face} primary={face.id === primaryId} projects={multipleProjects} />
            ))}
          </NeedsList>
        ) : null}
        {showWaiting && waiting.length > 0 ? (
          <div className="needs-drawer-muted" data-testid="needs-waiting">
            <NeedsList label="Waiting">
              {waiting.map((face) => <NeedRow key={face.id} face={face} primary={false} projects={multipleProjects} />)}
            </NeedsList>
          </div>
        ) : null}
        {showMuted && muted.length > 0 ? (
          <div className="needs-drawer-muted" data-testid="needs-muted">
            <NeedsList label="Muted">
              {muted.map((face) => <NeedRow key={face.id} face={face} primary={false} projects={multipleProjects} />)}
            </NeedsList>
          </div>
        ) : null}
      </div>
      {next || noCalendar || muted.length > 0 || waiting.length > 0 ? (
        <div className="needs-drawer-foot">
          <span className="needs-drawer-offer">
            {next ? <span className="needs-drawer-next" data-testid="needs-next">{next}</span> : null}
            {noCalendar ? (
              <span className="needs-drawer-next needs-drawer-offer" data-testid="needs-no-calendar">
                <span className="surface-token">NO CALENDAR</span>
                <Button dense variant="ghost" aria-label="Connect calendar" data-testid="needs-row-verb" data-verb="connect-calendar"
                  onClick={() => openSurfaceOr("configure-settings", "/settings", "meetings")}>Connect calendar</Button>
              </span>
            ) : null}
          </span>
          <span className="object-verbs">
          {waiting.length > 0 ? (
            <Button dense variant="ghost" aria-expanded={showWaiting} data-testid="needs-waiting-toggle"
              onClick={() => setShowWaiting((open) => !open)}>
              {waitingWord}
            </Button>
          ) : null}
          {muted.length > 0 ? (
            <Button dense variant="ghost" aria-expanded={showMuted} data-testid="needs-muted-toggle"
              onClick={() => setShowMuted((open) => !open)}>
              {mutedWord}
            </Button>
          ) : null}
          </span>
        </div>
      ) : null}
    </div>
  );
}
