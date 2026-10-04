// Regression (Astra, #822): an untitled thread with messages read `New
// thread` for ever, because the mapper gave the name before the window could
// read the first message. This runs the whole path: the hub's wire (the shape
// of thread_service._thread_dict and GET /api/threads/<id>) → the real
// mappers → the real store → the real window and its Dock chip. The
// transport is the only double.
import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const apiFetch = vi.fn();
vi.mock("../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../lib/api")>("../../lib/api");
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});

import { EMPTY_ITEMS, fromWireThread } from "../api";
import { allObjects } from "../world";
import { Pullout } from "../components/Pullout";
import { Dock } from "../components/DeskWindow";
import { registrySnapshot } from "../components/window/windowRegistry";
import { useThreadStore } from "../threads";
import { useDesk } from "../store";
import { RuntimeBusProvider } from "../../runtime/RuntimeBus";

const ID = "th_902f6b8ce0be";
const NOW = "2026-10-04T09:40:00Z";
/** One row of GET /api/threads: the hub made this thread with no title. */
const listWire = (title: string) => ({
  id: ID, title, recipe_id: null, profile_override: null, directory_id: null, call_mode: 0,
  token_in: 12, token_out: 40, created_at: NOW, updated_at: NOW, last_turn_at: NOW, mode: null,
});
/** GET /api/threads/<id>: the flat thread with its messages and their parts. */
const detailWire = (title: string, first: string | null) => ({
  ...listWire(title),
  messages: first === null ? [] : [
    { id: "m1", thread_id: ID, parent_id: null, role: "user", streaming: 0, created_at: NOW, updated_at: NOW, completed_at: NOW,
      parts: [{ id: "p1", message_id: "m1", ordinal: 0, kind: "text", text: first, sensitive: 0 }] },
    { id: "m2", thread_id: ID, parent_id: "m1", role: "assistant", streaming: 0, created_at: NOW, updated_at: NOW, completed_at: NOW,
      parts: [{ id: "p2", message_id: "m2", ordinal: 0, kind: "text", text: "Dual-write went live.", sensitive: 0 }] },
  ],
  siblings: {}, refs: [], draft_annotations: [],
});

function open(title: string, first: string | null) {
  apiFetch.mockImplementation(async (path: string) =>
    String(path).startsWith(`/api/threads/${ID}`) && !String(path).includes("/", `/api/threads/${ID}`.length) ? detailWire(title, first) : {});
  const items = { ...EMPTY_ITEMS, thread: [fromWireThread(listWire(title))!] };
  const o = allObjects(items).find((x) => x.id === ID)!;
  render(<RuntimeBusProvider><Pullout o={o} pulloutId={`thread:${ID}`} /><Dock /></RuntimeBusProvider>);
  return o;
}
const label = () => registrySnapshot.find((w) => w.id === `pullout:thread:${ID}`)?.label;
const titleBar = () => document.querySelector(".desk-window .desk-window-title")?.textContent?.trim();
const chip = () => document.querySelector(".desk-dock-chip .desk-dock-label")?.textContent?.trim();

beforeEach(() => {
  localStorage.clear();
  apiFetch.mockReset();
  useThreadStore.setState({ threads: {}, buffers: {}, loading: {} });
  useDesk.setState({ panelRects: {}, panelSaved: [], panelOrder: [], panelMin: [], panelMax: [], windowsById: {} });
  vi.stubGlobal("WebSocket", class { addEventListener() {} removeEventListener() {} close() {} send() {} readyState = 3; });
});
afterEach(() => vi.unstubAllGlobals());

describe("an untitled thread's window: hub wire → mapper → window and Dock chip", () => {
  it("is named by the first words of its first message, on the title bar, the registry and the chip", async () => {
    const o = open("", "What changed in the ledger this week?");
    expect(o.title).toBe("New thread");          // the Desk list holds no messages
    await waitFor(() => expect(label()).toBe("What changed in the ledger this week?"));
    expect(titleBar()).toBe("What changed in the ledger this week?");
    expect(chip()).toBe("What changed in the ledger this week?");
    expect(screen.getByRole("region", { name: "What changed in the ledger this week?" })).toBeTruthy();
    expect(registrySnapshot.map((w) => w.id)).toContain(`pullout:thread:${ID}`);   // the id did not change
  });

  it("with no message yet it is New thread; never the id", async () => {
    open("", null);
    await waitFor(() => expect(apiFetch).toHaveBeenCalled());
    expect(label()).toBe("New thread");
    expect(titleBar()).toBe("New thread");
    expect(chip()).toBe("New thread");
  });

  it("a thread with its own title keeps it, whatever its first message says", async () => {
    open("Ledger questions", "What changed in the ledger this week?");
    await waitFor(() => expect(useThreadStore.getState().threads[ID]?.messages.length).toBe(2));
    expect(label()).toBe("Ledger questions");
    expect(titleBar()).toBe("Ledger questions");
    expect(chip()).toBe("Ledger questions");
  });

  it("a thread whose owner named it `New thread` keeps that title", async () => {
    open("New thread", "What changed in the ledger this week?");
    await waitFor(() => expect(useThreadStore.getState().threads[ID]?.messages.length).toBe(2));
    expect(label()).toBe("New thread");
  });
});
