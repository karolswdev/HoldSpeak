// HS-174-02/03 — RemoteAccessModule unit tests.
// Counting rule, OFF hides everything, token appears once and not after
// re-render, Revoke removal.

import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor, act, cleanup, within } from "@testing-library/react";
import { RemoteAccessModule } from "../SettingsCore";

// Mock apiFetch
const mockApiFetch = vi.fn();
vi.mock("../../../lib/api", async (importOriginal) => ({
  ...await importOriginal<typeof import("../../../lib/api")>(),
  apiFetch: (...args: unknown[]) => mockApiFetch(...args),
}));

// Mock clipboard
const mockClipboard = { writeText: vi.fn().mockResolvedValue(undefined) };
Object.assign(navigator, { clipboard: mockClipboard });

const EPOCH_ACTIVE = Math.floor(Date.now() / 1000) + 86400; // tomorrow
const EPOCH_EXPIRED = Math.floor(Date.now() / 1000) - 86400; // yesterday
const EPOCH_LAST_USED = Math.floor(Date.now() / 1000) - 3600; // 1 hour ago

// The hub's own answers (tests/integration/test_remote_settings_wire.py, the
// test diet's SCAR LAW): the palette is the issued NAME, a string.
import REMOTE_OFF from "./wire/remote-settings.off.wire.json";
import REMOTE_ISSUED from "./wire/remote-settings.issued.wire.json";
import REMOTE_ONE from "./wire/remote-settings.one-credential.wire.json";
import PROJECTS from "../../../desk/__tests__/fixtures/settings-wire/grant-projects.json";

function makeRemoteWire(overrides: Record<string, unknown> = {}) {
  return { ...structuredClone(REMOTE_OFF.wire), ...overrides };
}

