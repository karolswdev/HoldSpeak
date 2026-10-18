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
import { AppHead, EgressChip, ScrollHint, StatusStrip, StringGadget, SurfaceFooter, SurfaceSection, SurfaceState } from "../surface";
import { openSourceRef } from "../surface/citations";
import { NeedsList, NeedsRow } from "../surface/objects";
import { spriteUrl } from "../sprites";
import { groupGaps, readCoverage } from "../coverage";
import {
  armingFace,
  chipsOn,
  coverageGroupFace,
  needFace,
  needFaces,
  needsHead,
  nextWord,
  NO_CHIPS,
  passesChips,
  plateOf,
  urlHost,
  type NeedFace,
  type NeedsChips,
} from "./needsFace";
import { NoteSendWells } from "../documentSendsLazy";
import { wireDate } from "../surface/format";
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

type Well = "owner" | "date" | "detail" | "project" | "nudge" | "decide" | "whose";

/** Betterment D3: Drop says what went and offers Undo for 8 s. */
type Dropped = { name: string; undo(): Promise<unknown>; id: number };
const UNDO_MS = 8000;
export const useDropped = create<{ dropped: Dropped | null; set(d: Dropped | null): void }>(
  (setState) => ({ dropped: null, set: (dropped) => setState({ dropped }) }),
);
let dropSeq = 0;

/** Drop, then the Undo receipt in the foot (8 s). */
export function offerUndo(name: string, undo: () => Promise<unknown>): void {
  const id = ++dropSeq;
  useDropped.getState().set({ name, undo, id });
  window.setTimeout(() => {
    if (useDropped.getState().dropped?.id === id) useDropped.getState().set(null);
  }, UNDO_MS);
}

const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** `Thu 22 Oct`: a due day as the rows say it. */
export function dayWord(iso: string | null | undefined): string {
  const d = iso ? wireDate(iso) : null;
  return d ? `${DAYS[d.getDay()]} ${d.getDate()} ${MONTHS[d.getMonth()]}` : "";
}

/** Betterment D2: the short message Nudge drafts. He reads it, can change
 *  it in the note, and presses Send himself. */
export function nudgeText(task: string, person: string, due: string | null | undefined): string {
  const first = person.trim().split(/\s+/)[0] || "Hi";
  const when = dayWord(due);
  return `${first}, is "${task}" on track${when ? ` for ${when}` : ""}? Tell me if you need help.`;
}

