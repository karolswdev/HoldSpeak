// HS-169-02 — DoorCore vitest: every state the one-screen Door passes through.

import React from "react";
import { render, screen, fireEvent, waitFor, act, within } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

/* ── Mock door API (includes discovery wires moved from setup/api by HS-170-02) ── */

const mockDoorCount = vi.fn();
const mockDoorCreate = vi.fn();
const mockDoorAddSources = vi.fn();
const mockDiscoverGitHub = vi.fn();
const mockDiscoverJira = vi.fn();
const mockDiscoverConfluence = vi.fn();

vi.mock("../api", () => ({
  doorCount: (...args: unknown[]) => mockDoorCount(...args),
  doorCreate: (...args: unknown[]) => mockDoorCreate(...args),
  doorAddSources: (...args: unknown[]) => mockDoorAddSources(...args),
  discoverGitHub: (...args: unknown[]) => mockDiscoverGitHub(...args),
  discoverJira: (...args: unknown[]) => mockDiscoverJira(...args),
  discoverConfluence: (...args: unknown[]) => mockDiscoverConfluence(...args),
}));

/* ── Mock connections API ── */

const mockFetchConnections = vi.fn();
const mockRecheckProvider = vi.fn();
const mockAddAtlassianAccount = vi.fn();

vi.mock("../../../../pages/cores/connections/api", () => ({
  fetchConnections: (...args: unknown[]) => mockFetchConnections(...args),
  recheckProvider: (...args: unknown[]) => mockRecheckProvider(...args),
  addAtlassianAccount: (...args: unknown[]) => mockAddAtlassianAccount(...args),
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
  SurfaceWell: ({ children }: { children?: React.ReactNode }) => <div data-testid="surface-well">{children}</div>,
  TransportKey: ({ label, onClick }: { label?: string; onClick?: () => void }) => (
    <button data-testid={`transport-${label?.toLowerCase()}`} onClick={onClick}>{label}</button>
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

import { AddSourcesWell, DoorCore } from "../DoorCore";

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
  mockDoorAddSources.mockResolvedValue({ projectId: "proj_room_1" });
  mockRecheckProvider.mockResolvedValue(null);
  mockAddAtlassianAccount.mockResolvedValue(undefined);
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

    it("shows NOT SIGNED IN chip for github when not signed in", async () => {
      mockFetchConnections.mockResolvedValue({
        tools: [
          { ...ghTool(false), state: "owner_action_required" },
          jiraTool(false),
        ],
      });
      render(<DoorCore scope="" />);
      await waitFor(() => {
        expect(screen.getByTestId("state-chip-not-signed-in")).toBeTruthy();
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

  /* ── HS-174-07: Confluence connector ── */

  describe("confluence source row", () => {
    it("shows C emblem and Confluence defaults (RECENT BLOGS on, PAGES BY ID off)", async () => {
      mockFetchConnections.mockResolvedValue({
        tools: [
          {
            provider_id: "github",
            state: "connected",
            account: { login: "karolswdev" },
            egress_host: "github.com",
          },
          {
            provider_id: "jira",
            state: "connected",
            account: { site: "karolsaneapple.atlassian.net", email: "karol@sane.com" },
            egress_host: "karolsaneapple.atlassian.net",
            connections: [
              {
                connection_ref: "karolsaneapple.atlassian.net|karol@sane.com",
                state: "connected",
                account: { site: "karolsaneapple.atlassian.net", email: "karol@sane.com" },
              },
            ],
          },
          {
            provider_id: "confluence",
            state: "connected",
            account: { site: "karolswdev.atlassian.net", email: "karolsane@gmail.com" },
            egress_host: "karolswdev.atlassian.net",
            connections: [
              {
                connection_ref: "karolswdev.atlassian.net|karolsane@gmail.com",
                state: "connected",
                account: { site: "karolswdev.atlassian.net", email: "karolsane@gmail.com" },
              },
            ],
          },
        ],
      });

      render(<DoorCore scope="" />);

      // Wait for the Confluence row to appear
      await waitFor(() => {
        expect(screen.getByTestId("door-row-confluence")).toBeTruthy();
      });

      // The emblem should be "C"
      const row = screen.getByTestId("door-row-confluence");
      expect(row.querySelector(".door-lead")?.textContent).toBe("C");

      // Defaults: RECENT BLOGS (on), PAGES BY ID (off)
      const recentBlogs = row.querySelector('[data-testid="door-row-confluence"] [aria-label="RECENT BLOGS"]')
        ?? row.textContent;
      expect(row.textContent).toContain("RECENT BLOGS");
      expect(row.textContent).toContain("PAGES BY ID");
    });

    it("shows NOT SET UP for a disconnected Confluence row", async () => {
      mockFetchConnections.mockResolvedValue({
        tools: [
          {
            provider_id: "confluence",
            state: "not_configured",
          },
        ],
      });

      render(<DoorCore scope="" />);

      await waitFor(() => {
        expect(screen.getByTestId("door-row-confluence")).toBeTruthy();
      });

      const row = screen.getByTestId("door-row-confluence");
      expect(row.textContent).toContain("NOT SET UP");
      expect(screen.getByTestId("door-connect-confluence")).toBeTruthy();
    });
  });
  /* PHILO-17 U29: sign in where the row is; no Settings window over the work. */
  describe("sign in in the row (U29)", () => {
    it("Connect opens the exact command with Copy in the row, not Settings", async () => {
      mockFetchConnections.mockResolvedValue({
        tools: [{ ...ghTool(false), state: "owner_action_required", recovery_hint: "gh auth login" }, jiraTool(false)],
      });
      render(<DoorCore scope="" />);
      await waitFor(() => expect(screen.getByTestId("door-connect-github")).toBeTruthy());
      await act(async () => {
        fireEvent.click(screen.getByTestId("door-connect-github"));
      });
      const well = await screen.findByTestId("signin-well-github");
      expect(well.textContent).toContain("gh auth login");
      expect(screen.getByTestId("transport-copy")).toBeTruthy();
      expect(mockOpenSurfaceWindow).not.toHaveBeenCalled();
    });

    it("the chip reads the producer's state, never the error text", async () => {
      // github_provider classifies gh's "not logged in" as owner_action_required;
      // a degraded check says what it is, whatever its text holds.
      mockFetchConnections.mockResolvedValue({
        tools: [{ ...ghTool(false), state: "degraded", error_detail: "connect to 10.0.0.1:401 timed out" }, jiraTool(false)],
      });
      render(<DoorCore scope="" />);
      await waitFor(() => expect(screen.getAllByTestId("state-chip-not-set-up").length).toBe(2));
      expect(screen.queryByTestId("state-chip-not-signed-in")).toBeNull();
    });

    it("Recheck in the row checks the provider and reads the connections again", async () => {
      mockFetchConnections.mockResolvedValue({
        tools: [{ ...ghTool(false), state: "owner_action_required" }, jiraTool(false)],
      });
      render(<DoorCore scope="" />);
      await waitFor(() => expect(screen.getByTestId("door-connect-github")).toBeTruthy());
      await act(async () => {
        fireEvent.click(screen.getByTestId("door-connect-github"));
      });
      const reads = mockFetchConnections.mock.calls.length;
      await act(async () => {
        fireEvent.click(await screen.findByTestId("signin-recheck-github"));
      });
      await waitFor(() => expect(mockRecheckProvider).toHaveBeenCalledWith("github"));
      await waitFor(() => expect(mockFetchConnections.mock.calls.length).toBeGreaterThan(reads));
    });

    it("Add for a Jira account checks it at once (never left NEVER CHECKED)", async () => {
      mockFetchConnections.mockResolvedValue({ tools: [ghTool(false), { ...jiraTool(false), connections: [] }] });
      render(<DoorCore scope="" />);
      await waitFor(() => expect(screen.getByTestId("door-connect-jira")).toBeTruthy());
      await act(async () => {
        fireEvent.click(screen.getByTestId("door-connect-jira"));
      });
      const well = await screen.findByTestId("signin-well-jira");
      const inputs = well.querySelectorAll("input");
      await act(async () => {
        fireEvent.change(inputs[0], { target: { value: "acme.atlassian.net" } });
        fireEvent.change(inputs[1], { target: { value: "me@acme.com" } });
      });
      // The exact sign-in command follows what is typed.
      expect(well.textContent).toContain("acli jira auth login --site acme.atlassian.net --email me@acme.com --token");
      await act(async () => {
        fireEvent.click(within(well).getByText("Add"));
      });
      await waitFor(() => expect(mockAddAtlassianAccount).toHaveBeenCalledWith("jira", "acme.atlassian.net", "me@acme.com"));
      await waitFor(() => expect(mockRecheckProvider).toHaveBeenCalledWith("jira"));
    });
  });

  /* PHILO-17 U10: the Room's Add source uses the same rows. */
  describe("Add source in the Room (U10)", () => {
    it("a repository the project already watches says Already watched", async () => {
      mockFetchConnections.mockResolvedValue(connectedTools());
      mockDoorAddSources.mockRejectedValue(new Error("Already watched"));
      const onAdded = vi.fn();
      render(<AddSourcesWell projectId="proj_room_1" onAdded={onAdded} onCancel={() => undefined} />);
      await waitFor(() => expect(screen.getByTestId("door-trigger-github")).toBeTruthy());
      await act(async () => {
        fireEvent.click(screen.getByTestId("door-trigger-github"));
      });
      await act(async () => {
        fireEvent.click(await screen.findByTestId("door-pick-karolswdev/HoldSpeak"));
      });
      await act(async () => {
        fireEvent.click(screen.getByTestId("room-add-sources-add"));
      });
      await waitFor(() => expect(screen.getByRole("alert").textContent).toBe("Already watched"));
      expect(onAdded).not.toHaveBeenCalled();
    });

    it("adds the picked repository to the existing project", async () => {
      mockFetchConnections.mockResolvedValue(connectedTools());
      const onAdded = vi.fn();
      render(<AddSourcesWell projectId="proj_room_1" onAdded={onAdded} onCancel={() => undefined} />);
      await waitFor(() => expect(screen.getByTestId("door-trigger-github")).toBeTruthy());
      expect((screen.getByTestId("room-add-sources-add") as HTMLButtonElement).disabled).toBe(true);
      await act(async () => {
        fireEvent.click(screen.getByTestId("door-trigger-github"));
      });
      await act(async () => {
        fireEvent.click(await screen.findByTestId("door-pick-karolswdev/HoldSpeak"));
      });
      await act(async () => {
        fireEvent.click(screen.getByTestId("room-add-sources-add"));
      });
      await waitFor(() => expect(mockDoorAddSources).toHaveBeenCalled());
      const [projectId, payloads] = mockDoorAddSources.mock.calls[0];
      expect(projectId).toBe("proj_room_1");
      expect(payloads).toEqual([
        expect.objectContaining({ provider: "github", scope: "karolswdev/HoldSpeak", watches: ["open_prs", "ci"] }),
      ]);
      expect(mockDoorCreate).not.toHaveBeenCalled();
      await waitFor(() => expect(onAdded).toHaveBeenCalled());
    });
  });
});
