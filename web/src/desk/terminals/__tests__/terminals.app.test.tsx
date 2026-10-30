import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { TerminalsCore } from "../TerminalsCore";
import { refreshTerminalInventory } from "../windows";
import fixture from "./fixtures/sessions.recorded.json";
import * as api from "../../../lib/api";
import { useDesk } from "../../store";

vi.mock("../../components/MicButton", () => ({ MicButton: () => <span data-testid="mic" /> }));

const sessions = fixture.sessions;

beforeEach(() => {
  localStorage.clear();
  useDesk.setState({
    terminalWindows: [],
    drafts: {},
    panelDepth: {},
    panelOrder: [],
    panelMin: [],
  });
  vi.restoreAllMocks();
});

function serveInventory() {
  vi.spyOn(api, "apiFetch").mockResolvedValue({ status: "ok", sessions } as never);
}

describe("Terminals inventory", () => {
  it("searches recorded metadata and opens the stable descriptor without using a pane selector", async () => {
    serveInventory();
    render(<TerminalsCore />);
    await screen.findByTestId(`terminal-row-${sessions[0].id}`);

    fireEvent.change(screen.getByRole("textbox", { name: "Find a session or folder" }), { target: { value: "scratch" } });
    expect(screen.queryByTestId(`terminal-row-${sessions[0].id}`)).toBeNull();
    const row = screen.getByTestId(`terminal-row-${sessions[1].id}`);
    expect(row).toHaveTextContent("/work/scratch");
    fireEvent.click(screen.getByTestId(`terminal-open-${sessions[1].id}`));
    expect(useDesk.getState().terminalWindows).toEqual([{ id: sessions[1].id, origin: null }]);
  });

  it("creates a named shell through the audited factory payload and opens the discovered descriptor", async () => {
    const apiRequest = vi.spyOn(api, "apiRequest");
    apiRequest
      .mockResolvedValueOnce(new Response(JSON.stringify({ status: "spawned", pane_id: "%9" }), { status: 200 }))
      .mockResolvedValue(new Response(JSON.stringify({ status: "ok" }), { status: 200 }));
    let reads = 0;
    vi.spyOn(api, "apiFetch").mockImplementation(async () => {
      reads += 1;
      return { status: "ok", sessions: reads > 1 ? [{ ...sessions[1], pane_id: "%9", session: "new-shell", label: "new-shell:0.0" }] : sessions } as never;
    });
    render(<TerminalsCore />);
    await screen.findByTestId(`terminal-row-${sessions[0].id}`);
    fireEvent.click(screen.getByTestId("terminal-new"));
    fireEvent.change(screen.getByRole("textbox", { name: "Shell name" }), { target: { value: "new-shell" } });
    fireEvent.change(screen.getByRole("textbox", { name: "Folder (optional)" }), { target: { value: "/work/scratch" } });
    fireEvent.click(screen.getByRole("button", { name: "Create shell" }));

    await waitFor(() => expect(useDesk.getState().terminalWindows).toEqual([{ id: sessions[1].id, origin: null }]));
    expect(apiRequest).toHaveBeenCalledWith("/api/coders/factory/spawn", expect.objectContaining({
      method: "POST",
      body: JSON.stringify({ name: "new-shell", cwd: "/work/scratch" }),
    }));
  });

  it("refreshes from the producer and keeps an empty response explicit", async () => {
    vi.spyOn(api, "apiFetch").mockResolvedValue({ status: "ok", sessions: [] } as never);
    await refreshTerminalInventory();
    render(<TerminalsCore />);
    expect(await screen.findByText("No terminal sessions")).toBeTruthy();
  });
});
