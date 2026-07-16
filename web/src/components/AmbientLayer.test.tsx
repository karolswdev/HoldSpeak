import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AmbientLayer } from "./AmbientLayer";

/**
 * HS-93-05 criterion 6, Web side. The hub owns the posture decision
 * (operation_policy.resolve_dictation_policy, proven in
 * tests/unit/test_dictation_preview.py): Secure always arms a preview,
 * Normal arms one only when the explicit preview preference is on, and
 * YOLO commits without arming. The Web keeps no private posture matrix;
 * it renders the gate exactly when the hub broadcasts `dictation_preview`
 * and commits by token only. These tests prove that expression plus the
 * retained-words, exactly-once, and destination-binding guarantees.
 */

const mocks = vi.hoisted(() => ({
  apiFetch: vi.fn(),
  frames: {} as Record<string, unknown>,
}));

vi.mock("../lib/api", () => {
  class ApiError extends Error {
    constructor(
      public status: number,
      message: string,
      public payload: unknown = {},
    ) {
      super(message);
      this.name = "ApiError";
    }
  }
  return {
    ApiError,
    apiFetch: mocks.apiFetch,
    readableError: (error: unknown) =>
      error instanceof Error ? error.message : "Request failed",
  };
});

vi.mock("../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({
    state: "connected",
    lastFrame: null,
    subscribe: () => () => undefined,
  }),
  useRuntimeFrame: (type: string) => mocks.frames[type] ?? null,
}));

vi.mock("../desk/projections", () => {
  const state = {
    ambient: [],
    refreshAmbient: vi.fn(),
    present: vi.fn(),
  };
  const useProjections = Object.assign(
    (selector: (value: typeof state) => unknown) => selector(state),
    { getState: () => state },
  );
  return { useProjections };
});

describe("posture-aware dictation preview gate", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    for (const key of Object.keys(mocks.frames)) delete mocks.frames[key];
    mocks.apiFetch.mockImplementation((path: string) => {
      if (path === "/api/settings")
        return Promise.resolve({ presence: { enabled: false } });
      return Promise.resolve({ success: true });
    });
  });

  it("Secure and Normal-with-preference: the hub-armed preview gates before any commit", async () => {
    mocks.frames.dictation_preview = {
      token: "tok-1",
      text: "The words that must not type yet.",
    };
    render(<AmbientLayer />);
    expect(
      screen.getByText("The words that must not type yet."),
    ).toBeInTheDocument();
    expect(screen.getByText("Preview before type")).toBeInTheDocument();
    expect(
      mocks.apiFetch.mock.calls.filter(([path]) =>
        String(path).includes("/api/dictation/preview"),
      ),
    ).toHaveLength(0);
  });

  it("Type it commits exactly once, by token only, and closes the gate", async () => {
    mocks.frames.dictation_preview = {
      token: "tok-1",
      text: "The words that must not type yet.",
    };
    render(<AmbientLayer />);
    const typeIt = screen.getByRole("button", { name: "Type it" });
    fireEvent.click(typeIt);
    fireEvent.click(typeIt);

    await waitFor(() =>
      expect(
        screen.queryByText("The words that must not type yet."),
      ).toBeNull(),
    );
    const commits = mocks.apiFetch.mock.calls.filter(
      ([path]) => path === "/api/dictation/preview/type",
    );
    expect(commits).toHaveLength(1);
    // Destination binding: the commit carries the server-minted token only.
    // The hub types its OWN stored text; client words never ride the commit.
    expect(commits[0][1]).toEqual({
      method: "POST",
      json: { token: "tok-1" },
    });
  });

  it("Discard burns the preview without ever committing", async () => {
    mocks.frames.dictation_preview = {
      token: "tok-1",
      text: "The words that must not type yet.",
    };
    render(<AmbientLayer />);
    fireEvent.click(screen.getByRole("button", { name: "Discard" }));

    await waitFor(() =>
      expect(
        screen.queryByText("The words that must not type yet."),
      ).toBeNull(),
    );
    expect(
      mocks.apiFetch.mock.calls.map(([path]) => path),
    ).not.toContain("/api/dictation/preview/type");
    expect(
      mocks.apiFetch.mock.calls.filter(
        ([path]) => path === "/api/dictation/preview/discard",
      ),
    ).toHaveLength(1);
  });

  it("a failed commit keeps the words and the gate for an explicit retry", async () => {
    mocks.frames.dictation_preview = {
      token: "tok-1",
      text: "The words that must not type yet.",
    };
    let attempts = 0;
    mocks.apiFetch.mockImplementation((path: string) => {
      if (path === "/api/settings")
        return Promise.resolve({ presence: { enabled: false } });
      if (path === "/api/dictation/preview/type") {
        attempts += 1;
        return attempts === 1
          ? Promise.reject(new Error("The hub could not be reached."))
          : Promise.resolve({ success: true, typed: "ok" });
      }
      return Promise.resolve({ success: true });
    });
    render(<AmbientLayer />);
    fireEvent.click(screen.getByRole("button", { name: "Type it" }));

    await screen.findByText("The hub could not be reached.");
    expect(
      screen.getByText("The words that must not type yet."),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Type it" }));
    await waitFor(() =>
      expect(
        screen.queryByText("The words that must not type yet."),
      ).toBeNull(),
    );
    expect(attempts).toBe(2);
  });

  it("YOLO and Normal-without-preference: no hub frame means no HoldSpeak prompt", () => {
    render(<AmbientLayer />);
    expect(screen.queryByText("Preview before type")).toBeNull();
    expect(screen.queryByRole("button", { name: "Type it" })).toBeNull();
    expect(
      mocks.apiFetch.mock.calls.filter(([path]) =>
        String(path).includes("/api/dictation/preview"),
      ),
    ).toHaveLength(0);
  });
});