/** Later: the row comes back tomorrow (the follow-through snooze is by day). */
export function tomorrowDay(now: Date = new Date()): string {
  const d = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

/** One follow-through verb on an action item (the hub's one write path). */
function followThrough(cardId: string, verb: string, payload: Record<string, unknown> = {}) {
  return apiFetch("/api/follow-through/complete", { method: "POST", json: { card_id: cardId, verb, payload } });
}

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
    case "review": {
      const label = v.label ?? "Review";
      return (
        <Button dense variant={lead} aria-label={named(label)} data-testid="needs-row-verb"
          data-verb={label === "Decide" ? "decide" : "review"}
          onClick={() => refOpener(v.ref)?.()}>{label}</Button>
      );
    }
    case "work": {
      const opener = faceOpener(face);
      const key = `action-item:${v.cardId}`;
      // Betterment D3: Drop removes it; Undo (8 s) opens it again.
      const drop = () => act("Drop", async () => {
        await followThrough(v.cardId, "dismiss");
        offerUndo(face.name, () => followThrough(v.cardId, "reopen"));
      }, key);
      const entries: WorkMenuEntry[] = [
        ...(opener ? [{ type: "item" as const, id: "open", label: "Open", onSelect: opener }] : []),
        ...(v.direction === "theirs"
          ? [{ type: "item" as const, id: "done", label: "Done", ghost: busy ? "Busy" : undefined,
            onSelect: () => void act("Done", () => followThrough(v.cardId, "done"), key) }]
          : []),
        ...(v.next === "set_date"
          ? [{ type: "item" as const, id: "date", label: "Set a date", onSelect: () => onWell("date") }]
          : []),
        { type: "item", id: "later", label: "Later", ghost: busy ? "Busy" : undefined,
          onSelect: () => void act("Later", () => followThrough(v.cardId, "snooze", { until: tomorrowDay() }), key) },
        ...(face.arrival ? [] : [{ type: "item" as const, id: "drop", label: "Drop", ghost: busy ? "Busy" : undefined,
          onSelect: () => void drop() }]),
      ];
      return <>
        {v.direction === "theirs" ? (
          <Button dense variant={lead} aria-label={named("Nudge")} aria-expanded={well === "nudge"}
            data-testid="needs-row-verb" data-verb="nudge"
            onClick={() => onWell(well === "nudge" ? null : "nudge")}>Nudge</Button>
        ) : (
          <Button dense variant={lead} disabled={busy} aria-label={named("Done")} data-testid="needs-row-verb" data-verb="done"
            onClick={() => void act("Done", () => followThrough(v.cardId, "done"), key)}>Done</Button>
        )}
        {face.arrival ? (
          <Button dense variant="ghost" disabled={busy} aria-label={named("Drop")} data-testid="needs-row-verb" data-verb="drop"
            onClick={() => void drop()}>Drop</Button>
        ) : null}
        <Button ref={moreRef} dense variant="ghost" aria-label={named("More")} aria-haspopup="menu" aria-expanded={more}
          data-testid="needs-row-verb" data-verb="more" onClick={() => setMore((value) => !value)}>More</Button>
        {more && moreRef.current ? <WorkMenu label={named("More")} x={moreRef.current.getBoundingClientRect().left}
          y={moreRef.current.getBoundingClientRect().bottom} entries={entries} autoFocus onClose={() => setMore(false)}
          returnFocus={() => moreRef.current?.focus()} /> : null}
      </>;
    }
    case "whose":
      return (
        <Button dense variant={lead} aria-label={named("Whose?")} aria-expanded={well === "whose"}
          data-testid="needs-row-verb" data-verb="whose"
          onClick={() => onWell(well === "whose" ? null : "whose")}>Whose?</Button>
      );
    case "decide":
      return (
        <Button dense variant={lead} aria-label={named("Decide")} aria-expanded={well === "decide"}
          data-testid="needs-row-verb" data-verb="decide"
          onClick={() => onWell(well === "decide" ? null : "decide")}>Decide</Button>
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
  const cardId = v.kind === "commitment" || v.kind === "name-owner" || v.kind === "work" ? v.cardId : null;
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

/** Betterment D2: Decide, in place: Accept writes the decision (the
 *  proposal's Confirm), Not now holds it back (Defer), Drop removes it
 *  (Decline). Open item shows it where it came from. */
function DecideWell({ face, onDone }: { face: NeedFace; onDone(): void }) {
  const [busy, setBusy] = useState(false);
  const v = face.verbs;
  if (v.kind !== "decide") return null;
  const opener = faceOpener(face);
  const run = async (label: string, path: string, json?: unknown): Promise<void> => {
    if (busy) return Promise.reject(new Error("busy"));
    setBusy(true);
    const key = `proposal:${v.proposalId}`;
    try {
      await apiFetch(`/api/proposals/${encodeURIComponent(v.proposalId)}/${path}`, { method: "POST", ...(json ? { json } : {}) });
      clearWriteFailure(key);
      onDone();
      void refreshNeedsYou(true);
    } catch (error) {
      reportWriteFailure(label, error, () => void run(label, path, json), key);
      throw error;
    } finally {
      setBusy(false);
    }
  };
  return (
    <li className="needs-drawer-well needs-drawer-decide" role="region" aria-label={`Decide: ${face.name}`}
      data-testid="needs-decide"
      onKeyDown={(event) => { if (event.key === "Escape") { event.stopPropagation(); onDone(); } }}>
      <Button dense variant="primary" disabled={busy} aria-label={`Accept: ${face.name}`} data-testid="needs-decide-accept"
        autoFocus onClick={() => void run("Accept", "confirm").catch(() => undefined)}>Accept</Button>
      <Button dense variant="secondary" disabled={busy} aria-label={`Not now: ${face.name}`}
        onClick={() => void run("Not now", "defer", {}).catch(() => undefined)}>Not now</Button>
      <Button dense variant="ghost" disabled={busy} aria-label={`Drop: ${face.name}`}
        onClick={() => void run("Drop", "dismiss").then(() => offerUndo(face.name, () => apiFetch(
          `/api/proposals/${encodeURIComponent(v.proposalId)}/restore`, { method: "POST" }))).catch(() => undefined)}>Drop</Button>
      {opener ? <Button dense variant="ghost" aria-label={`Open item: ${face.name}`} onClick={() => opener()}>Open item</Button> : null}
    </li>
  );
}

/** Betterment D3: Whose? The meeting's speakers, one press each: the press
 *  keeps the promise with that owner (Confirm with the owner). */
function WhoseWell({ face, onDone }: { face: NeedFace; onDone(): void }) {
  const [busy, setBusy] = useState(false);
  const v = face.verbs;
  if (v.kind !== "whose") return null;
  const keep = async (owner: string) => {
    if (busy) return;
    setBusy(true);
    const key = `proposal:${v.proposalId}`;
    try {
      await apiFetch(`/api/proposals/${encodeURIComponent(v.proposalId)}/confirm`, { method: "POST", json: { owner } });
      clearWriteFailure(key);
      onDone();
      void refreshNeedsYou(true);
    } catch (error) {
      reportWriteFailure("Whose?", error, () => void keep(owner), key);
    } finally {
      setBusy(false);
    }
  };
  return (
    <li className="needs-drawer-well" role="region" aria-label={`Whose: ${face.name}`} data-testid="needs-whose"
      onKeyDown={(event) => { if (event.key === "Escape") { event.stopPropagation(); onDone(); } }}>
      {v.speakers.map((speaker, i) => (
        <Button key={speaker} dense variant={i === 0 ? "secondary" : "ghost"} disabled={busy} autoFocus={i === 0}
          aria-label={`${speaker}: ${face.name}`} onClick={() => void keep(speaker)}>{speaker}</Button>
      ))}
    </li>
  );
}

/** Betterment D2: Nudge prepares; it never sends. The drafted message is
 *  kept as a note and its Send well opens here, on his saved destination for
 *  that person when exactly one has the person's name. He presses Send. */
function NudgeWell({ face }: { face: NeedFace }) {
  const v = face.verbs;
  const [note, setNote] = useState<{ id: string; title: string } | null>(null);
  const [failed, setFailed] = useState(false);
  const started = useRef(false);
  const person = v.kind === "work" ? v.person : "";
  const text = v.kind === "work" ? nudgeText(face.name, person, v.due) : "";
  useEffect(() => {
    if (started.current || v.kind !== "work") return;
    started.current = true;
    const title = `Nudge: ${face.name}`;
    void (async () => {
      try {
        const made = await apiFetch<{ note?: { id?: string } }>("/api/notes", {
          method: "POST", json: { title, body_markdown: text, tags: ["nudge"] },
        });
        const id = String(made.note?.id ?? "");
        if (!id) { setFailed(true); return; }
        const first = person.split(/\s+/)[0]?.toLowerCase();
        try {
          const read = await apiFetch<{ destinations?: Array<{ id: string; name: string; state?: string }> }>("/api/channels/destinations");
          const theirs = (read?.destinations ?? []).filter((d) => d.state !== "parked" && first && d.name.toLowerCase().includes(first));
          if (theirs.length === 1) {
            const { pickDestination } = await import("../surface/send");
            pickDestination(`note:${id}`, theirs[0].id);
          }
        } catch { /* no saved destination read: he picks one in the well */ }
        setNote({ id, title });
      } catch (error) {
        setFailed(true);
        reportWriteFailure("Nudge", error);
      }
    })();
  }, [face.name, person, text, v.kind]);
  return (
    <li className="needs-drawer-well needs-drawer-nudge" role="region" aria-label={`Nudge: ${face.name}`}
      data-testid="needs-nudge">
      <p className="needs-nudge-text" data-testid="needs-nudge-text">{text}</p>
      {failed ? <SurfaceState error="The message was not prepared." />
        : note ? <NoteSendWells id={note.id} title={note.title} />
          : <SurfaceState loading />}
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

export function NeedRow({ face, primary, projects }: { face: NeedFace; primary: boolean; projects: boolean }) {
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
      {well === "project" && face.verbs.kind === "confirm" ? <li className="needs-drawer-well"><AddToProject meetingId={face.verbs.meetingId} /></li>
        : well === "detail" ? <DetailWell face={face} />
          : well === "nudge" ? <NudgeWell face={face} />
            : well === "decide" ? <DecideWell face={face} onDone={() => setWell(null)} />
              : well === "whose" ? <WhoseWell face={face} onDone={() => setWell(null)} />
              : well === "owner" || well === "date" ? <CommitWell face={face} which={well} onDone={() => setWell(null)} /> : null}
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

/** Betterment D2: one chip of the row. Pressed = on; a second press clears
 *  it. The count is what the list shows with the chip on. */
function Chip({ label, count, on, onPress, menu, testId }: {
  label: string;
  count?: number | null;
  on: boolean;
  onPress(event: React.MouseEvent<HTMLButtonElement>): void;
  menu?: boolean;
  testId: string;
}) {
  return (
    <Button dense variant={on ? "secondary" : "ghost"} className="surface-filter-token needs-chip"
      data-filter-active={on || undefined} aria-pressed={menu ? undefined : on}
      aria-haspopup={menu ? "menu" : undefined} data-testid={testId}
      aria-label={count != null ? `${label} · ${count}` : label}
      onClick={onPress}>
      {label}{count != null ? <span className="needs-chip-count">{count}</span> : null}{menu && !on ? " ▾" : ""}
    </Button>
  );
}

type Pick = { key: string; name: string; count: number };

/** Betterment D2: the chips over the one list (Mine, They owe me, To decide,
 *  This week, a person, a Project; More holds the muted projects). Chips
 *  combine; one at zero is not drawn unless it is on. At the phone width the
 *  row scrolls in one line. */
function NeedsChipRow({ chips, setChips, counts, people, projects, muted, showMuted, setShowMuted }: {
  chips: NeedsChips;
  setChips(next: NeedsChips): void;
  counts: { mine: number; theirs: number; decide: number; week: number };
  people: Pick[];
  projects: Pick[];
  muted: number;
  showMuted: boolean;
  setShowMuted(next: boolean): void;
}) {
  const [menu, setMenu] = useState<{ kind: "person" | "project" | "more"; x: number; y: number } | null>(null);
  const anchors = useRef<Record<string, HTMLButtonElement | null>>({});
  const at = (kind: "person" | "project" | "more", event: React.MouseEvent<HTMLButtonElement>) => {
    const box = event.currentTarget.getBoundingClientRect();
    anchors.current[kind] = event.currentTarget;
    setMenu({ kind, x: box.left, y: box.bottom });
  };
  const direction = (value: "mine" | "theirs" | "decide") =>
    setChips({ ...chips, direction: chips.direction === value ? null : value });
  const person = people.find((p) => p.key === chips.person);
  const project = projects.find((p) => p.key === chips.project);
  const entries: WorkMenuEntry[] = !menu ? [] : menu.kind === "more"
    ? [{ type: "item", id: "muted", label: `Muted projects · ${muted}`, checked: showMuted, onSelect: () => setShowMuted(!showMuted) }]
    : (menu.kind === "person" ? people : projects).map((p) => ({
      type: "item" as const, id: `${menu.kind}-${p.key}`, label: `${p.name} · ${p.count}`,
      onSelect: () => setChips({ ...chips, [menu.kind]: p.key }),
    }));
  const directions: Array<["mine" | "theirs" | "decide", string, number]> = [
    ["mine", "Mine", counts.mine], ["theirs", "They owe me", counts.theirs], ["decide", "To decide", counts.decide],
  ];
  return (
    <div className="kit-filterbar needs-chips" data-testid="needs-filter">
      <span className="surface-filter-tokens needs-chip-row" role="group" aria-label="Needs you filter">
        {directions.map(([value, label, count]) => (count > 0 || chips.direction === value ? (
          <Chip key={value} label={label} count={count > 0 ? count : null} on={chips.direction === value} testId={`needs-chip-${value}`}
            onPress={() => direction(value)} />
        ) : null))}
        {counts.week > 0 || chips.week ? (
          <Chip label="This week" count={counts.week > 0 ? counts.week : null} on={chips.week} testId="needs-chip-week"
            onPress={() => setChips({ ...chips, week: !chips.week })} />
        ) : null}
        {people.length > 0 || person ? (
          <Chip label={person?.name ?? "Person"} on={Boolean(person)} menu testId="needs-chip-person"
            onPress={(event) => (person ? setChips({ ...chips, person: null }) : at("person", event))} />
        ) : null}
        {projects.length > 1 || project ? (
          <Chip label={project?.name ?? "Project"} on={Boolean(project)} menu testId="needs-chip-project"
            onPress={(event) => (project ? setChips({ ...chips, project: null }) : at("project", event))} />
        ) : null}
        {muted > 0 ? (
          <Chip label="More" on={showMuted} menu testId="needs-chip-more" onPress={(event) => at("more", event)} />
        ) : null}
      </span>
      {menu ? (
        <WorkMenu label={menu.kind === "person" ? "Person" : menu.kind === "project" ? "Project" : "More"}
          x={menu.x} y={menu.y} entries={entries} autoFocus onClose={() => setMenu(null)}
          returnFocus={() => anchors.current[menu.kind]?.focus()} />
      ) : null}
    </div>
  );
}

/** The person and Project choices of the rows, with how many rows each has. */
function picksOf(faces: readonly NeedFace[], key: (f: NeedFace) => [string, string] | null): Pick[] {
  const out = new Map<string, Pick>();
  for (const face of faces) {
    const hit = key(face);
    if (!hit) continue;
    const [k, name] = hit;
    const row = out.get(k) ?? { key: k, name, count: 0 };
    row.count += 1;
    out.set(k, row);
  }
  return [...out.values()].sort((a, b) => a.name.localeCompare(b.name));
}

/** The Needs-you window body. Phase 16 (the interior kit; the canvas window
 *  "Needs you"): AppHead (`N need you` + the status strip) → FilterBar →
 *  Section `Actions · n` over the Ledger of kind-plated rows → the Foot
 *  (`Ranked hh:mm`). Every row is drawn (HS-200-15: no cap; B11: the head
 *  number is the rows drawn); the Ledger scrolls inside the window and
 *  ScrollHint says so (UX-CANON §B). */
/** The drawer is drawn after this long even when a read is still out (the
 *  Room's cap, roomReads.ts ROOM_READS_CAP_MS). */
const NEEDS_READS_CAP_MS = 8000;

/** The one list's rows, as both of its faces draw them (the Needs-you
 *  window and Today's top, Betterment daily D4): the recording that arms,
 *  the hub's members (with the asks folded into them), the rows the count
 *  leaves out, and the sources that could not be read. One read, one rank. */
export function useNeedFaces() {
  const needs = useNeedsYou();
  const flights = useAgentFlights((s) => s.flights);
  const sessions = useAgentFlights((s) => s.sessions);
  const arming = useDesk((s) => s.scheduledArming);
  const [, tick] = useState(0);

  // The countdown ticks while a recording arms.
  const live = Boolean(arming && !arming.outcome);
  useEffect(() => {
    if (!live) return;
    const t = window.setInterval(() => tick((n) => n + 1), 250);
    return () => window.clearInterval(t);
  }, [live]);

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
  // Betterment D1: a row the one count rule leaves out (a promise not kept
  // yet, what a person owes, his own work due on a later day) is listed
  // after the counted rows, marked not counted. Betterment D2: what a person
  // owes is in the one list too (They owe me), never a list of its own.
  const listedOnly = needs.unmutedItems
    .filter((item) => (item.counted === false || item.waiting) && !item.foldedInto)
    .map((item) => ({ ref: String(item.ref ?? item.id ?? ""), kind: "attention" as const, item }));
  const work = [
    ...armed,
    ...needFaces([...needs.members, ...foldedAsks], ctx),
    ...needFaces(listedOnly, ctx).map((face) => ({ ...face, uncounted: true })),
  ];
  const faces = [...work, ...sources];
  return { needs, now, ctx, coverage, multipleProjects, outcome, work, faces };
}

/** Betterment D3: the Undo receipt of the last Drop (8 s), in the foot of
 *  every face that draws the rows (the Needs-you window, Today). */
export function NeedsDroppedReceipt() {
  const dropped = useDropped((st) => st.dropped);
  if (!dropped) return null;
  return (
    <span className="surface-footer-receipt-line needs-dropped" role="status" data-testid="needs-dropped">
      {`Dropped · ${dropped.name}`}
      <Button dense variant="secondary" aria-label={`Undo: ${dropped.name}`} data-testid="needs-undo"
        onClick={() => {
          useDropped.getState().set(null);
          void dropped.undo().then(() => refreshNeedsYou(true)).catch((error) =>
            reportWriteFailure("Undo", error, () => void dropped.undo()));
        }}>Undo</Button>
    </span>
  );
}

export function NeedsDrawer() {
  const { needs, now, ctx, coverage, multipleProjects, outcome, faces } = useNeedFaces();
  const [door, setDoor] = useState<DoorRead | null>(null);
  const [chips, setChips] = useState<NeedsChips>(NO_CHIPS);
  const [showMuted, setShowMuted] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);

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

  const noCalendar = Boolean(door && door.calendar_configured === false);
  const asFace = (item: (typeof needs.mutedItems)[number]) =>
    needFace({ ref: String(item.id ?? item.ref ?? ""), kind: "attention", item }, ctx);
  // Listed, never counted: the muted (More ▸ Muted projects).
  const muted = needs.mutedItems.map(asFace);
  // PHILO-15-09 (B11, the A5 ruling): the head is the hub's one number, the
  // number the Dock badge and the bell say, and it counts every row under
  // it: a member, a source the hub could not read, a recording that arms.
  const head = needsHead(needs.count, needs.complete && coverage.complete);
  // Betterment D2: the chips narrow the one ranked list. Each chip's count
  // is what the list shows with that chip on (the others as they are).
  const base = showMuted ? muted : faces;
  const shown = base.filter((face) => passesChips(face, chips, now));
  const countWith = (next: Partial<NeedsChips>) =>
    base.filter((face) => passesChips(face, { ...chips, ...next }, now)).length;
  const counts = {
    mine: countWith({ direction: "mine" }), theirs: countWith({ direction: "theirs" }),
    decide: countWith({ direction: "decide" }), week: countWith({ week: true }),
  };
  const narrowed = base.filter((face) => passesChips(face, { ...chips, person: null, project: null }, now));
  const people = picksOf(narrowed.filter((f) => !chips.project || f.projectId === chips.project),
    (f) => (f.personKey ? [f.personKey, f.personName ?? f.personKey] : null));
  const projects = picksOf(narrowed.filter((f) => !chips.person || f.personKey === chips.person),
    (f) => (f.projectId ? [f.projectId, f.project?.name ?? f.projectId] : null));
  // Betterment D3: promises kept on arrival, NEW under their meeting at the
  // top. The hub is told they were seen once they are drawn; this window
  // keeps them grouped until it closes, so no row moves under his eye.
  const arrivals = useRef(new Map<string, NonNullable<NeedFace["arrival"]>>());
  for (const face of faces) if (face.arrival) arrivals.current.set(face.id, face.arrival);
  const arrivalOf = (face: NeedFace) => (showMuted ? undefined : face.arrival ?? arrivals.current.get(face.id));
  const groups: Array<{ arrival: NonNullable<NeedFace["arrival"]>; faces: NeedFace[] }> = [];
  for (const face of shown) {
    const arrival = arrivalOf(face);
    if (!arrival) continue;
    const group = groups.find((g) => g.arrival.meetingId === arrival.meetingId);
    if (group) group.faces.push({ ...face, arrival });
    else groups.push({ arrival, faces: [{ ...face, arrival }] });
  }
  const rest = shown.filter((face) => !arrivalOf(face));
  // One filled primary on a face with work: the first row drawn (a group's
  // row leads); a SETUP, repair or offer verb is never filled (HS-201-01).
  const firstId = showMuted ? null
    : [...groups.flatMap((g) => g.faces), ...rest].find((f) => !f.source && f.verbs.kind !== "setup")?.id ?? null;
  const groupKey = groups.map((g) => g.arrival.meetingId).sort().join("|");
  const told = useRef(new Set<string>());
  useEffect(() => {
    const fresh = groupKey.split("|").filter((id) => id && !told.current.has(id));
    if (!fresh.length) return;
    for (const id of fresh) told.current.add(id);
    void apiFetch("/api/desk/needs-you/seen", { method: "POST", json: { meeting_ids: fresh } }).catch(() => undefined);
  }, [groupKey]);
  const dropped = useDropped((st) => st.dropped);
  const all = [...faces, ...muted];
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
      {faces.length + muted.length > 0 ? (
        <NeedsChipRow chips={chips} setChips={setChips} counts={counts} people={people} projects={projects}
          muted={muted.length > 0 ? muted.length : 0} showMuted={showMuted} setShowMuted={setShowMuted} />
      ) : null}
      {/* A press on a row body opens it; each row's verbs carry the keyboard. */}
      <div ref={listRef} onClick={onRowPress} data-testid="needs-list" className="needs-drawer-list">
        <ScrollHint axis="y" scrollRef={listRef}>
          {showMuted && shown.length > 0 ? (
            <SurfaceSection label="Muted" count={shown.length || null} data-testid="needs-muted" className="needs-drawer-muted">
              <NeedsList label="Muted">
                {shown.map((face) => <NeedRow key={face.id} face={face} primary={false} projects={multipleProjects} />)}
              </NeedsList>
            </SurfaceSection>
          ) : shown.length > 0 ? (
            <>
              {groups.map((group) => (
                <SurfaceSection key={group.arrival.meetingId} className="needs-arrival" data-testid="needs-arrival"
                  label={`New from ${group.arrival.meetingTitle || "a meeting"}${dayWord(group.arrival.startedAt) ? ` · ${dayWord(group.arrival.startedAt)}` : ""}`}>
                  <NeedsList label={`New from ${group.arrival.meetingTitle || "a meeting"}`}>
                    {group.faces.map((face) => (
                      <NeedRow key={face.id} face={face} primary={face.id === firstId} projects={multipleProjects} />
                    ))}
                  </NeedsList>
                </SurfaceSection>
              ))}
              {rest.length > 0 ? (
                <NeedsList label="Needs you">
                  {rest.map((face) => (
                    <NeedRow key={face.id} face={face} primary={face.id === firstId} projects={multipleProjects} />
                  ))}
                </NeedsList>
              ) : null}
            </>
          ) : chipsOn(chips) ? (
            <p className="needs-drawer-none" data-testid="needs-none">Nothing matches these filters.</p>
          ) : null}
        </ScrollHint>
      </div>
      <SurfaceFooter
        receipt={
          dropped ? (
            <NeedsDroppedReceipt />
          ) : outcome.receipt ? (
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
