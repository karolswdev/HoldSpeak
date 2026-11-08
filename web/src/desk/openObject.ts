/** PHILO-13-06 (B1) — one open grammar: a named row opens its object in its
 * own window (the owner's fork 2, 2026-10-01: "Opens its own window").
 *
 * Every row that names an object asks this module for its opener. The
 * answer is a function, or null when the row names nothing that opens; a
 * null row draws no open (UX-CANON A.11: a verb that does nothing is a lie).
 * The opens go through the existing dispatch only: the citation species
 * (`openSourceRef`), a Project's drawer (`drawer/`), the People surface,
 * Intelligence. */
import { apiFetch } from "../lib/api";
import { openIntelligence } from "./intelligenceNavigation";
import { openAgentLane, openCoderSession, openPrimitive, openProjectRoom } from "./shell";
import { openSourceRef } from "./surface";
import { personWindowRef, type PersonLens } from "./objectWindows";
import { useDesk } from "./store";
import type { DeskNavigation } from "./store/types";

export type Opener = () => void;

/** The People lenses a row may open on (`PeopleCore` scope grammar). */
export type { PersonLens, PersonOpenRequest } from "./objectWindows";
export { PERSON_OPEN_EVENT } from "./objectWindows";

/** The People surface on one relationship: `people:<id>[:<lens>]`. */
export function personScope(relationshipId: string, lens?: PersonLens): string {
  return `people:${relationshipId}${lens ? `:${lens}` : ""}`;
}

/** PHILO-17 (2b): a person opens THAT person, in their own window
 * (`pullout:people:<id>`); the People drawer stays the roster. A lens in the
 * open is one request, counted (PHILO-13-06): an open window moves to it. */
export function openPerson(relationshipId: string, lens?: PersonLens): void {
  const ref = personWindowRef(personScope(relationshipId, lens));
  if (!ref) return;
  openPrimitive(ref);
}

/** PHILO-13-14 (C4) — `Draft update for <project>`: the Room opens and goes to
 * its Update posture, as its own `Draft update` Button does. The Room takes
 * the request once (a reload does not replay it). */
export const ROOM_UPDATES_EVENT = "holdspeak:room-updates";
const roomUpdates = new Set<string>();

export function openProjectUpdates(projectId: string): void {
  const id = projectId.trim();
  if (!id) return;
  roomUpdates.add(id);
  openProjectRoom(id);
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent<string>(ROOM_UPDATES_EVENT, { detail: id }));
  }
}

/** Betterment P4 (projects) — `Draft update for <project>` (the palette and
 * the Object menu): the Room opens and presses its own Draft update, the
 * same press as the Room head's Button. The Room takes the request once. */
export const ROOM_WRITE_EVENT = "holdspeak:room-write-update";
const roomWrites = new Set<string>();

export function writeProjectUpdate(projectId: string): void {
  const id = projectId.trim();
  if (!id) return;
  roomWrites.add(id);
  openProjectRoom(id);
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent<string>(ROOM_WRITE_EVENT, { detail: id }));
  }
}

/** True once for each request to write an update in `projectId`'s Room. */
export function takeRoomWriteRequest(projectId: string | null | undefined): boolean {
  return !!projectId && roomWrites.delete(projectId);
}

/** PHILO-17 words: a Project's Rename verb opens its Room and focuses the
 * existing name field. The Room consumes this request once after mounting. */
export const ROOM_RENAME_EVENT = "holdspeak:room-rename";
const roomRenames = new Set<string>();

export function openProjectRename(projectId: string): void {
  const id = projectId.trim();
  if (!id) return;
  roomRenames.add(id);
  openProjectRoom(id);
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent<string>(ROOM_RENAME_EVENT, { detail: id }));
  }
}

/** The Room takes a rename request once. */
export function takeRoomRenameRequest(projectId: string | null | undefined): boolean {
  return !!projectId && roomRenames.delete(projectId);
}

/** PHILO-14 A2b (Astra r1 on #945) — a proposal is an object: its row opens
 *  the destination that contains it, the Room with that proposal selected.
 *  The Room takes the request once (a reload does not replay it). */
export const ROOM_PROPOSAL_EVENT = "holdspeak:room-proposal";

/** HS-S12 (D12 / G-OPEN): a Room keeps ONE target per project, the latest
 * explicit one: a proposal to reveal or a place to open at. A newer request
 * replaces an older one, so a Room that mounts late never applies a stale
 * target over the latest (a proposal never loses to an older History). The
 * same proposal asked again is the same reveal in the same Room window. */
