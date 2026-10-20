// HS-130-07 — the command board is ONE honest writer of macro `items`.
// A checkbox toggle can no longer round-trip (and clobber) the whole macro
// array, and every write carries the `_revision` it read.
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { CommandsCore } from "../CommandsCore";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn() }));

vi.mock("../../../lib/api", () => ({
  apiFetch: mocks.apiFetch,
  readableError: (e: unknown) => (e instanceof Error ? e.message : "failed"),
}));
vi.mock("../../../desk/shell", () => ({ openSurfaceOr: vi.fn() }));

type Init = { method?: string; json?: any };

function callsTo(path: string): Init[] {
  return mocks.apiFetch.mock.calls
    .filter((c: unknown[]) => String(c[0]) === path)
    .map((c: unknown[]) => (c[1] ?? {}) as Init);
}

const SETTINGS = {
  _revision: "rev-1",
  dictation: {
    macros: {
      enabled: true,
      items: [
        { keyword: "docs", action: { kind: "open_url", payload: "https://x" } },
      ],
    },
  },
};

function appliedAddWithLostResponse() {
  const server = {
    settings: {
      ...SETTINGS,
      dictation: { macros: { enabled: true, items: [] as typeof SETTINGS.dictation.macros.items } },
    },
  };
  let puts = 0;
  mocks.apiFetch.mockImplementation((path: string, init?: Init) => {
    if (path === "/api/settings" && init?.method === "PUT") {
      puts += 1;
      server.settings = {
        ...server.settings,
        _revision: `rev-${puts + 1}`,
        dictation: {
          macros: {
            enabled: true,
            items: init.json.dictation.macros.items.map((macro: typeof SETTINGS.dictation.macros.items[number]) => ({
              ...macro,
              keyword: macro.keyword.trim(),
            })),
          },
        },
      };
      if (puts === 1) return Promise.reject(new Error("Response lost"));
      return Promise.resolve({ settings: server.settings });
    }
    if (path === "/api/settings") return Promise.resolve(server.settings);
    return Promise.resolve({});
  });
  return server;
}

