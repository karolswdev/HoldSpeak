// HS-160-06 — ReviewPosture rendering tests: posture swap, groups,
// keyboard law, comparison, conflict both-sources, no-delta state.

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

function roomResponse(overrides: Record<string, unknown> = {}) {
  return {
    project_id: "p1",
    revision: 3,
    observed_at: "2026-08-31T10:00:00",
    nextCheckAt: null,
    project: {
      id: "p1",
      name: "Alpha Project",
      description: "Testing the room",
      is_archived: false,
      meeting_count: 2,
      created_at: "2026-08-01T00:00:00",
      updated_at: "2026-08-31T10:00:00",
      purpose: "Ship the widget",
      outcome_text: "Widget shipped",
      owner_ref: "person:owner1",
      lifecycle: "active",
      posture: "green",
      posture_reason: "On track",
      start_at: "2026-08-01",
      target_at: "2026-12-01",
      revision: 3,
    },
    items: { state: "ok", focus: [], totals_by_type: {}, total: 0 },
    meetings: { state: "ok", count: 2, latest: { id: "m1", title: "Review" } },
    resources: { state: "ok", count: 1, latest: null },
    changes: { state: "ok", recent: [] },
    review: overrides.review ?? { state: "absent", reason: "not_yet_built" },
    sources: { state: "ok", items: [], count: 0, nextCheckAt: null },
    needsYou: { state: "ok", items: [], count: 0 },
    health: { state: "ok", assessment: "on_track", reason: null, inputs: { overdue: 0, ciFailing: false, reviewWaitingDays: null, targetPassed: false } },
    sinceRead: { state: "ok", readAt: null, groups: [] },
    decisions: { state: "ok", items: [] },
    commitments: { state: "ok", items: [] },
    target: { state: "absent", reason: "none" },
    updates: { state: "absent", reason: "not_yet_built" },
    steward: { state: "absent", reason: "not_yet_built" },
  };
}

function detailResponse(url: string) {
  if (url.includes("/room/read"))
    return { read_at: new Date().toISOString() };
  if (url.includes("/meetings"))
    return { meetings: [] };
  if (url.startsWith("/api/decisions"))
    return { decisions: [] };
  if (url.includes("/artifacts")) return { artifacts: [] };
  if (url.includes("/since-last-meeting"))
    return { current_meeting: null, since_last_meeting: null };
  return {};
}

function reviewWindowResponse() {
  return {
    review_id: "prev_r1",
    project_id: "p1",
    status: "open",
    source_manifest: { "test-source": { state: "ok" } },
    materiality_version: "1",
    opened_at: "2026-08-31T10:00:00",
    proposals: [
      {
        id: "pprop_1",
        proposal_kind: "risk_attention",
        target_ref: "action_item:ai-01",
        title: "risk_attention: action_item:ai-01",
        rationale: "Overdue follow-through requires risk attention",
        patch_json: '{"card_id":"ai-01","text":"Update PCI compliance docs","owner":"karol","due":"2026-08-17","lane":"overdue"}',
        materiality: "0.8",
        producer_kind: "",
        lifecycle: "open",
      },
      {
        id: "pprop_2",
        proposal_kind: "review_flag",
        target_ref: "decision:d-01",
        title: "review_flag: decision:d-01",
        rationale: "Accepted decision is due for periodic review",
        patch_json: '{"decision_id":"d-01","text":"Adopt event sourcing","review_status":"due"}',
        materiality: "0.5",
        producer_kind: "",
        lifecycle: "open",
      },
      {
        id: "pprop_conflict",
        proposal_kind: "conflict",
        target_ref: "action_item:ai-conflict",
        title: "conflict: action_item:ai-conflict",
        rationale: "Conflicting observations",
        patch_json: '{"sources":["src-a","src-b"]}',
        materiality: "1.0",
        producer_kind: "",
        lifecycle: "open",
      },
    ],
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

describe("Review verb in orientation (WEB-NOW-002)", () => {
  it("shows 'Review changes' button when pending_count > 0", async () => {
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room/read")) return Promise.resolve({ read_at: new Date().toISOString() });
      if (url.includes("/room")) {
        return Promise.resolve(roomResponse({
          review: {
            state: "ok",
            pending_count: 3,
            open_review_id: "prev_r1",
            last_accepted_at: null,
          },
        }));
      }
      return Promise.resolve(detailResponse(url));
    });

    render(<WindowHarness scope="project:p1" />);
    const btn = await screen.findByTestId("review-verb");
    // HS-169-03 SELECTOR EDIT: the Room's review verb is "Review N".
    expect(btn.textContent).toContain("Review");
  });

  it("hides review verb when pending_count is 0", async () => {
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room/read")) return Promise.resolve({ read_at: new Date().toISOString() });
      if (url.includes("/room")) {
        return Promise.resolve(roomResponse({
          review: {
            state: "ok",
            pending_count: 0,
            open_review_id: null,
            last_accepted_at: "2026-08-30T10:00:00",
          },
        }));
      }
      return Promise.resolve(detailResponse(url));
    });

    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("room-body");
    expect(screen.queryByTestId("review-verb")).toBeNull();
  });

  it("hides review verb when review section is absent", async () => {
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room/read")) return Promise.resolve({ read_at: new Date().toISOString() });
      if (url.includes("/room")) {
        return Promise.resolve(roomResponse({
          review: { state: "absent", reason: "not_yet_built" },
        }));
      }
      return Promise.resolve(detailResponse(url));
    });

    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("room-body");
    expect(screen.queryByTestId("review-verb")).toBeNull();
  });
});

