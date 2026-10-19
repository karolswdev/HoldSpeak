// The Connections app (the test diet, 2026-10-11): the browser tests of the
// Connections face, moved to the real ConnectionsPane and its real read
// (connections/api.ts). Only `fetch` is replaced, and it answers with the
// hub's OWN /api/connections answers, recorded by
// tests/integration/test_desk_connections.py (which proves no fixture field
// is invented: the scar law).
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { useState } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ConnectionsPane } from "../../pages/cores/connections";
import { AddAccountFields } from "../../pages/cores/connections/ConnectionsPane";
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
    expect(chipWords(ghCard)).toBe("Works · Checked now");
    const alphaRef = tool("jira").connections.find((c: Json) => c.account.site === "alpha.atlassian.net").connection_ref;
    const betaRef = tool("jira").connections.find((c: Json) => c.account.site === "beta.atlassian.net").connection_ref;
    expect(chipWords(screen.getByTestId(`connections-jira-conn-${alphaRef}`))).toBe("Works · Checked 2 h ago");
    expect(chipWords(screen.getByTestId(`connections-jira-conn-${betaRef}`))).toBe("Not checked");
    expect(chipWords(screen.getByTestId("connections-confluence"))).toBe("Not checked");
    expect(chipWords(screen.getByTestId("connections-calendar"))).toBe("Not set up");
    // Engines has its own home; Found reads account files without a CLI.
    expect(screen.queryByTestId("connections-models")).toBeNull();
    expect([...reads].sort()).toEqual(["GET /api/connections", "GET /api/onboarding/connections"]);
  });
});

