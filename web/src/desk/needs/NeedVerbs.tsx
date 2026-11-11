/** The verbs of one Needs-you row and the wells they open in place (the
 *  Decide choices, Whose?, Nudge, a date or an owner, a source's detail,
 *  a prepared send). The ledger's rows and the first plate draw them
 *  (NeedRow.tsx, FirstPlate.tsx); NeedsDrawer.tsx composes the window. */
import { useEffect, useRef, useState } from "react";
import { create } from "zustand";
import { TonightVerb } from "../programs/TonightVerb";
import { Button } from "../../components/signal/Signal";
import { apiFetch, readableError } from "../../lib/api";
import { doneRoute, followThrough, markDone, tomorrowDay } from "./needsApi";
import { commandForDoorVerb, labelFor, supportsDoorVerb, type DoorVerb } from "../chair/doorVerbs";
import { useGate } from "../gate";
import { clearWriteFailure, reportWriteFailure } from "../hooks/useWriteReceipt";
import { refreshNeedsYou } from "../needsYou";
import { openProjectProposal, refOpener, type Opener } from "../openObject";
import { openCoderSession, openProjectRoom, openSurfaceOr } from "../shell";
import { useDesk } from "../store";
import { acceptDecision } from "../decide";
import { ConfirmVerb, StringGadget, SurfaceState, InspectorFacts } from "../surface";
import { openSourceRef } from "../surface/citations";
import { spriteUrl } from "../sprites";
import { discardPrepared, SendFace, retryInline, sendPrepared } from "../surface/send";
import { egressOf, farSide, previewOf, type Channel, type Send as ChannelSend } from "../../features/channels/channels";
import { urlHost, type NeedFace, dayWord } from "./needsFace";
import { NoteSendWells } from "../documentSendsLazy";
import { cancelArming } from "./arming";
import { WorkMenu, type WorkMenuEntry } from "../components/DeskMenu";
import { openHand } from "../agentHand";
import { runAsProgram } from "../programs/RunAsProgram";
import { AddToProject } from "../AddToProject";
import { briefable, copyPageLink, deferItem, LATER_TIMES, revokePage, sendToTelegram } from "../reach";
import { openPhoneWing } from "../calls/phoneFocus";
import { PROGRAM_CHOICE_WORDS, programDecideBody, fixedAnswers, laterAnswers, dismissAnswer, sendNeed } from "./needActions";
import { useReadInPlace } from "./ItemReader";

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
  if (face.verbs.kind === "session") {
    const key = face.verbs.sessionKey;
    return () => openCoderSession(key);
  }
  return refOpener(face.openRef);
}

export type Well = "owner" | "date" | "detail" | "project" | "nudge" | "decide" | "whose" | "send";

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


/** Betterment D2: the short message Nudge drafts. He reads it, can change
 *  it in the note, and presses Send himself. */
export function nudgeText(task: string, person: string, due: string | null | undefined): string {
  const first = person.trim().split(/\s+/)[0] || "Hi";
  const when = dayWord(due);
  return `${first}, is "${task}" on track${when ? ` for ${when}` : ""}? Tell me if you need help.`;
}

/** PHILO-15 B61: the receipt a source Retry leaves in the drawer. */
/** W6-H words: `title` is the raw reason of a failed check (the hover only). */
type SourceReceipt = { tone: "ok" | "fail"; text: string; title?: string };
export const useSourceReceipt = create<{ receipt: SourceReceipt | null; set(r: SourceReceipt | null): void }>(
  (setState) => ({ receipt: null, set: (receipt) => setState({ receipt }) }),
);

export function hhmm(d: Date): string {
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
    return { tone: "ok", text: `Checked ${name} at ${hhmm(new Date())}` };
  } catch (error) {
    return { tone: "fail", text: `Could not check ${name} · Nothing changed · Try again`, title: readableError(error) };
  } finally {
    void refreshNeedsYou(true);
  }
}

/** DELIGHT: mark the pressed verb's row to settle out, and wait the 180 ms
 *  it takes. Nothing under reduced motion (or with no media query). */
