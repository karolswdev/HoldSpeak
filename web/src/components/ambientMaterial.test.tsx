import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AmbientLayer } from "./AmbientLayer";

const mocks = vi.hoisted(() => ({
  apiFetch: vi.fn(),
  frames: new Map<string, unknown>(),
  listeners: new Set<(frame: { type: string; data: unknown }) => void>(),
  subscribe: (topic: string, listener: (frame: { type: string; data: unknown }) => void) => {
    if (topic === "*") mocks.listeners.add(listener);
    return () => { mocks.listeners.delete(listener); };
  },
}));

vi.mock("../lib/api", () => ({
  ApiError: class extends Error {},
  apiFetch: mocks.apiFetch,
  readableError: (error: unknown) => error instanceof Error ? error.message : "Request failed",
}));
vi.mock("../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ subscribe: mocks.subscribe }),
  useRuntimeFrame: (topic: string) => mocks.frames.get(topic) ?? null,
}));
vi.mock("../desk/projections", () => {
  const state = { ambient: [], refreshAmbient: vi.fn(), present: vi.fn() };
  return {
    useProjections: Object.assign(
      (selector: (value: typeof state) => unknown) => selector(state),
      { getState: () => state },
    ),
  };
});

beforeEach(() => {
  mocks.frames.clear();
  mocks.listeners.clear();
  mocks.apiFetch.mockReset();
  mocks.apiFetch.mockImplementation(async (path: string) => path === "/api/settings"
    ? { presence: { enabled: true, mascot: true } }
    : { success: true });
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("ambient Workbench notices", () => {
  it("keeps the complete dictation text in a well and types its exact token", async () => {
    const text = "Release check\nKeep <rollback> and the full owner text.";
    mocks.frames.set("dictation_preview", { token: "preview-1", text });
    const { container } = render(<AmbientLayer />);
    const preview = screen.getByLabelText("Dictation preview");
    expect(preview.querySelector(".surface-well .ambient-content")?.textContent).toBe(text);
    expect(preview.querySelector("rollback")).toBeNull();
    expect(screen.getByRole("button", { name: "Type it" })).toHaveClass("btn--primary");
    expect(container.querySelector(".ambient-notices")?.contains(preview)).toBe(true);
    fireEvent.click(screen.getByRole("button", { name: "Type it" }));
    await waitFor(() => expect(screen.queryByLabelText("Dictation preview")).toBeNull());
    expect(mocks.apiFetch).toHaveBeenCalledWith("/api/dictation/preview/type", {
      method: "POST", json: { token: "preview-1" },
    });
  });

  it("discards the dictation preview through its existing writer", async () => {
    mocks.frames.set("dictation_preview", { token: "discard-1", text: "Owner draft" });
    render(<AmbientLayer />);
    fireEvent.click(screen.getByRole("button", { name: "Discard" }));
    await waitFor(() => expect(screen.queryByLabelText("Dictation preview")).toBeNull());
    expect(mocks.apiFetch).toHaveBeenCalledWith("/api/dictation/preview/discard", {
      method: "POST", json: { token: "discard-1" },
    });
  });

  it("keeps a failed preview visible and retries the same type action", async () => {
    mocks.frames.set("dictation_preview", { token: "retry-1", text: "Keep my words" });
    mocks.apiFetch.mockImplementation(async (path: string) => {
      if (path === "/api/settings") return { presence: { enabled: true, mascot: true } };
      throw new Error("Writer unavailable");
    });
    render(<AmbientLayer />);
    fireEvent.click(screen.getByRole("button", { name: "Type it" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Writer unavailable");
    expect(screen.getByText("Keep my words")).toBeTruthy();
    mocks.apiFetch.mockResolvedValue({ success: true });
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    await waitFor(() => expect(screen.queryByLabelText("Dictation preview")).toBeNull());
    expect(mocks.apiFetch.mock.calls.filter(([path]) => path === "/api/dictation/preview/type"))
      .toEqual([
        ["/api/dictation/preview/type", { method: "POST", json: { token: "retry-1" } }],
        ["/api/dictation/preview/type", { method: "POST", json: { token: "retry-1" } }],
      ]);
  });

  it("keeps wake discard local", () => {
    mocks.frames.set("wake_preview", { token: "wake-1", text: "Wake draft" });
    render(<AmbientLayer />);
    fireEvent.click(screen.getByRole("button", { name: "Discard" }));
    expect(screen.queryByLabelText("Dictation preview")).toBeNull();
    expect(mocks.apiFetch.mock.calls.map(([path]) => path)).toEqual(["/api/settings"]);
  });

  it("omits zero queue counts, uses shared rows and opens the existing queue route", () => {
    mocks.frames.set("runtime_queue", {
      queued: 0, running: 0, failed: 0, scheduled_retries: 2,
      jobs: [{ id: "job-1", label: "Migration notes", status: "retrying" }],
    });
    render(<AmbientLayer />);
    const queue = screen.getByLabelText("Intelligence queue");
    fireEvent.click(within(queue).getByRole("button", { name: "2 retrying" }));
    expect(queue.textContent).not.toMatch(/\b0\b/);
    expect(queue.querySelector(".surface-rows .surface-row")?.textContent).toContain("Migration notes");
    expect(within(queue).queryByRole("link")).toBeNull();
    const route = { href: "" };
    vi.stubGlobal("window", new Proxy(window, {
      get: (target, key) => key === "location" ? route : Reflect.get(target, key),
    }));
    fireEvent.click(within(queue).getByRole("button", { name: "Open queue" }));
    expect(route.href).toBe("/history");
    vi.unstubAllGlobals();
  });

  it("withholds an empty queue", () => {
    mocks.frames.set("runtime_queue", { queued: 0, running: 0, failed: 0, scheduled_retries: 0 });
    render(<AmbientLayer />);
    expect(screen.queryByLabelText("Intelligence queue")).toBeNull();
  });

  it("leaves an Ask run to its producer face without a global card", async () => {
    mocks.frames.set("intel_status", {
      state: "running", scope: "run", capability: { kind: "ask", id: "ask", name: "Ask" },
    });
    render(<AmbientLayer />);
    await waitFor(() => expect(mocks.apiFetch).toHaveBeenCalledWith("/api/settings"));
    expect(document.querySelector(".ambient-theater")).toBeNull();
  });

  it("renders complete learning text safely alongside the other notices", async () => {
    mocks.frames.set("dictation_preview", { token: "preview-2", text: "Owner text" });
    mocks.frames.set("runtime_queue", { running: 1 });
    mocks.frames.set("intel_status", { state: "analyzing", label: "Migration analysis", detail: "Reconciliation checks" });
    const { container } = render(<AmbientLayer />);
    await waitFor(() => expect(mocks.apiFetch).toHaveBeenCalledWith("/api/settings"));
    const body = "Use <script>literal text</script>\nKeep the rollback check before release.";
    act(() => {
      for (const listener of mocks.listeners) listener({
        type: "learning_event", data: { id: "learn-1", title: "Release preference", body },
      });
    });
    const qlippy = await screen.findByLabelText("Qlippy");
    expect(container.querySelector(".ambient-theater")).toHaveTextContent("Migration analysis");
    expect(container.querySelector(".ambient-theater")).toHaveTextContent("Reconciliation checks");
    expect(qlippy.querySelector(".surface-well .ambient-content")?.textContent).toBe(body);
    expect(qlippy.querySelector("script")).toBeNull();
    expect(qlippy.querySelector(".qlippy-face")).toBeNull();
    expect(qlippy.textContent).not.toContain("Review this moment when you are ready");
    expect(container.querySelector(".ambient-notices")?.children).toHaveLength(4);
    fireEvent.click(within(qlippy).getByRole("button", { name: "Dismiss" }));
    expect(screen.queryByLabelText("Qlippy")).toBeNull();
    expect(screen.getByLabelText("Dictation preview")).toBeTruthy();
  });
});
