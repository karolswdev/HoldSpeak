// HS-169-02 — DoorCore vitest: every state the one-screen Door passes through.

import React from "react";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

/* ── Mock door API ── */

const mockDoorCount = vi.fn();
const mockDoorCreate = vi.fn();

vi.mock("../api", () => ({
  doorCount: (...args: unknown[]) => mockDoorCount(...args),
  doorCreate: (...args: unknown[]) => mockDoorCreate(...args),
}));

/* ── Mock setup/api (discovery wires) ── */

const mockDiscoverGitHub = vi.fn();
const mockDiscoverJira = vi.fn();

vi.mock("../../setup/api", () => ({
  discoverGitHub: (...args: unknown[]) => mockDiscoverGitHub(...args),
  discoverJira: (...args: unknown[]) => mockDiscoverJira(...args),
}));

/* ── Mock connections API ── */

const mockFetchConnections = vi.fn();

vi.mock("../../../../pages/cores/connections/api", () => ({
  fetchConnections: (...args: unknown[]) => mockFetchConnections(...args),
}));

/* ── Mock shell ── */

const mockOpenSurface = vi.fn();

vi.mock("../../../../desk/shell", () => ({
  openSurface: (...args: unknown[]) => mockOpenSurface(...args),
}));

/* ── Mock desk store ── */

const mockOpenSurfaceWindow = vi.fn();
const mockCloseSurfaceWindow = vi.fn();

vi.mock("../../../../desk/store", () => ({
  useDesk: {
    getState: () => ({
      windowsById: {},
      openSurfaceWindow: mockOpenSurfaceWindow,
      closeSurfaceWindow: mockCloseSurfaceWindow,
    }),
    subscribe: () => () => {},
  },
}));

/* ── Mock surface barrel (renders inline for test env) ── */

vi.mock("../../../../desk/surface", () => ({
  SurfaceLedgerRow: ({
    primary,
    lead,
    cells,
    trailing,
    children,
    open,
    wrap,
    expands,
    onToggle,
    ...rest
  }: Record<string, unknown>) => (
    <li
      className="surface-ledger-row"
      data-open={open || undefined}
      {...(rest["data-testid"] ? { "data-testid": rest["data-testid"] } : {})}
    >
      {lead != null ? <span className="surface-ledger-lead">{lead as React.ReactNode}</span> : null}
      <span className="surface-ledger-primary">{primary as React.ReactNode}</span>
      {cells != null ? <span className="surface-ledger-cells">{cells as React.ReactNode}</span> : null}
      {trailing != null ? <span className="surface-ledger-trailing">{trailing as React.ReactNode}</span> : null}
      {children as React.ReactNode}
    </li>
  ),
  SurfaceFooter: ({
    receipt,
    verbs,
  }: {
    receipt?: React.ReactNode;
    verbs?: React.ReactNode;
  }) => (
    <footer data-testid="surface-footer">
      {receipt}
      {verbs}
    </footer>
  ),
  StateChip: ({ state, label, icon }: { state?: string; label?: string; icon?: string }) => (
    <span data-testid={`state-chip-${label?.toLowerCase().replace(/\s+/g, "-") ?? state}`} className={`state-chip-${state}`}>
      {icon ?? ""}{label}
    </span>
  ),
  EgressChip: ({ label, scope }: { label?: string; scope?: string }) => (
    <span data-testid="egress-chip" className="egress-chip">
      {label}
    </span>
  ),
  CheckGadget: ({
    label,
    checked,
    onChange,
  }: {
    label?: string;
    checked?: boolean;
    onChange?: (v: boolean) => void;
  }) => (
    <span
      data-testid={`check-gadget-${label?.toLowerCase().replace(/\s+/g, "-")}`}
      data-checked={checked}
      onClick={() => onChange?.(!checked)}
      role="checkbox"
      aria-checked={checked}
    >
      {label}
    </span>
  ),
  StringGadget: ({
    label,
    value,
    onChange,
    placeholder,
    autoFocus,
  }: {
    label?: string;
    value?: string;
    onChange?: (v: string) => void;
    placeholder?: string;
    autoFocus?: boolean;
  }) => (
    <input
      data-testid={`string-gadget-${label?.toLowerCase().replace(/\s+/g, "-")}`}
      value={value ?? ""}
      onChange={(e) => onChange?.(e.target.value)}
      placeholder={placeholder}
      autoFocus={autoFocus}
    />
  ),
  MicButton: ({
    onText,
    label,
  }: {
    onText: (text: string) => void;
    label?: string;
  }) => (
    <button
      data-testid="mic-btn"
      aria-label={label}
      onClick={() => onText("voice input")}
    >
      Mic
    </button>
  ),
}));

