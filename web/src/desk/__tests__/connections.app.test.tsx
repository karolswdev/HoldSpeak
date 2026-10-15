// The Connections app (the test diet, 2026-10-11): the browser tests of the
// Connections face, moved to the real ConnectionsPane and its real read
// (connections/api.ts). Only `fetch` is replaced, and it answers with the
// hub's OWN /api/connections answers, recorded by
// tests/integration/test_desk_connections.py (which proves no fixture field
// is invented: the scar law).
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ConnectionsPane } from "../../pages/cores/connections";
import checkedWire from "./fixtures/connections-wire/connections-checked.json";
import coldWire from "./fixtures/connections-wire/connections-cold.json";

type Json = Record<string, any>;
const clone = <T,>(value: T): T => JSON.parse(JSON.stringify(value));

let wire: Json;
let reads: string[];
beforeEach(() => {
  reads = [];
  vi.stubGlobal("fetch", vi.fn(async (input: string, init?: RequestInit) => {
    const path = new URL(String(input), "http://hub.test").pathname;
    reads.push(`${(init?.method ?? "GET").toUpperCase()} ${path}`);
    const body = path === "/api/connections" ? wire : { error: "not_found" };
    return new Response(JSON.stringify(body), {
      status: path === "/api/connections" ? 200 : 404,
      headers: { "content-type": "application/json" },
    });
  }));
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

/** The words of a card's own state chip (its icon left out). */
function chipWords(card: HTMLElement): string {
  const chip = card.querySelector(".surface-state-chip") as HTMLElement;
  expect(chip, "no state chip").not.toBeNull();
  const icon = chip.querySelector(".surface-state-chip-icon")?.textContent ?? "";
  return (chip.textContent ?? "").slice(icon.length).trim();
}

const tool = (id: string) => wire.tools.find((t: Json) => t.provider_id === id);
const agoIso = (seconds: number) => new Date(Date.now() - seconds * 1000).toISOString();

describe("each card shows its own check age", () => {
  it("GitHub checked now, Jira alpha 2 h ago, Jira beta and Confluence never; Calendar Not set up; Models no age; one read", async () => {
    // replaces: tests/e2e/test_philo9_b1_connections_glass.py::test_each_card_shows_its_own_age
    wire = clone(checkedWire);
    // The recorded answer carries the times of its recording; move them to
    // now so the ages are the ones the hub sent (values only, same fields).
    const gh = tool("github");
    gh.last_checked_at = agoIso(gh.checked_age_seconds ?? 0);
    for (const row of tool("jira").connections) {
      if (row.last_checked_at) row.last_checked_at = agoIso(row.checked_age_seconds);
    }
    render(<ConnectionsPane onFooterUpdate={vi.fn()} onOpenModule={vi.fn()} />);
    const ghCard = await screen.findByTestId("connections-github");
    expect(chipWords(ghCard)).toBe("Connected · Checked now");
    const alphaRef = tool("jira").connections.find((c: Json) => c.account.site === "alpha.atlassian.net").connection_ref;
    const betaRef = tool("jira").connections.find((c: Json) => c.account.site === "beta.atlassian.net").connection_ref;
    expect(chipWords(screen.getByTestId(`connections-jira-conn-${alphaRef}`))).toBe("Connected · Checked 2 h ago");
    expect(chipWords(screen.getByTestId(`connections-jira-conn-${betaRef}`))).toBe("Never checked");
    expect(chipWords(screen.getByTestId("connections-confluence"))).toBe("Never checked");
    expect(chipWords(screen.getByTestId("connections-calendar"))).toBe("Not set up");
    expect(chipWords(screen.getByTestId("connections-models"))).not.toContain("Checked");
    expect(reads).toEqual(["GET /api/connections"]);
  });
});

describe("the empty Jira card says the tool's own state", () => {
  it.each([
    ["acli on PATH", "never_checked", "Never checked"],
    ["acli missing", "unavailable", "acli missing"],
  ])("%s: %s", async (_name, state, words) => {
    // replaces: tests/e2e/test_philo9_b1_connections_glass.py::test_the_empty_jira_card_shows_its_own_state
    // The two states are the hub's own answers for an empty Jira
    // (tests/integration/test_desk_connections.py::test_the_empty_jira_card_is_the_tools_own_state).
    wire = clone(coldWire);
    expect(tool("jira").connections).toEqual([]);
    tool("jira").state = state;
    render(<ConnectionsPane onFooterUpdate={vi.fn()} onOpenModule={vi.fn()} />);
    const card = await screen.findByTestId("connections-jira");
    expect(chipWords(card)).toBe(words);
    expect(within(card).queryByText("Not set up")).toBeNull();
  });
});

// ── fork C2: Recheck redraws the card; a sign-in read from gh's config ──

import recheckGithubWire from "./fixtures/connections-wire/recheck-github.json";
import signedInWire from "./fixtures/connections-wire/connections-signed-in.json";

describe("Recheck asks the hub and the card shows its answer", () => {
  it("a never-checked GitHub card: Recheck posts the route and the card reads Connected · Checked now", async () => {
    // replaces: tests/e2e/test_hs168_connections_glass.py::test_connections_recheck_updates_card
    // (the hub half, a probe that reads Connected: tests/unit/test_philo9_b1_connections.py::test_each_remote_row_returns_its_own_stored_time)
    wire = clone(coldWire);
    const answer = clone(recheckGithubWire) as Json;
    answer.last_checked_at = new Date().toISOString();
    const base = globalThis.fetch;
    vi.stubGlobal("fetch", vi.fn(async (input: string, init?: RequestInit) => {
      const path = new URL(String(input), "http://hub.test").pathname;
      if (path === "/api/connections/github/recheck" && init?.method === "POST") {
        reads.push(`POST ${path}`);
        // Recheck stores this answer. The Accounts refresh GET must read it,
        // rather than replay the cold state that existed before the press.
        wire.tools = wire.tools.map((entry: Json) => entry.provider_id === "github" ? clone(answer) : entry);
        return new Response(JSON.stringify(answer), { status: 200, headers: { "content-type": "application/json" } });
      }
      return base(input, init);
    }));
    const onFooterUpdate = vi.fn();
    render(<ConnectionsPane onFooterUpdate={onFooterUpdate} onOpenModule={vi.fn()} />);
    const card = await screen.findByTestId("connections-github");
    expect(chipWords(card)).toBe("Never checked");
    fireEvent.click(within(card).getByRole("button", { name: /Recheck/ }));
    await screen.findByText(/Connected · Checked now/);
    expect(chipWords(screen.getByTestId("connections-github"))).toBe("Connected · Checked now");
    expect(reads).toContain("POST /api/connections/github/recheck");
    expect(reads.filter((read) => read === "GET /api/connections")).toHaveLength(2);
    const foot = onFooterUpdate.mock.calls.at(-1)?.[0];
    expect(foot.egressHost).toBe("github.com");
    expect(foot.checkedAt).toBeTruthy();
  });
});

describe("a sign-in read from gh's config", () => {
  it("SIGNED IN · karolswdev · FROM GH CONFIG, and no check time anywhere: the footer says NOT CHECKED", async () => {
    // replaces: tests/e2e/test_philo15_18_rest_of_day_glass.py::TestOneSignInTruth::test_first_run_and_connections_say_the_same_sign_in
    // (the Settings › Connections leg; the first-run leg is web/src/desk/firstrun/__tests__/OneScreen.test.tsx;
    // the hub half is tests/unit/test_onboarding_backends.py::test_b31_first_run_and_connections_read_one_gh_sign_in)
    wire = clone(signedInWire);
    expect(tool("github").checked_by).toBe("gh_config");
    const onFooterUpdate = vi.fn();
    render(<ConnectionsPane onFooterUpdate={onFooterUpdate} onOpenModule={vi.fn()} />);
    const card = await screen.findByTestId("connections-github");
    expect(chipWords(card).toUpperCase()).toBe("SIGNED IN · KAROLSWDEV · FROM GH CONFIG");
    expect(card.textContent?.toUpperCase()).not.toContain("NEVER CHECKED");
    expect(card.textContent).not.toMatch(/CHECKED\s+\d/i);
    // No row carries a check time: the footer has none (SettingsCore draws NOT CHECKED).
    expect(onFooterUpdate).toHaveBeenCalledWith({ egressHost: undefined, checkedAt: undefined });
  });
});

describe("the cold Connections face", () => {
  it("an isolated HOME with no gh sign-in draws the GitHub, Calendar and Models cards, GitHub Never checked with its Recheck", async () => {
    // replaces: tests/e2e/test_hs168_connections_glass.py::test_connections_cold_at_both_widths (the cards; the 1440/393 page-error fence is the sweep's surface-settings@integration:destinations case)
    // replaces: tests/e2e/test_hs168_connections_glass.py::test_connections_fold_sign_in_state (an empty GH_CONFIG_DIR: the GitHub card is drawn)
    // The hub's own cold answer (connections-cold.json, recorded and fenced by
    // tests/integration/test_desk_connections.py::test_the_connections_wire_fixtures_carry_no_invented_field).
    wire = clone(coldWire);
    render(<ConnectionsPane onFooterUpdate={vi.fn()} onOpenModule={vi.fn()} />);
    const gh = await screen.findByTestId("connections-github");
    expect(chipWords(gh)).toBe("Never checked");
    expect(within(gh).getByRole("button", { name: /Recheck/ })).toBeTruthy();
    for (const id of ["connections-calendar", "connections-models", "connections-jira", "connections-confluence"])
      expect(screen.getByTestId(id), id).toBeTruthy();
    expect(chipWords(screen.getByTestId("connections-calendar"))).toBe("Not set up");
    expect(reads).toEqual(["GET /api/connections"]);
  });
});
