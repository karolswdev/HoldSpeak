// HS-174-02/03 — RemoteAccessModule unit tests.
// Counting rule, OFF hides everything, token appears once and not after
// re-render, Revoke removal.

import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor, act, cleanup } from "@testing-library/react";
import { RemoteAccessModule } from "../SettingsCore";

// Mock apiFetch
const mockApiFetch = vi.fn();
vi.mock("../../../lib/api", () => ({
  apiFetch: (...args: unknown[]) => mockApiFetch(...args),
  readableError: (err: unknown) => String(err),
}));

// Mock clipboard
const mockClipboard = { writeText: vi.fn().mockResolvedValue(undefined) };
Object.assign(navigator, { clipboard: mockClipboard });

const EPOCH_ACTIVE = Math.floor(Date.now() / 1000) + 86400; // tomorrow
const EPOCH_EXPIRED = Math.floor(Date.now() / 1000) - 86400; // yesterday
const EPOCH_LAST_USED = Math.floor(Date.now() / 1000) - 3600; // 1 hour ago

function makeRemoteWire(overrides: Record<string, unknown> = {}) {
  return {
    enabled: false,
    bind_host: null,
    port: null,
    credentials: [],
    active_count: 0,
    total_count: 0,
    ...overrides,
  };
}

function makeCred(id: string, overrides: Record<string, unknown> = {}) {
  return {
    id,
    identity: `cred-${id}`,
    palette: ["project"],
    expires_at: EPOCH_ACTIVE,
    last_used_at: null,
    active: true,
    ...overrides,
  };
}

