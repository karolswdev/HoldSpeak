/** PHILO-17 — compatibility identity helpers for per-object windows.
 *
 * Meetings now live inside the one `surface-meetings` window. The old
 * `meeting:<id>` identity remains here so retired saved pullouts can migrate
 * and old adapters can close cleanly. People still opens in its own pullout.
 *
 * The old doors spoke a scope to the Meetings and People applications
 * (`meeting:<id>?view=review&segment=3`, `people:<id>:prep`). This module
 * turns that scope into the window's id and keeps its place (the view, the
 * transcript row, the lens) as a request the window takes once. No store
 * import: the store calls in here. */
import type { Primitive } from "../lib/primitives";
import type { WorldObject } from "./world";
import { heldArtifactSource } from "./api";

export type MeetingView = "outcomes" | "review" | "artifacts";

export interface MeetingOpenRequest {
  meetingId: string;
  view: MeetingView;
  /** The transcript row to show (a decision moment, a recall hit). */
  segment: number | null;
  seq: number;
}

/** The event an open meeting window hears when a door asks it for a place. */
export const MEETING_OPEN_EVENT = "holdspeak:meeting-open";

const meetingRequests = new Map<string, MeetingOpenRequest>();
let meetingSeq = 0;

/** The meeting a scope names (`meeting:<id>[?…]`), with no side effect. */
export function meetingOfScope(scope: string | null | undefined): string | null {
  const clean = (scope ?? "").trim();
  if (!clean.startsWith("meeting:")) return null;
  const id = clean.slice("meeting:".length).split("?", 1)[0];
  return id || null;
}

/** `meeting:<id>[?view=…&segment=…]` → the window's object ref
 * `meeting:<id>`, or null when the scope names no meeting. A view or a
 * segment in the scope is kept for the window (`takeMeetingRequest`). */
export function meetingWindowRef(scope: string | null | undefined): string | null {
  const clean = (scope ?? "").trim();
  if (!clean.startsWith("meeting:")) return null;
  const [id, query = ""] = clean.slice("meeting:".length).split("?", 2);
  if (!id) return null;
  const params = new URLSearchParams(query);
  const view = params.get("view");
  const segmentRaw = params.get("segment");
  if (view !== null || segmentRaw !== null) {
    meetingSeq += 1;
    const segment = segmentRaw !== null && Number.isFinite(Number(segmentRaw)) ? Number(segmentRaw) : null;
    const request: MeetingOpenRequest = {
      meetingId: id,
      view: view === "review" || view === "artifacts" ? view : "outcomes",
      segment,
      seq: meetingSeq,
    };
    meetingRequests.set(id, request);
    if (typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent<MeetingOpenRequest>(MEETING_OPEN_EVENT, { detail: request }));
    }
  }
  return `meeting:${id}`;
}

/** The place a door asked for `meetingId`'s window, without taking it (a
 * render may run again; the window takes it in an effect). */
export function peekMeetingRequest(meetingId: string): MeetingOpenRequest | null {
  return meetingRequests.get(meetingId) ?? null;
}

/** The place a door asked for `meetingId`'s window, once per request. */
export function takeMeetingRequest(meetingId: string): MeetingOpenRequest | null {
  const request = meetingRequests.get(meetingId) ?? null;
  meetingRequests.delete(meetingId);
  return request;
}

/** The People lenses a door may open a person on. */
export type PersonLens = "now" | "prep";

/** PHILO-13-06 (Astra's pass): every explicit open of a person on a lens is
 * one request, counted. An open window hears it and moves to the lens. */
export const PERSON_OPEN_EVENT = "holdspeak:person-open";
export type PersonOpenRequest = { relationshipId: string; lens?: PersonLens; seq: number };
const personLenses = new Map<string, PersonLens>();
let personSeq = 0;

/** `people:<relationship id>[:<lens>]` → the person window's object ref
 * `people:<id>`, or null for the roster (`people`, `people:project:<id>`). */
export function personWindowRef(scope: string | null | undefined): string | null {
  const clean = (scope ?? "").trim();
  if (!clean.startsWith("people:")) return null;
  const rest = clean.slice("people:".length);
  if (!rest || rest === "people" || rest.startsWith("project:")) return null;
  const [id, rawLens] = rest.split(":", 2);
  if (!id) return null;
  const lens = rawLens === "now" || rawLens === "prep" ? rawLens : undefined;
  personSeq += 1;
  if (lens) personLenses.set(id, lens);
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent<PersonOpenRequest>(PERSON_OPEN_EVENT, {
      detail: { relationshipId: id, lens, seq: personSeq },
    }));
  }
  return `people:${id}`;
}

/** The lens a door asked for, without taking it (see peekMeetingRequest). */
export function peekPersonLens(relationshipId: string): PersonLens | null {
  return personLenses.get(relationshipId) ?? null;
}

/** The lens a door asked for `relationshipId`'s window, once per request. */
export function takePersonLens(relationshipId: string): PersonLens | null {
  const lens = personLenses.get(relationshipId) ?? null;
  personLenses.delete(relationshipId);
  return lens;
}

/** The object a per-object window shows when the desk's items do not hold
 * it (the desk reads the newest meetings only; a person is not a desk
 * item). The window reads the rest itself. */
export function objectWindowStandIn(ref: string): WorldObject | null {
  if (ref.startsWith("artifact:")) {
    const id = ref.slice("artifact:".length).split("#", 1)[0];
    const artifact = heldArtifactSource(id);
    return artifact ? { kind: "artifact", id, title: artifact.title, ref: artifact } : null;
  }
  if (ref.startsWith("meeting:") && ref.length > "meeting:".length) {
    const id = ref.slice("meeting:".length);
    return {
      kind: "meeting",
      id,
      title: "Meeting",
      ref: { kind: "meeting", id, title: "Meeting", startedAt: "" } as Primitive,
    };
  }
  if (ref.startsWith("people:") && ref.length > "people:".length) {
    const id = ref.slice("people:".length);
    if (id === "people" || id.startsWith("project:")) return null;
    return {
      kind: "people",
      id,
      title: "Person",
      ref: { kind: "people", id, name: "Person" } as unknown as Primitive,
    };
  }
  // Programs (2026-10-28): a Program is the hub's, not a desk item; its
  // window reads its own record (ProgramWindow).
  // PG-REQ (REQ12): a Shot requirement's image window
  // (`program-shot:<program>:<requirement>`).
  if (ref.startsWith("program-shot:") && ref.split(":").length === 3) {
    const id = ref.slice("program-shot:".length);
    return {
      kind: "program-shot" as unknown as WorldObject["kind"],
      id,
      title: "Shot",
      ref: { kind: "program-shot", id, title: "Shot" } as unknown as Primitive,
    };
  }
  if (ref.startsWith("program:") && ref.length > "program:".length) {
    const id = ref.slice("program:".length);
    return {
      // A pullout family, not a desk primitive (pullouts/registry.ts
      // PULLOUT_FAMILIES): the kind names the family.
      kind: "program" as unknown as WorldObject["kind"],
      id,
      title: "Program",
      ref: { kind: "program", id, title: "Program" } as unknown as Primitive,
    };
  }
  return null;
}