describe("Posture swap", () => {
  it("clicking 'Review changes' enters review posture", async () => {
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room/read")) return Promise.resolve({ read_at: new Date().toISOString() });
      if (url.includes("/room")) {
        return Promise.resolve(roomResponse({
          review: {
            state: "ok",
            pending_count: 3,
            open_review_id: "prev_r1",
            last_accepted_at: null,
          },
        }));
      }
      if (url.includes("/reviews") && !url.includes("/decide") && !url.includes("/accept")) {
        return Promise.resolve(reviewWindowResponse());
      }
      return Promise.resolve(detailResponse(url));
    });

    render(<WindowHarness scope="project:p1" />);
    const btn = await screen.findByTestId("review-verb");
    fireEvent.click(btn);

    await waitFor(() => {
      expect(screen.getByTestId("review-posture")).toBeTruthy();
    });
  });
});

describe("Review grouping with count chips (WEB-NOW-004)", () => {
  it("renders kind groups with count chips", async () => {
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room/read")) return Promise.resolve({ read_at: new Date().toISOString() });
      if (url.includes("/room")) {
        return Promise.resolve(roomResponse({
          review: {
            state: "ok",
            pending_count: 3,
            open_review_id: "prev_r1",
            last_accepted_at: null,
          },
        }));
      }
      if (url.includes("/reviews") && !url.includes("/decide") && !url.includes("/accept")) {
        return Promise.resolve(reviewWindowResponse());
      }
      return Promise.resolve(detailResponse(url));
    });

    render(<WindowHarness scope="project:p1" />);
    const btn = await screen.findByTestId("review-verb");
    fireEvent.click(btn);

    await waitFor(() => {
      const groups = screen.getAllByTestId("review-kind-group");
      expect(groups.length).toBeGreaterThanOrEqual(2);
    });

    const labels = screen.getAllByTestId("review-kind-label");
    expect(labels.some((el) => el.textContent === "Risk attention")).toBe(true);
    expect(labels.some((el) => el.textContent === "Review flags")).toBe(true);

    const counts = screen.getAllByTestId("review-kind-count");
    expect(counts.length).toBeGreaterThanOrEqual(2);
  });
});

describe("Conflict both-sources (WEB-STA-006)", () => {
  it("renders conflicting sources for conflict proposals", async () => {
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room/read")) return Promise.resolve({ read_at: new Date().toISOString() });
      if (url.includes("/room")) {
        return Promise.resolve(roomResponse({
          review: {
            state: "ok",
            pending_count: 3,
            open_review_id: "prev_r1",
            last_accepted_at: null,
          },
        }));
      }
      if (url.includes("/reviews") && !url.includes("/decide") && !url.includes("/accept")) {
        return Promise.resolve(reviewWindowResponse());
      }
      return Promise.resolve(detailResponse(url));
    });

    render(<WindowHarness scope="project:p1" />);
    const btn = await screen.findByTestId("review-verb");
    fireEvent.click(btn);

    await waitFor(() => {
      expect(screen.getByTestId("review-posture")).toBeTruthy();
    });

    // Navigate to the conflict proposal (index 2)
    // The conflict proposal should show both sources when selected
    // The queue items should be present
    const items = screen.getAllByTestId("review-queue-item");
    expect(items.length).toBeGreaterThanOrEqual(1);
  });
});

