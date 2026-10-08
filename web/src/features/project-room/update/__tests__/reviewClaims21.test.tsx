// HS-200-06 -- the three claim axes on the glass: kind as the lead
// emblem, support and acceptance as their own tokens. A citation shows
// LINKED, never SUPPORTED; a migrated record says so; an edited
// sentence says its support was invalidated.

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

/** The chip's accessible label -- its glyph is decorative. */
function chipLabels(testId: string): (string | null)[] {
  return screen
    .getAllByTestId(testId)
    .map((el) =>
      el.querySelector(".surface-state-chip")?.getAttribute("aria-label") ??
      null,
    );
}

async function openEditor() {
  const btn = await screen.findByTestId("updates-verb");
  fireEvent.click(btn);
  await waitFor(() => screen.getByTestId("update-posture"));
  const items = await screen.findAllByTestId("update-list-item");
  fireEvent.click(items[0]);
  await waitFor(() => screen.getByTestId("update-editor"));
}


// PHILO-15 21 (Astra r1 P1-2): the owner reviews each claim in the editor.
// Accept / Reject are library Buttons on every claim row, wired to the hub's
// review route; the row that will not be sent reads OMITTED; a review leaves
// REVIEWED · hh:mm.
function draft(acceptance: Record<string, string>) {
  const claim = (span: string, text: string) => ({
    span_id: span, text, refs: ["item:hygiene"], section: "progress", kind: "inference",
    support: "source_linked", acceptance: acceptance[span] ?? "unreviewed",
  });
  return {
    id: "pupd-21", project_id: "p1", project_revision: 5, review_id: null, lifecycle: "draft",
    draft_revision: 1,
    body_md: "## Progress\n\n- The ledger moved to staging.\n- We ship Friday.\n",
    claims_json: JSON.stringify([claim("s0", "The ledger moved to staging."), claim("s1", "We ship Friday.")]),
    source_manifest_json: "{}", generator: "model:ia_1", generatorHost: "192.168.1.43:8080",
    generatorModel: "qwen3.8-27b", fallback_reason: null, created_at: "2026-10-08T07:00:00",
    updated_at: "2026-10-08T07:00:00", published_at: null,
  };
}

let state: Record<string, string> = {};
const reviews: Array<{ url: string; json: unknown }> = [];

function setup() {
  state = {};
  reviews.length = 0;
  apiFetch.mockImplementation((url: string, init?: { json?: { acceptance?: string } }) => {
    const m = url.match(/\/api\/updates\/pupd-21\/claims\/([^/]+)\/review$/);
    if (m) {
      reviews.push({ url, json: init?.json });
      state[m[1]] = String(init?.json?.acceptance);
      return Promise.resolve({ success: true, update: draft(state), reviewed_at: "2026-10-08T13:12:00+00:00" });
    }
    if (url.includes("/room/read")) return Promise.resolve({ read_at: new Date().toISOString() });
    if (url.includes("/room")) return Promise.resolve(roomResponse());
    if (url.match(/\/api\/projects\/[^/]+\/updates(\?|$)/)) return Promise.resolve({ updates: [draft(state)] });
    if (url.includes("/meetings")) return Promise.resolve({ meetings: [] });
    if (url.startsWith("/api/decisions")) return Promise.resolve({ decisions: [] });
    if (url.includes("/artifacts")) return Promise.resolve({ artifacts: [] });
    if (url.includes("/since-last-meeting")) return Promise.resolve({ current_meeting: null, since_last_meeting: null });
    return Promise.resolve({});
  });
}

function row(span: string): HTMLElement {
  return document.querySelector<HTMLElement>(`[data-testid='update-inline-claim'][data-span-id='${span}']`)!;
}

describe("PHILO-15 21: Accept / Reject on each claim", () => {
  it("an unreviewed inference reads OMITTED; Accept sends it, Reject keeps it OMITTED; each leaves a receipt", async () => {
    setup();
    render(<WindowHarness scope="project:p1" />);
    await openEditor();
    expect(row("s0").getAttribute("data-sends")).toBe("false");
    expect(row("s0").querySelector("[data-testid='update-claim-omitted']")?.textContent).toBe("OMITTED");
    expect(row("s0").querySelectorAll("button.signal-button, button").length).toBeGreaterThanOrEqual(2);

    fireEvent.click(screen.getByRole("button", { name: "Accept: The ledger moved to staging." }));
    await waitFor(() => expect(row("s0").getAttribute("data-sends")).toBe("true"));
    expect(row("s0").querySelector("[data-testid='update-claim-omitted']")).toBeNull();
    const at = new Date("2026-10-08T13:12:00+00:00");
    const hhmm = `${String(at.getHours()).padStart(2, "0")}:${String(at.getMinutes()).padStart(2, "0")}`;
    expect(screen.getByTestId("update-claim-receipt").textContent).toBe(`REVIEWED · ${hhmm}`);

    fireEvent.click(screen.getByRole("button", { name: "Reject: We ship Friday." }));
    await waitFor(() => expect(reviews).toHaveLength(2));
    expect(reviews.map((r) => r.json)).toEqual([{ acceptance: "accepted" }, { acceptance: "rejected" }]);
    expect(reviews[1].url).toBe("/api/updates/pupd-21/claims/s1/review");
    await waitFor(() => expect(
      (screen.getByRole("button", { name: "Reject: We ship Friday." }) as HTMLButtonElement).disabled).toBe(true));
    expect(row("s1").querySelector("[data-testid='update-claim-omitted']")?.textContent).toBe("OMITTED");
  });
});