async function settleOut(origin?: Element | null): Promise<Element | null> {
  const row = origin?.closest(".needs-row") ?? null;
  if (!row || !window.matchMedia?.("(prefers-reduced-motion: no-preference)")?.matches) return null;
  row.setAttribute("data-settle", "done");
  await new Promise((resolve) => window.setTimeout(resolve, 180));
  return row;
}

// One operation model is shared by Today's row and the Needs you reader.
export { PROGRAM_CHOICE_WORDS } from "./needActions";

/** Owner walk 2026-11-08: where the row's context menu opens (a right
 *  press, a long press, Shift+F10), and the row it is for. */
export type RowMenu = { x: number; y: number; row: Element | null };

/** The rows whose other verbs live in the row's context menu (the More
 *  Button is gone: one verb on the row, the rest on a right press). */
export function hasRowMenu(face: Pick<NeedFace, "verbs">): boolean {
  return face.verbs.kind === "work" || face.verbs.kind === "confirm" || face.verbs.kind === "program";
}

/** The context menu's Project entry: `Open the Project: <name>` opens the
 *  Project's Room (PHILO-17 U30: one home, never a drawer). */
export function projectEntries(project: { id: string; name: string } | null): WorkMenuEntry[] {
  return project
    ? [{ type: "item", id: "project-room", label: `Open the Project: ${project.name}`, onSelect: () => openProjectRoom(project.id) }]
    : [];
}

