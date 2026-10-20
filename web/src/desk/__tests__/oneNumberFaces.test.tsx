// One number on every face, read from one seeded desk (STATUS 2026-10-05:
// "the shade and palette show a per-Room count; the Chair caption
// `BRIEF · N THINGS WAITING` is a different count").
//
// The desk is minted by the REAL producers (`scripts/needs_you_faces_fixture.py`:
// the PHILO-13 oracle week + one Room commitment the owner waits on Priya
// for). Each face below gets the hub's real payloads and must say the hub's
// number: the shade's Projects list and the palette's project badge say the
// hub's members of that Project (`projectCounts`); the Chair's Brief caption
// says the hub's `count`.
import { execFileSync } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterAll, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn() }));

vi.mock("../../lib/api", async (original) => ({
  ...(await original<typeof import("../../lib/api")>()),
  apiFetch: mocks.apiFetch,
}));
vi.mock("../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe: () => () => undefined }),
  useRuntimeFrame: () => null,
}));
vi.mock("../thoughts", () => ({ unfinishedThoughts: async () => ({ items: [] }) }));
vi.mock("../components/MicButton", () => ({ MicButton: () => null }));
const shell = vi.hoisted(() => ({ openProjectRoom: vi.fn() }));
vi.mock("../shell", async (original) => ({
  ...(await original<typeof import("../shell")>()),
  openProjectRoom: shell.openProjectRoom,
}));
vi.mock("../projections", () => ({
  useProjections: () => ({
    projections: [], counts: {}, refresh: vi.fn().mockResolvedValue(undefined), present: vi.fn(),
  }),
}));

import { EMPTY_ITEMS } from "../api";
import { usePalette } from "../chromeState";
import { ChairHome } from "../chair/ChairHome";
import { DeskToolShelf } from "../components/DeskToolShelf";
import { SystemShade } from "../components/SystemShade";
import { resetNeedsYou } from "../needsYou";
import { useDesk } from "../store";
import { openChairWindows } from "../chair/__tests__/fixtures/openChairWindows";

// PHILO-14 A1: the Chair is the screen; these specs read its windows, so they open them first.
beforeEach(() => openChairWindows());

const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../../../..");
const PYTHON = resolve(REPO_ROOT, ".venv/bin/python");
const SCRIPT = resolve(REPO_ROOT, "scripts/needs_you_faces_fixture.py");
const WAITING_TASK = "W1 Priya sends the vendor quote";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Json = Record<string, any>;
let desk: Json;
let home: string;

function projectsOf(payload: Json): Array<{ id: string; name: string }> {
  const rows = Array.isArray(payload) ? payload : payload.projects ?? [];
  return rows.map((row: Json) => ({ id: String(row.id), name: String(row.name) }));
}

beforeAll(() => {
  home = mkdtempSync(join(tmpdir(), "one-number-faces-"));
  const text = execFileSync(PYTHON, [SCRIPT, "--home", home], {
    cwd: REPO_ROOT,
    env: { ...process.env, HOME: home },
    encoding: "utf8",
    maxBuffer: 32 * 1024 * 1024,
  });
  desk = JSON.parse(text) as Json;
}, 120_000);

afterAll(() => {
  if (home) rmSync(home, { recursive: true, force: true });
});

beforeEach(() => {
  resetNeedsYou();
  shell.openProjectRoom.mockReset();
  usePalette.setState({ open: false });
  mocks.apiFetch.mockReset();
  mocks.apiFetch.mockImplementation(async (path: string) => {
    const url = String(path);
    if (url.startsWith("/api/desk/needs-you")) return structuredClone(desk.needsYou);
    if (url.startsWith("/api/brief/latest")) return structuredClone(desk.brief);
    if (url === "/api/door") return structuredClone(desk.door);
    if (url.startsWith("/api/dictation/corrections")) return { items: [] };
    return null;
  });
  useDesk.setState({
    items: { ...EMPTY_ITEMS },
    projects: projectsOf(desk.projects) as never,
    inferenceTargets: [],
    models: [],
    setup: null,
    selectedIds: [],
    openPullout: vi.fn(),
    openToolInspector: vi.fn(),
    openChat: vi.fn(),
    diveInto: vi.fn(),
  });
});

