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
import { useState } from "react";
import { Button } from "../../components/signal/Signal";
import { apiFetch } from "../../lib/api";
import { useAgentFlights } from "../agentFlights";
import { commandForDoorVerb, labelFor, supportsDoorVerb, type DoorVerb } from "../chair/doorVerbs";
import { useGate } from "../gate";
import { clearWriteFailure, reportWriteFailure } from "../hooks/useWriteReceipt";
import { refreshNeedsYou, useNeedsYou } from "../needsYou";
import { refOpener } from "../openObject";
import { openCoderSession, openProjectRoom, openSurfaceOr } from "../shell";
import { useDesk } from "../store";
import { EgressChip, StringGadget } from "../surface";
import { openSourceRef } from "../surface/citations";
import { NeedsList, NeedsRow } from "../surface/objects";
import { readCoverage } from "../coverage";
import { coverageFace, needFaces, needsHead, urlHost, type NeedFace } from "./needsFace";
import "./needs.css";

/** Answer: the agent's window with the answer field focused. Lane C2 builds
 *  the agent window and honors the hint; today the session opener opens the
 *  answer well (Conductor F2 K5b). */
export function openAgentAnswer(sessionKey: string): void {
  openCoderSession(sessionKey, { answer: true });
}

type Well = "owner" | "date";

