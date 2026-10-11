// PARKED (PHILO-17 doors, 2026-10-10): the Dock's People tile carried the
// next 1:1 time ("1:1 15:00", desk-dock-people-state). People left the Dock
// (its door is the People drawer on the desk and Go), so this read left the
// Dock with it. Cut unchanged from components/window/Dock.tsx; nothing
// imports it. The drawer can pick it up if the owner wants the mark back.
import { apiFetch } from "../../../lib/api";
import { nextOneOnOneLabel, type DockRelationshipRead } from "../../components/window/dockState";

function wireRows<T>(body: unknown, key: string): T[] {
  if (Array.isArray(body)) return body as T[];
  if (!body || typeof body !== "object") return [];
  const rows = (body as Record<string, unknown>)[key];
  return Array.isArray(rows) ? rows as T[] : [];
}

type PeopleReadinessState = "unconfigured" | "locked" | "key_unavailable" | "corrupt" | "unavailable" | "ready";
const PEOPLE_READINESS_STATES: readonly PeopleReadinessState[] = [
  "unconfigured",
  "locked",
  "key_unavailable",
  "corrupt",
  "unavailable",
  "ready",
];

interface PeopleProjectionRead {
  readiness: PeopleReadinessState | null;
  nextOneOnOne: string | null;
  complete: boolean;
}

function peopleReadinessOf(body: unknown): PeopleReadinessState | null {
  if (!body || typeof body !== "object") return null;
  const value = (body as Record<string, unknown>).state ??
    (body as Record<string, unknown>).readiness;
  return PEOPLE_READINESS_STATES.includes(value as PeopleReadinessState)
    ? value as PeopleReadinessState
    : null;
}

export async function readPeopleProjection(): Promise<PeopleProjectionRead> {
  const readinessBody = await apiFetch<unknown>("/api/people/readiness");
  const readiness = peopleReadinessOf(readinessBody);
  if (readiness !== "ready") return { readiness, nextOneOnOne: null, complete: readiness !== null };

  const body = await apiFetch<unknown>("/api/people/relationships");
  const relationships = wireRows<DockRelationshipRead>(body, "relationships");
  const direct = relationships.filter((relationship) =>
    relationship.next_one_on_one !== undefined || relationship.nextOneOnOne !== undefined,
  );
  const ids = relationships
    .map((relationship) => relationship.id)
    .filter((id): id is string => Boolean(id));
  const details = await Promise.allSettled(
    ids.map((id) => apiFetch<unknown>(
      `/api/people/relationships/${encodeURIComponent(id)}/brief`,
    )),
  );
  const successfulDetails = details
    .filter((detail): detail is PromiseFulfilledResult<unknown> => detail.status === "fulfilled")
    .map((detail) => detail.value)
    .flatMap((value) => {
      const row = value && typeof value === "object"
        ? value as Record<string, unknown>
        : {};
      return [{
        brief: (row.brief && typeof row.brief === "object"
          ? row.brief
          : {}) as DockRelationshipRead,
      }];
    });
  const complete = relationships.length === 0 || direct.length === relationships.length ||
    (ids.length === relationships.length && successfulDetails.length === ids.length);
  return {
    readiness,
    nextOneOnOne: nextOneOnOneLabel([...relationships, ...successfulDetails]),
    complete,
  };
}

