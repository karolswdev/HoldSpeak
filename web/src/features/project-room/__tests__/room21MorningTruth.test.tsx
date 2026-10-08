/**
 * PHILO-15 21 — the second morning tells no lies (Room side).
 *
 * B69: the Room head and the OPEN HERE line read the hub's ONE freshness
 * state per source (the rule Needs you reads): STALE says STALE, never
 * "Clear here · CHECKED 10H AGO"; quiet hours read QUIET UNTIL 08:00, never
 * a next check in the past. B70: a done action's row reads DONE · <time>.
 * B72: an update list row names the model and its host, never `ia_…`.
 * B75: a GitHub sign-in from gh's file is ready on the Door.
 */
import { render, screen } from "@testing-library/react";
import { useState, type ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { EMPTY_ITEMS } from "../../../desk/api";
import { TitleSlotContext } from "../../../desk/surface/title";
import { WingSlotContext } from "../../../desk/surface/wings";
import { useDesk } from "../../../desk/store";
import { ProjectRoomCore } from "../ProjectRoomCore";
import { generatorChipBoundary } from "../update/UpdatePosture";
import { isUsable } from "../door/useDoorController";

const apiFetch = vi.fn();
vi.mock("../../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../../lib/api")>("../../../lib/api");
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});
vi.mock("../../../desk/shell", async () => {
  const actual = await vi.importActual<typeof import("../../../desk/shell")>("../../../desk/shell");
  return { ...actual, openPrimitive: vi.fn(), openSurfaceOr: vi.fn() };
});

function WindowHarness({ scope }: { scope?: string }) {
  const [wings, setWings] = useState<ReactNode>(null);
  return (
    <TitleSlotContext.Provider value={() => {}}>
      <WingSlotContext.Provider value={setWings}>
        <div data-testid="wing-slot">{wings}</div>
        <ProjectRoomCore scope={scope} />
      </WingSlotContext.Provider>
    </TitleSlotContext.Provider>
  );
}

