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
    expect(chips.map((c) => [c.textContent, c.getAttribute("data-scope")])).toEqual([[`REMOTE · ${remote.caller}`, "remote"]]);
    expect(finished.textContent).not.toContain("Service.");
  });
});
