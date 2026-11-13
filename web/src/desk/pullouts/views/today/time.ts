/** Today's clock and day words (moved out of TodayView, 2026-11-08). */
import { wireDate } from "../../../surface";
import { meetingRowState } from "../../../../pages/cores/history/helpers";
import { clockOf } from "../../../surface/format";

/** Icons D: the 20 px drawings that lead a row of the day. */
export const GLYPHS = `${import.meta.env.BASE_URL || "/_built/"}desk/sprites/20/`;

/** One row of the Door's `upcoming` (a calendar event or an armed recording). */
export type DayEvent = {
  id: string;
  source?: string;
  title?: string;
  event_title?: string;
  starts_at: string;
  ends_at?: string | null;
  person_label?: string;
  person_relationship_id?: string;
  project_id?: string;
  project_name?: string;
  armed?: { recording_id: string; arms_at?: string | null; state?: string } | null;
  armed_schedule_id?: string;
  people_count?: number;
  you_owe_count?: number;
};
export type WeekDay = { date: string; dow: string; count: number };
export type DoorRead = { upcoming?: DayEvent[]; calendar_configured?: boolean; week?: { days?: WeekDay[]; has_calendar?: boolean } };
export type MeetingRow = Record<string, unknown>;

export const SHORT_DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
export const WEEK_DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
export const SHORT_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export const pad = (n: number) => String(n).padStart(2, "0");
export const clock = (d: Date) => clockOf(d);
export const startOfDay = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
export function when(value: unknown): Date | null {
  return wireDate(value);
}

export const LONG_DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

/** DELIGHT slice 2 (2026-10-27, canvases/delight-2026-10-27.html "Today
 *  knows the hour"): the part of the day, from the clock. Night is before
 *  05:00 and from 22:00. */
export type DayPart = "morning" | "afternoon" | "evening" | "night";
export function dayPart(d: Date): DayPart {
  const h = d.getHours();
  if (h < 5 || h >= 22) return "night";
  if (h < 12) return "morning";
  if (h < 18) return "afternoon";
  return "evening";
}

/** The day line greets by the hour: `Tuesday morning`. */
export function dayGreeting(d: Date): string {
  return `${LONG_DAYS[d.getDay()]} ${dayPart(d)}`;
}

/** The day's light on Today's paper: a warm wash in the morning, none in
 *  the afternoon, a cool wash in the evening and at night (static colour,
 *  at most 6 % tint; today.css). */
export function dayLight(d: Date): "warm" | "cool" | undefined {
  const part = dayPart(d);
  if (part === "morning") return "warm";
  if (part === "afternoon") return undefined;
  return "cool";
}


/** `in 68 min`, `in 2 h 05 min`, `now`. */
export function countdown(start: Date, now: Date): string {
  const minutes = Math.ceil((start.getTime() - now.getTime()) / 60_000);
  if (minutes <= 0) return "now";
  if (minutes < 60) return `in ${minutes} min`;
  return `in ${Math.floor(minutes / 60)} h ${pad(minutes % 60)} min`;
}

/** The meetings still to finish: a recorded meeting whose summary is not
 *  made (or failed) from the last seven days, newest first. */
export function toFinish(rows: MeetingRow[], now: Date): MeetingRow[] {
  const since = now.getTime() - 7 * 86_400_000;
  return rows.filter((row) => {
    const at = when(row.started_at ?? row.created_at);
    if (!at || at.getTime() < since) return false;
    const verb = meetingRowState(row).verb;
    return verb === "Run summary" || verb === "Retry";
  });
}

/** The step of the next meeting: 0 Prep, 1 Record, 2 Summary, 3 Send. */
export function currentStep(event: DayEvent, now: Date): number {
  const start = when(event.starts_at);
  if (start && start.getTime() <= now.getTime()) return 1;
  if (event.armed || event.source === "scheduled_recording") return 1;
  return 0;
}

/** The local day of `d`, `YYYY-MM-DD`. */
export function localDay(d: Date): string {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}