async function addWithLostResponse() {
  render(<CommandsCore />);
  await screen.findByText("No voice commands");
  fireEvent.click(screen.getAllByRole("button", { name: "Add command" })[0]);
  fireEvent.change(screen.getByRole("textbox", { name: "Spoken keyword" }), { target: { value: "  type ledger  " } });
  fireEvent.change(screen.getByLabelText("Command behavior"), { target: { value: "type_text" } });
  fireEvent.change(screen.getByRole("textbox", { name: "Payload" }), { target: { value: "Ledger is ready." } });
  fireEvent.click(screen.getByRole("button", { name: "Save command" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("Command save not confirmed");
}

beforeEach(() => {
  vi.clearAllMocks();
  mocks.apiFetch.mockImplementation((path: string, init?: Init) => {
    if (path === "/api/settings" && init?.method === "PUT")
      return Promise.resolve({ settings: SETTINGS });
    if (path === "/api/settings") return Promise.resolve(SETTINGS);
    return Promise.resolve({});
  });
});

describe("CommandsCore is one honest items-writer (HS-130-07)", () => {
  it("has no persistent enablement toggle — it links to Settings", async () => {
    render(<CommandsCore />);
    await screen.findByText("“docs”");
    // The old "Commands enabled" checkbox is gone (Settings owns enablement).
    expect(
      screen.queryByRole("checkbox", { name: /Commands enabled/i }),
    ).toBeNull();
    // The effective state is shown and a link opens Settings.
    expect(screen.getByText("Commands on")).toBeVisible();
    expect(
      screen.getByRole("button", { name: /Manage in Settings/i }),
    ).toBeVisible();
  });

  it("gives a desk verb a valid default payload when its kind changes", async () => {
    mocks.apiFetch.mockImplementation((path: string, init?: Init) => {
      if (path === "/api/settings" && init?.method === "PUT") {
        return Promise.resolve({ settings: { ...SETTINGS, dictation: { macros: { enabled: true, items: init.json.dictation.macros.items } } } });
      }
      return Promise.resolve({ ...SETTINGS, dictation: { macros: { enabled: true, items: [] } } });
    });
    render(<CommandsCore />);
    await screen.findByText("No voice commands");
    fireEvent.click(screen.getAllByRole("button", { name: "Add command" })[0]);
    fireEvent.change(screen.getByRole("textbox", { name: "Spoken keyword" }), {
      target: { value: "start recording" },
    });
    fireEvent.change(screen.getByLabelText("Command behavior"), {
      target: { value: "desk_verb" },
    });
    expect(screen.getByLabelText("Desk verb")).toHaveValue("record");
    fireEvent.click(screen.getByRole("button", { name: "Save command" }));
    await waitFor(() => expect(screen.queryByLabelText("Desk verb")).toBeNull());
    expect(callsTo("/api/settings").find((call) => call.method === "PUT")?.json.dictation.macros.items).toEqual([
      { keyword: "start recording", action: { kind: "desk_verb", payload: "record" } },
    ]);
  });

  it("deleting a macro PUTs items-only with the revision — never the enabled bit", async () => {
    render(<CommandsCore />);
    await screen.findByText("“docs”");
    // ConfirmVerb: arm, then confirm.
    fireEvent.click(screen.getByRole("button", { name: "Delete" }));
    fireEvent.click(screen.getByRole("button", { name: "Delete?" }));

    await waitFor(() =>
      expect(
        callsTo("/api/settings").filter((c) => c.method === "PUT"),
      ).toHaveLength(1),
    );
    const [put] = callsTo("/api/settings").filter((c) => c.method === "PUT");
    // The write carries ONLY items (no `enabled` — no clobber) + the revision.
    expect(put.json).toEqual({
      dictation: { macros: { items: [] } },
      _revision: "rev-1",
    });
    expect(put.json.dictation.macros).not.toHaveProperty("enabled");
  });

  it("keeps every draft field after a rejected save and retries the same command", async () => {
    let puts = 0;
    mocks.apiFetch.mockImplementation((path: string, init?: Init) => {
      if (path === "/api/settings" && init?.method === "PUT") {
        puts += 1;
        if (puts === 1) return Promise.reject(new Error("Settings unavailable"));
        return Promise.resolve({ settings: { ...SETTINGS, dictation: { macros: { enabled: true, items: init.json.dictation.macros.items } } } });
      }
      return Promise.resolve(SETTINGS);
    });
    render(<CommandsCore />);
    await screen.findByText("“docs”");
    fireEvent.click(screen.getByRole("button", { name: "Edit" }));
    fireEvent.change(screen.getByRole("textbox", { name: "Spoken keyword" }), { target: { value: "type ledger" } });
    fireEvent.change(screen.getByLabelText("Command behavior"), { target: { value: "type_text" } });
    fireEvent.change(screen.getByRole("textbox", { name: "Payload" }), { target: { value: "Ledger is ready." } });
    fireEvent.click(screen.getByRole("button", { name: "Save command" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Command save not confirmed · Shown commands kept · Reload · Settings unavailable");
    expect(screen.getByRole("textbox", { name: "Spoken keyword" })).toHaveValue("type ledger");
    expect(screen.getByLabelText("Command behavior")).toHaveValue("type_text");
    expect(screen.getByRole("textbox", { name: "Payload" })).toHaveValue("Ledger is ready.");
    fireEvent.click(screen.getByRole("button", { name: "Save command" }));
    await waitFor(() => expect(screen.queryByRole("textbox", { name: "Payload" })).toBeNull());
    const writes = callsTo("/api/settings").filter((c) => c.method === "PUT");
    expect(writes).toHaveLength(2);
    expect(writes[1].json).toEqual(writes[0].json);
    expect(screen.getByText("“type ledger”")).toBeVisible();
  });

  it("reloads an applied Add after a lost response and saves exactly one command", async () => {
    appliedAddWithLostResponse();
    await addWithLostResponse();
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));

    await screen.findByText("“type ledger”");
    await waitFor(() => expect(screen.queryByRole("alert")).toBeNull());
    expect(screen.getByRole("textbox", { name: "Spoken keyword" })).toHaveValue("  type ledger  ");
    expect(callsTo("/api/settings").filter((c) => c.method === "PUT")).toHaveLength(1);
    expect(callsTo("/api/settings").filter((c) => !c.method)).toHaveLength(2);
    expect(callsTo("/api/commands/test")).toHaveLength(0);

    fireEvent.click(screen.getByRole("button", { name: "Save command" }));
    await waitFor(() => expect(screen.queryByRole("textbox", { name: "Payload" })).toBeNull());
    const writes = callsTo("/api/settings").filter((c) => c.method === "PUT");
    expect(writes).toHaveLength(2);
    expect(writes[1].json.dictation.macros.items).toHaveLength(1);
    expect(writes[1].json._revision).toBe("rev-2");
    expect(screen.getAllByText("“type ledger”")).toHaveLength(1);
  });

  it("preserves newer local fields while reconciling the saved Add row", async () => {
    appliedAddWithLostResponse();
    await addWithLostResponse();
    fireEvent.change(screen.getByRole("textbox", { name: "Spoken keyword" }), { target: { value: "new keyword" } });
    fireEvent.change(screen.getByLabelText("Command behavior"), { target: { value: "open_url" } });
    fireEvent.change(screen.getByRole("textbox", { name: "Payload" }), { target: { value: "https://new.example" } });
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));

    await screen.findByText("“type ledger”");
    expect(screen.getByRole("textbox", { name: "Spoken keyword" })).toHaveValue("new keyword");
    expect(screen.getByLabelText("Command behavior")).toHaveValue("open_url");
    expect(screen.getByRole("textbox", { name: "Payload" })).toHaveValue("https://new.example");
    fireEvent.click(screen.getByRole("button", { name: "Save command" }));
    await waitFor(() => expect(screen.queryByRole("textbox", { name: "Payload" })).toBeNull());
    const writes = callsTo("/api/settings").filter((c) => c.method === "PUT");
    expect(writes[1].json.dictation.macros.items).toEqual([
      { keyword: "new keyword", action: { kind: "open_url", payload: "https://new.example" } },
    ]);
  });

  it("does not take over a different draft opened after the failed save", async () => {
    appliedAddWithLostResponse();
    await addWithLostResponse();
    fireEvent.click(screen.getByRole("button", { name: "Close" }));
    fireEvent.click(screen.getAllByRole("button", { name: "Add command" })[0]);
    fireEvent.change(screen.getByRole("textbox", { name: "Spoken keyword" }), { target: { value: "second command" } });
    fireEvent.change(screen.getByRole("textbox", { name: "Payload" }), { target: { value: "https://second.example" } });
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));

    await screen.findByText("“type ledger”");
    expect(screen.getByRole("textbox", { name: "Spoken keyword" })).toHaveValue("second command");
    expect(screen.getByRole("textbox", { name: "Payload" })).toHaveValue("https://second.example");
    fireEvent.click(screen.getByRole("button", { name: "Save command" }));
    await waitFor(() => expect(screen.queryByRole("textbox", { name: "Payload" })).toBeNull());
    const writes = callsTo("/api/settings").filter((c) => c.method === "PUT");
    expect(writes[1].json.dictation.macros.items).toEqual([
      { keyword: "type ledger", action: { kind: "type_text", payload: "Ledger is ready." } },
      { keyword: "second command", action: { kind: "open_url", payload: "https://second.example" } },
    ]);
  });

  it.each(["absent", "changed", "ambiguous"])("keeps the draft and uncertainty when the saved row is %s", async (state) => {
    const server = appliedAddWithLostResponse();
    await addWithLostResponse();
    const saved = server.settings.dictation.macros.items[0];
    server.settings = {
      ...server.settings,
      dictation: {
        macros: {
          enabled: true,
          items: state === "absent" ? [] : state === "ambiguous" ? [saved, saved] : [
            { ...saved, action: { ...saved.action, payload: "Changed elsewhere." } },
          ],
        },
      },
    };
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));

    await screen.findByRole("textbox", { name: "Payload" });
    expect(screen.getByRole("alert")).toHaveTextContent("Command save not confirmed");
    expect(screen.getByRole("textbox", { name: "Spoken keyword" })).toHaveValue("  type ledger  ");
    expect(screen.getByRole("textbox", { name: "Payload" })).toHaveValue("Ledger is ready.");
    expect(callsTo("/api/settings").filter((c) => c.method === "PUT")).toHaveLength(1);
    expect(callsTo("/api/settings").filter((c) => !c.method)).toHaveLength(2);
  });

  it.each(["rejected request", "failed result"])("keeps explicit Test after a %s without an unrelated settings retry", async (failure) => {
    mocks.apiFetch.mockImplementation((path: string) => {
      if (path === "/api/commands/test") {
        return failure === "rejected request"
          ? Promise.reject(new Error("Test unavailable"))
          : Promise.resolve({ ok: false, error: "Test unavailable" });
      }
      return Promise.resolve(SETTINGS);
    });
    render(<CommandsCore />);
    await screen.findByText("“docs”");
    fireEvent.click(screen.getByRole("button", { name: "Test" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Test unavailable");
    expect(screen.queryByRole("button", { name: "Try again" })).toBeNull();
    expect(callsTo("/api/settings")).toHaveLength(1);
    fireEvent.click(screen.getByRole("button", { name: "Test" }));
    await waitFor(() => expect(callsTo("/api/commands/test")).toHaveLength(2));
    expect(callsTo("/api/commands/test")).toEqual([
      { method: "POST", json: SETTINGS.dictation.macros.items[0].action },
      { method: "POST", json: SETTINGS.dictation.macros.items[0].action },
    ]);
    expect(callsTo("/api/settings")).toHaveLength(1);
  });
});


it("previews a desk command without offering a local-action Test", async () => {
  mocks.apiFetch.mockImplementation(async (path: string) => path === "/api/settings"
    ? { ...SETTINGS, dictation: { macros: { enabled: true, items: [
      { keyword: "new note", action: { kind: "desk_verb", payload: "new_note" } },
    ] } } }
    : { ok: true, tested: false, preview: "opens a new note", note: "Preview · opens a new note" });
  render(<CommandsCore />);
  fireEvent.click(await screen.findByRole("button", { name: "Preview" }));
  await waitFor(() => expect(callsTo("/api/commands/test")).toEqual([
    expect.objectContaining({ method: "POST", json: { kind: "desk_verb", payload: "new_note" } }),
  ]));
  expect(await screen.findByText("Preview · opens a new note")).toBeTruthy();
  expect(screen.queryByRole("button", { name: "Test" })).toBeNull();
});