export function NeedVerbsView({ face, primary, onWell, well, menu = null, onMenu = () => undefined, extra = [], brass = false }: {
  face: NeedFace;
  primary: boolean;
  /** The bold face (2026-11-08): the plate's lead verb is the brass Button. */
  brass?: boolean;
  well: Well | null;
  onWell(next: Well | null): void;
  menu?: RowMenu | null;
  onMenu?(next: RowMenu | null): void;
  /** Entries every row's menu carries after its own (the Project). */
  extra?: WorkMenuEntry[];
}) {
  const [busy, setBusy] = useState(false);
  const projects = useDesk((state) => state.projects);
  const setSourceReceipt = useSourceReceipt((st) => st.set);
  // The item reader (2026-11-08): in the Needs-you window, Open on an item
  // with no other home reads it in place.
  const readHere = useReadInPlace(face);
  const lead = brass ? "brass" : primary ? "primary" : "secondary";
  const quiet = brass ? "brass" : "secondary";
  const v = face.verbs;
  const named = (verb: string) => `${verb}: ${face.name}`;

  /* DELIGHT (2026-10-27): `origin` is the pressed verb. When the hub says a
     Done is done, the row settles out (a green wash that fades, 180 ms,
     opacity and colour only), then the list reads again and the row is
     gone. If the row is still there after the read, it shows again. */
  const act = async (label: string, run: () => Promise<unknown>, key: string, origin?: Element | null) => {
    if (busy) return;
    setBusy(true);
    try {
      await run();
      clearWriteFailure(key);
      const settled = label === "Done" ? await settleOut(origin) : null;
      void Promise.resolve(refreshNeedsYou(false)).finally(() => settled?.removeAttribute("data-settle"));
    } catch (error) {
      reportWriteFailure(label, error, () => void act(label, run, key, origin), key);
    } finally {
      setBusy(false);
    }
  };

  switch (v.kind) {
    case "phone":
      // Phone (2026-10-28): the hub's verbs, the first the lead. Call now /
      // Call again ring his phone (his press is the egress); Answer here
      // needs his words, so it opens the Phone wing set to reply.
      return (
        <>
          {v.verbs.map((verb, index) => (
            <Button key={verb.id} dense variant={index === 0 ? lead : "ghost"} loading={busy && index === 0} disabled={busy}
              aria-label={named(verb.label)} data-testid="needs-row-verb" data-verb={`phone-${verb.id.replace(/_/g, "-")}`}
              onClick={(event) => verb.needs_text
                ? openPhoneWing(String((verb.body as { reply_to?: unknown } | undefined)?.reply_to ?? v.msgId ?? "") || null)
                : void act(index === 0 ? "Done" : verb.label, () => fixedAnswers(face).find(answer => answer.id === verb.id)!.run(), face.id, (event.currentTarget as Element).closest("li"))}>
              {verb.label}
            </Button>
          ))}
        </>
      );
    case "hub":
      // Engines (2026-11-08): the hub's verbs (Retry), the first the lead.
      return (
        <>
          {v.verbs.map((verb, index) => (
            <Button key={verb.id} dense variant={index === 0 ? lead : "ghost"} loading={busy && index === 0} disabled={busy}
              aria-label={named(verb.label)} data-testid="needs-row-verb" data-verb={`hub-${verb.id.replace(/_/g, "-")}`}
              onClick={(event) => void act(index === 0 ? "Done" : verb.label, () => fixedAnswers(face).find(answer => answer.id === verb.id)!.run(), face.id, (event.currentTarget as Element).closest("li"))}>
              {verb.label}
            </Button>
          ))}
        </>
      );
    case "program": {
      // Owner walk 2026-11-08: the row is one verb, the ask's lead (Merge on
      // a merge ask, Decide on a decision, else Open); a press on the row
      // opens the Program. Its other choices, Later (the times) and Send
      // (the briefing page) are the row's context menu.
      const opener = faceOpener(face);
      const decide = (choice: string, label: string, origin?: Element | null) => act(label, () => fixedAnswers(face).find(answer => answer.id === choice)!.run(), face.id, origin);
      const merges = v.ask === "merge" && v.choices.includes("merge");
      // One meaning for Decide on every row: it opens the choices in place.
      // An ask with no choices is Open (the Program, at its step).
      const decides = !merges && v.ask === "decide" && v.choices.length > 0;
      const leadWord = merges ? "Merge" : decides ? "Decide" : "Open";
      const ghost = busy ? "Busy" : undefined;
      const choiceEntries: WorkMenuEntry[] = v.choices.filter((choice) => !(merges && choice === "merge")).map((choice) => {
        const word = PROGRAM_CHOICE_WORDS[choice] ?? choice;
        return { type: "item" as const, id: `choice-${choice}`, label: word, ghost,
          onSelect: () => void decide(choice, choice === "prepare" ? word : "Done", menu?.row) };
      });
      const briefs = Boolean(v.ref && briefable(v.itemKind));
      const entries: WorkMenuEntry[] = [
        ...(opener ? [{ type: "item" as const, id: "open", label: "Open", onSelect: opener }] : []),
        ...choiceEntries,
        // PG-DIRECTION DIR4: Later is an answer (the times). A row he
        // deferred already sits in the Later group with its time.
        ...(briefs && !v.later ? [{ type: "sub" as const, id: "later", label: "Later",
          entries: LATER_TIMES.map((time) => ({ type: "item" as const, id: `later-${time.id}`, label: time.label, ghost,
            onSelect: () => void act("Later", () => laterAnswers(face).find(answer => answer.id === time.id)!.run(), face.id) })) }] : []),
        // PG-DIRECTION DIR3/DIR5: the item's briefing page. Revoke ends the
        // token, not the item.
        ...(briefs ? (v.page
          ? [{ type: "item" as const, id: "revoke-page", label: "Revoke the page", ghost,
            onSelect: () => void act("Revoke", () => revokePage(String(v.page?.package_id)), face.id) }]
          : [{ type: "sub" as const, id: "send", label: "Send", entries: [
            { type: "item" as const, id: "copy-link", label: "Copy page link", ghost,
              onSelect: () => void act("Copy page link", () => copyPageLink(String(v.ref)), face.id) },
            { type: "item" as const, id: "send-telegram", label: "Send to Telegram", ghost,
              onSelect: () => void act("Send to Telegram", () => sendToTelegram(String(v.ref)), face.id) },
          ] }]) : []),
      ];
      return <>
        <Button dense variant={quiet} loading={busy} disabled={busy || (!merges && !decides && !opener)} aria-label={named(leadWord)}
          aria-expanded={decides ? well === "decide" : undefined}
          data-testid="needs-row-verb" data-verb={merges ? "program-merge" : decides ? "program-decide" : "program-open"}
          onClick={(event) => merges ? void decide("merge", "Done", event.currentTarget)
            : decides ? onWell(well === "decide" ? null : "decide") : opener?.()}>{leadWord}</Button>
        {menu ? <WorkMenu label={face.name} x={menu.x} y={menu.y} entries={[...entries, ...extra]} autoFocus onClose={() => onMenu(null)}
          returnFocus={() => menu.row?.querySelector<HTMLElement>("[data-testid=needs-row-verb]")?.focus()} /> : null}
      </>;
    }
    case "allow-helper":
      return <Button dense variant={lead} loading={busy} disabled={busy}
        aria-label={named("Allow helper")} data-testid="needs-row-verb" data-verb="allow-helper"
        onClick={() => void act("Allow helper", () => fixedAnswers(face)[0].run(), face.id)}>Allow helper</Button>;
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
          () => fixedAnswers(face).find(answer => answer.id === (decision === "approved" ? "approve" : "deny"))!.run(), `gate:${v.proposalId}`);
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
        () => fixedAnswers(face)[0].run(), `gate:${v.proposalId}`);
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
          <Button dense variant={lead} aria-label={named(`Open PR #${v.number ?? ""}`)} data-testid="needs-row-verb" data-verb="open-pr"
            title={v.url} onClick={() => window.open(v.url, "_blank", "noopener")}>Open PR</Button>
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
    case "work": {
      const opener = readHere ?? faceOpener(face);
      const key = `action-item:${v.cardId}`;
      // Betterment D3: Drop removes it; Undo (8 s) opens it again.
      const drop = () => act("Drop", async () => {
        await dismissAnswer(face)!.run();
        offerUndo(face.name, () => followThrough(v.cardId, "reopen"));
      }, key);
      // Owner walk 2026-11-08: the row is one verb; the rest is the row's
      // context menu. Open is first there for the keyboard (a press on the
      // row opens it too).
      const entries: WorkMenuEntry[] = [
        ...(opener ? [{ type: "item" as const, id: "open", label: "Open", onSelect: opener }] : []),
        ...(v.direction === "theirs"
          ? [{ type: "item" as const, id: "done", label: "Done", ghost: busy ? "Busy" : undefined,
            onSelect: () => void act("Done", () => markDone(v), key, menu?.row) }]
          : []),
        ...(v.next === "set_date"
          ? [{ type: "item" as const, id: "date", label: "Set a date", onSelect: () => onWell("date") }]
          : []),
        { type: "item", id: "later", label: "Later", ghost: busy ? "Busy" : undefined,
          onSelect: () => void act("Later", () => laterAnswers(face)[0].run(), key) },
        { type: "item", id: "drop", label: "Drop", ghost: busy ? "Busy" : undefined, onSelect: () => void drop() },
        // One verb, one name (2026-11-08): the action becomes a Program from
        // where he reads it, through the one Run as a program.
        { type: "item", id: "program", label: "Run as a program", ghost: busy ? "Busy" : undefined,
          onSelect: () => void act("Run as a program", () => runAsProgram({ kind: "action", id: v.cardId }), key) },
        // Betterment AG4, under its honest name: one agent session on the
        // action (the launch sheet), not a Program.
        { type: "item", id: "hand", label: "Hand to an agent session",
          onSelect: () => openHand({ kind: "action", id: v.cardId, title: face.name }) },
      ];
      return <>
        {v.direction === "theirs" ? (
          <Button dense variant={lead} aria-label={named("Nudge")} aria-expanded={well === "nudge"}
            data-testid="needs-row-verb" data-verb="nudge"
            onClick={() => onWell(well === "nudge" ? null : "nudge")}>Nudge</Button>
        ) : (
          <Button dense variant={quiet} disabled={busy} aria-label={named("Done")} data-testid="needs-row-verb" data-verb="done"
            onClick={(event) => void act("Done", () => markDone(v), key, event.currentTarget)}>Done</Button>
        )}
        {menu ? <WorkMenu label={face.name} x={menu.x} y={menu.y} entries={[...entries, ...extra]} autoFocus onClose={() => onMenu(null)}
          returnFocus={() => menu.row?.querySelector<HTMLElement>("[data-testid=needs-row-verb]")?.focus()} /> : null}
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
    case "decision-confirm":
      return (
        <Button dense variant={lead} disabled={busy} aria-label={named("Confirm")}
          data-testid="needs-row-verb" data-verb="confirm"
          onClick={() => void act("Confirm", () => fixedAnswers(face)[0].run(), `decision:${v.decisionId}`)}>Confirm</Button>
      );
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
          onSelect: () => void act("Defer", () => laterAnswers(face)[0].run(), `proposal:${v.proposalId}`) },
        { type: "item", id: "decline", label: "Decline", ghost: busy ? "Busy" : undefined,
          onSelect: () => void act("Decline", () => dismissAnswer(face)!.run(), `proposal:${v.proposalId}`) },
      ];
      return <>
        <Button dense variant={lead} disabled={busy} aria-label={named("Confirm")} data-testid="needs-row-verb" data-verb="confirm"
          onClick={() => void act("Confirm", () => fixedAnswers(face)[0].run(), `proposal:${v.proposalId}`)}>Confirm</Button>
        {menu ? <WorkMenu label={face.name} x={menu.x} y={menu.y} entries={[...entries, ...extra]} autoFocus onClose={() => onMenu(null)}
          returnFocus={() => menu.row?.querySelector<HTMLElement>("[data-testid=needs-row-verb]")?.focus()} /> : null}
      </>;
    }
    case "door": {
      const verb = (v.card.lawful_verbs ?? []).find((x) => supportsDoorVerb(x as DoorVerb)) as DoorVerb | undefined;
      const cmd = verb ? commandForDoorVerb(verb) : null;
      if (!verb || !cmd) return null;
      const label = labelFor(verb);
      // One Done (2026-11-08): a Done on a Door card is markDone's.
      const run = () => fixedAnswers(face)[0].run();
      // JRN2: a Door task can go to tonight's program (a Planned step).
      const actionId = String(v.card.target_ref ?? "").startsWith("action_item:") ? String(v.card.target_ref).slice("action_item:".length) : "";
      return (
        <>
          {actionId ? <TonightVerb kind="action" itemId={actionId} name={String(v.card.title ?? v.card.text ?? actionId)} /> : null}
          <Button dense variant={lead} disabled={busy} aria-label={named(label)} data-testid="needs-row-verb" data-verb="door-verb"
            onClick={(event) => void act(label, run, `door:${cmd.endpoint}`, event.currentTarget)}>{label}</Button>
        </>
      );
    }
    case "link":
      return (
        /* Owner 2026-10-25: the host chip on every row is "an ancient relic";
           the browser shows where the link goes. The host stays on the verb's
           title for the pointer. */
        <Button dense variant={lead} aria-label={named("Open")} title={urlHost(v.url).toLowerCase() || undefined}
          data-testid="needs-row-verb" data-verb="open"
          onClick={() => window.open(v.url, "_blank", "noopener")}>Open link</Button>
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
        {/* Owner ruling 2026-10-25: no host chip on the row. A Retry that
            re-checks a remote source names the host in its hover title. */}
        <Button dense variant="secondary" disabled={busy} aria-label={named(v.verb)} data-testid="needs-row-verb" data-verb="repair"
          title={v.verb === "Retry" && v.watchIds?.length && v.host ? `Checks ${v.host.toLowerCase()} again` : undefined}
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
          {v.failed ? (
            <Button dense variant="secondary" aria-label={named("Record now")}
              data-testid="needs-row-verb" data-verb="record"
              onClick={() => void useDesk.getState().startRecording(
                v.calendarEventId ? { calendarEventId: v.calendarEventId } : undefined,
              )}>Record now</Button>
          ) : (
            <Button dense variant="danger" aria-label={named(v.refused ? "Retry cancel" : "Cancel")}
              data-testid="needs-row-verb" data-verb={v.refused ? "retry" : "cancel"}
              onClick={() => void cancelArming(v.scheduleId)}>{v.refused ? "Retry" : "Cancel"}</Button>
          )}
          <Button dense variant="ghost" aria-label={named("Open")} data-testid="needs-row-verb" data-verb="open"
            onClick={() => openSurfaceOr("review-meetings", "/history", v.failed ? "record" : undefined)}>Open meetings</Button>
        </>
      );
    case "calendar":
      return (
        <Button dense variant="secondary" aria-label="Connect calendar" data-testid="needs-row-verb" data-verb="connect-calendar"
          onClick={() => openSurfaceOr("configure-settings", "/settings", "integration:calendar")}>Connect calendar</Button>
      );
    case "send": {
      const s = v.send as unknown as ChannelSend;
      const channel = String(s.channel || "file") as Channel;
      const account = (s.account || {}) as Record<string, string | boolean>;
      const target = (s.target || {}) as Record<string, string | number>;
      const eg = egressOf({ channel, account, synced: false, target });
      const check = () => {
        const url = farSide(channel, target, account);
        if (url) window.open(url, "_blank", "noopener");
        return apiFetch(`/api/channels/sends?send_id=${encodeURIComponent(v.sendId)}`);
      };
      const run = () => sendNeed(v);
      // A settled UNKNOWN can be inspected without being replayable. The
      // hub withholds retry_command for legacy or foreign rows, so do not draw
      // a dead Try again verb that cannot name the original operation.
      const canRetry = v.state !== "failed" && (v.state !== "unknown" || Boolean(s.retry_command));
      return (
        <>
          {/* Owner ruling 2026-10-25: no host chip on the row. The fact names
              the destination; Look opens the preview; Send names the
              address in its hover title. */}
          {v.state === "unknown" ? (
            <Button dense variant="ghost" disabled={busy} aria-label={named("Check")} data-testid="needs-row-verb" data-verb="check"
              onClick={() => void act("Check", check, face.id)}>Check</Button>
          ) : null}
          {canRetry ? (
            <Button dense variant={lead} loading={busy} disabled={busy} aria-label={named(v.state === "prepared" ? "Send" : "Try again")}
              data-testid="needs-row-verb" data-verb={v.state === "prepared" ? "send" : "try-again"}
              title={eg.title || eg.label || undefined}
              onClick={() => void act(v.state === "prepared" ? "Send" : "Try again", run, face.id)}>
              {v.state === "prepared" ? "Send" : "Try again"}
            </Button>
          ) : null}
          {v.state === "prepared" ? (
            <>
              <Button dense variant="ghost" aria-label={named("Look")} aria-expanded={well === "send"}
                data-testid="needs-row-verb" data-verb="look" onClick={() => onWell(well === "send" ? null : "send")}>Look</Button>
              <ConfirmVerb targetId={v.sendId} label="Discard" confirmLabel="Discard?" busy={busy}
                data-testid="needs-send-discard" onConfirm={() => void act("Discard", () => dismissAnswer(face)!.run(), face.id)} />
            </>
          ) : null}
        </>
      );
    }
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

