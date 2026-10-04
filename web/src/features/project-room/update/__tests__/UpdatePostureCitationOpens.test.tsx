// Astra's last review of #768 — an Update citation opens through the one
// open grammar. Red before: UpdatePosture called `openSourceRef`, so a click
// on `action_item:<id>` logged "unknown id" and opened nothing.
//
// The draft is REAL: tests/fixtures/update_draft_action_citation.json is the
// real drafter's row (tests/unit/test_drafters_read_memory.py fences it:
// test_the_web_click_fixture_is_what_the_real_drafter_makes).

import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { useState, type ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { TitleSlotContext } from "../../../../desk/surface/title";
import { WingSlotContext } from "../../../../desk/surface/wings";
import { useDesk } from "../../../../desk/store";
import { EMPTY_ITEMS } from "../../../../desk/api";
import { ProjectRoomCore } from "../../ProjectRoomCore";

vi.mock("../../../../desk/ask", async () => {
  const actual =
    await vi.importActual<typeof import("../../../../desk/ask")>(
      "../../../../desk/ask",
    );
  return { ...actual, runAsk: vi.fn() };
});

vi.mock("../../../../desk/components/DeskEditor", () => ({
  DeskEditor: ({
    value,
    onChange,
    ariaLabel,
    placeholder,
  }: {
    value: string;
    onChange: (value: string) => void;
    ariaLabel?: string;
    placeholder?: string;
  }) => (
    <textarea
      aria-label={ariaLabel || "Body"}
      data-testid="update-body-textarea"
      placeholder={placeholder}
      value={value}
      onChange={(event) => onChange(event.target.value)}
    />
  ),
}));

const apiFetch = vi.fn();
vi.mock("../../../../lib/api", async () => {
  const actual =
    await vi.importActual<typeof import("../../../../lib/api")>(
      "../../../../lib/api",
    );
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});

vi.mock("../../../../desk/shell", async () => {
  const actual = await vi.importActual<typeof import("../../../../desk/shell")>(
    "../../../../desk/shell",
  );
  return { ...actual, openPrimitive: vi.fn(), openSurfaceOr: vi.fn() };
});

vi.mock("../../../../desk/intelligenceNavigation", async () => {
  const actual = await vi.importActual<
    typeof import("../../../../desk/intelligenceNavigation")
  >("../../../../desk/intelligenceNavigation");
  return { ...actual, openIntelligence: vi.fn() };
});

function WindowHarness({ scope }: { scope?: string }) {
  const [wings, setWings] = useState<ReactNode>(null);
  return (
    <TitleSlotContext.Provider value={() => {}}>
      <WingSlotContext.Provider value={setWings}>
        <div>{wings}</div>
        <ProjectRoomCore scope={scope} />
      </WingSlotContext.Provider>
    </TitleSlotContext.Provider>
  );
}

function roomResponse() {
  return {
    project_id: "p1",
    revision: 5,
    observed_at: "2026-09-06T10:00:00",
    nextCheckAt: null,
    project: {
      id: "p1",
      name: "Alpha Project",
      description: "Testing claim axes",
      is_archived: false,
      meeting_count: 0,
      created_at: "2026-08-01T00:00:00",
      updated_at: "2026-09-06T10:00:00",
      purpose: "Ship the widget",
      outcome_text: "Widget shipped",
      owner_ref: "person:owner1",
      lifecycle: "active",
      posture: "green",
      posture_reason: "On track",
      start_at: "2026-08-01",
      target_at: "2026-12-01",
      revision: 5,
    },
    items: { state: "ok", focus: [], totals_by_type: {}, total: 0 },
    meetings: { state: "ok", count: 0, latest: null },
    resources: { state: "ok", count: 0, latest: null },
    changes: { state: "ok", recent: [] },
    review: { state: "absent", reason: "not_yet_built" },
    needsYou: { state: "ok", items: [], count: 0 },
    sources: { state: "ok", items: [], count: 0, nextCheckAt: null },
    health: {
      state: "ok",
      assessment: "on_track",
      reason: null,
      inputs: {
        overdue: 0,
        ciFailing: false,
        reviewWaitingDays: null,
        targetPassed: false,
      },
    },
    sinceRead: { state: "ok", readAt: null, groups: [] },
    decisions: { state: "ok", items: [] },
    commitments: { state: "ok", items: [] },
    target: { state: "absent", reason: "none" },
    updates: { state: "absent", reason: "not_yet_built" },
    steward: { state: "absent", reason: "not_yet_built" },
  };
}

import { openIntelligence } from "../../../../desk/intelligenceNavigation";
import { openPrimitive, openSurfaceOr } from "../../../../desk/shell";

const FIXTURE = resolve(
  __dirname,
  "../../../../../../tests/fixtures/update_draft_action_citation.json",
);

function realDraft(): Record<string, unknown> {
  const row = JSON.parse(readFileSync(FIXTURE, "utf8")) as Record<string, unknown>;
  return {
    ...row,
    id: "pupd-real-01",
    project_id: "p1",
    created_at: "2026-09-06T10:00:00",
    updated_at: "2026-09-06T10:00:00",
  };
}

function setupUpdatePosture(draft: Record<string, unknown>) {
  apiFetch.mockImplementation((url: string) => {
    if (url.includes("/room/read")) {
      return Promise.resolve({ read_at: new Date().toISOString() });
    }
    if (url.includes("/room")) return Promise.resolve(roomResponse());
    if (
      url.match(/\/api\/projects\/[^/]+\/updates$/) ||
      url.match(/\/api\/projects\/[^/]+\/updates\?/)
    ) {
      return Promise.resolve({ updates: [draft] });
    }
    if (url.includes("/updates/draft")) {
      return Promise.resolve({ success: true, update: draft });
    }
    if (url.includes("/markdown")) return Promise.resolve("## Progress\n");
    if (url.includes("/meetings")) return Promise.resolve({ meetings: [] });
    if (url.startsWith("/api/decisions")) {
      return Promise.resolve({ decisions: [] });
    }
    if (url.includes("/artifacts")) return Promise.resolve({ artifacts: [] });
    if (url.includes("/since-last-meeting")) {
      return Promise.resolve({
        current_meeting: null,
        since_last_meeting: null,
      });
    }
    return Promise.resolve({});
  });
}

beforeEach(() => {
  useDesk.setState({
    windowsById: {},
    items: { ...EMPTY_ITEMS },
    projects: [],
    inferenceTargets: [],
  });
});

afterEach(() => {
  vi.clearAllMocks();
});

async function openEditor() {
  const btn = await screen.findByTestId("updates-verb");
  fireEvent.click(btn);
  await waitFor(() => screen.getByTestId("update-posture"));
  const items = await screen.findAllByTestId("update-list-item");
  fireEvent.click(items[0]);
  await waitFor(() => screen.getByTestId("update-editor"));
}

describe("an Update citation opens through the one open grammar", () => {
  it("a click on the action item's citation reaches Follow-through", async () => {
    setupUpdatePosture(realDraft());
    render(<WindowHarness scope="project:p1" />);
    await openEditor();

    const chip = screen
      .getAllByTestId("update-claim-ref")
      .find((el) => el.getAttribute("data-ref") === "action_item:act-fixture-01");
    expect(chip).toBeTruthy();
    fireEvent.click(chip!);

    expect(openIntelligence).toHaveBeenCalledWith({
      view: "follow-through",
      followThroughId: "act-fixture-01",
    });
    expect(openPrimitive).not.toHaveBeenCalled();
  });

  it("the meeting's citation on the same draft opens the meeting", async () => {
    setupUpdatePosture(realDraft());
    render(<WindowHarness scope="project:p1" />);
    await openEditor();

    const chip = screen
      .getAllByTestId("update-claim-ref")
      .find((el) => el.getAttribute("data-ref") === "meeting:m-fixture");
    fireEvent.click(chip!);

    expect(openSurfaceOr).toHaveBeenCalledWith("review-meetings", "/history", "meeting:m-fixture");
  });
});
