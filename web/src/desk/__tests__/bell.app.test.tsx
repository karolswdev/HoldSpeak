// The bell's shade (SystemShade): a new artifact reads as new in the owner's
// zone. The test diet (2026-10-11) moves the Bell leg of
// tests/e2e/test_times_local_zone_glass.py here.
//
// The real SystemShade renders over the real projections store
// (desk/projections.ts); only `apiFetch` is mocked, and
// `/api/desk/projections` answers with the hub's envelope and an artifact
// row as ProjectionRepository._artifacts builds it (a draft artifact is
// `needs_attention`, its label is the artifact title). The hub half (a new
// artifact's stamp carries its offset; the normalizer keeps it exact) is
// tests/unit/test_times_dst_denver.py::test_a_new_artifact_stamp_carries_its_offset.
//
// The zone is pinned to America/Denver at module top, the way
// web/src/pages/cores/__tests__/peoplePrepB4.test.tsx pins it.
process.env.TZ = "America/Denver";

import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterAll, afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../lib/api";
import { SystemShade } from "../components/SystemShade";
import { useProjections } from "../projections";
import { recordedGet, type Gets } from "../../test/recordedHub";
import recorded from "./fixtures/needsYou.recorded.json";
import briefWire from "../../test/wire/brief-latest.generated.wire.json";
import remoteReceiptWire from "../../test/wire/desk-projections.remote-receipt.wire.json";

vi.mock("../../lib/api", async (original) => ({
  ...(await original<typeof import("../../lib/api")>()),
  apiFetch: vi.fn(),
}));

vi.mock("../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "offline", lastFrame: null, subscribe: () => () => undefined }),
  useOptionalRuntimeBus: () => ({ state: "offline", lastFrame: null, subscribe: () => () => undefined }),
}));

const shell = vi.hoisted(() => ({ openSurfaceOr: vi.fn(), openProjectRoom: vi.fn() }));
vi.mock("../shell", async (original) => ({
  ...(await original<typeof import("../shell")>()),
  openSurfaceOr: shell.openSurfaceOr,
  openProjectRoom: shell.openProjectRoom,
}));

/** `ProjectionRepository._artifacts` for a draft artifact of meeting m-zone. */
function artifactRow(timestamp: string) {
  return {
    version: 1,
    id: "artifact:m-zone-notes:draft",
    projection_kind: "attention",
    subject_ref: "artifact:m-zone-notes",
    subject_label: "Ledger cutover sync: notes",
    title: "Artifact needs review",
    summary: "Open the Artifact to inspect its content and cited source records.",
    reason_code: "artifact_draft",
    decision_kind: "review",
    attention_state: "needs_attention",
    actual_destination: "this_machine",
    authority_basis: "content_review",
    attempt: null,
    outcome: "draft",
    timestamp,
    correlation_id: "meeting:m-zone",
    source_kind: "artifact",
    source_id: "m-zone-notes",
    source_api: "/api/meetings/m-zone/artifacts",
    detail_url: "/?open=m-zone-notes",
    control_mode: null,
    policy_version: null,
    effect_class: null,
    severity: "normal",
    dismissed: false,
    origin: null,
    caller: null,
    caller_identity: null,
  };
}

function hub(timestamp: string) {
  vi.mocked(apiFetch).mockImplementation(async (path: string) => {
    if (String(path).startsWith("/api/desk/projections")) {
      return {
        projections: [artifactRow(timestamp)],
        counts: { needs_attention: 1, receipts: 0 },
        subject_counts: {},
        page: { offset: 0, limit: 50, total: 1, has_more: false },
      } as never;
    }
    return { items: [] } as never;
  });
}

const pad = (n: number) => String(n).padStart(2, "0");

