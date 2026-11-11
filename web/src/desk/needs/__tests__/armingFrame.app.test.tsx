/* The hub's scheduled_recording.arming frame reaches Needs you's arming row
   through the Dock, the desk's one subscriber to the scheduled-recording
   frames (the subscription left with the parked CaptureHero; restored
   2026-11-08). The frame is driven through the Dock's own subscription to
   the rendered row. */
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

const bus = vi.hoisted(() => {
  const listeners = new Map<string, Set<(frame: { type: string; data: unknown }) => void>>();
  const subscribe = (type: string, handler: (frame: { type: string; data: unknown }) => void) => {
    const set = listeners.get(type) ?? new Set();
    set.add(handler);
    listeners.set(type, set);
    return () => set.delete(handler);
  };
  const emit = (type: string, data: unknown) => {
    for (const handler of listeners.get(type) ?? []) handler({ type, data });
  };
  return { listeners, subscribe, emit, value: { state: "connected", subscribe } };
});

vi.mock("../../../runtime/RuntimeBus", async (original) => ({
  ...(await original<typeof import("../../../runtime/RuntimeBus")>()),
  useOptionalRuntimeBus: () => bus.value,
  useRuntimeBus: () => bus.value,
}));

vi.mock("../../../lib/api", async (original) => ({
  ...(await original<typeof import("../../../lib/api")>()),
  apiFetch: vi.fn(async (path: string) => {
    const value = String(path);
    if (value.startsWith("/api/desk/needs-you")) {
      return { count: 0, items: [], arming: [], coverage: { complete: true, groups: [] } };
    }
    if (value.startsWith("/api/scheduled-recordings")) return { items: [] };
    if (value === "/api/meetings/ready") return { meetings: [] };
    return {};
  }),
}));

import { Dock } from "../../components/window/Dock";
import { NeedsDrawer } from "../NeedsDrawer";
import { useDesk } from "../../store";

afterEach(() => {
  useDesk.setState({ scheduledArming: null } as never);
});

describe("the arming frame reaches Needs you", () => {
  it("a scheduled_recording.arming frame on the bus draws the arming row; cancelled takes it away", async () => {
    render(
      <>
        <Dock />
        <NeedsDrawer />
      </>,
    );
    await waitFor(() => expect(bus.listeners.get("scheduled_recording.arming")?.size).toBe(1));
    const armed = () => document.querySelector<HTMLElement>("[data-object-id='arming:sch-7']");
    expect(armed()).toBeNull();

    act(() => bus.emit("scheduled_recording.arming", {
      schedule_id: "sch-7", title: "Ledger cutover sync", countdown_seconds: 30, fire_at: Date.now() / 1000 + 30,
    }));
    await waitFor(() => expect(armed()).not.toBeNull());
    expect(armed()!.textContent).toContain("Ledger cutover sync");
    expect(armed()!.querySelector("button")).toBeNull();
    fireEvent.click(armed()!);
    expect(screen.getByRole("button", {name: "Cancel recording"})).toBeTruthy();

    act(() => bus.emit("scheduled_recording.cancelled", { schedule_id: "sch-7" }));
    await waitFor(() => expect(armed()).toBeNull());
    expect(screen.getByTestId("needs-receipt").textContent).toMatch(/^Cancelled · Ledger cutover sync · \d\d:\d\d$/);
  });
});