describe("one needs-you number on every face (one seeded desk, real producers)", () => {
  it("the seeded desk tells the faces apart: a Room row the hub does not count", () => {
    const hub = desk.needsYou as Json;
    const room = projectsOf(desk.projects).find((p) => p.name === "A2 oracle room")!;
    // The Room rows alone hold the row the owner waits on Priya for ...
    const roomRows = (hub.roomItems as Json[]).filter((row) => row.projectId === room.id && !row.muted);
    expect(roomRows.map((row) => row.title)).toContain(WAITING_TASK);
    // ... and the hub's one rule does not count it.
    expect(hub.projectCounts).toEqual({ [room.id]: roomRows.length - 1 });
    expect(hub.count).toBe(hub.members.length);
  });

  it("the shade's Projects list says the hub's members of each Project", async () => {
    const hub = desk.needsYou as Json;
    const room = projectsOf(desk.projects).find((p) => p.name === "A2 oracle room")!;
    const muted = projectsOf(desk.projects).find((p) => p.name === "M1 muted room")!;
    render(<SystemShade open onClose={() => {}} onOpenMemory={() => {}} />);
    const section = await screen.findByTestId("shade-projects");
    const total = Object.values(hub.projectCounts as Record<string, number>).reduce((a, b) => a + b, 0);
    expect(within(section).getByRole("heading").textContent).toBe(`Projects · ${total} OPEN`);
    const rows = within(section).getAllByTestId("shade-project-row");
    const roomRow = rows.find((row) => row.textContent?.includes(room.name))!;
    expect(roomRow.textContent).toContain(`${hub.projectCounts[room.id]} OPEN`);
    const mutedRow = rows.find((row) => row.textContent?.includes(muted.name))!;
    expect(mutedRow.textContent).toContain("MUTED");
    expect(mutedRow.textContent).not.toMatch(/\d+ OPEN/);
  });

  it("Open on a Room row closes the shade and opens that Room", async () => {
    // replaces: tests/e2e/test_hs171_shade_glass.py::test_shade_projects_1440 (the Open leg; the 393 twin is the same DOM)
    const room = projectsOf(desk.projects).find((p) => p.name === "A2 oracle room")!;
    const onClose = vi.fn();
    render(<SystemShade open onClose={onClose} onOpenMemory={() => {}} />);
    const section = await screen.findByTestId("shade-projects");
    const row = within(section).getAllByTestId("shade-project-row").find((r) => r.textContent?.includes(room.name))!;
    fireEvent.click(within(row).getByRole("button", { name: "Open" }));
    expect(onClose).toHaveBeenCalledTimes(1);
    expect(shell.openProjectRoom).toHaveBeenCalledWith(room.id);
  });

  it("the palette's PROJECTS rows: the hub's counted Room first, the rest by name", async () => {
    // replaces: tests/e2e/test_hs171_command_deck_glass.py::test_command_deck_projects_1440 (the order leg; the 393 twin is the same DOM)
    const hub = desk.needsYou as Json;
    const real = projectsOf(desk.projects);
    const counted = real.filter((p) => (hub.projectCounts[p.id] ?? 0) > 0);
    expect(counted.map((p) => p.name)).toEqual(["A2 oracle room"]);
    // One more Room the hub does not count, named to sort before the counted one.
    useDesk.setState({ projects: [...real, { id: "proj-a1", name: "A1 quiet room" }] as never });
    render(
      <MemoryRouter>
        <DeskToolShelf />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByRole("button", { name: /Search/ }));
    fireEvent.change(screen.getByRole("combobox", { name: "Find, open or ask" }), { target: { value: "room" } });
    await screen.findByText("Open A2 oracle room");
    await waitFor(() => {
      const labels = screen.queryAllByRole("option")
        .filter((o) => o.id.startsWith("desk-palette-option-project.open."))
        .map((o) => o.querySelector(".desk-deck-label")?.textContent);
      expect(labels).toEqual(["Open A2 oracle room", "Open A1 quiet room", "Open M1 muted room"]);
    });
  });

  it("the palette's project badge says the hub's members of that Project", async () => {
    const hub = desk.needsYou as Json;
    const room = projectsOf(desk.projects).find((p) => p.name === "A2 oracle room")!;
    render(
      <MemoryRouter>
        <DeskToolShelf />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByRole("button", { name: /Search/ }));
    fireEvent.change(screen.getByRole("combobox", { name: "Find, open or ask" }), { target: { value: "room" } });
    const label = await screen.findByText(`Open ${room.name}`);
    const row = label.closest("li, [role=option], div");
    await waitFor(() => expect(row?.textContent).toContain(`${hub.projectCounts[room.id]} OPEN`));
  });

  it("the palette re-reads the hub when it opens again: a muted Room loses its badge", async () => {
    const hub = desk.needsYou as Json;
    const after = desk.needsYouAfterMute as Json;
    const room = projectsOf(desk.projects).find((p) => p.name === "A2 oracle room")!;
    expect(after.projectCounts?.[room.id] ?? 0).toBe(0);
    let answer: Json = hub;
    mocks.apiFetch.mockImplementation(async (path: string) => {
      const url = String(path);
      if (url.startsWith("/api/desk/needs-you")) return structuredClone(answer);
      return null;
    });
    render(
      <MemoryRouter>
        <DeskToolShelf />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByRole("button", { name: /Search/ }));
    fireEvent.change(screen.getByRole("combobox", { name: "Find, open or ask" }), { target: { value: "room" } });
    const label = await screen.findByText(`Open ${room.name}`);
    await waitFor(() =>
      expect(label.closest("li, [role=option], div")?.textContent).toContain(`${hub.projectCounts[room.id]} OPEN`));
    // The owner mutes the Room; the palette closes and opens again.
    answer = after;
    act(() => usePalette.setState({ open: false }));
    act(() => usePalette.setState({ open: true }));
    fireEvent.change(screen.getByRole("combobox", { name: "Find, open or ask" }), { target: { value: "room" } });
    const again = await screen.findByText(`Open ${room.name}`);
    await waitFor(() =>
      expect(again.closest("li, [role=option], div")?.textContent).not.toMatch(/\d+ OPEN/));
  });

});
