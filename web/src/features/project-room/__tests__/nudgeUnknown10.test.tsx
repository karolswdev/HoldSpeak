import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { NudgeCard } from "../NudgeCard";
import { decodeRoomSnapshot } from "../model";
import TAPE from "./room-wires/nudge10.json";
const io = vi.hoisted(() => ({ api: vi.fn() }));
vi.mock("../../../lib/api", async original => ({ ...await original<typeof import("../../../lib/api")>(), apiFetch: (...args: unknown[]) => io.api(...args) }));
const gets = TAPE.before as Record<string, any>;
const room = decodeRoomSnapshot(gets[`/api/projects/${TAPE.pid}/room`]);
const need = room.needsYou.state === "ok" ? room.needsYou.items.find(row => row.verb === "nudge")! : null!;
const nudges = gets[`/api/projects/${TAPE.pid}/nudges?state=proposed`].nudges;
const props = { needsYouItem: need, nudgeItem: nudges[0], person: room.health.state === "ok" ? room.health.people?.[0] : undefined, onReload: vi.fn() };
beforeEach(() => { io.api.mockReset(); });
describe("Nudge result custody in the inspector", () => {
  // Replaces the NudgeCard source-only EgressChip case in egress_labels_canon.
  it("names the destination beside the Send act before, during and after a refused press", async () => {
    let answer!: (value: unknown) => void;
    io.api.mockImplementation(() => new Promise(resolve => { answer = resolve; }));
    render(<NudgeCard {...props} />);
    const send = screen.getByRole("button", { name: "Send" });
    const act = send.closest<HTMLElement>(".surface-inspector-actions")!;
    expect(within(act).getByText("github.com", { exact: true })).toBeVisible();
    fireEvent.click(send);
    expect(within(act).getByText("github.com", { exact: true })).toBeVisible();
    answer({ success: false, outcome: "failed", message: "Injected refusal" });
    await screen.findByText("Injected refusal");
    expect(within(act).getByText("github.com", { exact: true })).toBeVisible();
    expect(within(act).getByRole("button", { name: "Send" })).toBeEnabled();
  });
  it("keeps an unknown result through close and reopen without another Send", async () => {
    io.api.mockResolvedValue(TAPE.send.answer); const local = vi.fn();
    const mounted = render(<NudgeCard {...props} onLocal={local} />);
    fireEvent.click(screen.getByRole("button", { name: "Send" }));
    await screen.findByText("Result unknown"); expect(io.api).toHaveBeenCalledOnce();
    mounted.unmount(); render(<NudgeCard {...props} local={{ state: "unknown" }} />);
    expect(screen.getByText("Result unknown")).toBeInTheDocument(); expect(screen.queryByRole("button", { name: "Send" })).toBeNull();
  });
  it("keeps a sending result unknown on reopen, including a lost network answer", async () => {
    io.api.mockRejectedValue(new TypeError("lost reply")); render(<NudgeCard {...props} />);
    fireEvent.click(screen.getByRole("button", { name: "Send" })); await screen.findByText("Result unknown");
    expect(screen.queryByRole("button", { name: "Send" })).toBeNull();
  });
  it("does not dispatch a second Send while the first press is pending", async () => {
    let resolve!: (value: unknown) => void; io.api.mockImplementation(() => new Promise(answer => { resolve = answer; }));
    render(<NudgeCard {...props} />); const send = screen.getByRole("button", { name: "Send" }); fireEvent.click(send); fireEvent.click(send);
    expect(io.api).toHaveBeenCalledOnce(); resolve(TAPE.send.answer); await screen.findByText("Result unknown");
  });
  it("retains edited text for a known failure and retries the current words", async () => {
    io.api.mockResolvedValue({ success: false, outcome: "failed", message: "Injected refusal" }); render(<NudgeCard {...props} />);
    const field = screen.getByRole("textbox", { name: "Comment" }); fireEvent.change(field, { target: { value: "Please review the current change" } });
    fireEvent.click(screen.getByRole("button", { name: "Send" })); await screen.findByText("Injected refusal");
    expect(field).toHaveValue("Please review the current change"); fireEvent.change(field, { target: { value: "Please review the revised change" } });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));
    await waitFor(() => expect(io.api.mock.calls.at(-1)?.[1].json.text).toBe("Please review the revised change"));
  });
});