describe("RemoteAccessModule", () => {
  beforeEach(() => {
    mockApiFetch.mockReset();
  });
  afterEach(() => {
    cleanup();
  });

  it("shows only the toggle row when OFF; no credentials, no Issue", async () => {
    mockApiFetch.mockResolvedValueOnce(makeRemoteWire({ enabled: false }));
    render(<RemoteAccessModule />);

    await waitFor(() => {
      expect(screen.getByText("Streamable HTTP")).toBeTruthy();
    });

    // CycleGadget select has OFF
    const select = screen.getByRole("combobox", { name: /remote transport/i });
    expect(select).toBeTruthy();
    expect((select as HTMLSelectElement).value).toBe("OFF");

    // No credentials ledger
    expect(screen.queryByText("CREDENTIALS")).toBeNull();

    // No Issue credential button
    expect(screen.queryByText("Issue credential")).toBeNull();
  });

  it("counting rule: N CREDENTIALS counts all (incl. expired), N ACTIVE counts non-expired only", async () => {
    const creds = [
      makeCred("a", { active: true }),
      makeCred("b", { active: false, expires_at: EPOCH_EXPIRED }),
      makeCred("c", { active: true }),
    ];
    mockApiFetch.mockResolvedValueOnce(
      makeRemoteWire({ enabled: true, bind_host: "100.64.0.2", port: 8765, credentials: creds, total_count: 3, active_count: 2 }),
    );
    render(<RemoteAccessModule />);

    await waitFor(() => {
      expect(screen.getByText("Streamable HTTP")).toBeTruthy();
    });

    // N CREDENTIALS on the toggle row: total count = 3
    const totalToken = screen.getByTestId("remote-total-count");
    expect(totalToken.textContent).toBe("3 CREDENTIALS");

    // N ACTIVE in the ledger head: 2 active
    const activeToken = screen.getByTestId("remote-active-count");
    expect(activeToken.textContent).toBe("2 ACTIVE");
  });

  it("token appears once after issue and is not re-rendered after refetch", async () => {
    // Initial load: ON with no credentials
    mockApiFetch.mockResolvedValueOnce(
      makeRemoteWire({ enabled: true, bind_host: "100.64.0.2", port: 8765 }),
    );
    render(<RemoteAccessModule />);

    await waitFor(() => {
      expect(screen.getByText("Issue credential")).toBeTruthy();
    });

    // Click Issue credential to open the well
    fireEvent.click(screen.getByText("Issue credential"));

    await waitFor(() => {
      expect(screen.getByPlaceholderText("e.g. sweep-runner")).toBeTruthy();
    });

    // Fill in the name
    const nameInput = screen.getByPlaceholderText("e.g. sweep-runner");
    fireEvent.change(nameInput, { target: { value: "test-runner" } });

    // Mock the POST to issue credential
    const issuedToken = "hs_agent_test1234567890abcdef";
    mockApiFetch.mockResolvedValueOnce({
      token: issuedToken,
      id: "new-cred-id",
      identity: "test-runner",
      palette: "PROJECT",
      expires_at: EPOCH_ACTIVE,
    });
    // Mock the refetch after issue
    const credsAfterIssue = [makeCred("new-cred-id", { identity: "test-runner" })];
    mockApiFetch.mockResolvedValueOnce(
      makeRemoteWire({ enabled: true, bind_host: "100.64.0.2", port: 8765, credentials: credsAfterIssue, total_count: 1, active_count: 1 }),
    );

    // Click Issue button
    fireEvent.click(screen.getByTestId("issue-submit"));

    // Wait for the one-time token to appear
    await waitFor(() => {
      expect(screen.getByTestId("token-value")).toBeTruthy();
    });

    expect(screen.getByTestId("token-value").textContent).toBe(issuedToken);
    expect(screen.getByText("TOKEN SHOWN ONCE — COPY IT NOW")).toBeTruthy();
    expect(screen.getByTestId("token-copy")).toBeTruthy();

    // Now clicking Issue credential again should dismiss the token
    fireEvent.click(screen.getByText("Issue credential"));

    // The token should be gone
    expect(screen.queryByTestId("token-value")).toBeNull();
  });

  it("Revoke removes the credential row", async () => {
    const creds = [
      makeCred("keep-id", { identity: "keeper" }),
      makeCred("revoke-id", { identity: "goner" }),
    ];
    mockApiFetch.mockResolvedValueOnce(
      makeRemoteWire({ enabled: true, bind_host: "100.64.0.2", port: 8765, credentials: creds, total_count: 2, active_count: 2 }),
    );
    render(<RemoteAccessModule />);

    await waitFor(() => {
      expect(screen.getByText("keeper")).toBeTruthy();
      expect(screen.getByText("goner")).toBeTruthy();
    });

    // Mock DELETE and refetch
    mockApiFetch.mockResolvedValueOnce({ success: true, revoked: "revoke-id" });
    const afterRevoke = [makeCred("keep-id", { identity: "keeper" })];
    mockApiFetch.mockResolvedValueOnce(
      makeRemoteWire({ enabled: true, bind_host: "100.64.0.2", port: 8765, credentials: afterRevoke, total_count: 1, active_count: 1 }),
    );

    // Find all Revoke buttons and click the second one (for "goner")
    const revokeButtons = screen.getAllByText("Revoke");
    expect(revokeButtons.length).toBe(2);
    fireEvent.click(revokeButtons[1]);

    // After revoke, "goner" should be gone
    await waitFor(() => {
      expect(screen.queryByText("goner")).toBeNull();
    });
    expect(screen.getByText("keeper")).toBeTruthy();
  });

  it("shows EXPIRED warning and NEVER USED for expired credentials", async () => {
    const creds = [
      makeCred("exp", { identity: "old-runner", expires_at: EPOCH_EXPIRED, active: false, last_used_at: null }),
    ];
    mockApiFetch.mockResolvedValueOnce(
      makeRemoteWire({ enabled: true, bind_host: "100.64.0.2", port: 8765, credentials: creds, total_count: 1, active_count: 0 }),
    );
    render(<RemoteAccessModule />);

    await waitFor(() => {
      expect(screen.getByText("old-runner")).toBeTruthy();
    });

    // EXPIRED warning chip visible
    expect(screen.getByText("EXPIRED")).toBeTruthy();

    // NEVER USED visible
    expect(screen.getByText("NEVER USED")).toBeTruthy();
  });

  it("shows address token when ON with bind_host and port", async () => {
    mockApiFetch.mockResolvedValueOnce(
      makeRemoteWire({ enabled: true, bind_host: "100.64.0.2", port: 8765 }),
    );
    render(<RemoteAccessModule />);

    await waitFor(() => {
      expect(screen.getByTestId("remote-address")).toBeTruthy();
    });

    expect(screen.getByTestId("remote-address").textContent).toBe("100.64.0.2:8765");
  });
});