/** A wall-clock stamp in the process zone, with or without its offset. */
function localStamp(date: Date, withOffset: boolean): string {
  const base = `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
  if (!withOffset) return base;
  const off = -date.getTimezoneOffset();
  const sign = off >= 0 ? "+" : "-";
  return `${base}${sign}${pad(Math.floor(Math.abs(off) / 60))}:${pad(Math.abs(off) % 60)}`;
}

async function stampWords(): Promise<string> {
  render(<SystemShade open onClose={() => undefined} onOpenMemory={() => undefined} />);
  const label = await screen.findByText(/Ledger cutover sync: notes/);
  const small = label.closest("small") ?? label;
  return small.textContent || "";
}

beforeEach(() => {
  vi.mocked(apiFetch).mockReset();
  useProjections.setState({ projections: [], counts: {}, subject_counts: {} });
});

afterAll(() => {
  delete process.env.TZ;
});

describe("Bell: a new artifact reads as new in the owner's zone", () => {
  it("runs in America/Denver", () => {
    expect(Intl.DateTimeFormat().resolvedOptions().timeZone).toBe("America/Denver");
  });

  it("a stamp with its local offset (the hub's stamp today) reads just now", async () => {
    // replaces: tests/e2e/test_times_local_zone_glass.py::test_bell_reads_a_new_artifact_as_new
    hub(localStamp(new Date(), true));
    expect(await stampWords()).toMatch(/· (just now|[0-5]m ago)$/);
  });

  it("a bare local ISO stamp reads just now, never 6h ago", async () => {
    // replaces: tests/e2e/test_times_local_zone_glass.py::test_bell_reads_a_new_artifact_as_new (the defect's own shape)
    hub(localStamp(new Date(), false));
    const words = await stampWords();
    expect(words).toMatch(/· (just now|[0-5]m ago)$/);
    expect(words).not.toMatch(/[67]h ago/);
  });

  it("the normalizer's UTC `...Z` stamp reads just now", async () => {
    // replaces (part): tests/e2e/test_times_local_zone_glass.py::test_bell_reads_a_new_artifact_as_new
    hub(new Date().toISOString().replace(/\.\d+Z$/, "Z"));
    expect(await stampWords()).toMatch(/· (just now|[0-5]m ago)$/);
  });
});

/* ── HS-171-04 / HS-174-04: the shade's sections over the hub's recorded answers ──
 * Each read is a recorded hub answer: needsYou.recorded.json
 * (scripts/record_needs_you_fixture.py), brief-latest.generated and
 * desk-projections.remote-receipt (tests/integration/test_face_wire_fences.py). */

const QUIET = (recorded as unknown as { calendar: { quiet: { gets: Gets } } }).calendar.quiet.gets;
const BRIEF = (briefWire as { wire: { sections: Record<string, unknown[]>; generated_at: string } }).wire;

function replayShade(gets: Gets): string[] {
  const misses: string[] = [];
  vi.mocked(apiFetch).mockImplementation(async (path: string) => recordedGet(gets, path, misses) as never);
  return misses;
}

const needsYouReads = () =>
  vi.mocked(apiFetch).mock.calls.filter(([path]) => String(path).startsWith("/api/desk/needs-you")).length;

describe("the shade on a quiet desk with a brief (HS-171-04)", () => {
  afterEach(() => {
    shell.openSurfaceOr.mockReset();
    vi.useRealTimers();
  });

  it("no Room has items: no Projects section; the Brief row says its kind, its count and its day", async () => {
    // replaces: tests/e2e/test_hs171_shade_glass.py::test_shade_quiet_1440 (the 393 twin is the same DOM)
    // replaces: tests/e2e/test_hs171_shade_glass.py::test_shade_brief_row_1440
    replayShade({ ...QUIET, "/api/brief/latest": BRIEF });
    const onClose = vi.fn();
    render(<SystemShade open onClose={onClose} onOpenMemory={() => undefined} />);
    const row = await screen.findByTestId("shade-brief-row");
    expect(screen.queryByTestId("shade-projects")).toBeNull();
    const things = Object.values(BRIEF.sections).flat().length;
    const kind = (BRIEF.sections.this_week ?? []).length > 0 ? "Weekly brief" : "Daily brief";
    expect(row.querySelector("strong")?.textContent).toBe(kind);
    const chip = row.querySelector(".surface-token")?.textContent ?? "";
    expect(chip).toBe(`${things} THING${things === 1 ? "" : "S"}`);
    // The hub's generated_at in the owner's zone, as MON DD.
    const day = new Date(BRIEF.generated_at).toLocaleDateString("en-US", { month: "short", day: "2-digit" }).toUpperCase();
    expect(row.querySelector(".desk-shade-why")?.textContent).toBe(day);
    expect(day).toMatch(/^[A-Z]{3} \d{2}$/);
    fireEvent.click(within(row).getByRole("button", { name: "Open" }));
    expect(onClose).toHaveBeenCalled();
    expect(shell.openSurfaceOr).toHaveBeenCalledWith("open-intelligence", "/");
  });

  it("the shade reads needs-you every 5 s while open, and never after it closes", async () => {
    // replaces: tests/e2e/test_hs171_shade_glass.py::test_shade_polling_stops_on_close
    vi.useFakeTimers();
    replayShade(QUIET);
    const view = render(<SystemShade open onClose={() => undefined} onOpenMemory={() => undefined} />);
    await act(async () => { await vi.advanceTimersByTimeAsync(0); });
    const atOpen = needsYouReads();
    expect(atOpen).toBe(1);
    await act(async () => { await vi.advanceTimersByTimeAsync(5000); });
    expect(needsYouReads()).toBe(atOpen + 1);
    view.rerender(<SystemShade open={false} onClose={() => undefined} onOpenMemory={() => undefined} />);
    const atClose = needsYouReads();
    await act(async () => { await vi.advanceTimersByTimeAsync(15000); });
    expect(needsYouReads()).toBe(atClose);
  });
});

describe("the shade says it is reading until its first reads land (PHILO-17 Missed sweep)", () => {
  it("a held brief read keeps the shade busy; the Brief row lands, then the shade is still", async () => {
    // The sweep's `missed` case: Finished drew from the cached projections,
    // then Projects and Brief landed above it (264 px) after it read as settled.
    const misses: string[] = [];
    let release: () => void = () => undefined;
    const held = new Promise<void>((resolve) => { release = resolve; });
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      if (String(path).startsWith("/api/brief/latest")) await held;
      return recordedGet({ ...QUIET, "/api/brief/latest": BRIEF }, path, misses) as never;
    });
    render(<SystemShade open onClose={() => undefined} onOpenMemory={() => undefined} />);
    expect(document.querySelector('#desk-system-shade [aria-busy="true"]')).not.toBeNull();
    await act(async () => { await Promise.resolve(); });
    expect(screen.queryByTestId("shade-brief-row")).toBeNull();
    expect(document.querySelector('#desk-system-shade [aria-busy="true"]')).not.toBeNull();
    await act(async () => { release(); await held; });
    await screen.findByTestId("shade-brief-row");
    await waitFor(() => expect(document.querySelector('#desk-system-shade [aria-busy="true"]')).toBeNull());
  });
});

describe("a remote write in the shade's Finished rows (HS-174-04)", () => {
  it("the remote sweep wears REMOTE · <caller> in the accent scope", async () => {
    // replaces: tests/e2e/test_hs174_receipts_glass.py::test_shade_remote_receipts_1440 (the 393 twin drew the same rows)
    // The hub projects the remote sweep; it does not project the local steward run
    // the rig also seeded (the recorded answer holds one row).
    const wire = (remoteReceiptWire as { wire: { projections: Array<{ origin: string | null; caller: string | null }> } }).wire;
    const remote = wire.projections.find((row) => row.origin === "remote")!;
    replayShade({ ...QUIET, "/api/desk/projections?offset=0&limit=50": wire });
    render(<SystemShade open onClose={() => undefined} onOpenMemory={() => undefined} />);
    const finished = await waitFor(() => {
      const node = document.querySelector<HTMLElement>('section[aria-label="Finished"]');
      expect(node).not.toBeNull();
      return node!;
    });
    const chips = within(finished).getAllByTestId("shade-finished-egress").map((slot) => slot.querySelector(".gadget-chip-egress")!);
    expect(chips.map((c) => [c.textContent, c.getAttribute("data-scope")])).toEqual([[`Remote · ${remote.caller}`, "remote"]]);
    expect(finished.textContent).not.toContain("Service.");
  });
});

/* ── Betterment daily D1: one number on the bell and the Project icon ──────────
 * The recon week (tests/fixtures/daily_week) on the real hub, today as its
 * Monday, after the nine keeps: the hub counts 4 (mine due today 2, to decide
 * 2; what Mira, Theo and Jun owe never counts). The recorded answer is
 * tests/unit/test_desk_needs_you.py::test_the_one_number_is_mine_due_today_and_to_decide
 * (fixtures/daily-week/needs-you.json). The bell said 11 and the Project icon
 * 12 in the recon (RECON.md §2). */
import dailyWeek from "./fixtures/daily-week/needs-you.json";
import { DeskChrome } from "../components/DeskChrome";
import { projectOpenHere, readNeedsYouAnswer, readProjectCounts, refreshNeedsYou, resetNeedsYou } from "../needsYou";
import { composeScreen } from "../screen/compose";
import { EMPTY_ITEMS } from "../api";

describe("Bell: the daily week's one number", () => {
  it("the bell, the members and the Project icon all say 4", async () => {
    resetNeedsYou();
    const gets: Gets = { "/api/desk/needs-you?fresh=1": dailyWeek.needsYou };
    vi.mocked(apiFetch).mockImplementation(async (path: string) => recordedGet(gets, path) as never);
    render(<DeskChrome />);
    await act(async () => { await refreshNeedsYou(true); });
    const bell = await screen.findByTestId("desk-bell");
    await waitFor(() => expect(bell.querySelector("strong")?.textContent).toBe("4"));

    const read = readNeedsYouAnswer(dailyWeek.needsYou as never);
    expect(read.count).toBe(4);
    expect(read.members.map((m) => m.item?.title).filter(Boolean).sort()).toEqual([
      "Do it", "Email Dana about the cutover window",
      "Review design doc on settlement retries",
      "Talk about the staff path in our next one-on-one",
    ]);

    const project = dailyWeek.projects.projects as Array<{ id: string; name: string }>;
    const counts = projectOpenHere({ projectCounts: readProjectCounts(dailyWeek.needsYou as never), unmutedItems: read.unmutedItems });
    expect(Object.values(counts)).toEqual([4]);
    // The Room's own count (it counts what others owe) is not the badge.
    expect(Object.values(dailyWeek.needsYou.roomCounts)).toEqual([9]);
    const screenObjects = composeScreen({
      items: { ...EMPTY_ITEMS, project: project.map((p) => ({ id: p.id, name: p.name })) },
      projectCounts: counts, needsCount: read.count, needsRefs: new Set(), heldCalls: 0,
      sessions: [], flights: [], filed: new Set(), persons: [], membersLoaded: true,
    } as never);
    const icon = (screenObjects as Array<{ kind?: string; lamp?: { count?: number } }>).find((o) => o.kind === "project");
    expect(icon?.lamp?.count).toBe(4);
  });
});

/* ── MENUBAR-STILL (2026-10-29): the count's slot is there before the read ──
 * The desk sweep's desk-1440 still fence saw the bell and the hub dot move
 * 27 px under load: the Needs-you read landed inside the 1.5 s watch and its
 * count mounted, so the bell grew. The slot is drawn before the read, the
 * count lands IN it, and the CSS gives the slot its full width at once. */
import chromeMenusCss from "../components/chrome-menus.css?raw";
import tokensCss from "../../styles/tokens.css?raw";

describe("Bell: the count's slot holds the bar still", () => {
  it("draws the empty slot before the Needs-you read and the count lands in the same slot", async () => {
    resetNeedsYou();
    let answer: (value: unknown) => void = () => undefined;
    const held = new Promise((resolve) => { answer = resolve; });
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      if (path.startsWith("/api/desk/needs-you")) return (await held) as never;
      return recordedGet({}, path) as never;
    });
    render(<DeskChrome />);
    const bell = await screen.findByTestId("desk-bell");
    const slot = within(bell).getByTestId("desk-bell-slot");
    expect(slot.querySelector("strong")).toBeNull();
    expect(slot.textContent).toBe("");

    await act(async () => { answer(dailyWeek.needsYou); await held; });
    await waitFor(() => expect(slot.querySelector("strong")?.textContent).toBe("4"));
    expect(within(bell).getByTestId("desk-bell-slot")).toBe(slot);
  });

  it("gives the slot its two-digit width from the badge token, empty or full", () => {
    const rule = chromeMenusCss.match(/\.desk-menubar \.desk-bell-slot \{([^}]*)\}/);
    expect(rule?.[1]).toMatch(/min-width:\s*var\(--desk-badge-slot-w\)/);
    expect(rule?.[1]).toMatch(/flex:\s*0 0 auto/);
    expect(tokensCss).toMatch(/--desk-badge-slot-w:\s*calc\(var\(--desk-badge-h\) \+ 6px\)/);
  });
});
