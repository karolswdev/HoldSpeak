// Conductor R7 (canvas K7a, RATIFIED 2026-10-07): Settings › People — People MCP access.
// (1) "Yes": the module as drawn; (2) "Of course it should, buddy!": the strip is disabled
// while HOLDSPEAK_MCP_PEOPLE_ACCESS overrides the setting.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { PeopleAccessModule } from "../settings/People";

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

const strip = () => screen.getByRole("combobox", { name: "Agent access" });

describe("Settings › People", () => {
  it("shows Off / Read / Read and write (PHILO-17 U35 plain words) with the setting pressed, agents READ and SOURCE · SETTING", async () => {
    render(<PeopleAccessModule />);
    await screen.findByTestId("people-access-agents");
    const tokens = within(strip()).getAllByRole("option");
    expect(tokens.map((t) => t.textContent)).toEqual(["Off", "Read", "Read and write"]);
    expect(screen.getByText("Agent access")).toBeTruthy();
    expect(strip()).toHaveValue("write");
    expect(screen.getByTestId("people-access-agents").textContent).toBe("Read");
    expect(screen.queryByTestId("people-access-source")).toBeNull();
    expect(strip()).not.toBeDisabled();
  });

  it("a press PUTs the mode and shows the operation's receipt and AGENTS · OFF", async () => {
    render(<PeopleAccessModule />);
    await screen.findByTestId("people-access-agents");
    fireEvent.change(strip(), {target: {value:"off"}});
    await waitFor(() => expect(screen.getByTestId("people-access-agents").textContent).toBe("Off"));
    expect(puts).toEqual([{ mode: "off" }]);
    const receipt = screen.getByTestId("people-access-receipt");
    expect(receipt.getAttribute("data-outcome")).toBe("succeeded");
    expect(receipt.getAttribute("data-operation-id")).toBe("op_1");
    expect(receipt.textContent).toContain("Saved · Off");
    expect(receipt.querySelectorAll(".gadget-state").length).toBeLessThanOrEqual(1);
  });

  it("is disabled while the variable overrides the setting, and names it", async () => {
    getAnswer = () => ({ status: 200, body: { mode: "write", effective: "off", source: "env",
                                             env_var: "HOLDSPEAK_MCP_PEOPLE_ACCESS", agents: "off" } });
    render(<PeopleAccessModule />);
    await screen.findByTestId("people-access-agents");
    expect(strip()).toBeDisabled();
    expect(strip()).toHaveValue("off");
    expect(screen.getByTestId("people-access-source").textContent).toBe("Set by environment");
    expect(screen.getByTestId("people-access-agents").textContent).toBe("Off");
    fireEvent.click(strip());
    expect(puts).toEqual([]);
  });

  it("a refused press shows REFUSED with its code", async () => {
    putAnswer = () => ({ status: 409, body: { success: false, code: "people_access_env_override", operation_id: "op_2" } });
    render(<PeopleAccessModule />);
    await screen.findByTestId("people-access-agents");
    fireEvent.change(strip(), {target: {value:"read"}});
    const receipt = await screen.findByTestId("people-access-receipt");
    expect(receipt.getAttribute("data-outcome")).toBe("refused");
    expect(receipt.textContent).toContain("Not saved");
    expect(receipt.textContent).toContain("Set by environment");
  });

  // Astra round 1 on #919, finding 2 (her probe, ported): a read failure is its own state.
  it("keeps the refusal receipt when the refresh after a refused press fails", async () => {
    render(<PeopleAccessModule />);
    await screen.findByTestId("people-access-agents");
    getAnswer = () => ({ status: 503, body: { code: "unavailable" } });
    putAnswer = () => ({ status: 409, body: { code: "people_access_env_override", operation_id: "op_review" } });
    fireEvent.change(strip(), {target: {value:"off"}});
    await waitFor(() => expect(screen.queryByTestId("people-access-agents")).toBeNull());
    expect(screen.getByTestId("people-access-receipt").textContent).toContain("Set by environment");
    const failed = screen.getByTestId("people-access-read-failed");
    expect(failed.textContent).toContain("Read failed");
    expect(failed.getAttribute("data-code")).toBe("unavailable");
  });

  it("names an initial read failure and reads again on Retry", async () => {
    getAnswer = () => ({ status: 503, body: { code: "unavailable" } });
    render(<PeopleAccessModule />);
    const failed = await screen.findByTestId("people-access-read-failed");
    expect(failed.textContent).toContain("Read failed");
    expect(failed.textContent).toContain("Unavailable");
    expect(screen.queryByRole("combobox", { name: "Agent access" })).toBeNull();
    getAnswer = () => ({ status: 200, body: { mode: "write", effective: "write", source: "config", env_var: null, agents: "read" } });
    fireEvent.click(within(failed).getByRole("button", { name: "Retry" }));
    await screen.findByTestId("people-access-agents");
    expect(screen.queryByTestId("people-access-read-failed")).toBeNull();
    expect(strip()).toBeTruthy();
  });
});