export function SendNeedWell({ face, onDone }: { face: NeedFace; onDone(): void }) {
  const v = face.verbs;
  if (v.kind !== "send") return null;
  const s = v.send as unknown as ChannelSend;
  return <li className="needs-drawer-well" role="region" aria-label={`Preview: ${face.name}`} data-testid="needs-send-preview">
    <SendFace destination={{id:v.destinationId,name:s.destination_name ?? "Destination",channel:s.channel,target:s.target,account:s.account}}
      preview={previewOf(s.channel,s.target,s.account,s.preview,s.file_path)} previewTestId="needs-send-preview-well" completion={{done:onDone}} />
  </li>;
}

export function CommitWell({ face, which, onDone }: { face: NeedFace; which: Well; onDone(): void }) {
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const v = face.verbs;
  const cardId = v.kind === "name-owner" || v.kind === "work" ? v.cardId : null;
  const save = async () => {
    const value = draft.trim();
    if (!value || !cardId || busy) return;
    setBusy(true);
    const verb = which === "owner" ? "delegate" : "due";
    const label = which === "owner" ? "Name an owner" : "Set a date";
    try {
      await followThrough(cardId, verb, verb === "delegate" ? { to: value } : { due_at: value });
      clearWriteFailure(`action-item:${cardId}`);
      onDone();
      void refreshNeedsYou(false);
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

/** One choice in the Decide panel. */
type DecideChoice = { id: string; label: string; key: string; run(): Promise<unknown>; after?(): void; settles: boolean; quiet?: boolean };

/** The choices Decide opens: a meeting's decision (Accept, Not now, Drop)
 *  or a Program ask (the hub's choices, each its `decide` route). */
function decideChoices(face: NeedFace): DecideChoice[] {
  if (face.verbs.kind !== "decide" && face.verbs.kind !== "program") return [];
  const v = face.verbs;
  return fixedAnswers(face).map(answer => ({...answer, key: v.kind === "decide" ? `proposal:${v.proposalId}` : face.id,
    settles: !answer.keeps, quiet: answer.destructive,
    ...(answer.id === "dismiss" && v.kind === "decide" ? {after: () => offerUndo(face.name, () => apiFetch(`/api/proposals/${encodeURIComponent(v.proposalId)}/restore`, {method: "POST"}))} : {}),
  }));
}

/** Decide, in place (Betterment D2; owner rule "the row is the object, one
 *  verb"): the row's choices under it, the first the lead. A meeting's
 *  decision: Accept writes it (the proposal's Confirm), Not now holds it back
 *  (Defer), Drop removes it (Decline). A Program ask: the hub's choices, each
 *  posted to the step's decide route. On success the row settles out. Open
 *  item shows it where it came from. */
export function DecideWell({ face, onDone }: { face: NeedFace; onDone(): void }) {
  const [busy, setBusy] = useState(false);
  const panel = useRef<HTMLLIElement | null>(null);
  const choices = decideChoices(face);
  if (!choices.length) return null;
  const opener = faceOpener(face);
  const press = async (choice: DecideChoice): Promise<void> => {
    if (busy) return;
    setBusy(true);
    try {
      await choice.run();
      clearWriteFailure(choice.key);
      const settled = choice.settles ? await settleOut(panel.current?.previousElementSibling) : null;
      onDone();
      choice.after?.();
      void Promise.resolve(refreshNeedsYou(false)).finally(() => settled?.removeAttribute("data-settle"));
    } catch (error) {
      reportWriteFailure(choice.label, error, () => void press(choice), choice.key);
    } finally {
      setBusy(false);
    }
  };
  return (
    <li ref={panel} className="needs-drawer-well needs-drawer-decide" role="region" aria-label={`Decide: ${face.name}`}
      data-testid="needs-decide"
      onKeyDown={(event) => { if (event.key === "Escape") { event.stopPropagation(); onDone(); } }}>
      {choices.map((choice, index) => (
        <Button key={choice.id} dense variant={index === 0 ? "primary" : choice.quiet ? "ghost" : "secondary"}
          disabled={busy} autoFocus={index === 0} aria-label={`${choice.label}: ${face.name}`}
          data-testid={choice.id === "accept" ? "needs-decide-accept" : "needs-decide-choice"} data-choice={choice.id}
          onClick={() => void press(choice)}>{choice.label}</Button>
      ))}
      {opener ? <Button dense variant="ghost" aria-label={`Open item: ${face.name}`} onClick={() => opener()}>Open item</Button> : null}
    </li>
  );
}

/** Betterment D3: Whose? The meeting's speakers, one press each: the press
 *  keeps the promise with that owner (Confirm with the owner). */
export function WhoseWell({ face, onDone }: { face: NeedFace; onDone(): void }) {
  const [busy, setBusy] = useState(false);
  const v = face.verbs;
  if (v.kind !== "whose") return null;
  const keep = async (owner: string) => {
    if (busy) return;
    setBusy(true);
    const key = `proposal:${v.proposalId}`;
    try {
      await fixedAnswers(face).find(answer => answer.id === owner)!.run();
      clearWriteFailure(key);
      onDone();
      void refreshNeedsYou(false);
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
export function NudgeWell({ face, embedded = false }: { face: NeedFace; embedded?: boolean }) {
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
  const Tag = embedded ? "div" : "li";
  return (
    <Tag className={embedded ? "surface-preference-well" : "needs-drawer-well needs-drawer-nudge"} role="region" aria-label={`Nudge: ${face.name}`}
      data-testid="needs-nudge">
      {embedded ? <InspectorFacts name={face.name} rows={[{label: "Message", value: <span data-testid="needs-nudge-text">{text}</span>}]} /> : <p className="needs-nudge-text" data-testid="needs-nudge-text">{text}</p>}
      {failed ? <SurfaceState error="The message was not prepared." />
        : note ? <NoteSendWells id={note.id} title={note.title} />
          : <SurfaceState loading />}
    </Tag>
  );
}

/** PHILO-17 (needsyou): a source row's detail: each source and the hub's
 *  own reason, one line each. */
export function DetailWell({ face }: { face: NeedFace }) {
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
