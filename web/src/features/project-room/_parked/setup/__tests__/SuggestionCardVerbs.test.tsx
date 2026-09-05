// PARKED (HS-170-02): retired by Phase 169; kept for reference, not built or scanned.
// HS-168-05 -- card verb tests: each card species carries one named verb.
// Connected+untested -> "Set up" primary, click calls onSelect.
// Connected+tested -> "Remove" ghost, click calls onDeselect.
// Disconnected -> "Connect" ghost, click calls onConnect (not onSelect).
// Native -> no "Set up", no "Connect", no "Remove".

import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { SetupProposal } from "../model";

/* ── Mock surface library ── */
vi.mock("../../../../desk/surface", () => ({
  ChoiceCardShell: ({
    children,
    label,
    onClick,
    onKeyDown,
    ...rest
  }: Record<string, unknown>) => (
    <div
      data-testid={rest["data-testid"] as string}
      onClick={onClick as () => void}
      onKeyDown={onKeyDown as () => void}
      role={rest.role as string}
      aria-selected={rest["aria-selected"] as boolean}
    >
      <span>{label as string}</span>
      {children as React.ReactNode}
    </div>
  ),
  Disclosure: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  EgressChip: () => null,
  StateChip: ({ label }: { label: string }) => <span data-testid="state-chip">{label}</span>,
  ProvenanceChip: ({ source }: { source: string }) => (
    <span className="surface-provenance-source">{source}</span>
  ),
  SurfaceSection: ({ label, children }: { label?: string; children: React.ReactNode }) => (
    <section data-testid={`surface-section-${label ?? ""}`}>{label ? <h3>{label}</h3> : null}{children}</section>
  ),
  useRovingRows: () => {},
}));

/* ── Mock Signal library ── */
vi.mock("../../../../components/signal/Signal", () => ({
  Button: ({
    children,
    onClick,
    variant,
    dense,
    ...rest
  }: Record<string, unknown>) => (
    <button
      data-testid={rest["data-testid"] as string}
      data-variant={variant as string}
      aria-label={rest["aria-label"] as string}
      onClick={onClick as () => void}
    >
      {children as React.ReactNode}
    </button>
  ),
}));

/* ── Mock connections ── */
vi.mock("../../../../pages/cores/connections", () => ({
  connectionChipLabel: (state: string, _provider: string) => {
    if (state === "connected") return "Connected";
    if (state === "not_configured") return "Not set up";
    return state;
  },
}));

vi.mock("../../../../pages/cores/connections/api", () => ({}));

import { SuggestionCards } from "../SuggestionCards";

/* ── Fixture helpers ── */

function makeProposal(overrides: Partial<SetupProposal> & { id: string; providerId: string }): SetupProposal {
  return {
    id: overrides.id,
    sessionId: "psetup_test",
    providerId: overrides.providerId,
    specSchema: "WatchSpec@1",
    spec: {
      schema: "WatchSpec@1",
      name: overrides.providerId === "github" ? "PR health" : overrides.providerId === "jira" ? "Issue tracker" : "Meeting notes",
      intent: "Watch",
      provider: { id: overrides.providerId, transport: "cli" },
      subject: { kind: "pull_requests", scope: {} },
      trigger: { kind: "poll", everyMinutes: 35 },
      rules: [],
      action: { schema: "WatchAction@1", kind: "project.observe" },
      mode: "yolo",
    },
    rationale: { fact: "test" },
    state: "proposed",
    testState: null,
    testResult: null,
    createdAt: "2026-09-01T10:00:00",
    updatedAt: "2026-09-01T10:00:00",
    connection: undefined,
    ...overrides,
  } as SetupProposal;
}

const CONNECTED_GH = makeProposal({
  id: "wprop_gh_01",
  providerId: "github",
  connection: { state: "connected", errorCode: null, errorDetail: null, display: { account: "user", recoveryHint: null } } as SetupProposal["connection"],
});

const TESTED_GH = makeProposal({
  id: "wprop_gh_02",
  providerId: "github",
  state: "selected",
  testState: "passed",
  testResult: { entityCount: 3, representativeEntities: [], observedAt: "2026-09-01", error: null, message: "Tested -- 3 matches" },
  connection: { state: "connected", errorCode: null, errorDetail: null, display: { account: "user", recoveryHint: null } } as SetupProposal["connection"],
});

const DISCONNECTED_GH = makeProposal({
  id: "wprop_gh_03",
  providerId: "github",
  connection: { state: "not_configured", errorCode: null, errorDetail: null, display: { account: null, recoveryHint: null } } as SetupProposal["connection"],
});

