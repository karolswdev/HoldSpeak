// HS-168-03 — ConnectionsPane vitest: states, verbs, deep links, labels.
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ConnectionsPane, type ConnectionsFoot } from "../connections";
import type { ConnectionsResponse, ConnectionTool } from "../connections/api";
import { decodeConnectionsResponse, decodeState } from "../connections/api";
import { checkedAgo, checkedWords, stateWords } from "../connections/ConnectionsPane";
// The hub's own /api/connections on a fresh HOME (scripts/record_needs_you_fixture.py,
// the "grouped" boot): the test diet's SCAR LAW, no typed state.
import RECORDED from "../../../desk/__tests__/fixtures/needsYou.recorded.json";
import CALENDAR_WIRE from "../../../test/wire/onboarding-calendar.wire.json";
import CALENDAR_USE_WIRE from "../../../test/wire/onboarding-calendar.use.wire.json";
import CALENDAR_CHECK_WIRE from "../../../test/wire/onboarding-calendar.check.wire.json";
/* Betterment ST2: Accounts that say Works. The doubles are the hub's OWN
   answers, recorded by tests/integration/test_desk_connections.py
   (test_the_st2_wire_fixtures_are_the_hubs_own): two Jira sites checked, a
   third only in acli's file, its Use, and a Remove. */
import ST2_CONNECTIONS from "../../../desk/__tests__/fixtures/connections-wire/st2-connections.json";
import ST2_FOUND from "../../../desk/__tests__/fixtures/connections-wire/st2-found.json";
import ST2_USE from "../../../desk/__tests__/fixtures/connections-wire/st2-use.json";
import ST2_AFTER_USE from "../../../desk/__tests__/fixtures/connections-wire/st2-connections-after-use.json";
import ST2_FOUND_AFTER_USE from "../../../desk/__tests__/fixtures/connections-wire/st2-found-after-use.json";
import ST2_REMOVE from "../../../desk/__tests__/fixtures/connections-wire/st2-remove.json";

const RECORDED_CONNECTIONS = RECORDED.grouped.gets["/api/connections"] as unknown as ConnectionsResponse;
/** Window grammar 2026-10-27: a row's state is a dot + word, then the quiet
 *  age of its own check; read as one line, "Works · checked 5 minutes ago". */
function rowWords(el: HTMLElement): string {
  const cell = el.querySelector(".connections-row-state");
  expect(cell, "no row state").not.toBeNull();
  const word = cell!.querySelector(".connections-state")?.textContent ?? "";
  const when = cell!.querySelector(".connections-checked")?.textContent ?? "";
  return when ? `${word} · ${when}` : word;
}

function recordedTool(id: string): ConnectionTool {
  const tool = RECORDED_CONNECTIONS.tools.find((t) => t.provider_id === id);
  if (!tool) throw new Error(`the recorded hub sent no ${id} row`);
  return structuredClone(tool);
}

/* ── Mock the API module ── */
vi.mock("../connections/api", async (importOriginal) => {
  const original = await importOriginal<typeof import("../connections/api")>();
  return {
    ...original,
    fetchConnections: vi.fn(),
    recheckProvider: vi.fn(),
  };
});

vi.mock("../../../lib/api", async (importOriginal) => ({
  ApiError: (await importOriginal<typeof import("../../../lib/api")>()).ApiError,
  apiFetch: vi.fn(),
  readableError: (e: unknown) => String(e),
}));

import { ACCOUNTS_CHANGED, fetchConnections, recheckProvider } from "../connections/api";
import { apiFetch } from "../../../lib/api";

const mockFetchConnections = vi.mocked(fetchConnections);
const mockRecheckProvider = vi.mocked(recheckProvider);

/* ── Fixtures ── */

function connectedGithub(): ConnectionTool {
  return {
    provider_id: "github",
    state: "connected",
    account: { login: "karolswdev" },
    next_action: { kind: "recheck", label: "Recheck" },
    recovery_hint: "gh auth login",
    last_checked_at: "2026-09-04T13:28:04Z",
    egress_host: "github.com",
  };
}

function signInGithub(): ConnectionTool {
  return {
    provider_id: "github",
    state: "owner_action_required",
    account: {},
    next_action: { kind: "sign_in", label: "Sign in" },
    recovery_hint: "gh auth login",
    last_checked_at: undefined,
    egress_host: "github.com",
  };
}

function unavailableGithub(): ConnectionTool {
  return {
    provider_id: "github",
    state: "unavailable",
    account: {},
    next_action: { kind: "install", label: "Install" },
    recovery_hint: "brew install gh",
    last_checked_at: undefined,
    egress_host: "github.com",
  };
}

function degradedGithub(): ConnectionTool {
  return {
    provider_id: "github",
    state: "degraded",
    account: {},
    error_detail: "Connection timed out",
    reason: "gh did not answer",
    last_checked_at: "2026-09-04T13:00:00Z",
    egress_host: "github.com",
  };
}

/** GitHub before any check: the hub's own row on a fresh HOME. The hub sends
 *  `not_configured` only when it has no GitHub service, which a real hub
 *  always has (connections_service.py `_not_configured_entry`). */
function neverCheckedGithub(): ConnectionTool {
  return recordedTool("github");
}

function connectedJira(): ConnectionTool {
  return {
    provider_id: "jira",
    state: "connected",
    account: { site: "alpha.atlassian.net", email: "user@example.com" },
    last_checked_at: "2026-09-04T13:28:04Z",
    egress_host: "alpha.atlassian.net",
    connections: [
      {
        connection_ref: "alpha-user",
        state: "connected",
        account: { site: "alpha.atlassian.net", email: "user@example.com" },
        egress_host: "alpha.atlassian.net",
      },
    ],
  };
}

function twoJiraConnections(): ConnectionTool {
  return {
    provider_id: "jira",
    state: "connected",
    account: { site: "alpha.atlassian.net", email: "user@example.com" },
    last_checked_at: "2026-09-04T13:28:04Z",
    egress_host: "alpha.atlassian.net",
    connections: [
      {
        connection_ref: "alpha-user",
        state: "connected",
        account: { site: "alpha.atlassian.net", email: "user@example.com" },
        egress_host: "alpha.atlassian.net",
      },
      {
        connection_ref: "beta-admin",
        state: "owner_action_required",
        account: { site: "beta.atlassian.net", email: "admin@example.com" },
        recovery_hint: "acli jira auth login --site beta.atlassian.net --email admin@example.com --token",
        egress_host: "beta.atlassian.net",
      },
    ],
  };
}

/** Jira with no account: the hub sends `never_checked` (acli on PATH) or
 *  `unavailable` (acli missing), never `not_configured`. */
function emptyJira(): ConnectionTool {
  return recordedTool("jira");
}

function connectedCalendar(): ConnectionTool {
  return {
    provider_id: "calendar",
    state: "connected",
    account: { sources: 2 },
  };
}

function connectedModels(): ConnectionTool {
  return {
    provider_id: "models",
    state: "connected",
    account: { assigned: 5, total: 7 },
  };
}

function fullResponse(): ConnectionsResponse {
  return {
    tools: [connectedGithub(), connectedJira(), connectedCalendar(), connectedModels()],
  };
}

