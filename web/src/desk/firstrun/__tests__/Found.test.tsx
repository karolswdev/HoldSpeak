/* First run C1 — FOUND: #855's stored proposals, one "Use it" press each.
 * A proposal renders with its egress chip; Use it calls the route and the
 * row says IN USE; no proposals -> no section. */
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn() }));
vi.mock("../../../lib/api", () => ({
  apiFetch: mocks.apiFetch,
  readableError: (error: unknown) => (error instanceof Error ? error.message : "Request failed"),
}));

import { Found, useProposals, type DefaultProposal } from "../Found";

function Harness() {
  return <Found proposals={useProposals()} />;
}

const LAN: DefaultProposal = {
  id: "lan:lan-main", label: "qwen3.8-27b", host: "192.168.1.43", lamp: "private_network",
  profile_id: "lan-main", profile_revision: 1, verb: "Use it",
};
const CLOUD: DefaultProposal = {
  id: "cloud:openai", label: "OpenAI", host: "api.openai.com", lamp: "cloud",
  profile_id: "openai", profile_revision: 2, verb: "Use it",
};

let proposals: DefaultProposal[];
const posts: unknown[] = [];

beforeEach(() => {
  proposals = [LAN, CLOUD];
  posts.length = 0;
  mocks.apiFetch.mockReset().mockImplementation(async (path: string, init: { method?: string; json?: unknown } = {}) => {
    if (path === "/api/inference/defaults") return { schema: "InferenceDefaultsState@1", proposals };
    if (path === "/api/inference/defaults/use-proposal" && init.method === "POST") {
      posts.push(init.json);
      return { proposal: (init.json as { proposal_id: string }).proposal_id, assignment: { revision: 1 } };
    }
    throw new Error(`unexpected ${path}`);
  });
});

describe("FOUND", () => {
  it("renders each proposal with the egress chip on its row", async () => {
    render(<Harness />);
    const list = await screen.findByTestId("firstrun-found");
    expect(screen.getByRole("heading", { name: "FOUND" })).toBeTruthy();
    const rows = list.querySelectorAll("[data-testid='firstrun-proposal']");
    expect(rows.length).toBe(2);
    expect(rows[0].textContent).toContain("LAN SERVER");
    expect(rows[0].querySelector(".gadget-chip-egress")?.textContent).toBe("192.168.1.43 · LAN");
    expect(rows[1].textContent).toContain("KEY SET");
    expect(rows[1].textContent).toContain("$");
    expect(rows[1].querySelector(".gadget-chip-egress")?.textContent).toBe("API.OPENAI.COM");
    expect(rows[1].querySelector(".gadget-chip-egress")?.getAttribute("data-scope")).toBe("cloud");
  });

  it("Use it calls the route and the row says IN USE", async () => {
    render(<Harness />);
    const use = await screen.findByRole("button", { name: "Use qwen3.8-27b" });
    await act(async () => {
      fireEvent.click(use);
    });
    expect(posts).toEqual([{ proposal_id: "lan:lan-main" }]);
    await waitFor(() => expect(screen.getByRole("status", { name: "IN USE · DEFAULT" })).toBeTruthy());
    expect(screen.queryByRole("button", { name: "Use qwen3.8-27b" })).toBeNull();
    // The other row is still a choice.
    expect(screen.getByRole("button", { name: "Use OpenAI" })).toBeTruthy();
  });

  it("names a refused press on its row", async () => {
    mocks.apiFetch.mockImplementation(async (path: string, init: { method?: string } = {}) => {
      if (init.method === "POST") throw new Error("This engine has no model profile revision.");
      return { proposals };
    });
    render(<Harness />);
    const use = await screen.findByRole("button", { name: "Use qwen3.8-27b" });
    await act(async () => {
      fireEvent.click(use);
    });
    expect(await screen.findByRole("status", { name: "NOT IN USE" })).toBeTruthy();
    expect(screen.getByText("This engine has no model profile revision.")).toBeTruthy();
  });

  it("draws no section when there is no proposal", async () => {
    proposals = [];
    const { container } = render(<Harness />);
    await waitFor(() => expect(mocks.apiFetch).toHaveBeenCalled());
    await act(async () => undefined);
    expect(screen.queryByRole("heading", { name: "FOUND" })).toBeNull();
    expect(container.textContent).toBe("");
  });
});
