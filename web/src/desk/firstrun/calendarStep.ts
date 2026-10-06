/* First run, option A "One screen" (owner ratified 2026-10-05) — the
 * Calendar step. The reads and writes are the onboarding routes (PR #868):
 *
 *   GET  /api/onboarding/calendar              macOS calendars; never prompts
 *   POST /api/onboarding/calendar/macos/access  the macOS prompt (his press only)
 *   POST /api/onboarding/calendar/check {url}   reads one ICS link once
 *   POST /api/onboarding/calendar/use {id}      adds the calendar source
 *
 * and the Door read (`GET /api/door`) for what the calendar holds: the week's
 * count and the next meeting. The ingest reads a new source in the
 * background, so after "Use it" the face reads the Door again a few times. */
import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, apiFetch, readableError } from "../../lib/api";

export const CALENDAR_PATH = "/api/onboarding/calendar";
export const CALENDAR_ACCESS_PATH = "/api/onboarding/calendar/macos/access";
export const CALENDAR_CHECK_PATH = "/api/onboarding/calendar/check";
export const CALENDAR_USE_PATH = "/api/onboarding/calendar/use";
export const DOOR_PATH = "/api/door";

export type MacosState =
  | "not_determined"
  | "restricted"
  | "denied"
  | "full_access"
  | "write_only"
  | "unavailable";

export interface CalendarCandidate {
  id: string;
  kind: "macos" | "ics";
  label: string;
  account: string;
  calendar_kind?: string;
  lamp: string;
  egress_host: string | null;
  in_use: boolean;
  verb: string | null;
}

export interface CalendarDetect {
  macos: { state: MacosState; can_request: boolean; requested?: MacosState };
  candidates: CalendarCandidate[];
  sources: number;
}

export interface CalendarCheck {
  url: string;
  host: string;
  lamp: string;
  ok: boolean;
  candidate?: CalendarCandidate;
  events_next_days?: number;
  horizon_days?: number;
  error_class?: string;
  redirect_target?: string | null;
}

export interface UpcomingEvent {
  id: string;
  source: string;
  title: string;
  starts_at: string;
  armed_schedule_id?: string;
}

export interface DoorRead {
  upcoming?: UpcomingEvent[];
  calendar_configured?: boolean;
  week?: { total?: number; has_calendar?: boolean };
}

/** `FOUND · 2`: a state word and its count, or null at zero (UX-CANON A8). */
export function stateCount(word: string, count: number): string | null {
  return count > 0 ? `${word} · ${count}` : null;
}

/** The plain reason of a link the hub could not read, as one token. */
export function cantReadReason(errorClass: string | undefined, redirect?: string | null): string {
  switch (errorClass) {
    case "calendar_url_invalid":
    case "calendar_source_invalid":
      return "NOT A CALENDAR LINK";
    case "calendar_source_redirect": {
      const host = hostOf(redirect || "");
      return host ? `MOVED TO ${host.toUpperCase()}` : "LINK MOVED";
    }
    case "calendar_source_http_error":
      return "SERVER REFUSED";
    case "calendar_source_timeout":
      return "TIMED OUT";
    case "calendar_source_network_error":
      return "NO CONNECTION";
    case "calendar_source_too_large":
      return "TOO LARGE";
    default:
      return "NOT A CALENDAR";
  }
}

/** The host of a typed link (`webcal://` reads as `https://`), or "". */
export function hostOf(text: string): string {
  const raw = text.trim();
  if (!raw) return "";
  const url = raw.toLowerCase().startsWith("webcal://") ? `https://${raw.slice(9)}` : raw;
  try {
    const parsed = new URL(url);
    return parsed.protocol === "https:" ? parsed.hostname.toLowerCase() : "";
  } catch {
    return "";
  }
}

/** `10:30` today, else `TUE 10:30` (the Chair's NEXT clock). */
export function meetingClock(iso: string, now: Date = new Date()): string {
  const at = new Date(iso);
  if (Number.isNaN(at.getTime())) return "";
  const hhmm = `${String(at.getHours()).padStart(2, "0")}:${String(at.getMinutes()).padStart(2, "0")}`;
  const today =
    at.getFullYear() === now.getFullYear() && at.getMonth() === now.getMonth() && at.getDate() === now.getDate();
  if (today) return hhmm;
  return `${["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"][at.getDay()]} ${hhmm}`;
}

