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

import { render, screen } from "@testing-library/react";
import { afterAll, beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../lib/api";
import { SystemShade } from "../components/SystemShade";
import { useProjections } from "../projections";

vi.mock("../../lib/api", async (original) => ({
  ...(await original<typeof import("../../lib/api")>()),
  apiFetch: vi.fn(),
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