/* ── Mock TitleSlotContext ── */

vi.mock("../../../../desk/surface/title", () => ({
  TitleSlotContext: React.createContext(null),
}));

/* ── Import component AFTER mocks ── */

import { DoorCore } from "../DoorCore";

/* ── Fixture helpers ── */

function ghTool(connected: boolean) {
  return {
    provider_id: "github",
    state: connected ? "connected" : "not_configured",
    egress_host: "github.com",
    connections: undefined,
  };
}

function jiraTool(connected: boolean) {
  return {
    provider_id: "jira",
    state: connected ? "connected" : "not_configured",
    egress_host: "mysite.atlassian.net",
    connections: connected
      ? [
          {
            connection_ref: "mysite.atlassian.net|user@example.com",
            state: "connected",
            account: { site: "mysite.atlassian.net", email: "user@example.com" },
          },
        ]
      : undefined,
  };
}

function connectedTools() {
  return { tools: [ghTool(true), jiraTool(true)] };
}

function coldTools() {
  return { tools: [ghTool(false), jiraTool(false)] };
}

function liveCountResponse(
  provider: string,
): Record<string, unknown> {
  if (provider === "github") {
    return {
      tokens: [
        { key: "open_prs", label: "12 open PRs", count: 12 },
        { key: "ci", label: "CI green", count: 1 },
      ],
      plain: "12 open PRs · CI green",
      checkedAt: "2026-09-04T10:00:00Z",
      host: "GITHUB.COM",
      state: "live",
      reason: null,
    };
  }
  return {
    tokens: [
      { key: "overdue", label: "3 overdue", count: 3 },
      { key: "due_7_days", label: "5 due this week", count: 5 },
    ],
    plain: "3 overdue · 5 due this week",
    checkedAt: "2026-09-04T10:00:00Z",
    host: "MYSITE.ATLASSIAN.NET",
    state: "live",
    reason: null,
  };
}

function cantCheckResponse(): Record<string, unknown> {
  return {
    tokens: [],
    plain: "",
    checkedAt: "2026-09-04T10:00:00Z",
    host: "GITHUB.COM",
    state: "cant_check",
    reason: "GitHub CLI query failed",
  };
}

function ghDiscoveryItems() {
  return {
    items: [
      { id: "karolswdev/HoldSpeak", owner: "karolswdev", name: "HoldSpeak", visibility: "public" },
      { id: "karolswdev/reusable-processes", owner: "karolswdev", name: "reusable-processes", visibility: "private" },
    ],
    cursor: null,
  };
}

/* ── beforeEach ── */

beforeEach(() => {
  vi.clearAllMocks();
  mockFetchConnections.mockResolvedValue({ tools: [] });
  mockDoorCount.mockResolvedValue(liveCountResponse("github"));
  mockDoorCreate.mockResolvedValue({ projectId: "proj_test_123" });
  mockDiscoverGitHub.mockResolvedValue(ghDiscoveryItems());
  mockDiscoverJira.mockResolvedValue({ items: [], cursor: null });
});

/* ── Tests ── */