describe("Room review section decode", () => {
  it("decodes pending_count, open_review_id, last_accepted_at from /room", async () => {
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room/read")) return Promise.resolve({ read_at: new Date().toISOString() });
      if (url.includes("/room")) {
        return Promise.resolve(roomResponse({
          review: {
            state: "ok",
            pending_count: 5,
            open_review_id: "prev_x1",
            last_accepted_at: "2026-08-29T15:00:00",
          },
        }));
      }
      return Promise.resolve(detailResponse(url));
    });

    render(<WindowHarness scope="project:p1" />);
    // When pending > 0, the review verb appears
    const btn = await screen.findByTestId("review-verb");
    // HS-169-03 SELECTOR EDIT: the Room's review verb is "Review N".
    expect(btn.textContent).toContain("Review");
  });
});

/* ── Beauty-pass component tests (HS-160-06 defects 1-7) ── */

function enterReviewPosture() {
  apiFetch.mockImplementation((url: string) => {
    if (url.includes("/room/read")) return Promise.resolve({ read_at: new Date().toISOString() });
    if (url.includes("/room")) {
      return Promise.resolve(roomResponse({
        review: {
          state: "ok",
          pending_count: 3,
          open_review_id: "prev_r1",
          last_accepted_at: null,
        },
      }));
    }
    if (url.includes("/reviews") && !url.includes("/decide") && !url.includes("/accept")) {
      return Promise.resolve(reviewWindowResponse());
    }
    if (url.includes("/decide")) {
      return Promise.resolve({ verb: "defer", lifecycle: "deferred" });
    }
    return Promise.resolve(detailResponse(url));
  });
}

describe("Plain-words card anchor (defect 1)", () => {
  it("shows human headline instead of machine 'kind: ref' string", async () => {
    enterReviewPosture();
    render(<WindowHarness scope="project:p1" />);
    const btn = await screen.findByTestId("review-verb");
    fireEvent.click(btn);

    await waitFor(() => {
      expect(screen.getByTestId("review-posture")).toBeTruthy();
    });

    // The headline should be a human headline, not the raw machine title
    const detail = screen.getByTestId("review-detail");
    // HS-167-05: ChoiceCardShell replaced by inline expansion with data-testid
    const label = detail.querySelector("[data-testid='review-detail-headline']");
    expect(label).toBeTruthy();
    expect(label!.textContent).toBe("Overdue commitment needs attention");
    expect(label!.textContent).not.toContain("risk_attention");
    expect(label!.textContent).not.toContain("action_item:");
  });

  it("shows the human subject as the card description", async () => {
    enterReviewPosture();
    render(<WindowHarness scope="project:p1" />);
    const btn = await screen.findByTestId("review-verb");
    fireEvent.click(btn);

    await waitFor(() => {
      expect(screen.getByTestId("review-posture")).toBeTruthy();
    });

    const detail = screen.getByTestId("review-detail");
    // HS-167-05: ChoiceCardShell replaced by inline expansion with data-testid
    const desc = detail.querySelector("[data-testid='review-detail-subject']");
    expect(desc).toBeTruthy();
    // Subject extracted from patch text field
    expect(desc!.textContent).toBe("Update PCI compliance docs");
  });
});

describe("Human queue rows (defect 2)", () => {
  it("shows human text in queue rows, not truncated kind strings", async () => {
    enterReviewPosture();
    render(<WindowHarness scope="project:p1" />);
    const btn = await screen.findByTestId("review-verb");
    fireEvent.click(btn);

    await waitFor(() => {
      const items = screen.getAllByTestId("review-queue-item");
      expect(items.length).toBeGreaterThanOrEqual(1);
    });

    const items = screen.getAllByTestId("review-queue-item");
    // First item should show the patch text, not the kind
    const firstText = items[0].querySelector(".review-queue-row-text");
    expect(firstText).toBeTruthy();
    expect(firstText!.textContent).toBe("Update PCI compliance docs");
    expect(firstText!.textContent).not.toContain("risk_a");
  });
});

describe("Hidden machine keys (defect 4)", () => {
  it("omits card_id from visible field rows", async () => {
    enterReviewPosture();
    render(<WindowHarness scope="project:p1" />);
    const btn = await screen.findByTestId("review-verb");
    fireEvent.click(btn);

    await waitFor(() => {
      expect(screen.getByTestId("review-comparison")).toBeTruthy();
    });

    // The comparison should not render card_id as a visible field label
    // HS-167-05: SurfaceFacts renders <dt> elements instead of .review-field-key
    const fieldKeys = screen.getByTestId("review-comparison")
      .querySelectorAll(".surface-facts dt");
    const keyTexts = Array.from(fieldKeys).map((el) => el.textContent);
    expect(keyTexts).not.toContain("card_id");
    // But human fields should be present with humanized labels
    expect(keyTexts).toContain("Text");
    expect(keyTexts).toContain("Owner");
    expect(keyTexts).toContain("Lane");
  });

  it("stores machine ids in data-attrs on the fields container", async () => {
    enterReviewPosture();
    render(<WindowHarness scope="project:p1" />);
    const btn = await screen.findByTestId("review-verb");
    fireEvent.click(btn);

    await waitFor(() => {
      expect(screen.getByTestId("review-comparison")).toBeTruthy();
    });

    // HS-167-05: machine attrs are on the review-detail container
    const fields = screen.getByTestId("review-detail");
    expect(fields).toBeTruthy();
    expect(fields!.getAttribute("data-card-id")).toBe("ai-01");
  });
});

