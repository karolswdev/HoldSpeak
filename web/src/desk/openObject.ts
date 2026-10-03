/** PHILO-13-06 (B1) — one open grammar: a named row opens its object in its
 * own window (the owner's fork 2, 2026-10-01: "Opens its own window").
 *
 * Every row that names an object asks this module for its opener. The
 * answer is a function, or null when the row names nothing that opens; a
 * null row draws no open (UX-CANON A.11: a verb that does nothing is a lie).
 * The opens go through the existing dispatch only: the citation species
 * (`openSourceRef`), `openProjectRoom`, the People surface, Intelligence. */
import { apiFetch } from "../lib/api";
import { openIntelligence } from "./intelligenceNavigation";
import { openProjectRoom, openSurfaceOr } from "./shell";
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

/** True once for each request to open `projectId`'s Room in its Update posture. */
export function takeRoomUpdatesRequest(projectId: string | null | undefined): boolean {
  return !!projectId && roomUpdates.delete(projectId);
}

/** Refs the citation species opens in a window of their own. */
const WINDOW_REF = /^(meeting|decision|note|artifact|thread):\S/;
const FOLLOW_THROUGH_REF = /^(?:follow-through|action_item):(.+)$/;

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
  if (clean.startsWith("project:")) {
    const id = clean.slice("project:".length);
    return id ? () => openProjectRoom(id) : null;
  }
  const followThrough = FOLLOW_THROUGH_REF.exec(clean);
  if (followThrough) {
    const id = followThrough[1];
    return () => openIntelligence({ view: "follow-through", followThroughId: id });
  }
  if (clean.startsWith("decision:")) return () => openDecision(clean);
  if (WINDOW_REF.test(clean)) return () => openSourceRef(clean);
  return null;
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
