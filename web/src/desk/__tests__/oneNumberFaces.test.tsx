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

  it("the palette's project badge says the hub's members of that Project", async () => {
    const hub = desk.needsYou as Json;
    const room = projectsOf(desk.projects).find((p) => p.name === "A2 oracle room")!;
    render(
      <MemoryRouter>
        <DeskToolShelf />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByRole("button", { name: /Search/ }));
    const label = await screen.findByText(`Open ${room.name}`);
    const row = label.closest("li, [role=option], div");
    await waitFor(() => expect(row?.textContent).toContain(`${hub.projectCounts[room.id]} OPEN`));
  });

  it("the Chair's Brief caption says the hub's count, not the Brief's own rows", async () => {
    const hub = desk.needsYou as Json;
    await act(async () => {
      render(<ChairHome />);
    });
    const section = await screen.findByTestId("arrival-brief");
    await waitFor(() =>
      expect(within(section).getByRole("heading").textContent).toBe(`BRIEF · ${hub.count} THINGS WAITING`));
    // The Brief's own open rows are a different list (changed and broke rows
    // too); the caption does not count them.
    const shown = within(section).getAllByTestId("arrival-brief-row").length;
    const folded = Number(
      within(section).queryByTestId("arrival-brief-more")?.textContent?.match(/^(\d+) more$/)?.[1] ?? 0,
    );
    expect(shown + folded).not.toBe(hub.count);
  });
});