/* ── Render helper ── */

function renderPane(
  response: ConnectionsResponse = fullResponse(),
  opts?: { onOpen?: (id: string) => void; onFooter?: (foot: ConnectionsFoot) => void },
) {
  mockFetchConnections.mockResolvedValue(response);
  const onFooter = opts?.onFooter ?? vi.fn();
  const onOpen = opts?.onOpen ?? vi.fn();
  return {
    ...render(
      <ConnectionsPane onFooterUpdate={onFooter} onOpenModule={onOpen} />,
    ),
    onFooter,
    onOpen,
  };
}

/* ── Tests ── */

beforeEach(() => {
  vi.clearAllMocks();
});

describe("ConnectionsPane", () => {
  /* ── GitHub states ── */

  // replaces (the face half): tests/e2e/test_hs168_connections_glass.py::test_connections_real_readiness
  describe("GitHub connected", () => {
    it("shows Works chip, login and host, and the Check verb", async () => {
      renderPane();
      const card = (await screen.findByTestId("connections-github")).closest("li")!;
      expect(within(card).getByText("GitHub")).toBeInTheDocument();
      expect(within(card).getByText("karolswdev")).toBeInTheDocument();
      // PHILO-9-02 B1: the row carries its own check age.
      expect(rowWords(card)).toMatch(/^Works · checked /);
      expect(within(card).getByText("github.com")).toBeInTheDocument();
      expect(within(card).getByText("Check")).toBeInTheDocument();
    });
  });

  describe("GitHub owner_action_required", () => {
    it("shows Not signed in with an explicit sign-in command well", async () => {
      const response: ConnectionsResponse = {
        tools: [signInGithub(), emptyJira(), connectedCalendar(), connectedModels()],
      };
      renderPane(response);
      const card = (await screen.findByTestId("connections-github")).closest("li")!;
      // PHILO-17 U29: the cause in plain words.
      expect(within(card).getByText("Not signed in")).toBeInTheDocument();
      expect(within(card).queryByText("gh auth login")).toBeNull();
      fireEvent.click(within(card).getByRole("button", { name: "Sign in" }));
      expect(within(card).getByText("gh auth login")).toBeInTheDocument();
      expect(within(card).getByRole("button", { name: "Copy" })).toBeInTheDocument();
      expect(within(card).getByRole("button", { name: "Check" })).toBeInTheDocument();
    });
  });

  describe("GitHub unavailable", () => {
    it("says Could not check: gh is not installed, and Install gh shows the command", async () => {
      const response: ConnectionsResponse = {
        tools: [unavailableGithub(), emptyJira(), connectedCalendar(), connectedModels()],
      };
      renderPane(response);
      const card = (await screen.findByTestId("connections-github")).closest("li")!;
      expect(within(card).getByText(/^Could not check: gh is not installed/)).toBeInTheDocument();
      expect(within(card).queryByText("brew install gh")).toBeNull();
      fireEvent.click(within(card).getByRole("button", { name: "Install gh" }));
      expect(within(card).getByText("brew install gh")).toBeInTheDocument();
    });
  });

  describe("GitHub degraded", () => {
    it("says Could not check with the hub's reason, never Unreachable", async () => {
      const response: ConnectionsResponse = {
        tools: [degradedGithub(), emptyJira(), connectedCalendar(), connectedModels()],
      };
      renderPane(response);
      const card = (await screen.findByTestId("connections-github")).closest("li")!;
      // PHILO-9-02 B1: the row carries its own check age.
      expect(rowWords(card)).toMatch(/^Could not check: gh did not answer · checked /);
      expect(within(card).queryByText(/Unreachable/)).toBeNull();
      expect(within(card).getByText("Check")).toBeInTheDocument();
      expect(within(card).queryByText("gh auth login")).toBeNull();
    });
  });

  describe("GitHub never checked", () => {
    it("shows Not checked and the Check verb", async () => {
      const response: ConnectionsResponse = {
        tools: [neverCheckedGithub(), emptyJira(), connectedCalendar(), connectedModels()],
      };
      renderPane(response);
      const card = (await screen.findByTestId("connections-github")).closest("li")!;
      expect(within(card).getByText("Not checked")).toBeInTheDocument();
      expect(within(card).getByText("Check")).toBeInTheDocument();
    });
  });

  /* ── Jira ── */

  describe("Jira with 0 connections", () => {
    it("shows the tool's own state with Add account ghost card", async () => {
      const response: ConnectionsResponse = {
        tools: [connectedGithub(), emptyJira(), connectedCalendar(), connectedModels()],
      };
      renderPane(response);
      const card = (await screen.findByTestId("connections-jira")).closest("li")!;
      expect(within(card).getByText("Jira")).toBeInTheDocument();
      // PHILO-9-02 B1: the empty card says the tool's own state; the hub's
      // empty Jira is `never_checked` (the old typed `not_configured` row
      // read "Not set up", a state the hub never sends for it).
      expect(within(card).getByText("Not checked")).toBeInTheDocument();
      // PHILO-17 REFIT: Add account unfolds the Site and Email inputs.
      fireEvent.click(within(card).getByTestId("connections-add-open-jira"));
      // Ghost card has Site and Email inputs
      expect(within(card).getByLabelText("Site")).toBeInTheDocument();
      expect(within(card).getByLabelText("Email")).toBeInTheDocument();
      expect(within(card).getByText("Add")).toBeInTheDocument();
    });
  });

  describe("Jira with 1 connection", () => {
    it("shows the connection row with site and email", async () => {
      renderPane();
      const conn = await screen.findByTestId("connections-jira-conn-alpha-user");
      expect(within(conn).getByText("Jira")).toBeInTheDocument();
      expect(within(conn).getByText("user@example.com")).toBeInTheDocument();
      expect(within(conn).getByText("alpha.atlassian.net")).toBeInTheDocument();
      const chips = within(conn).getAllByText("Works");
      expect(chips.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe("Jira host (PHILO-4-01 r4; window grammar 2026-10-25)", () => {
    it("names the provider and the full host as quiet text next to the account, not a chip", async () => {
      renderPane();
      const conn = await screen.findByTestId("connections-jira-conn-alpha-user");
      const host = within(conn).getByText("alpha.atlassian.net");
      expect(host.classList.contains("connections-site")).toBe(true);
      expect(conn.querySelector(".gadget-chip-egress")).toBeNull();
      // The verb's hover title says where the check goes.
      expect(within(conn).getByRole("button", { name: "Check" }).getAttribute("title")).toBe("Checks alpha.atlassian.net");
      expect(conn.querySelector(".connections-tool-label")?.textContent).toBe("Jira");
      expect(conn.querySelector('.connections-tool-emblem[data-provider="jira"]')?.textContent).toBe("J");
    });
  });

  describe("Jira with 2 connections", () => {
    it("shows both connection rows", async () => {
      const response: ConnectionsResponse = {
        tools: [connectedGithub(), twoJiraConnections(), connectedCalendar(), connectedModels()],
      };
      renderPane(response);
      const alpha = await screen.findByTestId("connections-jira-conn-alpha-user");
      expect(within(alpha).getByText("Works")).toBeInTheDocument();
      const beta = await screen.findByTestId("connections-jira-conn-beta-admin");
      expect(within(beta).getByText("Not signed in")).toBeInTheDocument();
    });
  });

  /* ── Calendar + Models link cards ── */

  describe("Calendar card", () => {
    it("shows Connected with sources summary; Choose calendar is its verb (Betterment setup ST1: no Sources verb to Meetings)", async () => {
      const onOpen = vi.fn();
      renderPane(fullResponse(), { onOpen });
      const card = await screen.findByTestId("connections-calendar");
      expect(within(card).getByText("Calendar")).toBeInTheDocument();
      expect(within(card).getByText("2 sources")).toBeInTheDocument();
      expect(within(card).getByText("Connected")).toBeInTheDocument();
      expect(within(card).queryByText("Sources")).toBeNull();
      expect(within(card).getByRole("button", { name: "Choose calendar" })).toBeInTheDocument();
      expect(onOpen).not.toHaveBeenCalled();
    });
  });

  // Betterment setup ST1: Accounts no longer shows `Runs on N of 7 assigned`;
  // Engines is its one home (the card is parked in _parked/ConnectionsModelsCard.tsx).
  describe("no engine row in Accounts", () => {
    it("draws no Models card", async () => {
      renderPane();
      await screen.findByTestId("connections-calendar");
      expect(screen.queryByTestId("connections-models")).toBeNull();
      expect(screen.queryByText(/of 7 assigned/)).toBeNull();
    });
  });

  /* ── Recheck ── */

  describe("Recheck", () => {
    it("sends the selected account through the existing ref wire key", async () => {
      vi.mocked(apiFetch).mockResolvedValue(connectedJira());
      const actual = await vi.importActual<typeof import("../connections/api")>("../connections/api");
      await actual.recheckProvider("jira", "beta-admin");
      expect(apiFetch).toHaveBeenCalledWith("/api/connections/jira/recheck", {
        method: "POST", json: { ref: "beta-admin" },
      });
    });

    it("retries the selected account and lets one action own pending", async () => {
      let reject!: (cause: Error) => void;
      mockRecheckProvider.mockReturnValueOnce(new Promise((_resolve, no) => { reject = no; }));
      renderPane({ tools: [connectedGithub(), twoJiraConnections()] });
      const alpha = await screen.findByTestId("connections-jira-conn-alpha-user");
      const beta = screen.getByTestId("connections-jira-conn-beta-admin").closest("li")!;
      fireEvent.click(within(beta).getByRole("button", { name: "Sign in" }));
      fireEvent.click(within(beta).getByRole("button", { name: "Check" }));
      expect(mockRecheckProvider).toHaveBeenCalledWith("jira", "beta-admin");
      expect(within(alpha).getByRole("button", { name: "Check" })).toBeDisabled();
      fireEvent.click(within(alpha).getByRole("button", { name: "Check" }));
      expect(mockRecheckProvider).toHaveBeenCalledTimes(1);
      await act(async () => reject(new Error("offline")));
      mockRecheckProvider.mockResolvedValueOnce(twoJiraConnections());
      fireEvent.click(within(screen.getByRole("alert")).getByRole("button", { name: "Check" }));
      await waitFor(() => expect(mockRecheckProvider).toHaveBeenCalledTimes(2));
      expect(mockRecheckProvider).toHaveBeenLastCalledWith("jira", "beta-admin");
    });

    it("calls recheckProvider and updates the footer", async () => {
      const updated = connectedGithub();
      updated.last_checked_at = "2026-09-04T14:00:00Z";
      const response = fullResponse();
      mockRecheckProvider.mockImplementation(async (provider) => {
        response.tools = response.tools.map((tool) => tool.provider_id === provider ? updated : tool);
        return updated;
      });
      const onFooter = vi.fn();
      renderPane(response, { onFooter });

      const card = (await screen.findByTestId("connections-github")).closest("li")!;
      fireEvent.click(within(card).getByText("Check"));

      await waitFor(() => {
        expect(mockRecheckProvider).toHaveBeenCalledWith("github");
      });
      await waitFor(() => {
        expect(onFooter).toHaveBeenCalled();
        const lastCall = onFooter.mock.calls[onFooter.mock.calls.length - 1][0] as ConnectionsFoot;
        expect(lastCall.egressHost).toBe("github.com");
        expect(lastCall.checkedAt).toBeTruthy();
      });
      expect(mockFetchConnections.mock.calls.length).toBeGreaterThan(1);
    });
  });

  /* ── Footer receipt ── */

  describe("Footer", () => {
    it.each(["response", "failure"])("ignores a stale account read %s after the latest rows and footer arrive", async (outcome) => {
      let finish!: (response: ConnectionsResponse) => void;
      let fail!: (cause: Error) => void;
      mockFetchConnections.mockReturnValueOnce(new Promise((yes, no) => { finish = yes; fail = no; }));
      const latest = fullResponse();
      latest.tools[0] = { ...connectedGithub(), account: { login: "latest-owner" }, last_checked_at: "2026-09-04T18:00:00Z" };
      mockFetchConnections.mockResolvedValueOnce(latest);
      const onFooter = vi.fn();
      render(<ConnectionsPane onFooterUpdate={onFooter} onOpenModule={vi.fn()}/>);
      act(() => window.dispatchEvent(new Event(ACCOUNTS_CHANGED)));
      expect(await screen.findByText("latest-owner")).toBeInTheDocument();
      await act(async () => {
        if (outcome === "response") finish(fullResponse());
        else fail(new Error("old read failed"));
      });
      expect(screen.getByText("latest-owner")).toBeInTheDocument();
      expect(screen.queryByRole("alert")).toBeNull();
      expect(onFooter).toHaveBeenCalledTimes(1);
      expect(onFooter).toHaveBeenLastCalledWith(expect.objectContaining({ egressHost: "github.com" }));
    });

    it("reports egressHost and checkedAt on load", async () => {
      const onFooter = vi.fn();
      // Give GitHub a later timestamp so it is the last checked host.
      const response = fullResponse();
      response.tools[0].last_checked_at = "2026-09-04T14:00:00Z";
      renderPane(response, { onFooter });
      await waitFor(() => {
        expect(onFooter).toHaveBeenCalled();
        const call = onFooter.mock.calls[onFooter.mock.calls.length - 1][0] as ConnectionsFoot;
        expect(call.egressHost).toBe("github.com");
        expect(call.checkedAt).toBeTruthy();
      });
    });

    it("reports undefined when nothing checked", async () => {
      const onFooter = vi.fn();
      const response: ConnectionsResponse = structuredClone(RECORDED_CONNECTIONS);
      renderPane(response, { onFooter });
      await waitFor(() => {
        expect(onFooter).toHaveBeenCalled();
        const call = onFooter.mock.calls[0][0] as ConnectionsFoot;
        expect(call.egressHost).toBeUndefined();
        expect(call.checkedAt).toBeUndefined();
      });
    });
  });

  /* ── Labels ── */

  describe("Labels", () => {
    it("the integrations tile is labeled Accounts in the roster", async () => {
      const { PREF_MODULES } = await import("../settingsPrefs");
      const tile = PREF_MODULES.find((m) => m.id === "integrations");
      expect(tile?.label).toBe("Accounts");
    });

    it("the applications entry is labeled Accounts", async () => {
      const { DESK_APPLICATIONS } = await import("../../../desk/applications");
      const entry = DESK_APPLICATIONS.find(
        (a: { action: string }) => a.action === "configure-integrations",
      );
      expect((entry as { label: string }).label).toBe("Accounts");
    });
  });

  /* ── Deep link ── */

  describe("Deep link", () => {
    it("openSurfaceWindow configure-settings integrations still lands on the tile", async () => {
      // The id stays "integrations" — no deep link breaks.
      const { PREF_MODULES } = await import("../settingsPrefs");
      const ids = PREF_MODULES.map((m) => m.id);
      expect(ids).toContain("integrations");
    });
  });

  /* ── PHILO-9-02 B1: each row's own age, and never checked ── */

  describe("B1 the connection read contract", () => {
    it("decodes never_checked as its own state", () => {
      expect(decodeState("never_checked")).toBe("never_checked");
      expect(decodeState("bogus")).toBe("not_configured");
    });

    it("decodes each row's own check time and age", () => {
      const decoded = decodeConnectionsResponse({
        tools: [{
          provider_id: "jira",
          state: "connected",
          last_checked_at: "2026-09-28T10:05:00+00:00",
          checked_age_seconds: 60,
          connections: [
            {
              connection_ref: "a|a@x.com", state: "connected",
              account: { site: "a.atlassian.net", email: "a@x.com" },
              last_checked_at: "2026-09-28T10:00:00+00:00", checked_age_seconds: 360,
            },
            {
              connection_ref: "b|b@x.com", state: "never_checked",
              account: { site: "b.atlassian.net", email: "b@x.com" },
              last_checked_at: null, checked_age_seconds: null,
            },
          ],
        }],
      });
      const [a, b] = decoded.tools[0].connections ?? [];
      expect(decoded.tools[0].checked_age_seconds).toBe(60);
      expect(a.last_checked_at).toBe("2026-09-28T10:00:00+00:00");
      expect(a.checked_age_seconds).toBe(360);
      expect(b.state).toBe("never_checked");
      expect(b.last_checked_at).toBeUndefined();
    });

    it("words the age of one stored check", () => {
      const now = Date.parse("2026-09-28T12:00:00Z");
      expect(checkedAgo("2026-09-28T11:59:30Z", undefined, now)).toBe("Checked now");
      expect(checkedAgo("2026-09-28T11:55:00Z", undefined, now)).toBe("Checked 5 min ago");
      expect(checkedAgo("2026-09-28T09:00:00Z", undefined, now)).toBe("Checked 3 h ago");
      expect(checkedAgo("2026-09-26T12:00:00Z", undefined, now)).toBe("Checked 2 d ago");
      expect(checkedAgo(undefined, 125, now)).toBe("Checked 2 min ago");
      expect(checkedAgo(undefined, undefined, now)).toBeUndefined();
      // Window grammar 2026-10-27: the row says the age as a quiet sentence.
      expect(checkedWords("2026-09-28T11:59:30Z", undefined, now)).toBe("checked just now");
      expect(checkedWords("2026-09-28T11:59:00Z", undefined, now)).toBe("checked 1 minute ago");
      expect(checkedWords("2026-09-28T09:00:00Z", undefined, now)).toBe("checked 3 hours ago");
      expect(checkedWords("2026-09-17T12:00:00Z", undefined, now)).toBe("checked 11 days ago");
      expect(checkedWords(undefined, undefined, now)).toBeUndefined();
      expect(stateWords("never_checked", "github", {})).toBe("Not checked");
      expect(stateWords("connected", "jira", {})).toBe("Works");
      // Betterment ST2: the four row states in words.
      expect(stateWords("owner_action_required", "jira", {})).toBe("Not signed in");
      expect(stateWords("degraded", "jira", { other_account: true })).toBe("Signed in as another account");
      expect(stateWords("degraded", "github", { reason: "gh was not run" })).toBe("Could not check: gh was not run");
      expect(stateWords("unavailable", "confluence", {})).toBe("Could not check: acli is not installed");
    });

    it("each card shows its own age, and Not checked", async () => {
      const recent = new Date(Date.now() - 5 * 60_000).toISOString();
      const older = new Date(Date.now() - 3 * 3_600_000).toISOString();
      const response: ConnectionsResponse = {
        tools: [
          { provider_id: "github", state: "never_checked", account: {} },
          {
            provider_id: "jira", state: "connected", last_checked_at: recent,
            connections: [
              {
                connection_ref: "alpha-user", state: "connected",
                account: { site: "alpha.atlassian.net", email: "user@example.com" },
                last_checked_at: recent,
              },
              {
                connection_ref: "beta-user", state: "never_checked",
                account: { site: "beta.atlassian.net", email: "user@example.com" },
              },
            ],
          },
          {
            provider_id: "confluence", state: "connected", last_checked_at: older,
            connections: [{
              connection_ref: "gamma-user", state: "connected",
              account: { site: "gamma.atlassian.net", email: "user@example.com" },
              last_checked_at: older,
            }],
          },
          connectedCalendar(),
          connectedModels(),
        ],
      };
      renderPane(response);
      const gh = await screen.findByTestId("connections-github");
      expect(within(gh).getByText("Not checked")).toBeInTheDocument();
      expect(within(gh).getByText("Check")).toBeInTheDocument();
      const alpha = await screen.findByTestId("connections-jira-conn-alpha-user");
      expect(rowWords(alpha)).toBe("Works · checked 5 minutes ago");
      const beta = await screen.findByTestId("connections-jira-conn-beta-user");
      expect(within(beta).getByText("Not checked")).toBeInTheDocument();
      const gamma = await screen.findByTestId("connections-confluence-conn-gamma-user");
      expect(rowWords(gamma)).toBe("Works · checked 3 hours ago");
      // Calendar and Models are local reads: no age.
      const cal = await screen.findByTestId("connections-calendar");
      expect(within(cal).getByText("Connected")).toBeInTheDocument();
    });
  });
  /* PHILO-17 U29: the cause in plain words, the command on every row, Add checks at once. */
  describe("sign in (U29)", () => {
    it("the producer's owner_action_required reads Not signed in; a degraded check never does", async () => {
      const degraded: ConnectionTool = {
        provider_id: "github", state: "degraded", account: {},
        error_detail: "connect to 10.0.0.1:401 timed out", reason: "gh did not answer",
        last_checked_at: "2026-09-04T13:00:00Z", egress_host: "github.com",
      };
      renderPane({ tools: [degraded, emptyJira(), connectedCalendar(), connectedModels()] });
      const card = (await screen.findByTestId("connections-github")).closest("li")!;
      expect(rowWords(card)).toMatch(/^Could not check: gh did not answer · checked /);
      expect(within(card).queryByText("Not signed in")).toBeNull();
      expect(within(card).getByRole("button", { name: "Check" })).toBeInTheDocument();
    });

    it("Jira Add posts the account and checks it at once", async () => {
      vi.mocked(apiFetch).mockResolvedValue({});
      mockRecheckProvider.mockResolvedValue(null);
      renderPane({ tools: [connectedGithub(), emptyJira(), connectedCalendar(), connectedModels()] });
      const card = (await screen.findByTestId("connections-jira")).closest("li")!;
      fireEvent.click(within(card).getByTestId("connections-add-open-jira"));
      const inputs = card.querySelectorAll("input");
      fireEvent.change(inputs[0], { target: { value: "acme.atlassian.net" } });
      fireEvent.change(inputs[1], { target: { value: "me@acme.com" } });
      expect(within(card).getByText(/acli jira auth login/)).not.toBeVisible();
      fireEvent.click(within(card).getByText("Sign-in command"));
      expect(within(card).getByText("acli jira auth login --site acme.atlassian.net --email me@acme.com --token")).toBeInTheDocument();
      fireEvent.click(within(card).getByText("Add"));
      await waitFor(() => expect(apiFetch).toHaveBeenCalledWith(
        "/api/providers/jira/connections", { method: "POST", json: { site: "acme.atlassian.net", email: "me@acme.com" } }));
      await waitFor(() => expect(mockRecheckProvider).toHaveBeenCalledWith("jira"));
    });

    it("Confluence with no account has its Add", async () => {
      const conf: ConnectionTool = { provider_id: "confluence", state: "never_checked", account: {}, connections: [] };
      renderPane({ tools: [connectedGithub(), emptyJira(), conf, connectedCalendar(), connectedModels()] });
      const card = (await screen.findByTestId("connections-confluence")).closest("li")!;
      fireEvent.click(within(card).getByTestId("connections-add-open-confluence"));
      expect(within(card).getByText("Add")).toBeInTheDocument();
      expect(within(card).getByText(/acli confluence auth login/)).not.toBeVisible();
      fireEvent.click(within(card).getByText("Sign-in command"));
      expect(within(card).getByText(/acli confluence auth login/)).toBeInTheDocument();
    });
  });
});

/* replaces: tests/e2e/test_philo17_needs_you_grouped_glass.py::test_one_row_per_cause_and_repair_on_the_real_hub
   (the leg "Reconnect lands on Settings · Connections, GitHub focused"). Needs you's Reconnect opens
   Settings with scope "integration:github" (NeedsDrawer.test.tsx:961); SettingsCore passes it on as
   focusProvider (SettingsCore.tsx:2388). Here the pane puts focus on that provider's row. */
describe("ConnectionsPane focusProvider", () => {
  it("puts focus inside the named provider's row once the list loads", async () => {
    mockFetchConnections.mockResolvedValue(fullResponse());
    render(
      <ConnectionsPane onFooterUpdate={vi.fn()} onOpenModule={vi.fn()} focusProvider="github" />,
    );
    const card = (await screen.findByTestId("connections-github")).closest("li")!;
    await waitFor(() => {
      expect(document.activeElement).not.toBeNull();
      expect(card.contains(document.activeElement)).toBe(true);
    });
  });
});

describe("Accounts recovery", () => {
  it.each(["jira", "confluence"] as const)("keeps a new %s account draft and refusal across an existing sign-in detour", async (provider) => {
    const tool = connectedJira();
    tool.provider_id = provider;
    tool.connections![0].state = "owner_action_required";
    renderPane({ tools: [tool] });
    fireEvent.click(await screen.findByTestId(`connections-add-open-${provider}`));
    const form = screen.getByTestId(`connections-add-${provider}`);
    fireEvent.change(within(form).getByRole("textbox", { name: "Site" }), { target: { value: "next.atlassian.net" } });
    fireEvent.change(within(form).getByRole("textbox", { name: "Email" }), { target: { value: "next@example.com" } });
    const detour = () => {
      fireEvent.click(within(screen.getByTestId(`connections-${provider}-conn-alpha-user`)).getByRole("button", { name: "Sign in" }));
      expect(form).not.toBeVisible();
      fireEvent.click(screen.getByTestId(`connections-add-open-${provider}`));
      expect(screen.getByTestId(`connections-add-${provider}`)).toBe(form);
      expect(within(form).getByRole("textbox", { name: "Site" })).toHaveValue("next.atlassian.net");
      expect(within(form).getByRole("textbox", { name: "Email" })).toHaveValue("next@example.com");
    };
    detour();
    vi.mocked(apiFetch).mockRejectedValue(new Error("Account refused"));
    fireEvent.click(within(form).getByRole("button", { name: "Add" }));
    await within(form).findByText("Account not added");
    detour();
    expect(within(form).getByText("Account not added")).toBeVisible();
    expect(within(form).getByRole("button", { name: "Retry" })).toBeVisible();
  });

  it.each([
    ["jira", "owner_action_required"], ["jira", "unavailable"],
    ["confluence", "owner_action_required"], ["confluence", "unavailable"],
  ] as const)("distinguishes collapsed %s %s accounts with the same email by site", async (provider, state) => {
    const tool = twoJiraConnections();
    tool.provider_id = provider;
    for (const conn of tool.connections!) { conn.state = state; conn.account.email = "same@example.com"; }
    renderPane({ tools: [tool] });
    const rows = await Promise.all(tool.connections!.map(conn => screen.findByTestId(`connections-${provider}-conn-${conn.connection_ref}`)));
    rows.forEach((row, index) => {
      expect(within(row).getByText(tool.connections![index].account.site)).toBeVisible();
      expect(within(row).getByText("same@example.com")).toBeVisible();
      // The host is quiet text on the row; Check's hover title names it.
      expect(row.querySelectorAll(".gadget-chip-egress")).toHaveLength(0);
      expect(within(row).getByRole("button", { name: "Check" }).getAttribute("title")).toBe(`Checks ${tool.connections![index].account.site}`);
    });
  });

  it("leads populated rows with their provider and keeps commands closed until requested", async () => {
    const jira = connectedJira();
    const confluence = { ...structuredClone(jira), provider_id: "confluence" } as ConnectionTool;
    renderPane({ tools: [neverCheckedGithub(), jira, confluence] });
    const jiraRow = await screen.findByTestId("connections-jira-conn-alpha-user");
    const confluenceRow = await screen.findByTestId("connections-confluence-conn-alpha-user");
    expect(jiraRow.querySelector(".connections-tool-label")?.textContent).toBe("Jira");
    expect(confluenceRow.querySelector(".connections-tool-label")?.textContent).toBe("Confluence");
    screen.queryAllByText(/acli .* auth login/).forEach(command => expect(command).not.toBeVisible());
    const github = screen.getByTestId("connections-github");
    expect(within(github).queryByText("gh auth login")).toBeNull();
    fireEvent.click(within(github).getByRole("button", { name: "Check" }));
    await waitFor(() => expect(mockRecheckProvider).toHaveBeenCalledWith("github"));
  });

  it("opens a sign-in well only for a producer-named missing sign-in", async () => {
    renderPane({ tools: [signInGithub()] });
    const row = (await screen.findByTestId("connections-github")).closest("li")!;
    expect(within(row).queryByText("gh auth login")).toBeNull();
    fireEvent.click(within(row).getByRole("button", { name: "Sign in" }));
    expect(within(row).getByText("gh auth login")).toBeInTheDocument();
    expect(within(row).getAllByText("github.com")).toHaveLength(1);
  });

  it.each([{ state: "not_determined", can_request: true, verb: "Allow calendar access" }, { state: "denied", can_request: false, verb: "Open System Settings" }])("Settings calendar $state access remains available with an existing feed", async ({ state, can_request, verb }) => {
    vi.mocked(apiFetch).mockImplementation(async (path) => {
      if (path === "/api/onboarding/calendar") return { ...CALENDAR_WIRE.wire, macos: { state, can_request }, candidates: [] };
      if (path === "/api/settings") return { calendar: { sources: [{ id: "feed", url: CALENDAR_CHECK_WIRE.wire.url, enabled: true }] } };
      if (path === "/api/door") return { calendar_configured: true };
      return {};
    });
    mockFetchConnections.mockResolvedValue(fullResponse());
    render(<ConnectionsPane onFooterUpdate={vi.fn()} onOpenModule={vi.fn()} focusProvider="calendar" />);
    fireEvent.click(await screen.findByRole("button", { name: verb }));
    const destination = can_request ? "/api/onboarding/calendar/macos/access" : "/api/onboarding/calendar/macos/settings";
    await waitFor(() => expect(vi.mocked(apiFetch).mock.calls.some(([path, init]) => path === destination && init?.method === "POST")).toBe(true));
  });

  it("Settings calendar URL Add remains available with an existing feed, waits for the save gate and reconciles the accepted use", async () => {
    let allowed = false;
    const before = vi.fn(async () => allowed);
    const changed = vi.fn(async () => {});
    vi.mocked(apiFetch).mockImplementation(async (path) => {
      if (path === "/api/onboarding/calendar") return { ...CALENDAR_WIRE.wire, candidates: [] };
      if (path === "/api/settings") return { calendar: { sources: [{ id: "feed", url: CALENDAR_CHECK_WIRE.wire.url, enabled: true }] } };
      if (path === "/api/door") return { calendar_configured: true };
      if (path === "/api/onboarding/calendar/check") return CALENDAR_CHECK_WIRE.wire;
      if (path === "/api/onboarding/calendar/use") return CALENDAR_USE_WIRE.wire;
      return {};
    });
    mockFetchConnections.mockResolvedValue(fullResponse());
    render(<ConnectionsPane onFooterUpdate={vi.fn()} onOpenModule={vi.fn()} focusProvider="calendar" onCalendarChanged={changed} onBeforeCalendarChange={before} />);
    const field = await screen.findByRole("textbox", { name: "Calendar URL" });
    fireEvent.change(field, { target: { value: CALENDAR_CHECK_WIRE.wire.url } });
    fireEvent.click(screen.getByRole("button", { name: "Add" }));
    await waitFor(() => expect(before).toHaveBeenCalledOnce());
    expect(vi.mocked(apiFetch).mock.calls.some(([, init]) => init?.method === "POST")).toBe(false);
    expect(field).toHaveValue(CALENDAR_CHECK_WIRE.wire.url);
    allowed = true;
    fireEvent.click(screen.getByRole("button", { name: "Add" }));
    await waitFor(() => expect(changed).toHaveBeenCalledOnce());
    expect(vi.mocked(apiFetch).mock.calls.filter(([, init]) => init?.method === "POST").map(([path]) => path)).toEqual(["/api/onboarding/calendar/check", "/api/onboarding/calendar/use"]);
    expect(field).toHaveValue("");
  });

  it("Settings calendar chooser names its inset and shows loading until the read returns", async () => {
    let finishRead!: (answer: typeof CALENDAR_WIRE.wire) => void;
    const detection = new Promise<typeof CALENDAR_WIRE.wire>((resolve) => { finishRead = resolve; });
    vi.mocked(apiFetch).mockImplementation(async (path) => {
      if (path === "/api/onboarding/calendar") return detection;
      if (path === "/api/settings") return { calendar: { sources: [] } };
      return {};
    });
    mockFetchConnections.mockResolvedValue(fullResponse());
    render(<ConnectionsPane onFooterUpdate={vi.fn()} onOpenModule={vi.fn()} focusProvider="calendar" />);
    const chooser = await screen.findByRole("region", { name: "Choose calendar" });
    expect(chooser).toHaveAttribute("data-material", "inset");
    expect(within(chooser).getByRole("status", { name: "Checking calendars" })).toBeVisible();
    expect(within(chooser).queryByRole("status", { name: "No calendars found" })).toBeNull();
    expect(within(chooser).getByRole("textbox", { name: "Calendar URL" })).toBeVisible();
    finishRead(CALENDAR_WIRE.wire);
    await within(chooser).findByRole("button", { name: `Use ${CALENDAR_WIRE.wire.candidates[0].label}` });
    expect(within(chooser).queryByRole("status", { name: "CHECKING CALENDARS" })).toBeNull();
  });

  it.each([
    { state: "unavailable", label: "Calendars unavailable" },
    { state: "full_access", label: "No calendars found" },
  ])("Settings calendar chooser distinguishes $state from loading and reads again without a prompt", async ({ state, label }) => {
    let reads = 0;
    let finishRead!: (answer: typeof CALENDAR_WIRE.wire) => void;
    vi.mocked(apiFetch).mockImplementation(async (path) => {
      if (path === "/api/onboarding/calendar") {
        reads += 1;
        if (reads === 1) return { ...CALENDAR_WIRE.wire, macos: { state, can_request: false }, candidates: [] };
        return new Promise<typeof CALENDAR_WIRE.wire>((resolve) => { finishRead = resolve; });
      }
      if (path === "/api/settings") return { calendar: { sources: [{ id: "feed", url: CALENDAR_CHECK_WIRE.wire.url, enabled: true }] } };
      if (path === "/api/door") return { calendar_configured: true };
      return {};
    });
    mockFetchConnections.mockResolvedValue(fullResponse());
    render(<ConnectionsPane onFooterUpdate={vi.fn()} onOpenModule={vi.fn()} focusProvider="calendar" />);
    const chooser = await screen.findByTestId("firstrun-calendar");
    await within(chooser).findByRole("status", { name: label });
    expect(within(chooser).getByRole("status", { name: "In use" })).toBeVisible();
    expect(within(chooser).queryByRole("button", { name: "Allow calendar access" })).toBeNull();
    expect(within(chooser).queryByRole("button", { name: "Open System Settings" })).toBeNull();
    const field = within(chooser).getByRole("textbox", { name: "Calendar URL" });
    fireEvent.change(field, { target: { value: CALENDAR_CHECK_WIRE.wire.url } });
    expect(within(chooser).getByText(CALENDAR_CHECK_WIRE.wire.host)).toBeVisible();
    const check = within(chooser).getByRole("button", { name: "Check again" });
    fireEvent.click(check);
    await waitFor(() => expect(reads).toBe(2));
    expect(check).toBeDisabled();
    expect(within(chooser).getByRole("button", { name: "Add" })).toBeDisabled();
    fireEvent.click(check);
    expect(reads).toBe(2);
    finishRead(CALENDAR_WIRE.wire);
    await within(chooser).findByRole("button", { name: `Use ${CALENDAR_WIRE.wire.candidates[0].label}` });
    expect(within(chooser).queryByRole("status", { name: label })).toBeNull();
    expect(field).toHaveValue(CALENDAR_CHECK_WIRE.wire.url);
    expect(vi.mocked(apiFetch).mock.calls.some(([, init]) => init?.method === "POST")).toBe(false);
  });

  it("Settings calendar chooser retries a failed read without calling native permission or URL writes", async () => {
    let reads = 0;
    vi.mocked(apiFetch).mockImplementation(async (path) => {
      if (path === "/api/onboarding/calendar") {
        reads += 1;
        if (reads === 1) throw new Error("Calendar read unavailable");
        return CALENDAR_WIRE.wire;
      }
      if (path === "/api/settings") return { calendar: { sources: [] } };
      return {};
    });
    mockFetchConnections.mockResolvedValue(fullResponse());
    render(<ConnectionsPane onFooterUpdate={vi.fn()} onOpenModule={vi.fn()} focusProvider="calendar" />);
    const chooser = await screen.findByTestId("firstrun-calendar");
    await within(chooser).findByRole("status", { name: "Can't check" });
    expect(within(chooser).getByText("Error: Calendar read unavailable")).toBeVisible();
    fireEvent.click(within(chooser).getByRole("button", { name: "Retry" }));
    await within(chooser).findByRole("button", { name: `Use ${CALENDAR_WIRE.wire.candidates[0].label}` });
    expect(reads).toBe(2);
    expect(within(chooser).queryByRole("status", { name: "CAN'T CHECK" })).toBeNull();
    expect(vi.mocked(apiFetch).mock.calls.some(([, init]) => init?.method === "POST")).toBe(false);
  });
  it.each([true, false])("Settings refreshes a configured native calendar name with enabled=%s and reconciles only accepted writes", async (enabled) => {
    const candidate = CALENDAR_WIRE.wire.candidates[0];
    const changed = vi.fn(async () => {});
    const before = vi.fn(async () => true);
    let accepted = false;
    vi.mocked(apiFetch).mockImplementation(async (path) => {
      if (path === "/api/onboarding/calendar") {
        if (accepted && !enabled) throw new Error("Refresh unavailable");
        return CALENDAR_WIRE.wire;
      }
      if (path === "/api/settings") return { calendar: { sources: [{ id: "saved", url: candidate.id, enabled }] } };
      if (path === "/api/door") return { calendar_configured: true };
      if (path === "/api/onboarding/calendar/use") { accepted = true; return CALENDAR_USE_WIRE.wire; }
      return {};
    });
    mockFetchConnections.mockResolvedValue(fullResponse());
    render(<ConnectionsPane onFooterUpdate={vi.fn()} onOpenModule={vi.fn()} focusProvider="calendar" onCalendarChanged={changed} onBeforeCalendarChange={before} />);
    const refresh = await screen.findByRole("button", { name: `Refresh ${candidate.label} name` });
    fireEvent.click(refresh);
    await waitFor(() => expect(changed).toHaveBeenCalledOnce());
    expect(before).toHaveBeenCalledOnce();
    expect(apiFetch).toHaveBeenCalledWith("/api/onboarding/calendar/use", { method: "POST", json: { id: candidate.id, label: candidate.label } });
  });

  it("a refused pending Settings save prevents the calendar write", async () => {
    const before = vi.fn(async () => false);
    vi.mocked(apiFetch).mockImplementation(async (path) => {
      if (path === "/api/onboarding/calendar") return CALENDAR_WIRE.wire;
      if (path === "/api/settings") return { calendar: { sources: [] } };
      return {};
    });
    mockFetchConnections.mockResolvedValue(fullResponse());
    render(<ConnectionsPane onFooterUpdate={vi.fn()} onOpenModule={vi.fn()} focusProvider="calendar" onBeforeCalendarChange={before} />);
    fireEvent.click(await screen.findByRole("button", { name: `Use ${CALENDAR_WIRE.wire.candidates[0].label}` }));
    await waitFor(() => expect(before).toHaveBeenCalledOnce());
    expect(vi.mocked(apiFetch).mock.calls.some(([path]) => path === "/api/onboarding/calendar/use")).toBe(false);
  });

  it("a refused native calendar use keeps the chooser and does not reconcile", async () => {
    const changed = vi.fn(async () => {});
    vi.mocked(apiFetch).mockImplementation(async (path) => {
      if (path === "/api/onboarding/calendar") return CALENDAR_WIRE.wire;
      if (path === "/api/settings") return { calendar: { sources: [] } };
      if (path === "/api/door") return {};
      if (path === "/api/onboarding/calendar/use") throw new Error("Calendar refused");
      return {};
    });
    mockFetchConnections.mockResolvedValue(fullResponse());
    render(<ConnectionsPane onFooterUpdate={vi.fn()} onOpenModule={vi.fn()} focusProvider="calendar" onCalendarChanged={changed} />);
    fireEvent.click(await screen.findByRole("button", { name: `Use ${CALENDAR_WIRE.wire.candidates[0].label}` }));
    expect(await screen.findByText(/Calendar refused/)).toBeInTheDocument();
    expect(changed).not.toHaveBeenCalled();
  });

  it("the API rejects failed reads and checks instead of returning empty setup", async () => {
    const real = await vi.importActual<typeof import("../connections/api")>("../connections/api");
    vi.mocked(apiFetch).mockRejectedValue(new Error("Hub unavailable"));
    await expect(real.fetchConnections()).rejects.toThrow("Hub unavailable");
    await expect(real.recheckProvider("github")).rejects.toThrow("Hub unavailable");
  });

  it("keeps failed Add inputs and offers another account after an existing one", async () => {
    renderPane({ tools: [connectedJira()] });
    fireEvent.click(await screen.findByTestId("connections-add-open-jira"));
    const form = screen.getByTestId("connections-add-jira");
    fireEvent.change(within(form).getByRole("textbox", { name: "Site" }), { target: { value: "next.atlassian.net" } });
    fireEvent.change(within(form).getByRole("textbox", { name: "Email" }), { target: { value: "next@example.com" } });
    vi.mocked(apiFetch).mockRejectedValue(new Error("Account refused"));
    fireEvent.click(within(form).getByRole("button", { name: "Add" }));
    await within(form).findByText("Account not added");
    expect(within(form).getByRole("textbox", { name: "Site" })).toHaveValue("next.atlassian.net");
    expect(within(form).getByRole("textbox", { name: "Email" })).toHaveValue("next@example.com");
  });

  it("names a failed Recheck without presenting it as accepted", async () => {
    renderPane({ tools: [connectedGithub()] });
    const row = (await screen.findByTestId("connections-github")).closest("li")!;
    mockRecheckProvider.mockRejectedValue(new Error("Hub unavailable"));
    fireEvent.click(within(row).getByRole("button", { name: "Check" }));
    expect(await screen.findByText("Check failed")).toBeInTheDocument();
  });

  it("says Copy failed when the clipboard refuses", async () => {
    Object.defineProperty(navigator, "clipboard", { configurable: true, value: { writeText: vi.fn().mockRejectedValue(new Error("Refused")) } });
    renderPane({ tools: [signInGithub()] });
    fireEvent.click(await screen.findByRole("button", { name: "Sign in" }));
    fireEvent.click(within(screen.getByTestId("connections-github-unfold")).getByRole("button", { name: "Copy" }));
    expect(await screen.findByText("Copy failed")).toBeInTheDocument();
    expect(screen.queryByText("Copied")).toBeNull();
  });
});

describe("Accounts that say Works (betterment ST2)", () => {
  const decoded = (raw: unknown) => decodeConnectionsResponse(structuredClone(raw));
  const BETA = "beta.atlassian.net|owner@example.com";
  const GAMMA_ID = (ST2_FOUND.candidates.find((c: { site: string }) => c.site === "gamma.atlassian.net"))!.id;

  it("tells two Jira sites apart by the site in the row, each with its own Check", async () => {
    vi.mocked(apiFetch).mockImplementation(async (path) => path === "/api/onboarding/connections" ? structuredClone(ST2_FOUND) : {});
    renderPane(decoded(ST2_CONNECTIONS));
    for (const site of ["alpha.atlassian.net", "beta.atlassian.net"]) {
      const row = await screen.findByTestId(`connections-jira-conn-${site}|owner@example.com`);
      expect(within(row).getByText(site)).toBeInTheDocument();
      expect(rowWords(row)).toMatch(/^Works · checked/);
      expect(within(row).getByRole("button", { name: "Check" })).toBeInTheDocument();
    }
  });

  it("lists the acli profile HoldSpeak does not use under Found on this Mac, and one Use connects it", async () => {
    let used = false;
    vi.mocked(apiFetch).mockImplementation(async (path, init) => {
      if (path === "/api/onboarding/connections/use" && init?.method === "POST") { used = true; return structuredClone(ST2_USE); }
      if (path === "/api/onboarding/connections") return structuredClone(used ? ST2_FOUND_AFTER_USE : ST2_FOUND);
      return {};
    });
    mockFetchConnections.mockImplementation(async () => decoded(used ? ST2_AFTER_USE : ST2_CONNECTIONS));
    render(<ConnectionsPane onFooterUpdate={vi.fn()} onOpenModule={vi.fn()} />);
    const found = await screen.findByTestId(`connections-found-${GAMMA_ID}`);
    expect(within(found).getAllByText("gamma.atlassian.net")[0]).toBeInTheDocument();
    // Only accounts HoldSpeak does not use yet: the two checked Jira sites are not under Found.
    const list = screen.getByTestId("connections-found");
    expect(within(list).queryByTestId("connections-found-jira:alpha.atlassian.net|owner@example.com")).toBeNull();
    expect(within(list).queryByTestId("connections-found-jira:beta.atlassian.net|owner@example.com")).toBeNull();
    fireEvent.click(within(found).getByRole("button", { name: "Use" }));
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith(
      "/api/onboarding/connections/use", { method: "POST", json: { id: GAMMA_ID } }));
    act(() => { window.dispatchEvent(new Event(ACCOUNTS_CHANGED)); });
    const gamma = await screen.findByTestId("connections-jira-conn-gamma.atlassian.net|owner@example.com");
    await waitFor(() => expect(rowWords(gamma)).toMatch(/^Works · checked/));
    await waitFor(() => expect(screen.queryByTestId(`connections-found-${GAMMA_ID}`)).toBeNull());
  });

  it("pressing a row unfolds what uses it, Sign in again and Remove; Undo adds it back and checks it", async () => {
    let removed = false;
    vi.mocked(apiFetch).mockImplementation(async (path, init) => {
      if (init?.method === "DELETE") { removed = true; return structuredClone(ST2_REMOVE); }
      if (path === "/api/onboarding/connections") return structuredClone(ST2_FOUND_AFTER_USE);
      return {};
    });
    const afterRemove = decoded(ST2_CONNECTIONS);
    afterRemove.tools.find((t) => t.provider_id === "jira")!.connections =
      afterRemove.tools.find((t) => t.provider_id === "jira")!.connections!.filter((c) => c.connection_ref !== BETA);
    mockFetchConnections.mockImplementation(async () => removed ? afterRemove : decoded(ST2_CONNECTIONS));
    mockRecheckProvider.mockResolvedValue(null);
    render(<ConnectionsPane onFooterUpdate={vi.fn()} onOpenModule={vi.fn()} />);
    const line = await screen.findByTestId(`connections-jira-conn-${BETA}`);
    fireEvent.click(line);
    const unfold = await screen.findByTestId(`connections-jira-unfold-${BETA}`);
    expect(within(unfold).getByText("Nothing yet")).toBeInTheDocument();
    expect(within(unfold).queryByText(/acli jira auth login/)).toBeNull();
    fireEvent.click(within(unfold).getByRole("button", { name: "Sign in again" }));
    expect(apiFetch).toHaveBeenCalledWith("/api/connections/jira/signin", {
      method: "POST", json: { site: "beta.atlassian.net", email: "owner@example.com" },
    });
    // This fixture has no sign-in result; its unavailable native start falls
    // back asynchronously. The real successful flow is covered on glass.
    await waitFor(() => expect(within(unfold).getByText(`acli jira auth login --site beta.atlassian.net --email owner@example.com --token`)).toBeInTheDocument());
    fireEvent.click(within(unfold).getByRole("button", { name: "Remove" }));
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith(
      `/api/providers/jira/connections/${encodeURIComponent(BETA)}`, { method: "DELETE" }));
    const bar = await screen.findByTestId("connections-removed");
    expect(within(bar).getByText("Jira · beta.atlassian.net")).toBeInTheDocument();
    await waitFor(() => expect(screen.queryByTestId(`connections-jira-conn-${BETA}`)).toBeNull());
    removed = false;
    fireEvent.click(within(bar).getByRole("button", { name: "Undo" }));
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith(
      "/api/providers/jira/connections", { method: "POST", json: { site: "beta.atlassian.net", email: "owner@example.com" } }));
    await waitFor(() => expect(mockRecheckProvider).toHaveBeenCalledWith("jira"));
    expect(await screen.findByTestId(`connections-jira-conn-${BETA}`)).toBeInTheDocument();
  });

  it("names what uses an account in its unfold", async () => {
    vi.mocked(apiFetch).mockResolvedValue({});
    const wire = decoded(ST2_CONNECTIONS);
    const beta = wire.tools.find((t) => t.provider_id === "jira")!.connections!.find((c) => c.connection_ref === BETA)!;
    beta.used_by = [{ kind: "project", name: "Atlas" }, { kind: "destination", name: "Team Jira" }];
    renderPane(wire);
    fireEvent.click(await screen.findByTestId(`connections-jira-conn-${BETA}`));
    const unfold = await screen.findByTestId(`connections-jira-unfold-${BETA}`);
    expect(within(unfold).getByText("Project · Atlas")).toBeInTheDocument();
    expect(within(unfold).getByText("Send to · Team Jira")).toBeInTheDocument();
  });
});
