/** PHILO-17 (palette-rank, Astra on #1097): while the list waits for its
 * ranking reads, arrows do nothing and an Enter is remembered. It runs once,
 * on the RANKED first row, when the list draws. Typing more or Escape
 * forgets it. A name prompt still submits at once. */
import { act, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

const apiFetch = vi.fn();
vi.mock("../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../lib/api")>("../../lib/api");
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});
const opened = vi.hoisted(() => ({ rooms: [] as string[] }));
vi.mock("../shell", async () => {
  const actual = await vi.importActual<typeof import("../shell")>("../shell");
  return { ...actual, openProjectRoom: (id: string) => { opened.rooms.push(id); } };
});

import { EMPTY_ITEMS } from "../api";
import { useDesk } from "../store";
import { useNamePrompt, usePalette } from "../chromeState";
import { DeskToolShelf } from "../components/DeskToolShelf";

let releaseCounts: () => void = () => undefined;

beforeEach(() => {
  localStorage.clear();
  opened.rooms = [];
  usePalette.setState({ open: false });
  useNamePrompt.setState({ prompt: null } as never);
  useDesk.setState({
    items: { ...EMPTY_ITEMS },
    projects: [
      { id: "p-alpha", name: "Alpha release" },
      { id: "p-zeta", name: "Zeta release" },
    ] as never,
    inferenceTargets: [],
    models: [],
    setup: null,
    selectedIds: [],
    openPullout: vi.fn(),
    openToolInspector: vi.fn(),
    diveInto: vi.fn(),
  });
  apiFetch.mockReset();
  apiFetch.mockImplementation((path: string) => {
    if (path.startsWith("/api/desk/needs-you")) {
      // The counts land only when the test says so: Zeta has 2 open.
      return new Promise((resolve) => {
        releaseCounts = () => resolve({ projectCounts: { "p-zeta": 2 }, items: [], coverage: [] });
      });
    }
    if (path.startsWith("/api/people/relationships")) return Promise.resolve({ relationships: [] });
    return Promise.resolve({});
  });
});

function openDeck() {
  render(
    <MemoryRouter>
      <DeskToolShelf />
    </MemoryRouter>,
  );
  fireEvent.click(screen.getByRole("button", { name: /Search/ }));
  return screen.getByRole("combobox", { name: "Search tools and Desk items" });
}

describe("the deck while its ranking reads are out", () => {
  it("remembers an Enter and runs it on the ranked first row when the list draws", async () => {
    const input = openDeck();
    fireEvent.change(input, { target: { value: "release" } });
    fireEvent.keyDown(input, { key: "ArrowDown" }); // nothing to move to yet
    fireEvent.keyDown(input, { key: "Enter" });
    await act(async () => { await Promise.resolve(); });
    expect(opened.rooms).toEqual([]); // nothing opens before the list draws
    expect(screen.queryByRole("listbox")).toBeNull();
    await act(async () => { releaseCounts(); await Promise.resolve(); });
    // ranked: Zeta (2 open) before Alpha; the remembered Enter runs once
    await vi.waitFor(() => expect(opened.rooms).toEqual(["p-zeta"]));
    expect(usePalette.getState().open).toBe(false);
  });

  it("Escape during the hold forgets the Enter", async () => {
    const input = openDeck();
    fireEvent.change(input, { target: { value: "release" } });
    fireEvent.keyDown(input, { key: "Enter" });
    fireEvent.keyDown(document, { key: "Escape" });
    expect(usePalette.getState().open).toBe(false);
    await act(async () => { releaseCounts(); await Promise.resolve(); });
    act(() => usePalette.getState().setOpen(true));
    await screen.findByRole("listbox", {}, { timeout: 2000 });
    expect(opened.rooms).toEqual([]);
  });

  it("typing more during the hold forgets the Enter", async () => {
    const input = openDeck();
    fireEvent.change(input, { target: { value: "rel" } });
    fireEvent.keyDown(input, { key: "Enter" });
    fireEvent.change(input, { target: { value: "release" } });
    await act(async () => { releaseCounts(); await Promise.resolve(); });
    await screen.findByRole("listbox", {}, { timeout: 2000 });
    expect(opened.rooms).toEqual([]);
  });

  it("a name prompt submits at once, also during the hold", async () => {
    const submit = vi.fn();
    openDeck();
    act(() => useNamePrompt.setState({ prompt: { label: "Name the note", submit } } as never));
    const name = screen.getByTestId("palette-name");
    fireEvent.change(name, { target: { value: "Cutover notes" } });
    fireEvent.keyDown(name, { key: "Enter" });
    expect(submit).toHaveBeenCalledWith("Cutover notes", "");
  });

  it("a name prompt's Save submits its typed name during the hold", async () => {
    const submit = vi.fn();
    openDeck();
    act(() => useNamePrompt.getState().ask({ label: "Name the note", submit }));
    fireEvent.change(screen.getByTestId("palette-name"), { target: { value: "  Cutover notes  " } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    expect(submit).toHaveBeenCalledExactlyOnceWith("Cutover notes", "");
    expect(usePalette.getState().open).toBe(false);
    expect(useNamePrompt.getState().prompt).toBeNull();
  });

  it("Close abandons a name prompt without Save and returns focus to Search", async () => {
    const submit = vi.fn();
    openDeck();
    act(() => useNamePrompt.getState().ask({ label: "Name the note", submit }));
    fireEvent.change(screen.getByTestId("palette-name"), { target: { value: "Cutover notes" } });
    const launcher = screen.getByRole("button", { name: /^Search/ });
    fireEvent.click(screen.getByRole("button", { name: "Close" }));
    expect(submit).not.toHaveBeenCalled();
    expect(useNamePrompt.getState().prompt).toBeNull();
    expect(usePalette.getState().open).toBe(false);
    expect(document.activeElement).toBe(launcher);
  });
});