/** The next calendar meeting that has not started, or null. */
export function nextMeeting(door: DoorRead | null, now: Date = new Date()): UpcomingEvent | null {
  const rows = Array.isArray(door?.upcoming) ? door!.upcoming! : [];
  return (
    rows.find((row) => row.source === "calendar_event" && new Date(row.starts_at).getTime() > now.getTime()) ?? null
  );
}

type Busy = null | "access" | "add" | string;
export type CalendarFailure =
  | { kind: "cant_read"; reason: string; host: string }
  | { kind: "not_allowed" }
  | { kind: "refused"; reason: string };

export const SETTINGS_PATH = "/api/settings";
export const CALENDAR_SOURCES_PATH = "/api/calendar/sources";

/** A configured calendar source, as GET /api/settings carries it. */
export interface ConfiguredSource {
  id: string;
  url: string;
  enabled: boolean;
}

/** One enabled source's read state, as GET /api/calendar/sources reports it. */
interface SourceRead {
  id: string;
  status: string;
}

/** A row as the face draws it: IN USE only for an ENABLED source. */
export type CalendarRow = CalendarCandidate & { off: boolean };

/** How often and how long the face follows the ingest after "Use it". */
const FOLLOW_MS = 1000;
const FOLLOW_READS = 20;

/** IN USE per row: the row's source is configured AND enabled. A disabled
 * source is OFF (Settings turns it on); the candidate's own `in_use` (any
 * configured source, enabled or not) is not used. */
export function calendarRows(rows: CalendarCandidate[], sources: ConfiguredSource[]): CalendarRow[] {
  const byUrl = new Map(sources.map((source) => [source.url, source]));
  return rows.map((row) => {
    const source = byUrl.get(row.id);
    return { ...row, in_use: Boolean(source?.enabled), off: Boolean(source && !source.enabled) };
  });
}