const TEN_HOURS_AGO = new Date(Date.now() - 10 * 3600_000).toISOString();
const QUIET_END = (() => {
  const d = new Date(Date.now() + 3600_000);
  d.setMinutes(0, 0, 0);
  return d.toISOString();
})();
const pad = (n: number) => String(n).padStart(2, "0");
const hhmm = (iso: string) => {
  const d = new Date(iso);
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`;
};

let freshness: "stale" | "quiet" = "stale";
let decisions: unknown[] = [];

function roomResponse() {
  return {
    project_id: "p1", revision: 3, observed_at: "2026-10-08T07:05:00",
    project: {
      id: "p1", name: "Rehearsal repo hygiene", description: null, is_archived: false,
      meeting_count: 1, created_at: "2026-10-07T00:00:00", updated_at: "2026-10-08T07:05:00",
      purpose: null, outcome_text: "Rehearsal repo hygiene", owner_ref: null, lifecycle: "active",
      posture: null, posture_reason: null, start_at: "2026-10-07", target_at: null, revision: 3,
    },
    items: { state: "ok", focus: [], totals_by_type: {}, total: 0 },
    meetings: { state: "ok", count: 1, latest: null },
    resources: { state: "ok", count: 0, latest: null },
    changes: { state: "ok", recent: [] },
    review: { state: "absent", reason: "not_yet_built" },
    needsYou: { state: "ok", items: [], count: 0 },
    sources: {
      state: "ok",
      items: [{
        watchId: "w-gh", watchIds: ["w-gh"], provider: "github",
        scope: "karolswdev/holdspeak-dayone-rehearsal-1558", tokens: ["CLEAR"], checkedAt: TEN_HOURS_AGO,
        host: "github.com", state: "live", plainReason: null, suggested: false,
        nextCheckAt: freshness === "quiet" ? QUIET_END : new Date(Date.now() + 60_000).toISOString(),
        freshness, ...(freshness === "quiet" ? { quietUntil: QUIET_END } : {}),
      }],
      count: 1,
      nextCheckAt: freshness === "quiet" ? QUIET_END : new Date(Date.now() + 60_000).toISOString(),
      quietUntil: freshness === "quiet" ? QUIET_END : null,
    },
    health: { state: "ok", assessment: "on_track", reason: null, inputs: { overdue: 0, ciFailing: false, reviewWaitingDays: null, targetPassed: false } },
    sinceRead: { state: "ok", readAt: null, groups: [] },
    decisions: { state: "ok", items: decisions },
    commitments: { state: "ok", items: [] },
    target: { state: "absent", reason: "none" },
  };
}

function response(url: string) {
  if (url.includes("/room/read")) return { read_at: new Date().toISOString() };
  if (url.includes("/room")) return roomResponse();
  if (url.includes("/meetings")) return { meetings: [] };
  if (url.startsWith("/api/decisions")) return { decisions: [] };
  if (url.includes("/artifacts")) return { artifacts: [] };
  if (url.includes("/since-last-meeting")) return { current_meeting: null, since_last_meeting: null };
  return {};
}

beforeEach(() => {
  freshness = "stale";
  decisions = [];
  apiFetch.mockImplementation((url: string) => Promise.resolve(response(url)));
  useDesk.setState({ windowsById: {}, items: { ...EMPTY_ITEMS }, projects: [], inferenceTargets: [] });
});
afterEach(() => vi.clearAllMocks());

describe("B69: one state per source on the Room", () => {
  it("a STALE source reads STALE on the head and the row, never Clear here", async () => {
    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("room-body");
    expect(screen.getByTestId("room-headline").textContent).toBe("Not all read");
    expect(screen.getByTestId("room-sources-word").textContent).toMatch(/^STALE · CHECKED /);
    expect(screen.getByTestId("source-freshness").textContent).toContain("STALE");
  });

  it("quiet hours read QUIET UNTIL on the head, the row and OPEN HERE; no next check in the past", async () => {
    freshness = "quiet";
    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("room-body");
    expect(screen.getByTestId("room-headline").textContent).toBe("Clear here");
    expect(screen.getByTestId("room-sources-word").textContent).toBe(`QUIET UNTIL ${hhmm(QUIET_END)}`);
    expect(screen.getByTestId("source-freshness").textContent).toContain(`QUIET UNTIL ${hhmm(QUIET_END)}`);
    expect(screen.getByTestId("needs-you-empty").textContent).toBe(`Nothing open · quiet until ${hhmm(QUIET_END)}`);
  });
});

describe("B70: a done action says DONE", () => {
  it("the decision row of a done action reads DONE · <time>, not CONFIRMED", async () => {
    const doneAt = "2026-10-08T03:42:00+00:00";
    decisions = [{
      id: "dr-1", text: "Add a CODEOWNERS file", at: "2026-10-07T21:14:00", url: null, kind: "action",
      proposal_id: "p-1", source: "meeting", meeting_title: "Repo hygiene sync",
      confirmed_at: "2026-10-08T03:14:00+00:00", commitment_id: "c-1", done: true, done_at: doneAt,
    }];
    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("room-body");
    expect((await screen.findByTestId("done-state")).textContent).toBe(`DONE · ${hhmm(doneAt)}`);
    expect(screen.queryByTestId("confirmed-state")).toBeNull();
  });
});

describe("B72: a model draft names its model and host", () => {
  it("never the assignment id", () => {
    expect(generatorChipBoundary({
      generator: "model:ia_0488064ec64348ab8679b509e8952a60",
      generatorModel: "qwen3.8-27b", generatorHost: "192.168.1.43:8080",
    })).toBe("QWEN3.8-27B · 192.168.1.43:8080 · LAN");
    expect(generatorChipBoundary({ generator: "model:ia_1", generatorModel: null, generatorHost: null })).toBeUndefined();
    expect(generatorChipBoundary({ generator: "deterministic" })).toBeUndefined();
  });
});

describe("B75: one sign-in truth on the Door", () => {
  it("a sign-in from gh's own file is ready, as a probe's connected is", () => {
    expect(isUsable("signed_in")).toBe(true);
    expect(isUsable("connected")).toBe(true);
    expect(isUsable("never_checked")).toBe(false);
    expect(isUsable("owner_action_required")).toBe(false);
  });
});
