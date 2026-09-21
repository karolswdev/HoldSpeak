/* HS-202-04 — one verb per job, one all-clear per screen, on the Meetings
 * faces the five first-use jobs touch.
 *
 * Doctrine:
 *  - F07 (`surface-inventory-2026-09-20/02-coherence-astra.md:119`): the
 *    SAME job — recover a failed meeting Summary — wore two labels,
 *    `Retry` in the record (`history/NeedsYouTable.tsx:92`, and
 *    `meetings/MeetingIntelRecovery.tsx:246`) and `Retry intelligence` in
 *    the gear door's queue (`history/DoorSection.tsx:128`). One repair
 *    looked like two jobs, and the door's label also broke the registry's
 *    own rule that every face says Summary
 *    (`docs/product-language.json:23`). `Retry background work` stays: a
 *    deferred plugin job is a different object, not a second name for the
 *    summary's retry (Astra's verb map, same file).
 *  - M6 (`SURFACE-INVENTORY-2026-09-20.md:57`, walk leg
 *    `wing-meetings-outcomes`): the cold Meetings face printed
 *    `No meetings yet` twice — once as the display headline
 *    (`history/helpers.ts:223`) and once as the rail's empty label
 *    (`history/CatalogRail.tsx:309`). UX-CANON A.7: the name is said once
 *    per face; A.3: an empty state is ONE true line with the next move.
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { CatalogRail } from "../CatalogRail";
import { DoorSection } from "../DoorSection";
import { meetingsHeadline } from "../helpers";

vi.mock("../../../../lib/api", async (original) => ({
  ...(await original<typeof import("../../../../lib/api")>()),
  apiFetch: vi.fn(async () => ({})),
}));

function doorProps(jobs: Record<string, unknown>[]) {
  const resource = (data: Record<string, unknown>) => ({
    data,
    reload: vi.fn(async () => ({})),
  });
  return {
    actions: { data: {} },
    speakers: { data: {} },
    projects: { data: {} },
    intel: resource({ jobs }),
    plugin: resource({ jobs: [] }),
    queueStatus: "failed",
    setQueueStatus: vi.fn(),
  };
}

describe("the failed Summary offers one Retry (F07)", () => {
  it("names the queue's summary recovery Retry, never Retry intelligence", () => {
    render(
      <DoorSection
        {...doorProps([
          {
            id: "j1",
            meeting_id: "m-1",
            title: "Architecture review",
            status: "failed",
          },
        ])}
      />,
    );
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
    expect(screen.queryByText("Retry intelligence")).toBeNull();
  });

  it("keeps the deferred plugin job's own verb — a different object", () => {
    render(
      <DoorSection
        {...doorProps([
          { id: "j2", title: "Deferred job", status: "failed" },
        ])}
      />,
    );
    expect(
      screen.getByRole("button", { name: "Retry background work" }),
    ).toBeInTheDocument();
  });
});

describe("the cold Meetings face says its all-clear once (M6)", () => {
  it("does not repeat the headline's words in the rail's empty state", () => {
    const headline = meetingsHeadline([], false).text;
    render(
      <CatalogRail
        meetingRows={[]}
        meetings={{ loading: false, error: "", reload: vi.fn(async () => ({})) }}
        selected={null}
        setSelected={vi.fn()}
        onRunIntelligence={vi.fn()}
        runningId={null}
      />,
    );
    expect(headline).toBe("No meetings yet");
    expect(screen.queryByText(headline)).toBeNull();
  });

  it("states the next move instead", () => {
    render(
      <CatalogRail
        meetingRows={[]}
        meetings={{ loading: false, error: "", reload: vi.fn(async () => ({})) }}
        selected={null}
        setSelected={vi.fn()}
        onRunIntelligence={vi.fn()}
        runningId={null}
      />,
    );
    expect(screen.getByText("Record or import a meeting")).toBeInTheDocument();
  });
});
