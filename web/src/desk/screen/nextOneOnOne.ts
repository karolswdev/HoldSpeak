/** PHILO-17 (doors) — the next 1:1 on the People drawer.
 *
 *  The Dock's People tile carried the next 1:1 time (`1:1 15:00`). People
 *  left the Dock (its door is the drawer on the desk and Go), so the mark
 *  moved with it: the same read, People readiness first, then the
 *  relationships and (when the list rows do not carry it) their briefs.
 *  Nothing shows when People is not ready, a read fails, or there is no
 *  next 1:1. */
import { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch } from "../../lib/api";
import { useOnDeskChanged } from "../useDeskChangedRefresh";
import { formatDockTime, nextOneOnOneLabel, type DockRelationshipRead } from "../components/window/dockState";

function wireRows<T>(body: unknown, key: string): T[] {
  if (Array.isArray(body)) return body as T[];
  if (!body || typeof body !== "object") return [];
  const rows = (body as Record<string, unknown>)[key];
  return Array.isArray(rows) ? rows as T[] : [];
}

type PeopleReadinessState = "unconfigured" | "locked" | "key_unavailable" | "corrupt" | "unavailable" | "no_key_store" | "ready";
const PEOPLE_READINESS_STATES: readonly PeopleReadinessState[] = [
  "unconfigured",
  "no_key_store",
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


/** The People drawer's caption: `1:1 15:00`, or null (nothing to show). */
export function useNextOneOnOne(): string | null {
  return useNextOneOnOneRead().label;
}

/** The caption and whether its first read is still out: the caption adds a
 *  line to the drawer, so the Screen marks the People drawer busy until the
 *  read ends (a late caption moved the Conductor drawer 24 px under load). */
export function useNextOneOnOneRead(): { label: string | null; reading: boolean } {
  const [label, setLabel] = useState<string | null>(null);
  const [reading, setReading] = useState(true);
  // The newest read wins: an older answer that lands late is dropped.
  const generation = useRef(0);
  const read = useCallback(() => {
    const mine = ++generation.current;
    readPeopleProjection()
      .then((people) => {
        if (mine !== generation.current) return;
        setReading(false);
        if (people.readiness !== "ready" || !people.complete || !people.nextOneOnOne) setLabel(null);
        else setLabel(`1:1 ${formatDockTime(people.nextOneOnOne)}`);
      })
      .catch(() => {
        if (mine !== generation.current) return;
        setReading(false);
        setLabel(null);
      });
  }, []);
  useEffect(read, [read]);
  useOnDeskChanged(read);
  return { label, reading };
}
