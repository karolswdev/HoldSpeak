// Service reads and rechecks use recorded hub answers. No provider runs.
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { useState } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ConnectionsPane } from "../../pages/cores/connections";
import { AddAccountFields } from "../../pages/cores/connections/ConnectionsPane";
import checkedWire from "./fixtures/connections-wire/connections-checked.json";
import recheckGithubWire from "./fixtures/connections-wire/recheck-github.json";
type Json = Record<string, any>;
const clone = <T,>(value: T): T => JSON.parse(JSON.stringify(value));
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });
function serve({ stale = false, failCheck = false, refuseAdd = false } = {}) {
  const wire = clone(checkedWire) as Json;
  const calls: string[] = [];
  wire.tools = wire.tools.map((tool: Json) => ({ ...tool, checked_age_seconds: stale && tool.provider_id === "github" ? 301 : 0, ...(tool.connections ? { connections: tool.connections.map((row: Json) => ({ ...row, checked_age_seconds: 0 })) } : {}) }));
  let checkFailure = failCheck;
  vi.stubGlobal("fetch", vi.fn(async (input: string, init?: RequestInit) => {
    const path = new URL(String(input), "http://hub.test").pathname;
    const method = init?.method ?? "GET";
    calls.push(`${method} ${path}`);
    if (path.endsWith("/recheck")) {
      if (checkFailure) { checkFailure = false; throw new TypeError("No connection"); }
      return new Response(JSON.stringify(recheckGithubWire), { status: 200, headers: { "content-type": "application/json" } });
    }
    if (method === "POST" && path === "/api/providers/jira/connections") {
      return new Response(JSON.stringify(refuseAdd ? { error: "Account refused" } : { success: true }), { status: refuseAdd ? 409 : 200, headers: { "content-type": "application/json" } });
    }
    return new Response(JSON.stringify(wire), { status: 200, headers: { "content-type": "application/json" } });
  }));
  return calls;
}
describe("Services in the OS list grammar", () => {
  it("reads stale accounts without a probe and checks only the selection on a press", async () => {
    const calls = serve({ stale: true });
    render(<ConnectionsPane onFooterUpdate={vi.fn()} />);
    await screen.findByRole("grid", { name: "Services" });
    expect(calls.filter((call) => call.endsWith("/recheck"))).toEqual([]);
    expect(screen.getByRole("button", { name: "Check" })).toBeDisabled();
    expect(document.querySelectorAll('[role=row] button')).toHaveLength(0);
    expect(screen.getByRole("button", { name: "Sign in…" })).toBeDisabled();
    fireEvent.click(screen.getByText("GitHub"));
    expect(screen.getByRole("button", { name: "Sign in…" })).toBeEnabled();
    fireEvent.click(screen.getByRole("button", { name: "Check" }));
    await waitFor(() => expect(calls.filter((call) => call.endsWith("/recheck"))).toEqual(["POST /api/connections/github/recheck"]));
  });
  it("keeps a failed explicit check available for Retry without probing on open", async () => {
    const calls = serve({ stale: true, failCheck: true });
    render(<ConnectionsPane onFooterUpdate={vi.fn()} />);
    await screen.findByText("GitHub");
    expect(calls.filter((call) => call.endsWith("/recheck"))).toEqual([]);
    fireEvent.click(screen.getByText("GitHub"));
    fireEvent.click(screen.getByRole("button", { name: "Check" }));
    await screen.findByRole("alert");
    expect(screen.getByRole("alert")).toHaveTextContent("No connection");
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await waitFor(() => expect(calls.filter((call) => call.endsWith("/recheck"))).toEqual(["POST /api/connections/github/recheck", "POST /api/connections/github/recheck"]));
    await waitFor(() => expect(screen.queryByRole("alert")).toBeNull());
  });
  it("a refused Add retains the account draft in its inspector", async () => {
    serve({ refuseAdd: true }); render(<ConnectionsPane onFooterUpdate={vi.fn()} />);
    await screen.findByText("GitHub");
    fireEvent.click(screen.getByRole("button", { name: "Add account" }));
    fireEvent.click(screen.getByRole("menuitem", { name: "Jira" }));
    const site = screen.getByRole("textbox", { name: "Site" });
    const email = screen.getByRole("textbox", { name: "Email" });
    fireEvent.change(site, { target: { value: "alpha.atlassian.net" } });
    fireEvent.change(email, { target: { value: "owner@example.com" } });
    fireEvent.click(screen.getByRole("button", { name: "Add" }));
    await screen.findByRole("button", { name: "Retry" });
    expect(site).toHaveValue("alpha.atlassian.net"); expect(email).toHaveValue("owner@example.com");
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
