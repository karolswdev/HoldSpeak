// HS-135-10 -- Agents lane tests: blocked-first ordering (fixture),
// Answer fires the real openCoderSession (mocked), counts truthful,
// maxItems caps, empty state honest ("No sessions").

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AgentsLane } from "./AgentsLane";

// ---------------------------------------------------------------------------
// mocks
// ---------------------------------------------------------------------------

const apiFetch = vi.hoisted(() => vi.fn());

vi.mock("../../../lib/api", () => ({
  apiFetch,
  readableError: (reason: unknown) =>
    reason instanceof Error ? reason.message : "Request failed",
}));

const openCoderSession = vi.hoisted(() => vi.fn());
const openSurface = vi.hoisted(() => vi.fn(() => true));

vi.mock("../../shell", () => ({
  openCoderSession,
  openSurface,
}));

// ---------------------------------------------------------------------------
// fixtures
// ---------------------------------------------------------------------------

const blockedSession = {
  key: "claude:blocked-1",
  session: {
    session_id: "blocked-1",
    project: "holdspeak",
    awaiting_response: true,
    question: "Regenerate the schema snapshot?",
  },
};

const runningSession = {
  key: "claude:run-1",
  session: {
    session_id: "run-1",
    project: "holdspeak-mobile",
    awaiting_response: false,
    summary: "Running tests",
  },
};

const seededCoders = {
  agent: {
    sessions: [runningSession, blockedSession],
  },
};

const seededRecipes = {
  recipes: [
    { id: "r1", name: "Summarize like a PM" },
    { id: "r2", name: "Code reviewer", deleted: true },
  ],
};

function mockApis(
  coders = seededCoders,
  recipes = seededRecipes,
) {
  apiFetch.mockImplementation((path: string) => {
    if (path === "/api/coders/status") return Promise.resolve(coders);
    if (path === "/api/recipes") return Promise.resolve(recipes);
    return Promise.resolve({});
  });
}

// ---------------------------------------------------------------------------
// helpers
// ---------------------------------------------------------------------------

function renderLane(
  props: Partial<React.ComponentProps<typeof AgentsLane>> = {},
) {
  const onOpenInWindow = vi.fn();
  const result = render(
    <AgentsLane onOpenInWindow={onOpenInWindow} {...props} />,
  );
  return { ...result, onOpenInWindow };
}

// ---------------------------------------------------------------------------
// tests
// ---------------------------------------------------------------------------

describe("AgentsLane", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // -- blocked-first ordering -----------------------------------------------

  it("renders blocked sessions before running (blocked-first)", async () => {
    mockApis();
    renderLane();
    await waitFor(() => {
      expect(screen.getByText("holdspeak")).toBeInTheDocument();
    });
    const blockedRow = screen.getByText("holdspeak");
    const runningRow = screen.getByText("holdspeak-mobile");
    // Blocked must appear before running in document order.
    expect(
      blockedRow.compareDocumentPosition(runningRow) &
        Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
  });

  // -- Answer verb -----------------------------------------------------------

  it("blocked session shows Answer verb that fires openCoderSession", async () => {
    mockApis();
    renderLane();
    await waitFor(() => {
      expect(screen.getByText("holdspeak")).toBeInTheDocument();
    });
    const answerBtn = screen.getByRole("button", { name: "Answer holdspeak" });
    expect(answerBtn).toBeInTheDocument();
    fireEvent.click(answerBtn);
    expect(openCoderSession).toHaveBeenCalledWith("claude:blocked-1");
  });

  it("running session does NOT show Answer verb", async () => {
    mockApis();
    renderLane();
    await waitFor(() => {
      expect(screen.getByText("holdspeak-mobile")).toBeInTheDocument();
    });
    expect(
      screen.queryByRole("button", { name: /Answer holdspeak-mobile/ }),
    ).not.toBeInTheDocument();
  });

  // -- counts truthful -------------------------------------------------------

  it("shows truthful crew/blocked counts in the title", async () => {
    mockApis();
    renderLane();
    await waitFor(() => {
      expect(screen.getByText("holdspeak")).toBeInTheDocument();
    });
    // Crew: 1 (r2 is deleted), Blocked: 1.
    const heading = screen.getByText(/AGENTS/);
    expect(heading.textContent).toContain("CREW 1");
    expect(heading.textContent).toContain("BLOCKED 1");
  });

  // -- maxItems cap ----------------------------------------------------------

  it("caps visible items at maxItems", async () => {
    const manySessions = Array.from({ length: 5 }, (_, i) => ({
      key: `claude:s-${i}`,
      session: {
        session_id: `s-${i}`,
        project: `project-${i}`,
        awaiting_response: false,
      },
    }));
    mockApis(
      { agent: { sessions: manySessions } },
      { recipes: [] },
    );
    renderLane({ maxItems: 3 });
    await waitFor(() => {
      expect(screen.getByText("project-0")).toBeInTheDocument();
    });
    // Only 3 of 5 items visible.
    expect(screen.getByText("project-0")).toBeInTheDocument();
    expect(screen.getByText("project-1")).toBeInTheDocument();
    expect(screen.getByText("project-2")).toBeInTheDocument();
    expect(screen.queryByText("project-3")).not.toBeInTheDocument();
    expect(screen.queryByText("project-4")).not.toBeInTheDocument();
    // Footer overflow.
    expect(screen.getByText(/2 more/)).toBeInTheDocument();
  });

  // -- empty state -----------------------------------------------------------

  it("renders honest empty state when no sessions", async () => {
    mockApis({ agent: { sessions: [] } }, { recipes: [] });
    renderLane();
    await waitFor(() => {
      expect(screen.getByText("No sessions")).toBeInTheDocument();
    });
    const emptyState = screen.getByText("No sessions");
    expect(emptyState.closest(".surface-section")).not.toBeNull();
    expect(screen.getByRole("heading", { name: "AGENTS · CREW 0 · BLOCKED 0" })).toBeInTheDocument();
    expect(screen.getByLabelText("Open AGENTS · CREW 0 · BLOCKED 0")).toBeInTheDocument();
  });

  // -- header-click opens Agents window --------------------------------------

  it("header click opens the Agents window (surface-companion)", async () => {
    mockApis();
    renderLane();
    await waitFor(() => {
      expect(screen.getByText("holdspeak")).toBeInTheDocument();
    });
    const headerBtn = screen.getByLabelText(/Open AGENTS/);
    fireEvent.click(headerBtn);
    expect(openSurface).toHaveBeenCalledWith("surface-companion");
  });

  // -- state badges ----------------------------------------------------------

  it("shows BLOCKED lamp for blocked session and RUN lamp for running", async () => {
    mockApis();
    renderLane();
    await waitFor(() => {
      expect(screen.getByText("holdspeak")).toBeInTheDocument();
    });
    expect(screen.getByText("BLOCKED")).toBeInTheDocument();
    expect(screen.getByText("RUN")).toBeInTheDocument();
  });
});
