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
import { openDrawer } from "./drawer/store";
import { openIntelligence } from "./intelligenceNavigation";
import { openAgentLane, openCoderSession, openProjectRoom, openSurfaceOr } from "./shell";
import { openSourceRef } from "./surface";

export type Opener = () => void;

/** The People lenses a row may open on (`PeopleCore` scope grammar). */
export type PersonLens = "now" | "prep";

/** The People surface on one relationship: `people:<id>[:<lens>]`. */
export function personScope(relationshipId: string, lens?: PersonLens): string {
  return `people:${relationshipId}${lens ? `:${lens}` : ""}`;
}

/** PHILO-13-06 (Astra's pass): every explicit open of a person on a lens is
 * one request, counted. An open with an unchanged scope (the same 1:1 row
 * tapped again after he chose Now) still re-applies the lens: the People
 * window hears the request, not only the scope. */
export const PERSON_OPEN_EVENT = "holdspeak:person-open";
export type PersonOpenRequest = { relationshipId: string; lens?: PersonLens; seq: number };
let personOpenSeq = 0;

export function openPerson(relationshipId: string, lens?: PersonLens): void {
  openSurfaceOr("open-people", "/", personScope(relationshipId, lens));
  personOpenSeq += 1;
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent<PersonOpenRequest>(PERSON_OPEN_EVENT, {
      detail: { relationshipId, lens, seq: personOpenSeq },
    }));
  }
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

/** PHILO-14 A2b (Astra r1 on #945) — a proposal is an object: its row opens
 *  the destination that contains it, the Room with that proposal selected.
 *  The Room takes the request once (a reload does not replay it). */
export const ROOM_PROPOSAL_EVENT = "holdspeak:room-proposal";
const roomProposals = new Map<string, string>();

export function openProjectProposal(projectId: string, proposalId: string): void {
  const id = projectId.trim();
  if (!id) return;
  if (proposalId.trim()) roomProposals.set(id, proposalId.trim());
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
export type RoomPlace = "history" | "steward";
const roomPlaces = new Map<string, RoomPlace>();

export function openProjectRoomAt(projectId: string, place: RoomPlace): void {
  const id = projectId.trim();
  if (!id) return;
  roomPlaces.set(id, place);
  openProjectRoom(id);
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent<string>(ROOM_AT_EVENT, { detail: id }));
  }
}

/** The place to open `projectId`'s Room at, once per request. */
export function takeRoomAtRequest(projectId: string | null | undefined): RoomPlace | null {
  if (!projectId) return null;
  const place = roomPlaces.get(projectId) ?? null;
  roomPlaces.delete(projectId);
  return place;
}

/** The proposal to select in `projectId`'s Room, once per request. */
export function takeRoomProposalRequest(projectId: string | null | undefined): string | null {
  if (!projectId) return null;
  const proposal = roomProposals.get(projectId) ?? null;
  roomProposals.delete(projectId);
  return proposal;
}

/** True once for each request to open `projectId`'s Room in its Update posture. */
export function takeRoomUpdatesRequest(projectId: string | null | undefined): boolean {
  return !!projectId && roomUpdates.delete(projectId);
}

/** The event the Desk's attention drawer listens for to open the system
 * shade (its held tool calls, Needs you). */
export const OPEN_SYSTEM_SHADE_EVENT = "hs-open-system-shade";

export function openSystemShade(): void {
  window.dispatchEvent(new CustomEvent(OPEN_SYSTEM_SHADE_EVENT));
}

/** Refs the citation species opens in a window of their own. */
const WINDOW_REF = /^(meeting|decision|note|artifact|thread):\S/;
// `action:` is memory's name for the same action item (a recall hit, a chat citation).
const FOLLOW_THROUGH_REF = /^(?:follow-through|action_item|action):(.+)$/;

/** The opener for a qualified ref, or null when the ref names nothing that
 * opens (a count, a coverage line, a pipeline event). */