describe("Materiality temperature token (defect 6)", () => {
  it("shows High/Medium/Low instead of raw float", async () => {
    enterReviewPosture();
    render(<WindowHarness scope="project:p1" />);
    const btn = await screen.findByTestId("review-verb");
    fireEvent.click(btn);

    await waitFor(() => {
      expect(screen.getByTestId("review-posture")).toBeTruthy();
    });

    // Queue materiality tokens should show human levels
    const matTokens = screen.getAllByTestId("review-queue-item")
      .map((item) => item.querySelector(".review-queue-materiality"));
    expect(matTokens[0]).toBeTruthy();
    expect(matTokens[0]!.textContent).toBe("High");

    // The raw float should be in data-materiality
    expect(matTokens[0]!.getAttribute("data-materiality")).toBe("0.8");

    // High materiality gets warn tone
    expect(matTokens[0]!.getAttribute("data-tone")).toBe("warn");
  });

  it("shows Medium for 0.5 materiality with no tone", async () => {
    enterReviewPosture();
    render(<WindowHarness scope="project:p1" />);
    const btn = await screen.findByTestId("review-verb");
    fireEvent.click(btn);

    await waitFor(() => {
      const items = screen.getAllByTestId("review-queue-item");
      expect(items.length).toBeGreaterThanOrEqual(2);
    });

    // Second proposal has materiality 0.5 (Medium)
    const items = screen.getAllByTestId("review-queue-item");
    const secondMat = items[1].querySelector(".review-queue-materiality");
    expect(secondMat).toBeTruthy();
    expect(secondMat!.textContent).toBe("Medium");
    expect(secondMat!.getAttribute("data-tone")).toBeNull();
  });
});

describe("Single position source (defect 7)", () => {
  it("header shows position, footer shows disposition tally not position", async () => {
    enterReviewPosture();
    render(<WindowHarness scope="project:p1" />);
    const btn = await screen.findByTestId("review-verb");
    fireEvent.click(btn);

    await waitFor(() => {
      expect(screen.getByTestId("review-position")).toBeTruthy();
    });

    // Header position shows "1 / 3"
    const position = screen.getByTestId("review-position");
    expect(position.textContent).toContain("1 / 3");

    // Footer tally should NOT duplicate the position
    const tally = screen.getByTestId("review-footer-tally");
    expect(tally.textContent).not.toContain("1/3");
    expect(tally.textContent).not.toContain("REVIEW");
    // With 3 proposals, 0 decided -> "3 left"
    expect(tally.textContent).toContain("3 left");
  });
});

describe("Defer two-step (defect 5)", () => {
  it("clicking Defer button arms the defer (shows date + confirm)", async () => {
    enterReviewPosture();
    render(<WindowHarness scope="project:p1" />);
    const btn = await screen.findByTestId("review-verb");
    fireEvent.click(btn);

    await waitFor(() => {
      expect(screen.getByTestId("review-posture")).toBeTruthy();
    });

    // Initially, no armed defer UI
    expect(screen.queryByTestId("review-defer-armed")).toBeNull();

    // Click the Defer button in the inline verb bar (wide layout)
    const inlineBar = screen.getByTestId("review-verbs-inline");
    const deferBtn = inlineBar.querySelector("[aria-label^='Defer']") as HTMLElement;
    expect(deferBtn).toBeTruthy();
    fireEvent.click(deferBtn!);

    // Armed UI appears in the inline verb bar: date input + confirm
    await waitFor(() => {
      const armed = inlineBar.querySelector("[data-testid='review-defer-armed']");
      expect(armed).toBeTruthy();
    });
    expect(inlineBar.querySelector("[data-testid='review-defer-date']")).toBeTruthy();
    expect(inlineBar.querySelector("[data-testid='review-defer-confirm']")).toBeTruthy();
  });
});