function makeCred(id: string, overrides: Record<string, unknown> = {}) {
  return {
    ...structuredClone(REMOTE_ONE.wire.credentials[0]),
    id,
    identity: `cred-${id}`,
    expires_at: EPOCH_ACTIVE,
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
    // replaces: tests/e2e/test_hs174_remote_settings_glass.py::TestSettingsRemoteAccess::test_remote_off_state (with settings.app.test.tsx)
    mockApiFetch.mockResolvedValueOnce(makeRemoteWire({ enabled: false }));
    render(<RemoteAccessModule />);

    await waitFor(() => {
      expect(screen.getByText("Other devices")).toBeTruthy();
      expect(screen.queryByText("Streamable HTTP")).toBeNull();
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
      expect(screen.getByText("Other devices")).toBeTruthy();
      expect(screen.queryByText("Streamable HTTP")).toBeNull();
    });

    // N CREDENTIALS on the toggle row: total count = 3
    const totalToken = screen.getByTestId("remote-total-count");
    expect(totalToken.textContent).toBe("3 CREDENTIALS");

    // N ACTIVE CREDENTIALS in the ledger head (PHILO-7-02, the ratified
    // caption "AGENTS · N ACTIVE CREDENTIALS"): 2 active
    const activeToken = screen.getByTestId("remote-active-count");
    expect(activeToken.textContent).toBe("2 ACTIVE CREDENTIALS");
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
      ...structuredClone(REMOTE_ISSUED.wire),
      token: issuedToken,
      id: "new-cred-id",
      identity: "test-runner",
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

    // Find all Revoke credential buttons (PHILO-7-02: the ratified verb) and
    // click the second one (for "goner")
    const revokeButtons = screen.getAllByText("Revoke credential");
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


function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: unknown) => void;
  const promise = new Promise<T>((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}

describe("Remote access recovery ownership", () => {
  beforeEach(() => mockApiFetch.mockReset());
  afterEach(cleanup);

  const knownRemote = () => makeRemoteWire({ enabled: true, bind_host: "100.64.0.2", port: 8765,
    credentials: [makeCred("keeper", { identity: "keeper" })], total_count: 1, active_count: 1 });

  it("a failed first remote GET retries only that exact read", async () => {
    mockApiFetch.mockRejectedValueOnce(new TypeError("Hub unavailable")).mockResolvedValueOnce(knownRemote());
    render(<RemoteAccessModule />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Could not read remote access");
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    expect(await screen.findByText("keeper")).toBeInTheDocument();
    expect(screen.queryByRole("alert")).toBeNull();
    expect(mockApiFetch.mock.calls).toEqual([["/api/settings/remote"], ["/api/settings/remote"]]);
  });

  it("a failed remote reread keeps the known ledger through Retry and ignores an older failed read", async () => {
    const older = deferred<unknown>();
    const retry = deferred<unknown>();
    mockApiFetch.mockResolvedValueOnce(knownRemote()).mockRejectedValueOnce(new Error("Offline"))
      .mockReturnValueOnce(retry.promise).mockReturnValueOnce(older.promise).mockResolvedValueOnce(knownRemote());
    const view = render(<RemoteAccessModule />);
    const row = await screen.findByTestId("credential-row-keeper");
    view.rerender(<RemoteAccessModule onEnabledChange={() => {}} />);
    const notice = await screen.findByTestId("remote-read-error");
    expect(screen.getByTestId("credential-row-keeper")).toBe(row);
    fireEvent.click(within(notice).getByRole("button", { name: "Retry" }));
    expect(screen.getByTestId("credential-row-keeper")).toBe(row);
    await act(async () => retry.resolve(knownRemote()));
    expect(screen.queryByRole("alert")).toBeNull();
    view.rerender(<RemoteAccessModule onEnabledChange={() => {}} />);
    view.rerender(<RemoteAccessModule onEnabledChange={() => {}} />);
    await waitFor(() => expect(mockApiFetch).toHaveBeenCalledTimes(5));
    await act(async () => older.reject(new Error("Late offline")));
    expect(screen.queryByRole("alert")).toBeNull();
    expect(screen.getByTestId("credential-row-keeper")).toBe(row);
  });

  it.each(["toggle", "issue", "revoke"])("a failed %s names its write and Reload never repeats the writer", async (kind) => {
    mockApiFetch.mockImplementation((path: string, init?: { method?: string }) => {
      if (!init?.method) return Promise.resolve(knownRemote());
      return Promise.reject(new TypeError("Connection lost"));
    });
    const view = render(<RemoteAccessModule />);
    await screen.findByText("keeper");
    let action: string;
    if (kind === "toggle") {
      action = "Turn remote access off";
      fireEvent.change(screen.getByRole("combobox", { name: "Remote transport" }), { target: { value: "OFF" } });
    } else if (kind === "issue") {
      action = "Issue credential · new-runner";
      fireEvent.click(screen.getByTestId("issue-credential-btn"));
      fireEvent.change(screen.getByRole("textbox", { name: "Credential name" }), { target: { value: "new-runner" } });
      fireEvent.click(screen.getByTestId("issue-submit"));
    } else {
      action = "Revoke credential · keeper";
      fireEvent.click(screen.getByTestId("credential-revoke"));
    }
    const notice = await screen.findByTestId("remote-error");
    expect(notice).toHaveTextContent(`Change not confirmed · ${action}`);
    expect(within(notice).queryByRole("button", { name: "Retry" })).toBeNull();
    fireEvent.click(within(notice).getByRole("button", { name: "Reload current state" }));
    await waitFor(() => expect(mockApiFetch.mock.calls.filter(([, init]) => !init?.method)).toHaveLength(2));
    view.rerender(<RemoteAccessModule onEnabledChange={() => {}} />);
    await waitFor(() => expect(mockApiFetch.mock.calls.filter(([, init]) => !init?.method)).toHaveLength(3));
    expect(screen.getByTestId("remote-error")).toHaveTextContent(action);
    expect(mockApiFetch.mock.calls.filter(([, init]) => init?.method)).toHaveLength(1);
    expect(screen.getByRole("combobox", { name: "Remote transport" })).toHaveValue("ON");
  });

  it("Reload keeps unsaved Issue name, access, expiry and the expanded credential through read failure and recovery", async () => {
    let remoteReads = 0;
    mockApiFetch.mockImplementation((path: string, init?: { method?: string }) => {
      if (path === "/api/projects") return Promise.resolve(PROJECTS);
      if (init?.method === "POST") return Promise.reject(new TypeError("Issue response unavailable"));
      if (++remoteReads === 2) return Promise.reject(new TypeError("Read unavailable"));
      return Promise.resolve(knownRemote());
    });
    render(<RemoteAccessModule />);
    const row = await screen.findByTestId("credential-row-keeper");
    fireEvent.click(screen.getByRole("button", { name: "Projects: keeper" }));
    await screen.findByTestId(`project-line-${PROJECTS.projects[0].id}`);
    fireEvent.click(screen.getByTestId("issue-credential-btn"));
    fireEvent.change(screen.getByRole("textbox", { name: "Credential name" }), { target: { value: "new-runner" } });
    fireEvent.change(screen.getByRole("combobox", { name: "Access" }), { target: { value: "DESK" } });
    fireEvent.change(screen.getByRole("combobox", { name: "Expires after" }), { target: { value: "604800" } });
    fireEvent.click(screen.getByTestId("issue-submit"));
    fireEvent.click(within(await screen.findByTestId("remote-error")).getByRole("button", { name: "Reload current state" }));
    const readFailure = await screen.findByTestId("remote-read-error");
    expect(screen.getByTestId("remote-error")).toHaveTextContent("Issue credential · new-runner");
    fireEvent.click(within(readFailure).getByRole("button", { name: "Retry" }));
    await waitFor(() => expect(screen.queryByTestId("remote-read-error")).toBeNull());
    expect(screen.getByTestId("remote-error")).toHaveTextContent("Issue credential · new-runner");
    expect(screen.getByRole("textbox", { name: "Credential name" })).toHaveValue("new-runner");
    expect(screen.getByRole("combobox", { name: "Access" })).toHaveValue("DESK");
    expect(screen.getByRole("combobox", { name: "Expires after" })).toHaveValue("604800");
    expect(screen.getByRole("button", { name: "Projects: keeper" })).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByTestId("credential-row-keeper")).toBe(row);
    expect(mockApiFetch.mock.calls.filter(([, init]) => init?.method === "POST")).toHaveLength(1);
  });

  it.each(["desk", "project"])("the automatic %s grant reread retains the original transport failure and subject", async (kind) => {
    const wire = { ...knownRemote(), credentials: [makeCred("keeper", { identity: "keeper", palette: kind === "desk" ? "DESK" : "PROJECT" })] };
    mockApiFetch.mockImplementation((path: string, init?: { method?: string }) => {
      if (path === "/api/projects") return Promise.resolve(PROJECTS);
      if (init?.method) return Promise.reject(new TypeError("Grant response unavailable"));
      return Promise.resolve(wire);
    });
    render(<RemoteAccessModule />);
    await screen.findByText("keeper");
    if (kind === "project") {
      fireEvent.click(screen.getByRole("button", { name: "Projects: keeper" }));
      await screen.findByTestId(`project-line-${PROJECTS.projects[0].id}`);
      fireEvent.click(within(screen.getByTestId(`project-line-${PROJECTS.projects[0].id}`)).getByRole("button", { name: "Allow run and publish" }));
    } else fireEvent.click(screen.getByRole("button", { name: "Allow filing" }));
    await waitFor(() => expect(mockApiFetch.mock.calls.filter(([path]) => path === "/api/settings/remote")).toHaveLength(2));
    const notice = screen.getByTestId("remote-error");
    expect(notice).toHaveTextContent(kind === "desk" ? "Allow filing · keeper" : `Allow run and publish · keeper · ${PROJECTS.projects[0].name}`);
    fireEvent.click(within(notice).getByRole("button", { name: "Reload current state" }));
    await waitFor(() => expect(mockApiFetch.mock.calls.filter(([path]) => path === "/api/settings/remote")).toHaveLength(3));
    expect(screen.getByTestId("remote-error")).toHaveTextContent("Grant response unavailable");
    expect(mockApiFetch.mock.calls.filter(([, init]) => init?.method)).toHaveLength(1);
  });

  it("an older writer failure cannot replace a later explicit issue outcome or its one-time token", async () => {
    const revoke = deferred<unknown>();
    let issued = false;
    mockApiFetch.mockImplementation((_path: string, init?: { method?: string }) => {
      if (init?.method === "DELETE") return revoke.promise;
      if (init?.method === "POST") {
        issued = true;
        return Promise.resolve({ ...REMOTE_ISSUED.wire, identity: "new-runner" });
      }
      return Promise.resolve({ ...knownRemote(), credentials: [makeCred("keeper", { identity: "keeper" }),
        ...(issued ? [makeCred(REMOTE_ISSUED.wire.id, { identity: "new-runner" })] : [])] });
    });
    const view = render(<RemoteAccessModule />);
    await screen.findByText("keeper");
    fireEvent.click(screen.getByTestId("credential-revoke"));
    fireEvent.click(screen.getByTestId("issue-credential-btn"));
    fireEvent.change(screen.getByRole("textbox", { name: "Credential name" }), { target: { value: "new-runner" } });
    fireEvent.click(screen.getByTestId("issue-submit"));
    expect(await screen.findByTestId("token-value")).toHaveTextContent(REMOTE_ISSUED.wire.token);
    await act(async () => revoke.reject(new Error("Older revoke response unavailable")));
    view.rerender(<RemoteAccessModule onEnabledChange={() => {}} />);
    await waitFor(() => expect(mockApiFetch.mock.calls.filter(([, init]) => !init?.method)).toHaveLength(3));
    expect(screen.queryByTestId("remote-error")).toBeNull();
    expect(screen.getByTestId("token-value")).toHaveTextContent(REMOTE_ISSUED.wire.token);
    expect(mockApiFetch.mock.calls.filter(([, init]) => init?.method === "DELETE")).toHaveLength(1);
    expect(mockApiFetch.mock.calls.filter(([, init]) => init?.method === "POST")).toHaveLength(1);
  });

  it("failed project choices Retry rereads Projects, preserves known choices and never replays a grant", async () => {
    let projectReads = 0;
    mockApiFetch.mockImplementation((path: string) => {
      if (path === "/api/projects") return ++projectReads === 2 ? Promise.reject(new Error("Projects unavailable")) : Promise.resolve(PROJECTS);
      return Promise.resolve(knownRemote());
    });
    render(<RemoteAccessModule />);
    await screen.findByText("keeper");
    const open = () => fireEvent.click(screen.getByRole("button", { name: "Projects: keeper" }));
    open();
    await screen.findByTestId(`project-line-${PROJECTS.projects[0].id}`);
    open(); open();
    const failure = await screen.findByTestId("remote-projects-error");
    expect(screen.getByTestId(`project-line-${PROJECTS.projects[0].id}`)).toBeInTheDocument();
    fireEvent.click(within(failure).getByRole("button", { name: "Retry" }));
    await waitFor(() => expect(screen.queryByTestId("remote-projects-error")).toBeNull());
    expect(projectReads).toBe(3);
    expect(mockApiFetch.mock.calls.filter(([path]) => path === "/api/settings/remote")).toHaveLength(1);
    expect(mockApiFetch.mock.calls.every(([, init]) => !init?.method)).toBe(true);
  });
});
