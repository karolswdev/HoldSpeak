// Conductor R7 (canvas K7a, RATIFIED 2026-10-07): Settings › People — People MCP access.
// (1) "Yes": the module as drawn; (2) "Of course it should, buddy!": the strip is disabled
// while HOLDSPEAK_MCP_PEOPLE_ACCESS overrides the setting.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { PeopleAccessModule, PeopleHubCells } from "../settingsPeople";

type Answer = { status: number; body: unknown };
let getAnswer: () => Answer;
let putAnswer: (body: Record<string, unknown>) => Answer;
let puts: Record<string, unknown>[];

beforeEach(() => {
  puts = [];
  getAnswer = () => ({ status: 200, body: { mode: "write", effective: "write", source: "config", env_var: null, agents: "read" } });
  putAnswer = (body) => ({
    status: 200,
    body: { mode: body.mode, effective: body.mode, source: "config", env_var: null,
            agents: body.mode === "off" ? "off" : "read", operation_id: "op_1", receipt: { outcome: "succeeded" } },
  });
  vi.stubGlobal("fetch", vi.fn(async (url: string, init?: RequestInit) => {
    const method = (init?.method || "GET").toUpperCase();
    let answer: Answer;
    if (method === "PUT") {
      const body = JSON.parse(String(init?.body || "{}"));
      puts.push(body);
      answer = putAnswer(body);
    } else answer = getAnswer();
    return new Response(JSON.stringify(answer.body), { status: answer.status, headers: { "content-type": "application/json" } });
  }));
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

const strip = () => screen.getByRole("group", { name: "People MCP access" });

describe("Settings › People", () => {
  it("shows OFF / READ / WRITE with the setting pressed, AGENTS · READ and SOURCE · SETTING", async () => {
    render(<PeopleAccessModule />);
    await screen.findByTestId("people-access-agents");
    const tokens = within(strip()).getAllByRole("button");
    expect(tokens.map((t) => t.textContent)).toEqual(["OFF", "READ", "WRITE"]);
    expect(within(strip()).getByRole("button", { name: "WRITE" }).getAttribute("aria-pressed")).toBe("true");
    expect(screen.getByTestId("people-access-agents").textContent).toBe("AGENTS · READ");
    expect(screen.getByTestId("people-access-source").textContent).toBe("SOURCE · SETTING");
    expect(tokens.every((t) => !(t as HTMLButtonElement).disabled)).toBe(true);
  });

  it("a press PUTs the mode and shows the operation's receipt and AGENTS · OFF", async () => {
    render(<PeopleAccessModule />);
    await screen.findByTestId("people-access-agents");
    fireEvent.click(within(strip()).getByRole("button", { name: "OFF" }));
    await waitFor(() => expect(screen.getByTestId("people-access-agents").textContent).toBe("AGENTS · OFF"));
    expect(puts).toEqual([{ mode: "off" }]);
    const receipt = screen.getByTestId("people-access-receipt");
    expect(receipt.getAttribute("data-outcome")).toBe("succeeded");
    expect(receipt.getAttribute("data-operation-id")).toBe("op_1");
    expect(receipt.textContent).toContain("SUCCEEDED");
    expect(receipt.textContent).toContain("ACCESS · OFF");
  });

  it("is disabled while the variable overrides the setting, and names it", async () => {
    getAnswer = () => ({ status: 200, body: { mode: "write", effective: "off", source: "env",
                                             env_var: "HOLDSPEAK_MCP_PEOPLE_ACCESS", agents: "off" } });
    render(<PeopleAccessModule />);
    await screen.findByTestId("people-access-agents");
    const tokens = within(strip()).getAllByRole("button") as HTMLButtonElement[];
    expect(tokens.every((t) => t.disabled)).toBe(true);
    expect(within(strip()).getByRole("button", { name: "OFF" }).getAttribute("aria-pressed")).toBe("true");
    expect(screen.getByTestId("people-access-source").textContent).toBe("SOURCE · HOLDSPEAK_MCP_PEOPLE_ACCESS");
    expect(screen.getByTestId("people-access-agents").textContent).toBe("AGENTS · OFF");
    fireEvent.click(tokens[1]);
    expect(puts).toEqual([]);
  });

  it("a refused press shows REFUSED with its code", async () => {
    putAnswer = () => ({ status: 409, body: { success: false, code: "people_access_env_override", operation_id: "op_2" } });
    render(<PeopleAccessModule />);
    await screen.findByTestId("people-access-agents");
    fireEvent.click(within(strip()).getByRole("button", { name: "READ" }));
    const receipt = await screen.findByTestId("people-access-receipt");
    expect(receipt.getAttribute("data-outcome")).toBe("refused");
    expect(receipt.textContent).toContain("REFUSED");
    expect(receipt.textContent).toContain("PEOPLE_ACCESS_ENV_OVERRIDE");
  });

  it("the hub row's cells read MCP · <effective> and AGENTS · <mode>", async () => {
    render(<PeopleHubCells />);
    await screen.findByText("MCP · WRITE");
    expect(screen.getByText("AGENTS · READ")).toBeTruthy();
  });

  // Astra round 1 on #919, finding 2 (her probe, ported): a read failure is its own state.
  it("keeps the refusal receipt when the refresh after a refused press fails", async () => {
    render(<PeopleAccessModule />);
    await screen.findByTestId("people-access-agents");
    getAnswer = () => ({ status: 503, body: { code: "unavailable" } });
    putAnswer = () => ({ status: 409, body: { code: "people_access_env_override", operation_id: "op_review" } });
    fireEvent.click(within(strip()).getByRole("button", { name: "OFF" }));
    await waitFor(() => expect(screen.queryByTestId("people-access-agents")).toBeNull());
    expect(screen.getByTestId("people-access-receipt").textContent).toContain("PEOPLE_ACCESS_ENV_OVERRIDE");
    const failed = screen.getByTestId("people-access-read-failed");
    expect(failed.textContent).toContain("READ FAILED");
    expect(failed.getAttribute("data-code")).toBe("unavailable");
  });

  it("names an initial read failure and reads again on Retry", async () => {
    getAnswer = () => ({ status: 503, body: { code: "unavailable" } });
    render(<PeopleAccessModule />);
    const failed = await screen.findByTestId("people-access-read-failed");
    expect(failed.textContent).toContain("READ FAILED");
    expect(failed.textContent).toContain("UNAVAILABLE");
    expect(screen.queryByRole("group", { name: "People MCP access" })).toBeNull();
    getAnswer = () => ({ status: 200, body: { mode: "write", effective: "write", source: "config", env_var: null, agents: "read" } });
    fireEvent.click(within(failed).getByRole("button", { name: "Retry" }));
    await screen.findByTestId("people-access-agents");
    expect(screen.queryByTestId("people-access-read-failed")).toBeNull();
    expect(strip()).toBeTruthy();
  });
});
