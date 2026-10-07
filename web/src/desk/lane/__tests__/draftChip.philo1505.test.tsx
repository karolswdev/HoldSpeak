// PHILO-15 05, ruling 1 (inventory gap 8): the lane's draft chip names the
// model that drafts answers. Drafts are OWNER work and inherit the Default for
// AI work (tests/unit/test_philo15_05_default_feeds_drafts.py), so with only a
// default the chip names the default's host, never NOT SET; a default made
// after the first read shows at the next open; a this-device default reads
// THIS DEVICE, not its model label as a cloud host. No cache (Astra r1): a
// changed default shows at the next open, and an open lane re-reads on
// `desk_changed`.
import { act, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const api = vi.hoisted(() => ({ fetch: vi.fn() }));
vi.mock("../../../lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../../lib/api")>()),
  apiFetch: api.fetch,
}));
// The hub's bus: every mutating /api request announces `desk_changed`.
const bus = vi.hoisted(() => ({ handlers: new Set<(frame: unknown) => void>() }));
vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({
    subscribe: (type: string, handler: (frame: unknown) => void) => {
      if (type !== "desk_changed") return () => undefined;
      bus.handlers.add(handler);
      return () => bus.handlers.delete(handler);
    },
  }),
}));

import { useDraftEgress, __resetDraftEgress } from "../LaneWindow";
import { useDesk } from "../../store";

function Chip() {
  const egress = useDraftEgress(true);
  return <span data-testid="chip" data-scope={egress.scope ?? ""}>{egress.label}</span>;
}

/** The roster as GET /api/inference/assignments answers it: `effective` is
 * the whole chain, so a default with no exact assignment reads `global`. */
function roster(entry: Record<string, unknown> | null) {
  return {
    task_overrides: [{
      id: "background.cadence_draft",
      has_override: false,
      effective: entry
        ? { status: "assigned", inherited_from: "global", assignment: { entries: [entry] } }
        : { status: "no_assignment", inherited_from: null, assignment: null },
    }],
  };
}

beforeEach(() => {
  api.fetch.mockReset();
  bus.handlers.clear();
  __resetDraftEgress();
  act(() => {
    useDesk.setState({ inferenceTargets: [] } as never);
  });
});

describe("the draft chip reads the Default for AI work", () => {
  it("a LAN default alone: the chip names its host, not NOT SET", async () => {
    act(() => {
      useDesk.setState({
        inferenceTargets: [{ id: "lan-qwen", profile_id: "lan-qwen", endpoint: "http://192.168.1.43:8080/v1" }],
      } as never);
    });
    api.fetch.mockResolvedValue(roster({ profile_id: "lan-qwen", label: "Qwen3.8 27B", boundary: "private_network" }));
    render(<Chip />);
    await waitFor(() => expect(screen.getByTestId("chip").textContent).toBe("192.168.1.43 · LAN"));
    expect(screen.getByTestId("chip").dataset.scope).toBe("local");
  });

  it("a LAN default with no target to read: the chip names the default's model, scoped local", async () => {
    api.fetch.mockResolvedValue(roster({ profile_id: "lan-qwen", label: "qwen3.8-27b", boundary: "private_network" }));
    render(<Chip />);
    await waitFor(() => expect(screen.getByTestId("chip").textContent).toBe("QWEN3.8-27B"));
    expect(screen.getByTestId("chip").dataset.scope).toBe("local");
  });

  it("a this-device default with no endpoint reads THIS DEVICE, not its label as a cloud host", async () => {
    api.fetch.mockResolvedValue(roster({ profile_id: "this-machine", label: "Qwen3 8B", boundary: "local" }));
    render(<Chip />);
    await waitFor(() => expect(screen.getByTestId("chip").textContent).toBe("THIS DEVICE"));
    expect(screen.getByTestId("chip").dataset.scope).toBe("local");
  });

  it("no default and no assignment: NOT SET; a default made later shows at the next open", async () => {
    api.fetch.mockResolvedValueOnce(roster(null));
    const first = render(<Chip />);
    await waitFor(() => expect(api.fetch).toHaveBeenCalledTimes(1));
    expect(screen.getByTestId("chip").textContent).toBe("NOT SET");
    first.unmount();

    // Set up local AI made the default; the lane opens again.
    api.fetch.mockResolvedValueOnce(roster({ profile_id: "this-machine", label: "Qwen3 8B", boundary: "local" }));
    render(<Chip />);
    await waitFor(() => expect(screen.getByTestId("chip").textContent).toBe("THIS DEVICE"));
    expect(api.fetch).toHaveBeenCalledTimes(2);
  });

  // Astra r1 (#975): the rendered check shape. Rosters as the real services
  // mint them: a ready local default, then a ready OpenRouter default.
  const LOCAL = { profile_id: "this-machine", label: "This Machine", boundary: "local", readiness: "ready" };
  const CLOUD = { profile_id: "cloud-default", label: "OpenRouter Qwen", boundary: "cloud", readiness: "ready" };

  it("local default, then an OpenRouter default, then reopen: the OpenRouter name, not THIS DEVICE", async () => {
    api.fetch.mockResolvedValueOnce(roster(LOCAL));
    const first = render(<Chip />);
    await waitFor(() => expect(screen.getByTestId("chip").textContent).toBe("THIS DEVICE"));
    first.unmount();

    api.fetch.mockResolvedValueOnce(roster(CLOUD));
    render(<Chip />);
    await waitFor(() => expect(screen.getByTestId("chip").textContent).toBe("OPENROUTER QWEN"));
    expect(screen.getByTestId("chip").dataset.scope).toBe("cloud");
  });

  it("an open lane re-reads after a desk write (desk_changed): the new default shows without a reopen", async () => {
    api.fetch.mockResolvedValueOnce(roster(LOCAL));
    render(<Chip />);
    await waitFor(() => expect(screen.getByTestId("chip").textContent).toBe("THIS DEVICE"));

    api.fetch.mockResolvedValueOnce(roster(CLOUD));
    act(() => bus.handlers.forEach((handler) => handler({ type: "desk_changed", data: {} })));
    await waitFor(() => expect(screen.getByTestId("chip").textContent).toBe("OPENROUTER QWEN"), { timeout: 2000 });
    expect(screen.getByTestId("chip").dataset.scope).toBe("cloud");
  });
});
