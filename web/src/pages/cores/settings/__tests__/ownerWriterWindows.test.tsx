// One writer of the owner's name (2026-11-08): the first-run You card and the
// People window have no request of their own for /api/settings. Each window
// writes the owner's name through a Settings writer of its own
// (`useOwnerWriter`, settings/writer.ts): the revision the read gave, one 409
// word, one queue.
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fakeSettingsHub, STALE } from "./fakeSettingsHub";

const apiFetch = vi.hoisted(() => vi.fn());
const ApiError = vi.hoisted(() => class TestApiError extends Error {
  readonly status: number;
  readonly payload: unknown;

  constructor(status: number, message: string, payload?: unknown) {
    super(message);
    this.status = status;
    this.payload = payload;
  }
});
const take = vi.hoisted(() => ({
  state: "idle", take: null, failure: null, level: 0, keeping: false, message: "", playing: false,
  supported: true, kept: false, canPlay: false,
  begin: () => {}, stop: () => {}, play: () => {}, again: () => {}, keep: () => {}, finish: () => {}, leave: () => {},
}));

vi.mock("../../../../lib/api", () => ({
  apiFetch,
  ApiError,
  readableError: (cause: unknown) => cause instanceof Error ? cause.message : "Request failed",
}));
vi.mock("../../../../desk/firstrun/useFirstTake", () => ({ useFirstTake: () => take }));

import { SetupFace, type SetupInventory } from "../../../../desk/firstrun/SetupFace";
import { useOwnerName } from "../../../../desk/firstrun/ownerName";
import { PeopleCore } from "../../PeopleCore";
import { useOwnerWriter } from "../writer";

const inventory: SetupInventory = {
  owner_name: "",
  rows: [{ id: "speech", kind: "speech", label: "Speech", detail: "Whisper runs on this Mac", state: "works", action: "speech", verb: "Set up speech" }],
  people: [],
  suggestions: [],
};

beforeEach(() => {
  apiFetch.mockReset().mockImplementation(async (path: string) => {
    if (path === "/api/setup/lan") return { rows: [] };
    if (path === "/api/people/readiness") return { readiness: "ready", store: "encrypted" };
    if (String(path).startsWith("/api/people/relationships")) return { relationships: [] };
    if (path === "/api/people/suggestions") return { suggestions: [] };
    if (path === "/api/door") return { upcoming: [] };
    return {};
  });
});
afterEach(() => { cleanup(); vi.useRealTimers(); });

describe("the first-run You card writes through its window's one writer", () => {
  it("a name save carries the read's revision and lands; the next save carries the new one", async () => {
    const hub = fakeSettingsHub(apiFetch, ApiError, { _revision: "r7", owner: { name: "", aliases: [] } });
    render(<SetupFace initial={inventory} />);
    const name = screen.getByRole("textbox", { name: "Your name" });
    await waitFor(() => expect(name).toBeEnabled());

    fireEvent.change(name, { target: { value: "Karol" } });
    fireEvent.blur(name);
    await waitFor(() => expect((hub.doc.owner as { name: string }).name).toBe("Karol"));
    expect(hub.puts().map(([, init]) => init.json)).toEqual([{ owner: { name: "Karol", aliases: [] }, _revision: "r7" }]);

    fireEvent.change(name, { target: { value: "Karol S" } });
    fireEvent.blur(name);
    await waitFor(() => expect((hub.doc.owner as { name: string }).name).toBe("Karol S"));
    expect(hub.puts().map(([, init]) => init.json._revision)).toEqual(["r7", "r8"]);
  });
});

describe("the People window leaves the owner name in Settings", () => {
  it("an unset name adds no notice or settings read; the window sends no write, open or closed", async () => {
    const hub = fakeSettingsHub(apiFetch, ApiError, { _revision: "r3", owner: { name: "", aliases: [] } });
    const view = render(<PeopleCore />);
    await waitFor(() => expect(screen.queryByTestId("people-loading")).toBeNull());
    expect(screen.queryByTestId("people-who-are-you")).toBeNull();
    expect(apiFetch.mock.calls.some(([url, init]) => url === "/api/settings" && !init?.method)).toBe(false);
    view.unmount();
    expect(hub.puts()).toEqual([]);
    try { window.localStorage.removeItem("hs.people.name-asked"); } catch { /* none */ }
  });
});

describe("useOwnerWriter: the writer a window without Settings gets", () => {
  it("a save carries the read's revision; a change made elsewhere says the hub's word", async () => {
    const hub = fakeSettingsHub(apiFetch, ApiError, { _revision: "r3", owner: { name: "Karol", aliases: [] } });
    let owner!: ReturnType<typeof useOwnerName>;
    function Probe() {
      owner = useOwnerName(useOwnerWriter());
      return null;
    }
    render(<Probe />);
    await waitFor(() => expect(owner.loading).toBe(false));

    await act(async () => { owner.setName("Karol S"); await owner.flush(); });
    expect(hub.puts().map(([, init]) => init.json)).toEqual([{ owner: { name: "Karol S", aliases: [] }, _revision: "r3" }]);
    expect((hub.doc.owner as { name: string }).name).toBe("Karol S");

    hub.moveElsewhere();
    await act(async () => { owner.setName("Karol T"); await owner.flush(); });
    expect((hub.doc.owner as { name: string }).name).toBe("Karol S");
    expect(owner.error).toBe(STALE);
    expect(owner.fieldStatus("name")).toBe("Not saved");
  });
});