describe("DoorCore", () => {
  describe("first open", () => {
    it("renders the outcome well with placeholder", async () => {
      mockFetchConnections.mockResolvedValue({ tools: [] });
      render(<DoorCore scope="" />);

      await waitFor(() => {
        expect(screen.getByTestId("door-root")).toBeTruthy();
      });
      const input = screen.getByTestId("door-outcome-input") as HTMLInputElement;
      expect(input.placeholder).toBe("What are you delivering?");
      expect(input.value).toBe("");
    });

    it("shows 'THIS BECOMES THE PROJECT'S NAME' caption", async () => {
      render(<DoorCore scope="" />);
      await waitFor(() => {
        expect(screen.getByTestId("door-root")).toBeTruthy();
      });
      expect(screen.getByText(/THIS BECOMES THE PROJECT/)).toBeTruthy();
    });

    it("shows SOURCES label", async () => {
      render(<DoorCore scope="" />);
      await waitFor(() => {
        expect(screen.getByTestId("door-sources-label")).toBeTruthy();
      });
      expect(screen.getByTestId("door-sources-label").textContent).toContain("SOURCES");
    });
  });

  describe("cold state — not connected", () => {
    beforeEach(() => {
      mockFetchConnections.mockResolvedValue(coldTools());
    });

    it("shows Connect buttons for both providers", async () => {
      render(<DoorCore scope="" />);
      await waitFor(() => {
        expect(screen.getByTestId("door-connect-github")).toBeTruthy();
      });
      expect(screen.getByTestId("door-connect-jira")).toBeTruthy();
    });

    it("shows SIGN IN chip for github with not_configured state", async () => {
      mockFetchConnections.mockResolvedValue({
        tools: [
          { ...ghTool(false), state: "owner_action_required" },
          jiraTool(false),
        ],
      });
      render(<DoorCore scope="" />);
      await waitFor(() => {
        expect(screen.getByTestId("state-chip-sign-in")).toBeTruthy();
      });
    });

    it("shows NOT SET UP chip for not-configured providers", async () => {
      render(<DoorCore scope="" />);
      await waitFor(() => {
        const chips = screen.getAllByTestId("state-chip-not-set-up");
        expect(chips.length).toBeGreaterThanOrEqual(1);
      });
    });

    it("shows NO SOURCES · BLANK PROJECT receipt", async () => {
      render(<DoorCore scope="" />);
      await waitFor(() => {
        expect(screen.getByTestId("door-receipt")).toBeTruthy();
      });
      expect(screen.getByTestId("door-receipt").textContent).toBe(
        "NO SOURCES · BLANK PROJECT",
      );
    });
  });

  describe("connected state — rows with scope triggers", () => {
    beforeEach(() => {
      mockFetchConnections.mockResolvedValue(connectedTools());
    });

    it("shows scope trigger buttons for connected providers", async () => {
      render(<DoorCore scope="" />);
      await waitFor(() => {
        expect(screen.getByTestId("door-trigger-github")).toBeTruthy();
      });
      expect(screen.getByTestId("door-trigger-jira")).toBeTruthy();
    });

    it("shows placeholder text in trigger before scope picked", async () => {
      render(<DoorCore scope="" />);
      await waitFor(() => {
        expect(screen.getByTestId("door-trigger-github")).toBeTruthy();
      });
      expect(screen.getByTestId("door-trigger-github").textContent).toContain(
        "Choose a repository",
      );
      expect(screen.getByTestId("door-trigger-jira").textContent).toContain(
        "Choose a project",
      );
    });

    it("renders watch toggles for github (OPEN PRS, CI)", async () => {
      render(<DoorCore scope="" />);
      await waitFor(() => {
        expect(screen.getByTestId("check-gadget-open-prs")).toBeTruthy();
      });
      expect(screen.getByTestId("check-gadget-ci")).toBeTruthy();
    });

    it("renders watch toggles for jira (OVERDUE, DUE 7 DAYS, BLOCKED)", async () => {
      render(<DoorCore scope="" />);
      await waitFor(() => {
        expect(screen.getByTestId("check-gadget-overdue")).toBeTruthy();
      });
      expect(screen.getByTestId("check-gadget-due-7-days")).toBeTruthy();
      expect(screen.getByTestId("check-gadget-blocked")).toBeTruthy();
    });

    it("BLOCKED toggle defaults to off", async () => {
      render(<DoorCore scope="" />);
      await waitFor(() => {
        expect(screen.getByTestId("check-gadget-blocked")).toBeTruthy();
      });
      expect(
        screen.getByTestId("check-gadget-blocked").getAttribute("data-checked"),
      ).toBe("false");
    });

    it("shows EgressChip on connected rows", async () => {
      render(<DoorCore scope="" />);
      await waitFor(() => {
        const chips = screen.getAllByTestId("egress-chip");
        expect(chips.length).toBeGreaterThanOrEqual(2);
      });
    });

    it("shows Adjust button on connected rows", async () => {
      render(<DoorCore scope="" />);
      await waitFor(() => {
        expect(screen.getByTestId("door-adjust-github")).toBeTruthy();
      });
      expect(screen.getByTestId("door-adjust-jira")).toBeTruthy();
    });
  });

  describe("picker open", () => {
    beforeEach(() => {
      mockFetchConnections.mockResolvedValue(connectedTools());
    });

    it("opens picker on trigger click and shows search input", async () => {
      render(<DoorCore scope="" />);
      await waitFor(() => {
        expect(screen.getByTestId("door-trigger-github")).toBeTruthy();
      });

      await act(async () => {
        fireEvent.click(screen.getByTestId("door-trigger-github"));
      });

      await waitFor(() => {
        expect(screen.getByTestId("door-picker-github")).toBeTruthy();
      });
      expect(
        screen.getByTestId("string-gadget-search-repositories"),
      ).toBeTruthy();
    });

    it("shows discovered repo items", async () => {
      render(<DoorCore scope="" />);
      await waitFor(() => {
        expect(screen.getByTestId("door-trigger-github")).toBeTruthy();
      });

      await act(async () => {
        fireEvent.click(screen.getByTestId("door-trigger-github"));
      });

      await waitFor(() => {
        expect(
          screen.getByTestId("door-pick-karolswdev/HoldSpeak"),
        ).toBeTruthy();
      });
    });
  });

  describe("adjust open", () => {
    beforeEach(() => {
      mockFetchConnections.mockResolvedValue(connectedTools());
    });

    it("opens adjust well for github with base branch, labels, drafts", async () => {
      render(<DoorCore scope="" />);
      await waitFor(() => {
        expect(screen.getByTestId("door-adjust-github")).toBeTruthy();
      });

      await act(async () => {
        fireEvent.click(screen.getByTestId("door-adjust-github"));
      });

      await waitFor(() => {
        expect(screen.getByTestId("door-adjust-well-github")).toBeTruthy();
      });
      expect(screen.getByTestId("string-gadget-base-branch")).toBeTruthy();
      expect(screen.getByTestId("string-gadget-labels")).toBeTruthy();
      expect(screen.getByTestId("check-gadget-drafts")).toBeTruthy();
    });

    it("opens adjust well for jira with issue types and JQL", async () => {
      render(<DoorCore scope="" />);
      await waitFor(() => {
        expect(screen.getByTestId("door-adjust-jira")).toBeTruthy();
      });

      await act(async () => {
        fireEvent.click(screen.getByTestId("door-adjust-jira"));
      });

      await waitFor(() => {
        expect(screen.getByTestId("door-adjust-well-jira")).toBeTruthy();
      });
      expect(screen.getByTestId("string-gadget-issue-types")).toBeTruthy();
      expect(screen.getByTestId("string-gadget-jql-filter")).toBeTruthy();
    });
  });

  describe("checking state", () => {
    beforeEach(() => {
      mockFetchConnections.mockResolvedValue(connectedTools());
      mockDoorCount.mockImplementation(
        () => new Promise(() => {}),
      );
    });

    it("shows CHECKING chip after scope is picked", async () => {
      render(<DoorCore scope="" />);
      await waitFor(() => {
        expect(screen.getByTestId("door-trigger-github")).toBeTruthy();
      });

      await act(async () => {
        fireEvent.click(screen.getByTestId("door-trigger-github"));
      });
      await waitFor(() => {
        expect(
          screen.getByTestId("door-pick-karolswdev/HoldSpeak"),
        ).toBeTruthy();
      });

      await act(async () => {
        fireEvent.click(
          screen.getByTestId("door-pick-karolswdev/HoldSpeak"),
        );
      });

      await waitFor(() => {
        expect(screen.getByTestId("state-chip-checking")).toBeTruthy();
      });
    });
  });

  describe("live state — counts arrived", () => {
    beforeEach(() => {
      mockFetchConnections.mockResolvedValue(connectedTools());
      mockDoorCount.mockResolvedValue(liveCountResponse("github"));
    });

    it("shows count text after scope is picked and count resolves", async () => {
      render(<DoorCore scope="" />);
      await waitFor(() => {
        expect(screen.getByTestId("door-trigger-github")).toBeTruthy();
      });

      await act(async () => {
        fireEvent.click(screen.getByTestId("door-trigger-github"));
      });
      await waitFor(() => {
        expect(
          screen.getByTestId("door-pick-karolswdev/HoldSpeak"),
        ).toBeTruthy();
      });

      await act(async () => {
        fireEvent.click(
          screen.getByTestId("door-pick-karolswdev/HoldSpeak"),
        );
      });

      await waitFor(() => {
        expect(screen.getByTestId("door-counts-github")).toBeTruthy();
      });
      expect(screen.getByTestId("door-counts-github").textContent).toBe(
        "12 open PRs · CI green",
      );
    });
  });

  describe("cant_check state", () => {
    beforeEach(() => {
      mockFetchConnections.mockResolvedValue(connectedTools());
      mockDoorCount.mockResolvedValue(cantCheckResponse());
    });

    it("shows CAN'T CHECK chip with reason", async () => {
      render(<DoorCore scope="" />);
      await waitFor(() => {
        expect(screen.getByTestId("door-trigger-github")).toBeTruthy();
      });

      await act(async () => {
        fireEvent.click(screen.getByTestId("door-trigger-github"));
      });
      await waitFor(() => {
        expect(
          screen.getByTestId("door-pick-karolswdev/HoldSpeak"),
        ).toBeTruthy();
      });

      await act(async () => {
        fireEvent.click(
          screen.getByTestId("door-pick-karolswdev/HoldSpeak"),
        );
      });

      await waitFor(() => {
        expect(screen.getByTestId("state-chip-can't-check")).toBeTruthy();
      });
      expect(screen.getByText("GitHub CLI query failed")).toBeTruthy();
    });
  });

  describe("Create button state", () => {
    it("is disabled when outcome is empty", async () => {
      mockFetchConnections.mockResolvedValue(connectedTools());
      render(<DoorCore scope="" />);
      await waitFor(() => {
        expect(screen.getByTestId("door-create")).toBeTruthy();
      });
      expect(
        (screen.getByTestId("door-create") as HTMLButtonElement).disabled,
      ).toBe(true);
    });

    it("is enabled when outcome has text", async () => {
      mockFetchConnections.mockResolvedValue(connectedTools());
      render(<DoorCore scope="" />);
      await waitFor(() => {
        expect(screen.getByTestId("door-outcome-input")).toBeTruthy();
      });

      fireEvent.change(screen.getByTestId("door-outcome-input"), {
        target: { value: "Ship Q4 on time" },
      });

      expect(
        (screen.getByTestId("door-create") as HTMLButtonElement).disabled,
      ).toBe(false);
    });
  });

  describe("blank project receipt", () => {
    it("shows NO SOURCES · BLANK PROJECT when no scopes are picked", async () => {
      mockFetchConnections.mockResolvedValue(connectedTools());
      render(<DoorCore scope="" />);
      await waitFor(() => {
        expect(screen.getByTestId("door-receipt")).toBeTruthy();
      });
      expect(screen.getByTestId("door-receipt").textContent).toBe(
        "NO SOURCES · BLANK PROJECT",
      );
    });

    it("updates receipt after picking a scope", async () => {
      mockFetchConnections.mockResolvedValue(connectedTools());
      mockDoorCount.mockResolvedValue(liveCountResponse("github"));
      render(<DoorCore scope="" />);
      await waitFor(() => {
        expect(screen.getByTestId("door-trigger-github")).toBeTruthy();
      });

      await act(async () => {
        fireEvent.click(screen.getByTestId("door-trigger-github"));
      });
      await waitFor(() => {
        expect(
          screen.getByTestId("door-pick-karolswdev/HoldSpeak"),
        ).toBeTruthy();
      });

      await act(async () => {
        fireEvent.click(
          screen.getByTestId("door-pick-karolswdev/HoldSpeak"),
        );
      });

      await waitFor(() => {
        const receipt = screen.getByTestId("door-receipt").textContent ?? "";
        expect(receipt).toContain("SOURCE");
        expect(receipt).toContain("WATCH");
      });
    });
  });

  describe("every verb is a Button", () => {
    it("no raw <button> elements outside the library", async () => {
      mockFetchConnections.mockResolvedValue(connectedTools());
      render(<DoorCore scope="" />);
      await waitFor(() => {
        expect(screen.getByTestId("door-root")).toBeTruthy();
      });

      const root = screen.getByTestId("door-root");
      const rawButtons = root.querySelectorAll("button");
      for (const btn of rawButtons) {
        const testId = btn.getAttribute("data-testid") ?? "";
        const ariaLabel = btn.getAttribute("aria-label") ?? "";
        expect(
          testId.startsWith("door-") ||
            testId === "mic-btn" ||
            testId.startsWith("check-gadget-") ||
            ariaLabel.length > 0,
        ).toBe(true);
      }
    });
  });

  describe("create flow", () => {
    it("calls doorCreate and opens the project room", async () => {
      mockFetchConnections.mockResolvedValue(connectedTools());
      mockDoorCreate.mockResolvedValue({ projectId: "proj_new_abc" });
      render(<DoorCore scope="" />);
      await waitFor(() => {
        expect(screen.getByTestId("door-outcome-input")).toBeTruthy();
      });

      fireEvent.change(screen.getByTestId("door-outcome-input"), {
        target: { value: "Ship Q4 on time" },
      });

      await act(async () => {
        fireEvent.click(screen.getByTestId("door-create"));
      });

      await waitFor(() => {
        expect(mockDoorCreate).toHaveBeenCalledWith(
          "Ship Q4 on time",
          expect.any(Array),
        );
      });

      await waitFor(() => {
        expect(mockOpenSurface).toHaveBeenCalledWith(
          "open-project-memory",
          "project:proj_new_abc",
        );
      });
    });
  });

  describe("cancel", () => {
    it("closes the surface window", async () => {
      render(<DoorCore scope="" />);
      await waitFor(() => {
        expect(screen.getByTestId("door-cancel")).toBeTruthy();
      });

      fireEvent.click(screen.getByTestId("door-cancel"));
      expect(mockCloseSurfaceWindow).toHaveBeenCalledWith(
        "surface-project-setup",
      );
    });
  });
});
