// Conductor K3: the Agents window re-reads the sessions on a `scope:"coder"`
// frame (an agent began or stopped waiting), quietly: no visual change.
import { act, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../../lib/api";
import { CompanionCore } from "../CompanionCore";

const bus = vi.hoisted(() => ({ handlers: new Map<string, Set<(frame: unknown) => void>>() }));

vi.mock("../../../runtime/RuntimeBus", () => {
  const value = {
    state: "connected",
    lastFrame: null,
    subscribe: (type: string, handler: (frame: unknown) => void) => {
      const set = bus.handlers.get(type) ?? new Set();
      set.add(handler);
      bus.handlers.set(type, set);
      return () => set.delete(handler);
    },
  };
  return {
    useRuntimeBus: () => value,
    useOptionalRuntimeBus: () => value,
    useRuntimeFrame: () => null,
  };
});

function emit(frame: { type: string; data: unknown }) {
  for (const handler of bus.handlers.get(frame.type) ?? []) handler(frame);
}

let blocked = false;
vi.mock("../../../lib/api", async (importOriginal) => {
  const mod = (await importOriginal()) as Record<string, unknown>;
  return {
    ...mod,
    apiFetch: vi.fn(async (url: string) => {
      if (url === "/api/coders/sessions?include_ended=false")
        return {
          sessions: [{
            session: blocked
              ? { agent: "claude", session_id: "s1", project_name: "holdspeak", state: "waiting", awaiting_response: true, question: "Drop the old migration?" }
              : { agent: "claude", session_id: "s1", project_name: "holdspeak", state: "working", awaiting_response: false },
          }],
          flights: [],
        };
      return {};
    }),
  };
});

vi.mock("../../../desk/shell", () => ({ openCoderSession: vi.fn(), openPersona: vi.fn() }));

const coderCalls = () =>
  vi.mocked(apiFetch).mock.calls.filter(([url]) => url === "/api/coders/sessions?include_ended=false").length;

describe("Agents window follows the coder frame (Conductor K3)", () => {
  it("re-reads on a coder frame and not on another intel_status frame", async () => {
    render(<CompanionCore />);
    await screen.findByText("holdspeak");
    const before = coderCalls();
    expect(screen.queryByText("Drop the old migration?", { selector: "pre" })).toBeNull();

    act(() => emit({ type: "intel_status", data: { scope: "belt" } }));
    expect(coderCalls()).toBe(before);

    blocked = true;
    act(() => emit({ type: "intel_status", data: { state: "ready", scope: "coder", capability: { kind: "coder", id: "claude:s1" } } }));
    await waitFor(() => expect(coderCalls()).toBe(before + 1));
    expect(await screen.findByText("Drop the old migration?", { selector: "pre" })).toBeInTheDocument();
  });
});
