import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import DictationPage from "./DictationPage";

const mocks = vi.hoisted(() => ({
  apiFetch: vi.fn(),
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

import { ApiError } from "../lib/api";

const TARGETS = [
  {
    version: 1,
    id: "this_machine",
    profile_id: null,
    name: "This device",
    kind: "this_device",
    boundary: "on this machine",
    owner: "you",
    transport: "in-process",
    data_scope: { sent: [], returned: [] },
    engine: "local",
    model: "",
    context_limit: 0,
    readiness: { state: "ready", available: true, reason: "" },
    secret: { required: false, present: false },
  },
  {
    version: 1,
    id: "p1",
    profile_id: "p1",
    name: "Study",
    kind: "private_endpoint",
    boundary: "leaves this machine",
    owner: "you",
    transport: "http",
    data_scope: { sent: ["dictated text"], returned: [] },
    engine: "llama.cpp",
    model: "q6",
    context_limit: 8192,
    readiness: { state: "ready", available: true, reason: "" },
    secret: { required: false, present: false },
  },
];

function mockRoutes(options: {
  dryRun: () => Promise<unknown>;
}) {
  mocks.apiFetch.mockImplementation((path: string, init?: { method?: string }) => {
    if (path.startsWith("/api/dictation/readiness")) return Promise.resolve({});
    if (path === "/api/dictation/dry-run") return options.dryRun();
    if (path === "/api/inference-targets")
      return Promise.resolve({ targets: TARGETS });
    if (path === "/api/settings" && init?.method === "PUT")
      return Promise.resolve({ success: true });
    if (path === "/api/notes") return Promise.resolve({ success: true });
    return Promise.resolve({});
  });
}

async function openTryIt() {
  render(
    <MemoryRouter>
      <DictationPage />
    </MemoryRouter>,
  );
  fireEvent.click(screen.getByRole("tab", { name: "Try it" }));
  const editor = await screen.findByLabelText("Utterance");
  fireEvent.change(editor, {
    target: { value: "A draft that must not disappear." },
  });
  return editor;
}

describe("DictationPage Try it failure actions", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it("offers Retry, Copy, Keep as Note, and alternate Runs on for a delivery conflict, then re-runs on the picked target", async () => {
    let calls = 0;
    mockRoutes({
      dryRun: () => {
        calls += 1;
        return calls === 1
          ? Promise.reject(new ApiError(409, "conflict", {}))
          : Promise.resolve({ final_text: "Ran on the alternate target." });
      },
    });
    const editor = await openTryIt();
    fireEvent.click(screen.getByRole("button", { name: "Run dry test" }));

    await screen.findByText(/Delivery did not complete/);
    expect(editor).toHaveValue("A draft that must not disappear.");
    expect(
      screen.getByRole("button", { name: "Retry dry test" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Copy" })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Keep as Note" }),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Setup" })).toBeNull();

    const picker = await screen.findByRole("combobox", { name: "Runs on" });
    fireEvent.change(picker, { target: { value: "p1" } });

    await screen.findByText("Ran on the alternate target.");
    expect(mocks.apiFetch).toHaveBeenCalledWith("/api/settings", {
      method: "PUT",
      json: { dictation: { runtime: { profile_id: "p1" } } },
    });
    expect(calls).toBe(2);
    expect(editor).toHaveValue("A draft that must not disappear.");
  });

  it("maps this-device back to the hub default profile", async () => {
    let calls = 0;
    mockRoutes({
      dryRun: () => {
        calls += 1;
        return calls === 1
          ? Promise.reject(new ApiError(504, "timeout", {}))
          : Promise.resolve({ final_text: "Done." });
      },
    });
    await openTryIt();
    fireEvent.click(screen.getByRole("button", { name: "Run dry test" }));
    await screen.findByText(/Transcription timed out/);

    const picker = await screen.findByRole("combobox", { name: "Runs on" });
    fireEvent.change(picker, { target: { value: "this_machine" } });

    await screen.findByText("Done.");
    expect(mocks.apiFetch).toHaveBeenCalledWith("/api/settings", {
      method: "PUT",
      json: { dictation: { runtime: { profile_id: null } } },
    });
  });

  it("offers Setup without Retry or alternate Runs on for a rejected token", async () => {
    mockRoutes({
      dryRun: () => Promise.reject(new ApiError(401, "bad token", {})),
    });
    const editor = await openTryIt();
    fireEvent.click(screen.getByRole("button", { name: "Run dry test" }));

    await screen.findByText(/rejected the connection/);
    expect(editor).toHaveValue("A draft that must not disappear.");
    // HS-95-05: Setup opens through the shell dispatcher (button, not a route link).
    expect(screen.getByRole("button", { name: "Setup" })).toBeInTheDocument();
    expect(screen.queryByRole("combobox", { name: "Runs on" })).toBeNull();
    expect(
      screen.getByRole("button", { name: "Run dry test" }),
    ).toBeInTheDocument();
  });

  it("Keep as Note posts the retained draft to the real notes route", async () => {
    mockRoutes({
      dryRun: () => Promise.reject(new ApiError(504, "timeout", {})),
    });
    await openTryIt();
    fireEvent.click(screen.getByRole("button", { name: "Run dry test" }));
    await screen.findByText(/Transcription timed out/);

    fireEvent.click(screen.getByRole("button", { name: "Keep as Note" }));
    await screen.findByText("Kept as a Note on your Desk.");
    expect(mocks.apiFetch).toHaveBeenCalledWith("/api/notes", {
      method: "POST",
      json: {
        title: "Retained dictation draft",
        body_markdown: "A draft that must not disappear.",
        tags: ["dictation"],
      },
    });
    await waitFor(() =>
      expect(localStorage.getItem("hs.draft.v1.dictation-dry-run")).toBeNull(),
    );
  });
});
