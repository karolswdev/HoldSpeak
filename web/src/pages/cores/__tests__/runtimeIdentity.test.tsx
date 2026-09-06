// HS-200-02 — the RuntimeIdentityModule face (contract C1).
// The compact repair chips, the identity tokens, the diagnostics fold,
// and the two rules the canon holds: no counter of zero, and the
// database path never appears outside the RAW fold.

import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, cleanup } from "@testing-library/react";
import { RuntimeIdentityModule } from "../SettingsCore";

const mockApiFetch = vi.fn();
vi.mock("../../../lib/api", () => ({
  apiFetch: (...args: unknown[]) => mockApiFetch(...args),
  readableError: (err: unknown) => String(err),
}));

// The build id is compiled into the bundle by Vite; the test drives it.
let documentBuild = "";
vi.mock("../../../lib/buildId", () => ({
  documentBuildId: () => documentBuild,
}));

function makeWire(overrides: Record<string, unknown> = {}) {
  return {
    identity: {
      backend_version: "0.4.0",
      backend_revision: "d066a862aaaaaaaa",
      backend_revision_source: "git",
      process_start: "2026-09-06T10:36:02",
      pid: 81866,
      frontend_build: "3228921edf301508",
      database_id: "0123456789abcdef",
      database_path: "/Users/tester/.local/share/holdspeak/holdspeak.db",
      schema_version_expected: 76,
      schema_version_loaded: 76,
      config_revision: "cafebabecafebabe",
    },
    repair: [],
    owns_database: true,
    diagnoses: [],
    ownership: { held: true, lock_path: "/tmp/x.owner.lock", owner: { pid: 81866 } },
    bundle_on_disk: "3228921edf301508",
    ...overrides,
  };
}

function setDocumentBuild(value: string | null) {
  documentBuild = value ?? "";
}

describe("RuntimeIdentityModule", () => {
  beforeEach(() => {
    mockApiFetch.mockReset();
    setDocumentBuild("3228921edf301508");
  });
  afterEach(() => {
    cleanup();
    setDocumentBuild(null);
  });

  it("reads the identity route once and shows every C1 token", async () => {
    mockApiFetch.mockResolvedValueOnce(makeWire());
    render(<RuntimeIdentityModule />);

    await waitFor(() => {
      expect(screen.getByTestId("runtime-backend")).toBeTruthy();
    });
    expect(mockApiFetch).toHaveBeenCalledWith("/api/system/identity");
    expect(screen.getByTestId("runtime-backend").textContent).toBe("0.4.0 · d066a862aaaa");
    expect(screen.getByTestId("runtime-bundle").textContent).toBe("3228921edf30");
    expect(screen.getByTestId("runtime-document").textContent).toBe("3228921edf30");
    expect(screen.getByTestId("runtime-schema").textContent).toBe("SCHEMA 76");
    expect(screen.getByTestId("runtime-database").textContent).toBe("01234567");
    expect(screen.getByTestId("runtime-owns").textContent).toBe("OWNER");
  });

  it("a healthy runtime flies no chip at all — never a counter of zero", async () => {
    mockApiFetch.mockResolvedValueOnce(makeWire());
    render(<RuntimeIdentityModule />);

    await waitFor(() => { expect(screen.getByTestId("runtime-backend")).toBeTruthy(); });
    expect(screen.queryByTestId("runtime-repair")).toBeNull();
    expect(screen.queryByText("0")).toBeNull();
  });

  it("shows the server's repair tokens as chips", async () => {
    mockApiFetch.mockResolvedValueOnce(
      makeWire({
        repair: ["STALE BUNDLE", "TWO RUNTIMES"],
        owns_database: false,
        diagnoses: [
          { id: "stale_bundle", token: "STALE BUNDLE", detail: "Restart the hub." },
          { id: "two_runtimes", token: "TWO RUNTIMES", detail: "Another hub owns this database." },
        ],
      }),
    );
    render(<RuntimeIdentityModule />);

    await waitFor(() => { expect(screen.getByTestId("runtime-repair")).toBeTruthy(); });
    const chips = screen.getByTestId("runtime-repair");
    expect(chips.textContent).toContain("STALE BUNDLE");
    expect(chips.textContent).toContain("TWO RUNTIMES");
    expect(screen.getByTestId("runtime-owns").textContent).toBe("TENANT");
  });

  it("the loaded document disagreeing with the process is its own STALE BUNDLE", async () => {
    setDocumentBuild("ffffffffffffffff");
    mockApiFetch.mockResolvedValueOnce(makeWire());
    render(<RuntimeIdentityModule />);

    await waitFor(() => { expect(screen.getByTestId("runtime-repair")).toBeTruthy(); });
    expect(screen.getByTestId("runtime-repair").textContent).toContain("STALE BUNDLE");
    expect(screen.getByTestId("runtime-document").textContent).toBe("ffffffffffff");
  });

  it("never lists the same token twice", async () => {
    setDocumentBuild("ffffffffffffffff");
    mockApiFetch.mockResolvedValueOnce(makeWire({ repair: ["STALE BUNDLE"] }));
    render(<RuntimeIdentityModule />);

    await waitFor(() => { expect(screen.getByTestId("runtime-repair")).toBeTruthy(); });
    const chips = screen.getByTestId("runtime-repair").querySelectorAll(".surface-state-chip");
    expect(chips.length).toBe(1);
  });

  it("an absent bundle stamp reads NONE, not an empty token", async () => {
    setDocumentBuild(null);
    mockApiFetch.mockResolvedValueOnce(
      makeWire({ identity: { ...makeWire().identity, frontend_build: "" }, repair: ["STALE BUNDLE"] }),
    );
    render(<RuntimeIdentityModule />);

    await waitFor(() => { expect(screen.getByTestId("runtime-bundle")).toBeTruthy(); });
    expect(screen.getByTestId("runtime-bundle").textContent).toBe("NONE");
    expect(screen.getByTestId("runtime-document").textContent).toBe("NONE");
  });

  it("the database path lives inside the RAW fold only", async () => {
    mockApiFetch.mockResolvedValueOnce(makeWire());
    const { container } = render(<RuntimeIdentityModule />);

    await waitFor(() => { expect(screen.getByTestId("runtime-backend")).toBeTruthy(); });
    const fold = container.querySelector("details, .gadget-fold");
    expect(fold).toBeTruthy();
    const path = screen.getByTestId("runtime-path");
    expect(fold!.contains(path)).toBe(true);
  });

  it("every verb is the library Button — no raw <button> outside it", async () => {
    mockApiFetch.mockResolvedValueOnce(makeWire());
    const { container } = render(<RuntimeIdentityModule />);

    await waitFor(() => { expect(screen.getByTestId("runtime-backend")).toBeTruthy(); });
    // The canon fence (tests/e2e/test_hs170_settings_hub_glass.py:142): a
    // library button carries .btn, .surface-ledger-line or .gadget-cycle.
    const raw = Array.from(container.querySelectorAll("button")).filter(
      (node) =>
        !node.classList.contains("btn") &&
        !node.classList.contains("surface-ledger-line") &&
        !node.classList.contains("gadget-cycle"),
    );
    expect(raw.map((n) => n.className)).toEqual([]);
    expect(container.querySelectorAll("button.btn").length).toBe(1);
  });

  it("an unreadable route states it and shows no invented identity", async () => {
    mockApiFetch.mockRejectedValueOnce(new Error("boom"));
    render(<RuntimeIdentityModule />);

    await waitFor(() => { expect(screen.getByText("UNREADABLE")).toBeTruthy(); });
    expect(screen.queryByTestId("runtime-backend")).toBeNull();
  });
});