function NeedVerbsView({ face, primary, onWell, well }: {
  face: NeedFace;
  primary: boolean;
  well: Well | null;
  onWell(next: Well | null): void;
}) {
  const [busy, setBusy] = useState(false);
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
          <Button dense variant="ghost" aria-label={named("Open")} data-testid="needs-open"
            onClick={() => openCoderSession(v.sessionKey)}>Open</Button>
          <Button dense variant={lead} aria-label={named("Answer")} data-testid="needs-answer"
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
          <Button dense variant="ghost" disabled={busy} aria-label={named("Deny")} data-testid="needs-deny"
            onClick={deny}>Deny</Button>
          <Button dense variant={lead} disabled={busy} aria-label={named("Approve")} data-testid="needs-approve"
            onClick={approve}>Approve</Button>
        </>
      );
    }
    case "pr":
      return (
        <>
          <EgressChip label={urlHost(v.url) || "GITHUB.COM"} scope="cloud" />
          <Button dense variant={lead} aria-label={named(`Open PR #${v.number ?? ""}`)} data-testid="needs-open-pr"
            onClick={() => window.open(v.url, "_blank", "noopener")}>Open PR</Button>
        </>
      );
    case "session":
      return (
        <Button dense variant={lead} aria-label={named("Open the agent")} data-testid="needs-open"
          onClick={() => openCoderSession(v.sessionKey)}>Open</Button>
      );
    case "review":
      return (
        <Button dense variant={lead} aria-label={named("Review")} data-testid="needs-review"
          onClick={() => refOpener(v.ref)?.()}>Review</Button>
      );
    case "commitment": {
      if (v.next === "mark_done") {
        return (
          <Button dense variant={lead} disabled={busy} aria-label={named("Done")} data-testid="needs-done"
            onClick={() => void act("Done", () => apiFetch("/api/follow-through/complete", {
              method: "POST", json: { card_id: v.cardId, verb: "done", payload: {} },
            }), `action-item:${v.cardId}`)}>Done</Button>
        );
      }
      const which: Well = v.next === "name_owner" ? "owner" : "date";
      const label = which === "owner" ? "Name an owner" : "Set a date";
      return (
        <Button dense variant={lead} aria-label={named(label)} aria-expanded={well === which}
          data-testid={which === "owner" ? "needs-name-owner" : "needs-set-date"}
          onClick={() => onWell(well ? null : which)}>{label}</Button>
      );
    }
    case "name-owner":
      if (!v.cardId && !v.openRef) return null;
      return (
        <Button dense variant={lead} aria-label={named("Name an owner")}
          aria-expanded={v.cardId ? well === "owner" : undefined} data-testid="needs-name-owner"
          onClick={() => {
            if (v.cardId) onWell(well ? null : "owner");
            else if (v.openRef) useDesk.getState().openPullout(v.openRef);
          }}>Name an owner</Button>
      );
    case "confirm":
      return (
        <Button dense variant={lead} disabled={busy} aria-label={named("Confirm")} data-testid="needs-confirm"
          onClick={() => void act("Confirm", () => apiFetch(
            `/api/proposals/${encodeURIComponent(v.proposalId)}/confirm`, { method: "POST" },
          ), `proposal:${v.proposalId}`)}>Confirm</Button>
      );
    case "door": {
      const verb = (v.card.lawful_verbs ?? []).find((x) => supportsDoorVerb(x as DoorVerb)) as DoorVerb | undefined;
      const cmd = verb ? commandForDoorVerb(verb) : null;
      if (!verb || !cmd) return null;
      const label = labelFor(verb);
      return (
        <Button dense variant={lead} disabled={busy} aria-label={named(label)} data-testid="needs-door-verb"
          onClick={() => void act(label, () => apiFetch(cmd.endpoint, { method: "POST", json: cmd.body }),
            `door:${cmd.endpoint}`)}>{label}</Button>
      );
    }
    case "link":
      return (
        <>
          <EgressChip label={urlHost(v.url) || "NOT SET"} scope="cloud" />
          <Button dense variant={lead} aria-label={named("Open")} data-testid="needs-open"
            onClick={() => window.open(v.url, "_blank", "noopener")}>Open</Button>
        </>
      );
    case "summarize":
      // The summary route (where the text goes) is disclosed on the meeting,
      // before the run: Summarize opens it there.
      return (
        <Button dense variant={lead} aria-label={named("Summarize")} data-testid="needs-summarize"
          onClick={() => openSourceRef(`meeting:${v.meetingId}`)}>Summarize</Button>
      );
    case "setup":
      return (
        <Button dense variant={lead} aria-label={named(v.verb)} data-testid="needs-setup"
          onClick={() => (v.key === "unknown"
            ? void refreshNeedsYou(true)
            : openSurfaceOr("open-concierge", "/models"))}>{v.verb}</Button>
      );
    case "repair":
      return (
        <Button dense variant="secondary" aria-label={named(v.verb)} data-testid="needs-repair"
          onClick={() => {
            if (v.verb === "Retry") void refreshNeedsYou(true);
            else if (v.href.startsWith("/settings")) openSurfaceOr("configure-settings", "/settings", "connections");
            else openProjectRoom(v.projectId);
          }}>{v.verb}</Button>
      );
    case "open": {
      const open = refOpener(v.ref);
      if (!open) return null;
      return (
        <Button dense variant={lead} aria-label={named("Open")} data-testid="needs-open"
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

function NeedRow({ face, primary }: { face: NeedFace; primary: boolean }) {
  const [well, setWell] = useState<Well | null>(null);
  return (
    <>
      <NeedsRow
        id={face.id}
        kind={face.kind}
        name={face.name}
        fact={face.fact || undefined}
        lamp={face.lamp}
        verbs={<NeedVerbsView face={face} primary={primary} well={well} onWell={setWell} />}
      />
      {well ? <CommitWell face={face} which={well} onDone={() => setWell(null)} /> : null}
    </>
  );
}

/** The Needs-you window body. */
export function NeedsDrawer() {
  const needs = useNeedsYou();
  const flights = useAgentFlights((s) => s.flights);
  const sessions = useAgentFlights((s) => s.sessions);
  const now = new Date();
  const coverage = readCoverage(
    needs.room?.coverage, needs.room?.complete ?? undefined, Boolean(needs.errors.room),
  );
  const gaps = coverage.gaps.map(coverageFace);
  // Board A-5: one list, no group heads. A source the hub could not read
  // leads (HS-200-15: coverage above the answer), then the agents, then the
  // rest in the hub's rank order.
  const faces = [...gaps, ...needFaces(needs.members, { flights, sessions, now })];
  const head = needsHead(needs.count, needs.complete && coverage.complete);
  // One filled primary on a face with work; a SETUP or repair verb is never
  // filled (the quiet face has none: HS-201-01 ruling 2).
  const primaryId = faces
    .find((f) => f.verbs.kind !== "setup" && f.verbs.kind !== "repair")?.id ?? null;
  return (
    <div className="needs-drawer" data-testid="needs-drawer">
      {/* The Chair's head keeps its testids (the Chair-ready signal of the
          glass rigs): the drawer's head IS the Chair's display. */}
      <div className="needs-drawer-headline" data-testid="arrival-headline">
        <h2 className="surface-display needs-drawer-head" data-testid="arrival-display">{head}</h2>
      </div>
      {faces.length > 0 ? (
        <NeedsList label="Needs you">
          {faces.map((face) => (
            <NeedRow key={face.id} face={face} primary={face.id === primaryId} />
          ))}
        </NeedsList>
      ) : null}
    </div>
  );
}