type RoomTarget = { kind: "proposal"; proposalId: string } | { kind: "at"; place: RoomPlace };
const roomTargets = new Map<string, RoomTarget>();

export function openProjectProposal(projectId: string, proposalId: string): void {
  const id = projectId.trim();
  if (!id) return;
  if (proposalId.trim()) roomTargets.set(id, { kind: "proposal", proposalId: proposalId.trim() });
  openProjectRoom(id);
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent<string>(ROOM_PROPOSAL_EVENT, { detail: id }));
  }
}

/** Phase 16 (the interior kit, the canvas window "Payments ledger
 *  cutover"): the Room window's trailing verbs open the Room AT a place:
 *  `history` (its History wing) or `steward` (the Steward posture, where
 *  the sources are kept). The Room takes the request once (a reload does
 *  not replay it), as with Draft update. */
export const ROOM_AT_EVENT = "holdspeak:room-at";
export type RoomPlace = "room" | "history" | "steward" | { kind: "file"; ref: `note:${string}` };

export function openProjectRoomAt(projectId: string, place: RoomPlace): void {
  const id = projectId.trim();
  if (!id) return;
  openProjectRoom(id);
  requestRoomAt(id, place);
}

/** Ask `projectId`'s Room (open now or about to open) to show `place`;
 * `room` is the Room itself, every posture stepped aside (the Walk). */
export function requestRoomAt(projectId: string, place: RoomPlace): void {
  const id = projectId.trim();
  if (!id) return;
  roomTargets.set(id, { kind: "at", place });
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent<string>(ROOM_AT_EVENT, { detail: id }));
  }
}

/** Return to the Project that held an explicitly opened Note. */
export function openProjectRoomAtResource(projectId: string, resourceRef: `note:${string}`): void {
  if (!resourceRef.slice("note:".length)) return;
  openProjectRoomAt(projectId, { kind: "file", ref: resourceRef });
}

/** The place to open `projectId`'s Room at, once per request. */
export function takeRoomAtRequest(projectId: string | null | undefined): RoomPlace | null {
  if (!projectId) return null;
  const target = roomTargets.get(projectId);
  if (target?.kind !== "at") return null;
  roomTargets.delete(projectId);
  return target.place;
}

/** The proposal to select in `projectId`'s Room, once per request. */
export function takeRoomProposalRequest(projectId: string | null | undefined): string | null {
  if (!projectId) return null;
  const target = roomTargets.get(projectId);
  if (target?.kind !== "proposal") return null;
  roomTargets.delete(projectId);
  return target.proposalId;
}

/** True once for each request to open `projectId`'s Room in its Update posture. */
export function takeRoomUpdatesRequest(projectId: string | null | undefined): boolean {
  return !!projectId && roomUpdates.delete(projectId);
}

/** A Program window keeps ONE step target per Program, the latest explicit
 * one (HS-S12): a Needs you row that names a step opens the Program window
 * (`pullout:program:<id>`) with that step selected. The window takes the
 * request once, when it mounts or, if it is open, on the event. */
export const PROGRAM_STEP_EVENT = "holdspeak:program-step";
const programSteps = new Map<string, string>();

export function openProgramStep(programId: string, stepId = ""): void {
  const id = programId.trim();
  if (!id) return;
  const step = stepId.trim();
  if (step) {
    programSteps.set(id, step);
    if (typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent<string>(PROGRAM_STEP_EVENT, { detail: id }));
    }
  }
  void import("./store").then(({ useDesk }) => useDesk.getState().openPullout(`program:${id}`));
}

/** The step to select in `programId`'s window, once per request. */
export function takeProgramStepRequest(programId: string | null | undefined): string | null {
  if (!programId) return null;
  const step = programSteps.get(programId) ?? null;
  programSteps.delete(programId);
  return step;
}

/** Refs the citation species opens in a window of their own. */
const WINDOW_REF = /^(meeting|decision|note|artifact|thread):\S/;
// `action:` is memory's name for the same action item (a recall hit, a chat citation).
const FOLLOW_THROUGH_REF = /^(?:follow-through|action_item|action):(.+)$/;

/** The opener for a qualified ref, or null when the ref names nothing that
 * opens (a count, a coverage line, a pipeline event). */
