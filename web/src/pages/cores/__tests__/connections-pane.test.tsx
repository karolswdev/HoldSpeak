// HS-168-03 — ConnectionsPane vitest: states, verbs, deep links, labels.
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ConnectionsPane, type ConnectionsFoot } from "../connections";
import type { ConnectionsResponse, ConnectionTool } from "../connections/api";
import { decodeConnectionsResponse, decodeState } from "../connections/api";
import { checkedAgo, stateWords } from "../connections/ConnectionsPane";

/* ── Mock the API module ── */
vi.mock("../connections/api", async (importOriginal) => {
  const original = await importOriginal<typeof import("../connections/api")>();
  return {
    ...original,
    fetchConnections: vi.fn(),
    recheckProvider: vi.fn(),
  };
});

vi.mock("../../../lib/api", () => ({
  apiFetch: vi.fn(),
  readableError: (e: unknown) => String(e),
}));

import { fetchConnections, recheckProvider } from "../connections/api";

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
    last_checked_at: "2026-09-04T13:00:00Z",
    egress_host: "github.com",
  };
}

function notConfiguredGithub(): ConnectionTool {
  return {
    provider_id: "github",
    state: "not_configured",
    account: {},
    last_checked_at: undefined,
    egress_host: undefined,
  };
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

function emptyJira(): ConnectionTool {
  return {
    provider_id: "jira",
    state: "not_configured",
    account: {},
    connections: [],
  };
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

  describe("GitHub connected", () => {
    it("shows Connected chip, login summary, and quiet Recheck verb", async () => {
      renderPane();
      const card = await screen.findByTestId("connections-github");
      expect(within(card).getByText("GitHub")).toBeInTheDocument();
      expect(within(card).getByText("karolswdev")).toBeInTheDocument();
      // PHILO-9-02 B1: the chip carries the row's own check age.
      expect(within(card).getByText(/^Connected · Checked /)).toBeInTheDocument();
      expect(within(card).getByText("Recheck")).toBeInTheDocument();
    });
  });

  describe("GitHub owner_action_required", () => {
    it("shows Sign in chip with open fold and COPY transport key", async () => {
      const response: ConnectionsResponse = {
        tools: [signInGithub(), emptyJira(), connectedCalendar(), connectedModels()],
      };
      renderPane(response);
      const card = await screen.findByTestId("connections-github");
      expect(within(card).getByText("Sign in")).toBeInTheDocument();
      // Fold is open with the command
      expect(within(card).getByText("gh auth login")).toBeInTheDocument();
      // Copy transport key
      expect(within(card).getByText("Copy")).toBeInTheDocument();
      // Primary Recheck in the fold
      const recheckButtons = within(card).getAllByText("Recheck");
      expect(recheckButtons.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe("GitHub unavailable", () => {
    it("shows gh missing chip with fold and install hint", async () => {
      const response: ConnectionsResponse = {
        tools: [unavailableGithub(), emptyJira(), connectedCalendar(), connectedModels()],
      };
      renderPane(response);
      const card = await screen.findByTestId("connections-github");
      expect(within(card).getByText("gh missing")).toBeInTheDocument();
      expect(within(card).getByText("brew install gh")).toBeInTheDocument();
      expect(within(card).getByText("Copy")).toBeInTheDocument();
    });
  });

  describe("GitHub degraded", () => {
    it("shows Unreachable chip with error_detail as title", async () => {
      const response: ConnectionsResponse = {
        tools: [degradedGithub(), emptyJira(), connectedCalendar(), connectedModels()],
      };
      renderPane(response);
      const card = await screen.findByTestId("connections-github");
      // PHILO-9-02 B1: the chip carries the row's own check age.
      expect(within(card).getByText(/^Unreachable · Checked /)).toBeInTheDocument();
      // Quiet Recheck verb (no fold)
      expect(within(card).getByText("Recheck")).toBeInTheDocument();
    });
  });

  describe("GitHub not_configured", () => {
    it("shows Off chip and Recheck verb", async () => {
      const response: ConnectionsResponse = {
        tools: [notConfiguredGithub(), emptyJira(), connectedCalendar(), connectedModels()],
      };
      renderPane(response);
      const card = await screen.findByTestId("connections-github");
      expect(within(card).getByText("Off")).toBeInTheDocument();
      expect(within(card).getByText("Recheck")).toBeInTheDocument();
    });
  });

  /* ── Jira ── */

  describe("Jira with 0 connections", () => {
    it("shows Not set up with Add account ghost card", async () => {
      const response: ConnectionsResponse = {
        tools: [connectedGithub(), emptyJira(), connectedCalendar(), connectedModels()],
      };
      renderPane(response);
      const card = await screen.findByTestId("connections-jira");
      expect(within(card).getByText("Jira")).toBeInTheDocument();
      expect(within(card).getByText("Not set up")).toBeInTheDocument();
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
      // Site appears as both label and provenance boundary
      const siteTexts = within(conn).getAllByText("alpha.atlassian.net");
      expect(siteTexts.length).toBeGreaterThanOrEqual(1);
      expect(within(conn).getByText("user@example.com")).toBeInTheDocument();
      const chips = within(conn).getAllByText("Connected");
      expect(chips.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe("Jira host chip (PHILO-4-01 r4)", () => {
    it("truncates only the host chip, whose title is the full host", async () => {
      renderPane();
      const conn = await screen.findByTestId("connections-jira-conn-alpha-user");
      const chip = within(conn).getByText("ALPHA.ATLASSIAN.NET");
      expect(chip.classList.contains("gadget-chip")).toBe(true);
      expect(chip.classList.contains("gadget-chip-truncate")).toBe(true);
      // Never the inherited "route not set" default on a known destination.
      expect(chip.getAttribute("title")).toBe("alpha.atlassian.net");
      // The row label shows the full host, so the chip may truncate.
      expect(conn.querySelector(".connections-tool-label")?.textContent).toBe("alpha.atlassian.net");
    });
  });

  describe("Jira with 2 connections", () => {
    it("shows both connection rows", async () => {
      const response: ConnectionsResponse = {
        tools: [connectedGithub(), twoJiraConnections(), connectedCalendar(), connectedModels()],
      };
      renderPane(response);
      const alpha = await screen.findByTestId("connections-jira-conn-alpha-user");
      expect(within(alpha).getByText("Connected")).toBeInTheDocument();
      const beta = await screen.findByTestId("connections-jira-conn-beta-admin");
      expect(within(beta).getByText("Sign in")).toBeInTheDocument();
    });
  });

  /* ── Calendar + Models link cards ── */

  describe("Calendar card", () => {
    it("shows Connected with sources summary and Sources verb", async () => {
      renderPane();
      const card = await screen.findByTestId("connections-calendar");
      expect(within(card).getByText("Calendar")).toBeInTheDocument();
      expect(within(card).getByText("2 sources")).toBeInTheDocument();
      expect(within(card).getByText("Connected")).toBeInTheDocument();
      expect(within(card).getByText("Sources")).toBeInTheDocument();
    });

    it("opens meetings module when Sources is clicked", async () => {
      const onOpen = vi.fn();
      renderPane(fullResponse(), { onOpen });
      const card = await screen.findByTestId("connections-calendar");
      fireEvent.click(within(card).getByText("Sources"));
      expect(onOpen).toHaveBeenCalledWith("meetings");
    });
  });

  describe("Models card", () => {
    it("shows assigned summary and Open Models verb", async () => {
      renderPane();
      const card = await screen.findByTestId("connections-models");
      expect(within(card).getByText("Models")).toBeInTheDocument();
      expect(within(card).getByText("5 of 7 assigned")).toBeInTheDocument();
      expect(within(card).getByText("Open Models")).toBeInTheDocument();
    });

    it("opens models module when Open Models is clicked", async () => {
      const onOpen = vi.fn();
      renderPane(fullResponse(), { onOpen });
      const card = await screen.findByTestId("connections-models");
      fireEvent.click(within(card).getByText("Open Models"));
      expect(onOpen).toHaveBeenCalledWith("models");
    });
  });

  /* ── Recheck ── */

  describe("Recheck", () => {
    it("calls recheckProvider and updates the footer", async () => {
      const updated = connectedGithub();
      updated.last_checked_at = "2026-09-04T14:00:00Z";
      mockRecheckProvider.mockResolvedValue(updated);
      const onFooter = vi.fn();
      renderPane(fullResponse(), { onFooter });

      const card = await screen.findByTestId("connections-github");
      fireEvent.click(within(card).getByText("Recheck"));

      await waitFor(() => {
        expect(mockRecheckProvider).toHaveBeenCalledWith("github");
      });
      await waitFor(() => {
        expect(onFooter).toHaveBeenCalled();
        const lastCall = onFooter.mock.calls[onFooter.mock.calls.length - 1][0] as ConnectionsFoot;
        expect(lastCall.egressHost).toBe("github.com");
        expect(lastCall.checkedAt).toBeTruthy();
      });
    });
  });

  /* ── Footer receipt ── */

  describe("Footer", () => {
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
      const response: ConnectionsResponse = {
        tools: [notConfiguredGithub(), emptyJira(), { provider_id: "calendar", state: "not_configured", account: {} }, { provider_id: "models", state: "not_configured", account: {} }],
      };
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
    it("the integrations tile is labeled Connections in the roster", async () => {
      const { PREF_MODULES } = await import("../settingsPrefs");
      const tile = PREF_MODULES.find((m) => m.id === "integrations");
      expect(tile?.label).toBe("Connections");
    });

    it("the applications entry is labeled Connections", async () => {
      const { DESK_APPLICATIONS } = await import("../../../desk/applications");
      const entry = DESK_APPLICATIONS.find(
        (a: { action: string }) => a.action === "configure-integrations",
      );
      expect((entry as { label: string }).label).toBe("Connections");
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
      expect(stateWords("never_checked", "github", {})).toBe("Never checked");
      expect(stateWords("connected", "jira", {})).toBe("Connected");
    });

    it("each card shows its own age, and Never checked", async () => {
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
      expect(within(gh).getByText("Never checked")).toBeInTheDocument();
      expect(within(gh).getByText("Recheck")).toBeInTheDocument();
      const alpha = await screen.findByTestId("connections-jira-conn-alpha-user");
      expect(within(alpha).getByText("Connected · Checked 5 min ago")).toBeInTheDocument();
      const beta = await screen.findByTestId("connections-jira-conn-beta-user");
      expect(within(beta).getByText("Never checked")).toBeInTheDocument();
      const gamma = await screen.findByTestId("connections-confluence-conn-gamma-user");
      expect(within(gamma).getByText("Connected · Checked 3 h ago")).toBeInTheDocument();
      // Calendar and Models are local reads: no age.
      const cal = await screen.findByTestId("connections-calendar");
      expect(within(cal).getByText("Connected")).toBeInTheDocument();
    });
  });
});