export function refOpener(ref: string | null | undefined): Opener | null {
  const clean = (ref ?? "").trim();
  if (!clean) return null;
  if (clean.startsWith("people:")) {
    const id = clean.slice("people:".length);
    if (!id || id.startsWith("project:")) return null;
    return () => openPerson(id);
  }
  // PHILO-14 A2: a Project opens as its drawer (the Room is one press away,
  // in the drawer's head).
  if (clean.startsWith("project:")) {
    const id = clean.slice("project:".length);
    return id ? () => openDrawer(id) : null;
  }
  // Conductor F2: a Needs you coder row (R5) is `coder:<agent>:<session_id>`;
  // it opens the agent's session window.
  if (clean.startsWith("coder:")) {
    const key = clean.slice("coder:".length);
    return key.includes(":") ? () => openCoderSession(key) : null;
  }
  // PHILO-14 C2: a launched agent is `launch:<launch_id>`; it opens its lane.
  if (clean.startsWith("launch:")) {
    const id = clean.slice("launch:".length);
    return id ? () => openAgentLane(id) : null;
  }
  // Conductor R1: a held tool call of a launched agent is `gate:<proposal_id>`;
  // it opens the system shade, where the held call is listed.
  if (clean.startsWith("gate:")) {
    return clean.length > "gate:".length ? () => openSystemShade() : null;
  }
  const followThrough = FOLLOW_THROUGH_REF.exec(clean);
  if (followThrough) {
    const id = followThrough[1];
    return () => openIntelligence({ view: "follow-through", followThroughId: id });
  }
  // A desk decision has one ref name (`desk_decision:<id>`); its window is
  // the decision window.
  if (clean.startsWith("desk_decision:")) {
    const id = clean.slice("desk_decision:".length);
    return id ? () => openSourceRef(`decision:${id}`) : null;
  }
  if (clean.startsWith("decision:")) return () => openDecision(clean);
  if (WINDOW_REF.test(clean)) return () => openSourceRef(clean);
  return null;
}

/** Open a cited ref (a claim's source, a memory citation): the one open
 * grammar first; a ref it does not name goes to the citation species. Memory
 * ranks the child message that matched; the Desk opens the parent thread. */
export function openRef(ref: string): void {
  const clean = ref.startsWith("thread:") ? ref.split("#", 1)[0] : ref.trim();
  const open = refOpener(clean);
  if (open) open();
  else openSourceRef(clean);
}

/** A decision ref names a Desk decision (its own window) or a decision a
 * meeting recorded (`decisions` lifecycle rows, no Desk window): that one
 * opens its meeting, where it was made. One read tells which. */
function openDecision(ref: string): void {
  const id = ref.slice("decision:".length);
  void apiFetch<{ decision?: { source_meeting_id?: string | null } }>(`/api/decisions/${encodeURIComponent(id)}`)
    .then((body) => {
      const meeting = (body?.decision?.source_meeting_id ?? "").trim();
      openSourceRef(meeting ? `meeting:${meeting}` : ref);
    })
    .catch(() => openSourceRef(ref));
}

/** PHILO-14 A2b (Astra r1 on #945) — a decision record (`decision_record:
 *  <record id>`, `record-<hex>`) is not a `decisions` row: it opens the
 *  decision it was made from (its source), read from the record's own route.
 *  Not in `refOpener`: memory leaves record refs out (memoryRefsOpen). */
export function decisionRecordSourceRef(sourceType: unknown, sourceId: unknown): string | null {
  const id = String(sourceId ?? "").trim();
  if (!id) return null;
  if (sourceType === "desk") return `desk_decision:${id}`;
  if (sourceType === "meeting" || sourceType === "decision") return `decision:${id}`;
  return null;
}

export function openDecisionRecord(recordId: string): void {
  const id = recordId.trim();
  if (!id) return;
  void apiFetch<{ source_type?: string; source_id?: string; sources?: { source_type?: string; source_ref?: string }[] }>(
    `/api/decision-records/${encodeURIComponent(id)}`,
  )
    .then((record) => {
      const ref = decisionRecordSourceRef(record?.source_type, record?.source_id);
      if (ref) return openRef(ref);
      const meeting = (record?.sources ?? []).find((s) => s.source_type === "meeting" && s.source_ref);
      if (meeting) openSourceRef(`meeting:${String(meeting.source_ref).replace(/^meeting:/, "")}`);
    })
    .catch(() => undefined);
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
  if (project) return () => openDrawer(project);
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