export function refOpener(ref: string | null | undefined, navigation?: DeskNavigation): Opener | null {
  const clean = (ref ?? "").trim();
  if (!clean) return null;
  // `person:<id>` is the same person (a Note's @ link, the About picker).
  if (clean.startsWith("people:") || clean.startsWith("person:")) {
    const id = clean.slice(clean.indexOf(":") + 1);
    if (!id || id.startsWith("project:")) return null;
    return () => openPerson(id);
  }
  // PHILO-17 U30: a Project opens its Room (one home; the drawer is parked
  // as a project face).
  if (clean.startsWith("project:")) {
    const id = clean.slice("project:".length);
    return id ? () => openProjectRoom(id) : null;
  }
  // Conductor F2: a Needs you coder row (R5) is `coder:<agent>:<session_id>`;
  // it opens the agent's session window.
  if (clean.startsWith("coder:")) {
    const key = clean.slice("coder:".length);
    return key.includes(":") ? () => openCoderSession(key) : null;
  }
  // PHILO-14 C2: a launched agent is `launch:<launch_id>`; it opens its lane.
  // Programs (2026-10-28): a Program is `program:<id>`; it opens the
  // Program window `pullout:program:<id>`.
  // Programs PG14: an automation that started a Program is
  // `automation:<workbench id>`; it opens the automation window.
  if (clean.startsWith("automation:")) {
    const id = clean.slice("automation:".length);
    return id ? () => {
      void import("./store").then(({ useDesk }) => useDesk.getState().openWorkbenchWindow(id));
    } : null;
  }
  // `program:<id>:<step>` opens the same window with that step selected.
  if (clean.startsWith("program:")) {
    const [id, step = ""] = clean.slice("program:".length).split(":");
    return id ? () => openProgramStep(id, step) : null;
  }
  if (clean.startsWith("launch:")) {
    const id = clean.slice("launch:".length);
    return id ? () => openAgentLane(id) : null;
  }
  // Conductor R1: a held tool call of a launched agent is `gate:<proposal_id>`;
  // it opens the Needs you window, where the held call is listed with
  // Approve and Deny (the system shade it opened is parked).
  if (clean.startsWith("gate:")) {
    return clean.length > "gate:".length ? () => {
      void import("./chair/chairWindows").then((m) => m.openChairWindow("chair:needs"));
    } : null;
  }
  // S9: a Wrote row names the actual hub window that an Ask opened or
  // arranged.  Restore that window in the shared compositor; the hub frame
  // has already made its object scope available to this view.
  if (clean.startsWith("window:")) {
    const id = clean.slice("window:".length);
    if (!id) return null;
    return () => {
      void import("./store").then(({ useDesk }) => {
        const desk = useDesk.getState();
        if (id.startsWith("pullout:")) {
          const key = id.slice("pullout:".length);
          if (desk.pullouts.some((row) => row.id === key)) desk.restorePanel(id);
          else desk.openPullout(key);
        } else desk.restorePanel(id);
      });
    };
  }
  const followThrough = FOLLOW_THROUGH_REF.exec(clean);
  if (followThrough) {
    const id = followThrough[1];
    return () => openIntelligence({ view: "follow-through", followThroughId: id });
  }
  // A desk decision has one ref name (`desk_decision:<id>`); it opens its
  // record in the Decisions window reader, the one face of a decision.
  if (clean.startsWith("desk_decision:")) {
    const id = clean.slice("desk_decision:".length);
    return id ? () => openDeskDecisionRecord(id) : null;
  }
  if (clean.startsWith("decision:")) return () => openDecision(clean);
  if (WINDOW_REF.test(clean)) return navigation === undefined
    ? () => openSourceRef(clean) : () => openSourceRef(clean, navigation);
  return null;
}

/** Open a cited ref (a claim's source, a memory citation): the one open
 * grammar first; a ref it does not name goes to the citation species. Memory
 * ranks the child message that matched; the Desk opens the parent thread. */
export function openRef(ref: string, navigation?: DeskNavigation): void {
  const clean = ref.startsWith("thread:") ? ref.split("#", 1)[0] : ref.trim();
  const open = navigation === undefined ? refOpener(clean) : refOpener(clean, navigation);
  if (open) open();
  else if (navigation === undefined) openSourceRef(clean);
  else openSourceRef(clean, navigation);
}

/** A decision ref names a Desk decision or a decision a meeting recorded
 * (`decisions` lifecycle rows). Both open in the Decisions window reader, the
 * one face of a decision (2026-11-08); one read tells which. A Desk decision
 * opens its record (`openDeskDecisionRecord`). The owner, 2026-10-25: a
 * meeting decision that has a record opens that record; one with no record
 * yet opens in its reader from the meeting (`decision:<id>`). A failed read
 * opens the Decisions window on the decision by its id. */