const NATIVE_MEETING = makeProposal({
  id: "wprop_mtg_01",
  providerId: "meeting",
});

/* ── Tests ── */

describe("SuggestionCard verbs (HS-168-05)", () => {
  const onSelect = vi.fn();
  const onDeselect = vi.fn();
  const onTest = vi.fn();
  const onConnect = vi.fn();

  function renderCards(proposals: SetupProposal[]) {
    return render(
      <SuggestionCards
        proposals={proposals}
        onSelect={onSelect}
        onDeselect={onDeselect}
        onTest={onTest}
        onConnect={onConnect}
        suggesting={false}
      />,
    );
  }

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("connected + untested: Set up primary present, click calls onSelect", () => {
    renderCards([CONNECTED_GH]);

    const setupBtn = screen.getByTestId("setup-card-setup-wprop_gh_01");
    expect(setupBtn).toBeInTheDocument();
    expect(setupBtn.getAttribute("data-variant")).toBe("primary");
    expect(setupBtn.getAttribute("aria-label")).toBe("Set up: PR health");

    fireEvent.click(setupBtn);
    expect(onSelect).toHaveBeenCalledWith("wprop_gh_01");
  });

  it("connected + untested: card body click calls onSelect", () => {
    renderCards([CONNECTED_GH]);

    const card = screen.getByTestId("setup-card-wprop_gh_01");
    fireEvent.click(card);
    expect(onSelect).toHaveBeenCalledWith("wprop_gh_01");
    expect(onDeselect).not.toHaveBeenCalled();
  });

  it("connected + tested: Remove ghost present, Set up absent", () => {
    renderCards([TESTED_GH]);

    const removeBtn = screen.getByTestId("setup-card-remove-wprop_gh_02");
    expect(removeBtn).toBeInTheDocument();
    expect(removeBtn.getAttribute("data-variant")).toBe("ghost");

    expect(screen.queryByTestId("setup-card-setup-wprop_gh_02")).not.toBeInTheDocument();

    fireEvent.click(removeBtn);
    expect(onDeselect).toHaveBeenCalledWith("wprop_gh_02");
  });

  it("connected + tested: card body click re-opens wizard (onSelect)", () => {
    renderCards([TESTED_GH]);

    const card = screen.getByTestId("setup-card-wprop_gh_02");
    fireEvent.click(card);
    expect(onSelect).toHaveBeenCalledWith("wprop_gh_02");
  });

  it("disconnected: Connect ghost present, click calls onConnect not onSelect", () => {
    renderCards([DISCONNECTED_GH]);

    const connectBtn = screen.getByTestId("setup-card-connect-wprop_gh_03");
    expect(connectBtn).toBeInTheDocument();
    expect(connectBtn.getAttribute("data-variant")).toBe("ghost");

    fireEvent.click(connectBtn);
    expect(onConnect).toHaveBeenCalledWith("wprop_gh_03");
    expect(onSelect).not.toHaveBeenCalled();
  });

  it("disconnected: card body click calls onConnect not onSelect", () => {
    renderCards([DISCONNECTED_GH]);

    const card = screen.getByTestId("setup-card-wprop_gh_03");
    fireEvent.click(card);
    expect(onConnect).toHaveBeenCalledWith("wprop_gh_03");
    expect(onSelect).not.toHaveBeenCalled();
  });

  it("native: no Set up, no Connect, no Remove", () => {
    renderCards([NATIVE_MEETING]);

    expect(screen.queryByTestId("setup-card-setup-wprop_mtg_01")).not.toBeInTheDocument();
    expect(screen.queryByTestId("setup-card-connect-wprop_mtg_01")).not.toBeInTheDocument();
    expect(screen.queryByTestId("setup-card-remove-wprop_mtg_01")).not.toBeInTheDocument();
  });

  it("native: body click toggles selection (onSelect when not selected)", () => {
    renderCards([NATIVE_MEETING]);

    const card = screen.getByTestId("setup-card-wprop_mtg_01");
    fireEvent.click(card);
    expect(onSelect).toHaveBeenCalledWith("wprop_mtg_01");
    expect(onConnect).not.toHaveBeenCalled();
  });

  it("SUGGESTIONS label shows count", () => {
    renderCards([CONNECTED_GH, NATIVE_MEETING]);

    const section = screen.getByTestId("surface-section-SUGGESTIONS 2");
    expect(section).toBeInTheDocument();
  });
});