describe("the empty Jira card says the tool's own state", () => {
  it.each([
    ["acli on PATH", "never_checked", "Not checked"],
    ["acli missing", "unavailable", "Could not check: acli is not installed"],
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
  it("a never-checked GitHub card: Check posts the route and the card reads Works · Checked now", async () => {
    // replaces: tests/e2e/test_hs168_connections_glass.py::test_connections_recheck_updates_card
    // (the hub half, a probe that reads Works: tests/unit/test_philo9_b1_connections.py::test_each_remote_row_returns_its_own_stored_time)
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
    expect(chipWords(card)).toBe("Not checked");
    fireEvent.click(within(card).getByRole("button", { name: "Check" }));
    await screen.findByText(/Works · Checked now/);
    expect(chipWords(screen.getByTestId("connections-github"))).toBe("Works · Checked now");
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
  it("a cold HOME draws account and Calendar cards, with GitHub Not checked and Check", async () => {
    // replaces: tests/e2e/test_hs168_connections_glass.py::test_connections_cold_at_both_widths (the cards; the 1440/393 page-error fence is the sweep's surface-settings@integration:destinations case)
    // replaces: tests/e2e/test_hs168_connections_glass.py::test_connections_fold_sign_in_state (an empty GH_CONFIG_DIR: the GitHub card is drawn)
    // The hub's own cold answer (connections-cold.json, recorded and fenced by
    // tests/integration/test_desk_connections.py::test_the_connections_wire_fixtures_carry_no_invented_field).
    wire = clone(coldWire);
    render(<ConnectionsPane onFooterUpdate={vi.fn()} onOpenModule={vi.fn()} />);
    const gh = await screen.findByTestId("connections-github");
    expect(chipWords(gh)).toBe("Not checked");
    expect(within(gh).getByRole("button", { name: "Check" })).toBeTruthy();
    for (const id of ["connections-calendar", "connections-jira", "connections-confluence"])
      expect(screen.getByTestId(id), id).toBeTruthy();
    expect(screen.queryByTestId("connections-models")).toBeNull();
    expect(screen.getByTestId("connections-add-open-jira").closest(".surface-ledger-row"))
      .toBe(screen.getByTestId("connections-jira").closest(".surface-ledger-row"));
    expect(chipWords(screen.getByTestId("connections-calendar"))).toBe("Not set up");
    // Betterment ST2: plus the Found read (gh and acli files only, no CLI).
    expect([...reads].sort()).toEqual(["GET /api/connections", "GET /api/onboarding/connections"]);
  });
});

describe("account rows keep their status and actions together", () => {
  it.each(["jira", "confluence"])("keeps the empty %s Add form and refusal across Cancel/reopen", async (provider) => {
    wire = clone(coldWire);
    const base = globalThis.fetch;
    vi.stubGlobal("fetch", vi.fn(async (input: string, init?: RequestInit) => {
      const path = new URL(String(input), "http://hub.test").pathname;
      if (path === `/api/providers/${provider}/connections` && init?.method === "POST") {
        reads.push(`POST ${path}`);
        throw new Error("Add refused");
      }
      return base(input, init);
    }));
    render(<ConnectionsPane onFooterUpdate={vi.fn()} onOpenModule={vi.fn()} />);
    fireEvent.click(await screen.findByTestId(`connections-add-open-${provider}`));
    const form = screen.getByTestId(`connections-add-${provider}`);
    fireEvent.change(within(form).getByRole("textbox", { name: "Site" }), { target: { value: "draft.atlassian.net" } });
    fireEvent.change(within(form).getByRole("textbox", { name: "Email" }), { target: { value: "draft@example.com" } });
    fireEvent.click(within(form).getByRole("button", { name: "Add" }));
    await within(form).findByText("Account not added");
    fireEvent.click(within(form).getByRole("button", { name: "Cancel" }));
    expect(screen.getByTestId(`connections-add-${provider}`)).toBe(form);
    expect(form).not.toBeVisible();
    expect(screen.queryByRole("textbox", { name: "Site" })).toBeNull();
    fireEvent.click(screen.getByTestId(`connections-add-open-${provider}`));
    expect(screen.getByTestId(`connections-add-${provider}`)).toBe(form);
    expect(within(form).getByText("Account not added")).toBeVisible();
    expect(within(form).getByRole("button", { name: "Retry" })).toBeVisible();
    expect((within(form).getByRole("textbox", { name: "Site" }) as HTMLInputElement).value).toBe("draft.atlassian.net");
    expect((within(form).getByRole("textbox", { name: "Email" }) as HTMLInputElement).value).toBe("draft@example.com");
  });

  it("uses wrapping state chips and puts Add in the last provider account row", async () => {
    wire = clone(checkedWire);
    render(<ConnectionsPane onFooterUpdate={vi.fn()} onOpenModule={vi.fn()} />);
    await screen.findByTestId("connections-github");
    for (const chip of document.querySelectorAll(".connections-pane .surface-state-chip")) {
      expect(chip.hasAttribute("data-wrap")).toBe(true);
    }
    const rows = tool("jira").connections;
    const first = screen.getByTestId(`connections-jira-conn-${rows[0].connection_ref}`);
    const last = screen.getByTestId(`connections-jira-conn-${rows.at(-1).connection_ref}`);
    const add = screen.getByTestId("connections-add-open-jira");
    expect(add.closest(".surface-ledger-row")).toBe(last.closest(".surface-ledger-row"));
    expect(within(first).queryByRole("button", { name: "Add Jira account" })).toBeNull();
    expect(within(last).getByRole("button", { name: "Check" })).toBeTruthy();
    expect(document.querySelector(".connections-add-account")).toBeNull();
  });

  it("keeps Add drafts on Cancel and when switching to sign-in in the same row", async () => {
    wire = clone(checkedWire);
    const last = tool("jira").connections.at(-1);
    last.state = "owner_action_required";
    render(<ConnectionsPane onFooterUpdate={vi.fn()} onOpenModule={vi.fn()} />);
    const row = await screen.findByTestId(`connections-jira-conn-${last.connection_ref}`);
    fireEvent.click(screen.getByTestId("connections-add-open-jira"));
    let form = screen.getByTestId("connections-add-jira");
    expect(form.closest(".surface-ledger-row")).toBe(row.closest(".surface-ledger-row"));
    fireEvent.change(within(form).getByRole("textbox", { name: "Site" }), { target: { value: "draft.atlassian.net" } });
    fireEvent.change(within(form).getByRole("textbox", { name: "Email" }), { target: { value: "draft@example.com" } });
    fireEvent.click(within(form).getByRole("button", { name: "Cancel" }));
    expect(screen.getByTestId("connections-add-jira")).toBe(form);
    expect(form).not.toBeVisible();
    expect(within(row.closest(".surface-ledger-row") as HTMLElement).queryByRole("textbox", { name: "Site" })).toBeNull();
    fireEvent.click(screen.getByTestId("connections-add-open-jira"));
    expect(screen.getByTestId("connections-add-jira")).toBe(form);
    expect((within(form).getByRole("textbox", { name: "Site" }) as HTMLInputElement).value).toBe("draft.atlassian.net");
    fireEvent.click(within(row).getByRole("button", { name: "Sign in" }));
    expect(screen.getByTestId("connections-add-jira")).toBe(form);
    expect(form).not.toBeVisible();
    expect(within(row.closest(".surface-ledger-row") as HTMLElement).queryByRole("textbox", { name: "Site" })).toBeNull();
    expect(within(row.closest(".surface-ledger-row") as HTMLElement).getByText(`acli jira auth login --site ${last.account.site} --email ${last.account.email} --token`)).toBeTruthy();
    fireEvent.click(screen.getByTestId("connections-add-open-jira"));
    expect(screen.getByTestId("connections-add-jira")).toBe(form);
    expect(form).toBeVisible();
    expect((within(form).getByRole("textbox", { name: "Email" }) as HTMLInputElement).value).toBe("draft@example.com");
    // Betterment ST2: plus the Found read (gh and acli files only, no CLI).
    expect([...reads].sort()).toEqual(["GET /api/connections", "GET /api/onboarding/connections"]);
  });
});

describe("account writers retain their existing routes and results", () => {
  it("Recheck uses the provider route and marks only the selected account busy", async () => {
    wire = clone(checkedWire);
    const base = globalThis.fetch;
    let finish!: (response: Response) => void;
    const submissions: Json[] = [];
    vi.stubGlobal("fetch", vi.fn(async (input: string, init?: RequestInit) => {
      const path = new URL(String(input), "http://hub.test").pathname;
      if (path === "/api/connections/jira/recheck" && init?.method === "POST") {
        reads.push(`POST ${path}`);
        submissions.push(JSON.parse(String(init.body)));
        return new Promise<Response>((resolve) => { finish = resolve; });
      }
      return base(input, init);
    }));
    render(<ConnectionsPane onFooterUpdate={vi.fn()} onOpenModule={vi.fn()} />);
    const rows = tool("jira").connections;
    const first = await screen.findByTestId(`connections-jira-conn-${rows[0].connection_ref}`);
    const last = screen.getByTestId(`connections-jira-conn-${rows.at(-1).connection_ref}`);
    const recheck = within(last).getByRole("button", { name: "Check" }) as HTMLButtonElement;
    fireEvent.click(recheck);
    expect(recheck.disabled).toBe(true);
    expect(recheck).toHaveAttribute("aria-busy", "true");
    const peer = within(first).getByRole("button", { name: "Check" });
    expect(peer).toBeDisabled();
    expect(peer).not.toHaveAttribute("aria-busy", "true");
    fireEvent.click(peer);
    expect(reads.filter((read) => read.startsWith("POST"))).toEqual(["POST /api/connections/jira/recheck"]);
    expect(submissions).toEqual([{ ref: rows.at(-1).connection_ref }]);
    await act(async () => { finish(new Response(JSON.stringify(tool("jira")), { status: 200, headers: { "content-type": "application/json" } })); });
    await waitFor(() => expect(recheck.disabled).toBe(false));
    expect(reads.filter((read) => read.startsWith("POST"))).toEqual(["POST /api/connections/jira/recheck"]);
  });

  it("a refused Add keeps the draft for Retry; acceptance refreshes accounts and checks the provider", async () => {
    wire = clone(checkedWire);
    const recordedJira = clone(tool("jira"));
    const added = recordedJira.connections.at(-1);
    tool("jira").connections = [tool("jira").connections[0]];
    tool("jira").connections[0].state = "owner_action_required";
    const base = globalThis.fetch;
    const submissions: Json[] = [];
    vi.stubGlobal("fetch", vi.fn(async (input: string, init?: RequestInit) => {
      const path = new URL(String(input), "http://hub.test").pathname;
      if (path === "/api/providers/jira/connections" && init?.method === "POST") {
        reads.push(`POST ${path}`);
        submissions.push(JSON.parse(String(init.body)));
        if (submissions.length === 1) throw new Error("Add refused");
        wire.tools = wire.tools.map((entry: Json) => entry.provider_id === "jira" ? clone(recordedJira) : entry);
        // The Add client consumes no response fields. Its following GET and
        // Recheck replay the recorded hub answer, including the added row.
        return new Response(null, { status: 200 });
      }
      if (path === "/api/connections/jira/recheck" && init?.method === "POST") {
        reads.push(`POST ${path}`);
        return new Response(JSON.stringify(recordedJira), { status: 200, headers: { "content-type": "application/json" } });
      }
      return base(input, init);
    }));
    render(<ConnectionsPane onFooterUpdate={vi.fn()} onOpenModule={vi.fn()} />);
    fireEvent.click(await screen.findByTestId("connections-add-open-jira"));
    let form = screen.getByTestId("connections-add-jira");
    fireEvent.change(within(form).getByRole("textbox", { name: "Site" }), { target: { value: added.account.site } });
    fireEvent.change(within(form).getByRole("textbox", { name: "Email" }), { target: { value: added.account.email } });
    fireEvent.click(within(form).getByRole("button", { name: "Add" }));
    await within(form).findByText("Account not added");
    expect((within(form).getByRole("textbox", { name: "Site" }) as HTMLInputElement).value).toBe(added.account.site);
    expect((within(form).getByRole("textbox", { name: "Email" }) as HTMLInputElement).value).toBe(added.account.email);
    const existing = screen.getByTestId(`connections-jira-conn-${recordedJira.connections[0].connection_ref}`);
    fireEvent.click(within(existing).getByRole("button", { name: "Sign in" }));
    expect(form).not.toBeVisible();
    expect(within(existing.closest(".surface-ledger-row") as HTMLElement).queryByRole("textbox", { name: "Site" })).toBeNull();
    fireEvent.click(screen.getByTestId("connections-add-open-jira"));
    expect(screen.getByTestId("connections-add-jira")).toBe(form);
    expect(within(form).getByText("Account not added")).toBeVisible();
    fireEvent.click(within(form).getByRole("button", { name: "Retry" }));
    await screen.findByTestId(`connections-jira-conn-${added.connection_ref}`);
    await waitFor(() => {
      form = screen.getByTestId("connections-add-jira");
      expect((within(form).getByRole("textbox", { name: "Site" }) as HTMLInputElement).value).toBe("");
      expect((within(form).getByRole("textbox", { name: "Email" }) as HTMLInputElement).value).toBe("");
    });
    expect(submissions).toEqual([
      { site: added.account.site, email: added.account.email },
      { site: added.account.site, email: added.account.email },
    ]);
    expect(reads).toContain("POST /api/connections/jira/recheck");
    expect(form.closest(".surface-ledger-row")).toBe(screen.getByTestId(`connections-jira-conn-${added.connection_ref}`).closest(".surface-ledger-row"));
  });

  it("a failed Recheck offers Retry and redraws the recovered hub state", async () => {
    wire = clone(coldWire);
    const answer = clone(recheckGithubWire) as Json;
    answer.last_checked_at = new Date().toISOString();
    const base = globalThis.fetch;
    let attempts = 0;
    vi.stubGlobal("fetch", vi.fn(async (input: string, init?: RequestInit) => {
      const path = new URL(String(input), "http://hub.test").pathname;
      if (path === "/api/connections/github/recheck" && init?.method === "POST") {
        reads.push(`POST ${path}`);
        if (++attempts === 1) throw new Error("Check refused");
        wire.tools = wire.tools.map((entry: Json) => entry.provider_id === "github" ? clone(answer) : entry);
        return new Response(JSON.stringify(answer), { status: 200, headers: { "content-type": "application/json" } });
      }
      return base(input, init);
    }));
    render(<ConnectionsPane onFooterUpdate={vi.fn()} onOpenModule={vi.fn()} />);
    const card = await screen.findByTestId("connections-github");
    fireEvent.click(within(card).getByRole("button", { name: "Check" }));
    const alert = await screen.findByRole("alert");
    expect(within(alert).getByText("Check failed")).toBeTruthy();
    fireEvent.click(within(alert).getByRole("button", { name: "Check" }));
    await screen.findByText("Works · Checked now");
    expect(screen.queryByRole("alert")).toBeNull();
    expect(attempts).toBe(2);
  });
});

describe("Add input custody", () => {
  it("keeps local field defaults for callers without a controlled draft", async () => {
    const onAdd = vi.fn().mockRejectedValueOnce(new Error("Add refused"));
    render(<AddAccountFields provider="confluence" onAdd={onAdd} />);
    const site = screen.getByRole("textbox", { name: "Site" }) as HTMLInputElement;
    const email = screen.getByRole("textbox", { name: "Email" }) as HTMLInputElement;
    fireEvent.change(site, { target: { value: "alpha.atlassian.net" } });
    fireEvent.change(email, { target: { value: "owner@example.com" } });
    fireEvent.click(screen.getByRole("button", { name: "Add" }));
    await screen.findByText("Account not added");
    expect(site.value).toBe("alpha.atlassian.net");
    expect(email.value).toBe("owner@example.com");
    onAdd.mockResolvedValueOnce(undefined);
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await waitFor(() => expect(site.value).toBe(""));
    expect(email.value).toBe("");
    expect(onAdd).toHaveBeenCalledWith("alpha.atlassian.net", "owner@example.com");
  });

  it("clears accepted submitted values and preserves edits made while Add is pending", async () => {
    let finish!: () => void;
    const onAdd = vi.fn(() => new Promise<void>((resolve) => { finish = resolve; }));
    function DraftFields() {
      const [draft, setDraft] = useState({ site: "alpha.atlassian.net", email: "owner@example.com" });
      return <AddAccountFields compact provider="jira" onAdd={onAdd} draft={draft} onDraftChange={setDraft} />;
    }
    render(<DraftFields />);
    const site = screen.getByRole("textbox", { name: "Site" }) as HTMLInputElement;
    const email = screen.getByRole("textbox", { name: "Email" }) as HTMLInputElement;
    const add = screen.getByRole("button", { name: "Add" }) as HTMLButtonElement;
    fireEvent.click(add);
    expect(onAdd).toHaveBeenCalledWith("alpha.atlassian.net", "owner@example.com");
    expect(add.disabled).toBe(true);
    fireEvent.change(site, { target: { value: "newer.atlassian.net" } });
    fireEvent.change(email, { target: { value: "newer@example.com" } });
    await act(async () => { finish(); });
    expect(site.value).toBe("newer.atlassian.net");
    expect(email.value).toBe("newer@example.com");
    onAdd.mockResolvedValueOnce(undefined);
    fireEvent.click(add);
    await waitFor(() => expect(site.value).toBe(""));
    expect(email.value).toBe("");
    expect(onAdd.mock.calls).toEqual([
      ["alpha.atlassian.net", "owner@example.com"],
      ["newer.atlassian.net", "newer@example.com"],
    ]);
  });
});
