// A test hub for `GET /api/desk/needs-you`.
//
// The hub applies the one needs-you rule and the faces read its answer
// (`holdspeak/services/needs_you_membership.py`). A face test that mocks the
// hub's SOURCES (the Door, the Room rows, the assignment roster, the
// meetings, the mute list) wraps its mock in `asHub`: the answer is then
// composed from those same mocked sources with `computeNeedsYou`, the
// browser statement of the rule that the real-producer oracle
// (`desk/needsYou.test.ts`, `tests/unit/test_one_needs_you_rule.py`) holds
// to the hub's own answer. A mock that already answers as the hub does
// (it carries `members`) passes through unchanged.
import { fromWireMeeting } from "../desk/api";
import {
  computeNeedsYou,
  meetingNeedsYou,
  type NeedsYouAnswer,
  type NeedsYouRoomItem,
} from "../desk/needsYou";
import type { Meeting } from "../lib/primitives";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Fetch = (path: any, ...rest: any[]) => Promise<any>;

function reason(error: unknown): string {
  return error instanceof Error ? error.message : "Request failed. Retry the read.";
}

async function summaryAttention(impl: Fetch): Promise<unknown[]> {
  const out: unknown[] = [];
  let offset = 0;
  for (;;) {
    const body = await impl(`/api/meetings?summary_attention=true&limit=500&offset=${offset}`);
    const rows: unknown[] = Array.isArray(body) ? body : Array.isArray(body?.meetings) ? body.meetings : [];
    out.push(...rows);
    const total = Number(body?.total);
    offset += rows.length;
    if (rows.length < 500 || (Number.isFinite(total) && offset >= total)) break;
  }
  return out;
}

export async function hubAnswer(impl: Fetch, path = "/api/desk/needs-you"): Promise<NeedsYouAnswer | null> {
  const room = await impl(path);
  if (room && Array.isArray(room.members)) return room;
  const value = room ?? {};
  const sourceErrors: Record<string, string> = {};
  let door = null;
  try { door = await impl("/api/door"); } catch (error) { sourceErrors.door = reason(error); }
  let assignments = null;
  let assignmentRead: "ok" | "failed" = "ok";
  try { assignments = await impl("/api/inference/assignments"); } catch (error) {
    sourceErrors.assignments = reason(error);
    assignmentRead = "failed";
  }
  let wireMeetings: unknown[] = [];
  try { wireMeetings = await summaryAttention(impl); } catch (error) { sourceErrors.meetings = reason(error); }
  let muted: string[] = [];
  try {
    const heartbeat = await impl("/api/settings/heartbeat");
    muted = Array.isArray(heartbeat?.muted_projects) ? heartbeat.muted_projects.map(String) : [];
  } catch { /* the mute list is the hub's own setting */ }

  const failing = wireMeetings.filter((row) => {
    const meeting = fromWireMeeting(row);
    return meeting !== null && meetingNeedsYou(meeting);
  });
  const roomItems: NeedsYouRoomItem[] = Array.isArray(value.items) ? value.items : [];
  const result = computeNeedsYou({
    door,
    roomItems,
    mutedProjectIds: muted,
    assignments,
    assignmentRead,
    meetings: failing.map(fromWireMeeting).filter((meeting): meeting is Meeting => meeting !== null),
  });
  return {
    ...value,
    count: result.count,
    waitingCount: result.waitingCount,
    members: result.members.map(({ ref, kind }) => ({ ref, kind })),
    items: [
      ...result.unmutedItems.map((item) => ({ ...item, muted: false })),
      ...result.mutedItems.map((item) => ({ ...item, muted: true })),
    ],
    mutedCount: result.mutedItems.length,
    blockers: result.blockers,
    failedMeetings: failing,
    roomItems,
    roomComplete: value.complete,
    complete: value.complete !== false && Object.keys(sourceErrors).length === 0,
    sourceErrors,
  };
}

/** Wrap a source-level `apiFetch` mock so the needs-you route answers as the hub does. */
export function asHub<F extends Fetch>(impl: F): F {
  return (async (path: unknown, ...rest: unknown[]) => {
    if (typeof path === "string" && path.startsWith("/api/desk/needs-you")) return hubAnswer(impl, path);
    return impl(path, ...rest);
  }) as F;
}