export function useCalendarStep() {
  const [detect, setDetect] = useState<CalendarDetect | null>(null);
  const [unread, setUnread] = useState("");
  const [busy, setBusy] = useState<Busy>(null);
  const [failure, setFailure] = useState<CalendarFailure | null>(null);
  const [added, setAdded] = useState<CalendarCandidate[]>([]);
  const [sources, setSources] = useState<ConfiguredSource[]>([]);
  const [door, setDoor] = useState<DoorRead | null>(null);
  const [following, setFollowing] = useState(false);
  const pending = useRef<Set<string>>(new Set());
  const timer = useRef<number | null>(null);

  const readSources = useCallback(async () => {
    const answer = await apiFetch<{ calendar?: { sources?: ConfiguredSource[] } }>(SETTINGS_PATH).catch(() => null);
    const list = answer?.calendar?.sources;
    if (Array.isArray(list)) setSources(list.map((s) => ({ id: String(s.id), url: String(s.url), enabled: s.enabled !== false })));
  }, []);

  const read = useCallback(async () => {
    try {
      setDetect(await apiFetch<CalendarDetect>(CALENDAR_PATH));
      setUnread("");
    } catch (error) {
      setUnread(readableError(error));
    }
    await readSources();
  }, [readSources]);

  /** The Door as it is now: the week, the next meeting, `calendar_configured`. */
  const readDoor = useCallback(async () => {
    const answer = await apiFetch<DoorRead>(DOOR_PATH).catch(() => null);
    if (answer) setDoor(answer);
    return answer;
  }, []);

  useEffect(() => {
    void read();
    void readDoor();
    return () => {
      if (timer.current !== null) window.clearTimeout(timer.current);
    };
  }, [read, readDoor]);

  /** Follow the ingest: read the Door on each tick until every source added
   * here reports a finished read (`status: success`), or the reads run out.
   * An earlier event already on the Door never stops the follow. */
  const follow = useCallback(
    (sourceId: string) => {
      if (sourceId) pending.current.add(sourceId);
      if (timer.current !== null) window.clearTimeout(timer.current);
      setFollowing(true);
      let reads = 0;
      const tick = async () => {
        reads += 1;
        const answer = await apiFetch<{ sources?: SourceRead[] }>(CALENDAR_SOURCES_PATH).catch(() => null);
        for (const row of answer?.sources ?? []) {
          if (row.status === "success") pending.current.delete(String(row.id));
        }
        await readDoor();
        if (pending.current.size === 0 || reads >= FOLLOW_READS) {
          pending.current.clear();
          timer.current = null;
          setFollowing(false);
          return;
        }
        timer.current = window.setTimeout(() => void tick(), FOLLOW_MS);
      };
      timer.current = window.setTimeout(() => void tick(), FOLLOW_MS);
    },
    [readDoor],
  );

  /** The owner's press: the macOS Calendars prompt. Never on load. */
  const requestAccess = useCallback(async () => {
    setBusy("access");
    setFailure(null);
    try {
      setDetect(await apiFetch<CalendarDetect>(CALENDAR_ACCESS_PATH, { method: "POST" }));
    } catch (error) {
      setFailure({ kind: "refused", reason: readableError(error) });
    } finally {
      setBusy(null);
    }
  }, []);

  const use = useCallback(
    async (candidate: CalendarCandidate) => {
      setBusy(candidate.id);
      setFailure(null);
      try {
        const answer = await apiFetch<{ source?: { id?: string } }>(CALENDAR_USE_PATH, {
          method: "POST",
          json: { id: candidate.id, label: candidate.label },
        });
        if (candidate.kind === "ics") setAdded((prev) => [...prev.filter((c) => c.id !== candidate.id), candidate]);
        await read();
        await readDoor();
        follow(String(answer?.source?.id ?? ""));
      } catch (error) {
        if (error instanceof ApiError && error.status === 409) {
          setFailure({ kind: "not_allowed" });
          await read();
        } else {
          setFailure({ kind: "refused", reason: readableError(error) });
        }
      } finally {
        setBusy(null);
      }
    },
    [read, readDoor, follow],
  );

  /** Add: read the typed link once (egress to its host), then use it. */
  const addUrl = useCallback(
    async (url: string) => {
      const host = hostOf(url);
      setBusy("add");
      setFailure(null);
      let check: CalendarCheck;
      try {
        check = await apiFetch<CalendarCheck>(CALENDAR_CHECK_PATH, { method: "POST", json: { url } });
      } catch (error) {
        const code = error instanceof ApiError ? errorCode(error) : "";
        setFailure(
          code === "calendar_url_invalid"
            ? { kind: "cant_read", reason: cantReadReason(code), host }
            : { kind: "refused", reason: readableError(error) },
        );
        setBusy(null);
        return false;
      }
      setBusy(null);
      if (!check.ok || !check.candidate) {
        setFailure({ kind: "cant_read", reason: cantReadReason(check.error_class, check.redirect_target), host: check.host || host });
        return false;
      }
      await use(check.candidate);
      return true;
    },
    [use],
  );

  const candidates = detect?.candidates ?? [];
  const macos = detect?.macos ?? null;
  const rows = calendarRows(
    [...candidates, ...added.filter((a) => !candidates.some((c) => c.id === a.id))],
    sources,
  );
  // IN USE: the Door's own fact — at least one ENABLED source that passes
  // validation (door_service `_calendar_configured`). Never a raw count.
  const inUse = door?.calendar_configured === true;
  const deniedState = macos && ["denied", "restricted", "write_only"].includes(macos.state);
  return {
    loaded: detect !== null || unread !== "",
    unread,
    macos,
    rows,
    inUse,
    following,
    notAllowed: Boolean(deniedState) || failure?.kind === "not_allowed",
    busy,
    failure,
    door,
    week: door?.week?.total ?? 0,
    next: nextMeeting(door),
    read,
    readDoor,
    requestAccess,
    use,
    addUrl,
  };
}

function errorCode(error: ApiError): string {
  const payload = (error.payload && typeof error.payload === "object" ? error.payload : {}) as { code?: unknown };
  return typeof payload.code === "string" ? payload.code : "";
}

export type CalendarStep = ReturnType<typeof useCalendarStep>;