function openDecision(ref: string): void {
  const id = ref.slice("decision:".length);
  if (!id) return;
  void apiFetch<{ decision?: { source_meeting_id?: string | null } }>(`/api/decisions/${encodeURIComponent(id)}`)
    .then(async (body) => {
      const meeting = (body?.decision?.source_meeting_id ?? "").trim();
      if (!meeting) return openDeskDecisionRecord(id);
      const records = await apiFetch<{ id?: string }[]>(
        `/api/decision-records/source/meeting/${encodeURIComponent(id)}`,
      ).catch(() => []);
      const record = (Array.isArray(records) ? records : []).find((row) => String(row?.id ?? "").trim());
      if (record) openDecisionRecord(String(record.id));
      else useDesk.getState().openSurfaceWindow("open-decisions", `decision:${id}`);
    })
    .catch(() => useDesk.getState().openSurfaceWindow("open-decisions", `decision:${id}`));
}

/** PHILO-14 A2b (Astra r1 on #945) — the ref of the decision a record
 *  (`decision_record:<record id>`, `record-<hex>`) was made from (its
 *  source): the drawer's member ref and the reader's "From" link. The record
 *  itself opens in the Decisions window (`openDecisionRecord`). */
export function decisionRecordSourceRef(sourceType: unknown, sourceId: unknown): string | null {
  const id = String(sourceId ?? "").trim();
  if (!id) return null;
  if (sourceType === "desk") return `desk_decision:${id}`;
  if (sourceType === "meeting" || sourceType === "decision") return `decision:${id}`;
  return null;
}

/** The owner, 2026-10-25: a decision record has ONE face, the reader in the
 *  Decisions window (`record:<id>`; #1474). The reader reads its own record,
 *  so the press opens the window at once, with no read first. An open
 *  Decisions window comes to the front and shows this record. */
export function openDecisionRecord(recordId: string): void {
  const id = recordId.trim();
  if (!id) return;
  useDesk.getState().openSurfaceWindow("open-decisions", `record:${id}`);
}

/** A Desk decision (`desk_decision`) opens its record in the Decisions
 *  window reader, the one face of a decision (2026-11-08): the record the
 *  caller knows, else the records the hub names for that source. A source
 *  with no record, or a failed read, opens the Decisions window. */
export function openDeskDecisionRecord(deskDecisionId: string, recordId?: string | null): void {
  const known = String(recordId ?? "").trim();
  if (known) return openDecisionRecord(known);
  const id = deskDecisionId.trim();
  if (!id) return;
  void apiFetch<unknown>(`/api/decision-records/source/desk/${encodeURIComponent(id)}`)
    .then((records) => {
      const ids = (Array.isArray(records) ? records : [])
        .map((row) => String((row as { id?: unknown })?.id ?? "").trim())
        .filter(Boolean);
      if (ids.length) openDecisionRecords(ids);
      else useDesk.getState().openSurfaceWindow("open-decisions");
    })
    .catch(() => useDesk.getState().openSurfaceWindow("open-decisions"));
}

/** The records that govern one piece of work (WHY with several): the
 *  Decisions window lists only those, the first in the reader. One record
 *  opens its reader alone. */
export function openDecisionRecords(recordIds: string[]): void {
  const ids = recordIds.map((id) => id.trim()).filter(Boolean);
  if (ids.length === 1) openDecisionRecord(ids[0]);
  else if (ids.length) useDesk.getState().openSurfaceWindow("open-decisions", `records:${ids.join(",")}`);
}

/** A calendar row: its person at Prep when the event is linked to one, else
 * its project Room, else nothing. */
export function calendarOpener(event: {
  person_relationship_id?: string | null;
  project_id?: string | null;
}): Opener | null {
  const person = (event.person_relationship_id ?? "").trim();
  if (person) return () => openPerson(person, "prep");
  const project = (event.project_id ?? "").trim();
  if (project) return () => openProjectRoom(project);
  return null;
}

/* ── owner string → relationship (POST /api/people/resolve) ─────────── */

const ownerCache = new Map<string, Promise<string | null>>();

/** The relationship an owner string names, through the People route. A
 * locked store or no match answers null: the row stays without an open. */
export function resolveOwner(owner: string): Promise<string | null> {
  const key = owner.trim().toLowerCase();
  if (!key) return Promise.resolve(null);
  let hit = ownerCache.get(key);
  if (!hit) {
    hit = apiFetch<{ relationship_id?: string | null }>("/api/people/resolve", {
      method: "POST",
      json: { identity: owner.trim() },
    })
      .then((body) => (body?.relationship_id ? String(body.relationship_id) : null))
      .catch(() => {
        ownerCache.delete(key);
        return null;
      });
    ownerCache.set(key, hit);
  }
  return hit;
}

/** Test seam. */
export function __resetOwnerCache(): void {
  ownerCache.clear();
}
