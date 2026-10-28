/**
 * HS-175 counsel C7(b) + C8 on the Room's SOURCES rows: a paused Watch
 * says PAUSED beside its Resume verb (MTG / GH / J alike); CHECKED prints
 * the viewer's local clock from the hub's offset-carrying instant.
 */
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { useState, type ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { EMPTY_ITEMS } from "../../../desk/api";
import { TitleSlotContext } from "../../../desk/surface/title";
import { WingSlotContext } from "../../../desk/surface/wings";
import { useDesk } from "../../../desk/store";
import { ProjectRoomCore } from "../ProjectRoomCore";

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

const CHECKED_AT = "2026-09-05T23:47:00+00:00";

function roomResponse() {
  return {
    project_id: "p1", revision: 3, observed_at: "2026-09-04T10:00:00",
    project: {
      id: "p1", name: "Ship the Q4 platform", description: null, is_archived: false,
      meeting_count: 1, created_at: "2026-08-01T00:00:00", updated_at: "2026-09-04T10:00:00",
      purpose: null, outcome_text: "Ship the Q4 platform", owner_ref: null, lifecycle: "active",
      posture: null, posture_reason: null, start_at: "2026-08-01", target_at: null, revision: 3,
    },
    items: { state: "ok", focus: [], totals_by_type: {}, total: 0 },
    meetings: { state: "ok", count: 1, latest: null },
    resources: { state: "ok", count: 0, latest: null },
    changes: { state: "ok", recent: [] },
    review: { state: "absent", reason: "not_yet_built" },
    needsYou: { state: "ok", items: [], count: 0 },
    sources: {
      state: "ok",
      items: [
        { watchId: "w-gh", watchIds: ["w-gh"], provider: "github", scope: "acme/app", tokens: ["2 OPEN PRS"], checkedAt: CHECKED_AT, host: "github.com", state: "paused", plainReason: null, suggested: false, nextCheckAt: null },
        { watchId: "w-mtg", watchIds: ["w-mtg"], provider: "meeting", scope: "MEETINGS", tokens: ["1 THIS WEEK", "NEXT THU 08:00"], checkedAt: CHECKED_AT, host: "", state: "paused", plainReason: null, suggested: false, nextCheckAt: null },
      ],
      count: 2, nextCheckAt: null,
    },
    health: { state: "ok", assessment: "on_track", reason: null, inputs: { overdue: 0, ciFailing: false, reviewWaitingDays: null, targetPassed: false } },
    sinceRead: { state: "ok", readAt: null, groups: [] },
    decisions: { state: "ok", items: [] },
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
  apiFetch.mockImplementation((url: string) => Promise.resolve(response(url)));
  useDesk.setState({ windowsById: {}, items: { ...EMPTY_ITEMS }, projects: [], inferenceTargets: [] });
});
afterEach(() => vi.clearAllMocks());

describe("HS-175 C7(b): a paused Watch says so", () => {
  it("shows PAUSED + Resume on the meeting row and on the GitHub row", async () => {
    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("room-body");
    // The testid sits on the row's line; the open line 2 is its sibling.
    const line = await screen.findByTestId("source-meeting-row");
    const mtg = line.parentElement as HTMLElement;
    expect(within(mtg).getByTestId("source-paused").textContent).toContain("Paused");
    expect(within(mtg).getByTestId("source-meeting-verb").textContent).toBe("Resume");
    const pausedChips = screen.getAllByTestId("source-paused");
    expect(pausedChips).toHaveLength(2);
    expect(screen.getAllByRole("button", { name: "Resume" })).toHaveLength(2);
    expect(screen.queryByRole("button", { name: "Pause" })).toBeNull();
  });
});

describe("HS-175 C8: CHECKED in the viewer's clock", () => {
  it("formats the hub's offset-carrying instant in local time", async () => {
    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("room-body");
    const mtg = (await screen.findByTestId("source-meeting-row")).parentElement as HTMLElement;
    const d = new Date(CHECKED_AT);
    const pad = (n: number) => String(n).padStart(2, "0");
    expect(within(mtg).getByTestId("source-meeting-checked").textContent).toContain(`Checked ${pad(d.getHours())}:${pad(d.getMinutes())}`);
  });
});


describe("merged Watch outcomes", () => {
  it.each([
    { state: "live", label: "Pause", path: "pause" },
    { state: "paused", label: "Resume", path: "resume" },
    { state: "cant_check", label: "Remove", path: "retire" },
  ])("$label settles all siblings, rereads, and retries only the failed ID", async ({ state, label, path }) => {
    let finishSibling: (value: unknown) => void = () => {};
    let reads = 0;
    let failedAttempts = 0;
    const accepted = new Set<string>();
    apiFetch.mockImplementation((url: string) => {
      if (url === `/api/watches/w-failed/${path}`) {
        if (++failedAttempts === 1) return Promise.reject(new TypeError("offline"));
        accepted.add("w-failed");
        return Promise.resolve({});
      }
      if (url === `/api/watches/w-sibling/${path}`) return new Promise((resolve) => {
        finishSibling = (value) => { accepted.add("w-sibling"); resolve(value); };
      });
      if (url === "/api/projects/p1/room") {
        reads += 1;
        const body = roomResponse();
        body.sources.items = [{ ...body.sources.items[0], watchId: "w-failed", watchIds: ["w-failed", "w-sibling"], state, scope: "acme/merged" }];
        return Promise.resolve(body);
      }
      return Promise.resolve(response(url));
    });
    render(<WindowHarness scope="project:p1" />);
    const verb = await screen.findByRole("button", { name: label });
    const before = reads;
    fireEvent.click(verb);
    if (label === "Remove") fireEvent.click(screen.getByRole("button", { name: "Remove?" }));
    await waitFor(() => expect(failedAttempts).toBe(1));
    expect(reads).toBe(before);
    expect(screen.queryByRole("button", { name: "Try again" })).toBeNull();
    await act(async () => { finishSibling({}); });
    await waitFor(() => expect(reads).toBe(before + 1));
    expect(screen.getByRole("alert")).toHaveTextContent(`Could not ${label.toLowerCase()} the watch on acme/merged · The other watches changed`);
    expect(accepted.has("w-sibling")).toBe(true);
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    await waitFor(() => expect(reads).toBe(before + 2));
    expect(failedAttempts).toBe(2);
    expect(apiFetch.mock.calls.filter(([url]) => url === `/api/watches/w-sibling/${path}`)).toHaveLength(1);
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("accepted writes with a failed reread offer read recovery, without replaying writes", async () => {
    let mutated = false;
    apiFetch.mockImplementation((url: string) => {
      if (url === "/api/watches/w-gh/resume") { mutated = true; return Promise.resolve({}); }
      if (url === "/api/projects/p1/room" && mutated) return Promise.reject(new TypeError("offline"));
      return Promise.resolve(response(url));
    });
    render(<WindowHarness scope="project:p1" />);
    const verbs = await screen.findAllByRole("button", { name: "Resume" });
    fireEvent.click(verbs[0]);
    expect(await screen.findByRole("alert")).toHaveTextContent("Could not load the Project");
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    await waitFor(() => expect(apiFetch.mock.calls.filter(([url]) => url === "/api/projects/p1/room").length).toBe(3));
    expect(apiFetch.mock.calls.filter(([url]) => url === "/api/watches/w-gh/resume")).toHaveLength(1);
  });
});
