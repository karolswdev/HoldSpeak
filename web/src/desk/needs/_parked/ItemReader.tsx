// PARKED: the separate action-item screen is now the shared need reader.
/** The item reader (owner, 2026-11-08, on his phone: "I can't open any of
 *  these"). The row is the object (#1836, #1854): an action item that has
 *  no other home (no meeting window, no decision, its ref is
 *  `action_item:<id>`) opens ITSELF, in place in the Needs-you window, as
 *  the Decisions window opens a record in its reader. Back returns to the
 *  list (on the phone the window head's Back, when the window hosts it).
 *
 *  It shows the whole text (wrapped), one quiet line of facts in words
 *  (whose, since when, the due day, where it came from) and the row menu's
 *  verbs as library Buttons: Done, Later, Run as a program, Hand to an
 *  agent session, Open the Project. Each verb calls the function the row
 *  menu calls. After Done or Later the item leaves the list, so the reader
 *  returns to it.
 */
import { createContext, useContext, useRef, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { openHand } from "../agentHand";
import { clearWriteFailure, reportWriteFailure } from "../hooks/useWriteReceipt";
import { refreshNeedsYou } from "../needsYou";
import { runAsProgram } from "../programs/RunAsProgram";
import { openProjectRoom } from "../shell";
import { useDesk } from "../store";
import { Toolbar, ToolbarFold, type ToolbarFoldVerb } from "../surface";
import { useHasWindowBack, useWindowBack } from "../surface/back";
import { wireDate } from "../surface/format";
import { useCompactViewport } from "../useCompactViewport";
import { followThrough, markDone, tomorrowDay } from "./needsApi";
import { dayWord, tierWord, whenWord, type NeedFace } from "./needsFace";

/** The refs that name an action item and nothing else (openObject's
 *  FOLLOW_THROUGH_REF). */
const ITEM_REF = /^(?:follow-through|action_item|action):(.+)$/;

/** The action item a row reads in place, or null. A work row whose ref is
 *  its own action item (or that has no ref) has no other home; a row whose
 *  ref is a meeting, a decision or a Project keeps opening that. */
export function readsInPlace(face: Pick<NeedFace, "verbs" | "openRef" | "proposal">): string | null {
  if (face.verbs.kind !== "work" || face.proposal) return null;
  if (face.openRef && !ITEM_REF.test(face.openRef)) return null;
  return face.verbs.cardId || null;
}

/** The Needs-you window's reader opener; null outside that window (Today's
 *  rows open the window, through the `action_item:<id>` ref). */
export const ItemReaderContext = createContext<((id: string) => void) | null>(null);

/** The row's open, inside the Needs-you window: the reader for an item with
 *  no other home; else null (the caller keeps its own open). */
export function useReadInPlace(face: Pick<NeedFace, "verbs" | "openRef" | "proposal">): (() => void) | null {
  const read = useContext(ItemReaderContext);
  const id = readsInPlace(face);
  return read && id ? () => read(id) : null;
}

/** The reader's one quiet line: whose, since when, the due day, the origin.
 *  Only the facts there are; never an empty label. */
export function readerFacts(face: NeedFace, now: Date = new Date()): string {
  const v = face.verbs;
  if (v.kind !== "work") return "";
  const since = face.since ? wireDate(face.since) : null;
  const due = v.due ? dayWord(v.due) || v.due.trim() : "";
  return [
    face.tier ? tierWord(face.tier) : "",
    v.direction === "theirs" ? v.person || face.personName || "" : "Yours",
    since ? `since ${whenWord(since, now)}` : "",
    due ? `due ${due}` : "",
    face.origin ?? "",
  ].filter(Boolean).join(" · ");
}

export function ItemReader({ face, onBack }: { face: NeedFace; onBack(): void }) {
  const [busy, setBusy] = useState<"" | "done" | "later" | "program">("");
  const projects = useDesk((state) => state.projects);
  const backRef = useRef(onBack);
  backRef.current = onBack;
  const compact = useCompactViewport();
  // On the phone the window's head Back is the one Back (when the window
  // hosts it): it returns to the list.
  useWindowBack(compact ? { onBack: () => backRef.current(), testId: "needs-reader-back" } : null, [compact]);
  const viaFrame = useHasWindowBack() && compact;
  const v = face.verbs;
  if (v.kind !== "work") return null;
  const key = `action-item:${v.cardId}`;

  const run = async (which: "done" | "later" | "program", label: string, write: () => Promise<unknown>, leaves: boolean) => {
    if (busy) return;
    setBusy(which);
    try {
      await write();
      clearWriteFailure(key);
      if (leaves) onBack();
      void refreshNeedsYou(false);
    } catch (error) {
      reportWriteFailure(label, error, () => void run(which, label, write, leaves), key);
    } finally {
      setBusy("");
    }
  };

  const projectId = face.project?.id || face.projectId || "";
  const projectName = face.project?.name
    || projects.find((project) => project.id === projectId)?.name || "";
  const more: ToolbarFoldVerb[] = [
    { key: "program", label: "Run as a program", testId: "needs-reader-program", busy: busy === "program",
      onSelect: () => void run("program", "Run as a program", () => runAsProgram({ kind: "action", id: v.cardId }), false) },
    { key: "hand", label: "Hand to an agent session", testId: "needs-reader-hand",
      onSelect: () => openHand({ kind: "action", id: v.cardId, title: face.name }) },
    ...(projectId && projectName ? [{ key: "project", label: `Open the Project: ${projectName}`, testId: "needs-reader-project",
      onSelect: () => openProjectRoom(projectId) }] : []),
  ];
  const facts = readerFacts(face);

  return (
    <div className="needs-reader-window" data-testid="needs-reader" data-item-id={v.cardId}>
      <Toolbar label="Item" data-testid="needs-reader-toolbar">
        {viaFrame ? null : (
          <Button dense variant="secondary" onClick={onBack} data-testid="needs-reader-back">
            <span aria-hidden="true">‹</span> Needs you
          </Button>
        )}
        <Button dense variant="primary" loading={busy === "done"} disabled={Boolean(busy)} aria-label={`Done: ${face.name}`}
          data-testid="needs-reader-done" onClick={() => void run("done", "Done", () => markDone(v), true)}>Done</Button>
        <Button dense variant="secondary" loading={busy === "later"} disabled={Boolean(busy)} aria-label={`Later: ${face.name}`}
          title="Comes back tomorrow" data-testid="needs-reader-later"
          onClick={() => void run("later", "Later", () => followThrough(v.cardId, "snooze", { until: tomorrowDay() }), true)}>Later</Button>
        <ToolbarFold foldAt="narrow" verbs={more} data-testid="needs-reader-fold" />
      </Toolbar>
      <article className="needs-reader" aria-labelledby={`needs-reader-text-${v.cardId}`}>
        <h2 id={`needs-reader-text-${v.cardId}`} className="needs-reader-text" data-testid="needs-reader-text">{face.name}</h2>
        {facts ? <p className="needs-reader-facts" data-testid="needs-reader-facts">{facts}</p> : null}
      </article>
    </div>
  );
}
