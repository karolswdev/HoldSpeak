// New Project (the Door), app-level: the real Desk store, the real window
// host (SurfaceWindows) and the real DoorCore/useDoorController. Only
// apiFetch is mocked, with the hub's real answers:
//   GET  /api/connections  -> {tools: [...]}  (decodeConnectionsResponse)
//   POST /api/projects/door -> {projectId}    (ProjectDoorService.create; a blank
//        create is exempt, so the route adds no kernel fields; fenced by
//        tests/integration/test_desk_new_project.py)
//
// replaces: tests/e2e/test_hs169_door_legs_glass.py::test_cancel_door
// replaces: tests/e2e/test_hs169_door_legs_glass.py::test_blank_project (the Door-closes half;
//           the zero-watches half is tests/integration/test_desk_new_project.py)

import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { __resetSurfaces, stageSurfaceOpen } from "../../../../desk/shell";
import { SurfaceWindows } from "../../../../desk/components/SurfaceWindows";
import { useDesk } from "../../../../desk/store";
import { DeskMenuBar } from "../../../../desk/components/DeskMenuBar";
import { ApiError } from "../../../../lib/api";
// The final diet lane's recorded wires (scripts/record_room_wires.py: the real
// hub through TestClient on each browser test's own seed; nothing typed).
import D174 from "./room-door-wires/door174.json";
import S17 from "../../__tests__/room-wires/sources17.json";
import D169 from "./room-door-wires/door169.json";

const apiFetch = vi.fn();
vi.mock("../../../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../../../lib/api")>("../../../../lib/api");
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});

const DOOR_WINDOW = "surface-project-setup";
const NEW_PROJECT_ID = "proj_0a1b2c3d4e5f60718293a4b5";

function doorPosts(): Array<[string, { method?: string; json?: Record<string, unknown> }]> {
  return apiFetch.mock.calls.filter(
    ([url, init]) => String(url) === "/api/projects/door" && (init as { method?: string } | undefined)?.method === "POST",
  ) as Array<[string, { method?: string; json?: Record<string, unknown> }]>;
}

beforeEach(() => {
  localStorage.clear();
  sessionStorage.clear();
  useDesk.setState({
    windowsById: {},
    panelRects: {},
    panelSaved: [],
    panelOrder: [],
    panelMin: [],
    panelMax: [],
    zoneWindows: [],
    zoneViewPrefs: {},
  });
  __resetSurfaces();
  apiFetch.mockReset();
  apiFetch.mockImplementation((url: string, init?: { method?: string }) => {
    if (url === "/api/connections") return Promise.resolve({ tools: [] });
    if (url === "/api/projects/door" && init?.method === "POST") {
      return Promise.resolve({ projectId: NEW_PROJECT_ID });
    }
    // Everything else the Room window asks for once it opens: an empty answer.
    return Promise.resolve({});
  });
});

afterEach(__resetSurfaces);

/** The same open the browser test made: a staged `project-setup` open the
 *  window host consumes once its registry is ready. */
async function openTheDoor(): Promise<void> {
  stageSurfaceOpen("project-setup");
  render(<SurfaceWindows />);
  await screen.findByTestId("door-root", undefined, { timeout: 5000 });
  expect(useDesk.getState().windowsById[DOOR_WINDOW]?.applicationKey).toBe("project-setup");
}

describe("New Project: the Door", () => {
  it("Cancel closes the Door and creates no project", async () => {
    await openTheDoor();

    fireEvent.change(screen.getByTestId("door-outcome-input"), { target: { value: "This will be cancelled" } });
    fireEvent.click(screen.getByTestId("door-cancel"));

    await waitFor(() => expect(screen.queryByTestId("door-root")).toBeNull());
    expect(useDesk.getState().windowsById[DOOR_WINDOW]).toBeUndefined();
    expect(doorPosts()).toHaveLength(0);
  });

  it("Create with no sources sends a blank project, opens its Room and closes the Door", async () => {
    await openTheDoor();

    expect(screen.getByTestId("door-receipt").textContent).toBe("NO SOURCES · BLANK PROJECT");
    fireEvent.change(screen.getByTestId("door-outcome-input"), {
      target: { value: "Blank project for glass test" },
    });
    await act(async () => {
      fireEvent.click(screen.getByTestId("door-create"));
    });

    await waitFor(() => expect(screen.queryByTestId("door-root")).toBeNull());
    expect(doorPosts()).toHaveLength(1);
    expect(doorPosts()[0][1].json).toEqual({ outcome: "Blank project for glass test", sources: [] });
    expect(useDesk.getState().windowsById[DOOR_WINDOW]).toBeUndefined();
    expect(useDesk.getState().windowsById["surface-project-memory"]?.scope).toBe(`project:${NEW_PROJECT_ID}`);
  });
});

/* ── The final diet lane: the hub's recorded answers, replayed ──────── */

const misses: string[] = [];

function replay(gets: Record<string, unknown>) {
  misses.length = 0;
  apiFetch.mockImplementation((url: string, init: { method?: string } = {}) => {
    const method = init.method ?? "GET";
    const key = method === "GET" ? url : `${method} ${url}`;
    if (key in gets) {
      const value = gets[key] as Record<string, unknown>;
      if (value && "__status" in value) return Promise.reject(new ApiError(Number(value.__status), "recorded refusal", value.body));
      return Promise.resolve(JSON.parse(JSON.stringify(value)));
    }
    misses.push(`${method} ${url}`);
    return Promise.reject(new ApiError(404, `not recorded: ${method} ${url}`, {}));
  });
}

describe("HS-174-07: the Door's Confluence row", () => {
  // replaces: tests/e2e/test_hs174_door_confluence_glass.py::test_door_confluence_connected_1440
  // replaces: tests/e2e/test_hs174_door_confluence_glass.py::test_door_confluence_connected_393 (a shot and a clean
  //   console at 393: the console fence is here, the drawn/fit/clipped fences are the sweep's surface-project-setup case)
  it("signed in: the C row offers RECENT BLOGS and PAGES BY ID and names the account; no console error", async () => {
    const errors = vi.spyOn(console, "error");
    replay(D174.connected);
    await openTheDoor();
    const row = await screen.findByTestId("door-row-confluence");
    const text = row.textContent ?? "";
    expect(text).toContain("RECENT BLOGS");
    expect(text).toContain("PAGES BY ID");
    expect(text).toContain("SIGNED IN AS KAROLSANE@GMAIL.COM");
    expect(errors).not.toHaveBeenCalled();
    expect(misses).toEqual([]);
    errors.mockRestore();
  });

  // replaces: tests/e2e/test_hs174_door_confluence_glass.py::test_door_confluence_not_connected_1440
  it("not signed in: the Door still draws, with no SIGNED IN claim; no console error", async () => {
    const errors = vi.spyOn(console, "error");
    replay(D174.not_connected);
    await openTheDoor();
    await waitFor(() => expect(misses.filter((m) => m !== "GET /api/connections")).toEqual([]));
    expect(screen.getByTestId("door-root").textContent).not.toContain("SIGNED IN AS");
    expect(errors).not.toHaveBeenCalled();
    expect(misses).toEqual([]);
    errors.mockRestore();
  });
});

describe("PHILO-17 U30: Go ▸ Projects ▸ <name> opens the project's Room", () => {
  // replaces: tests/e2e/test_philo17_sources_glass.py::test_room_add_source_and_sign_in (its Go ▸ Projects leg at 1440;
  //   the Room half is room.app.test.tsx "PHILO-17 sources: the Room's SOURCES on a bare project")
  it("the desk's projects come from the hub's /api/projects; the pick opens that project's Room, never a drawer", async () => {
    // The production opener: SurfaceWindows registers open-project-memory (SurfaceWindows.tsx:127-133);
    // nothing is stubbed but apiFetch, which replays the hub's recorded reads for this project's Room.
    replay(S17.before);
    await useDesk.getState().refresh();
    render(
      <>
        <DeskMenuBar />
        <SurfaceWindows />
      </>,
    );
    fireEvent.click(screen.getByRole("button", { name: /^Go$/ }), { detail: 0 });
    const go = screen.getByRole("menu", { name: "Go menu" });
    fireEvent.click(within(go).getByRole("menuitem", { name: /^Projects\W*$/ }));
    fireEvent.click(screen.getByRole("menuitem", { name: /Ledger cutover/ }));
    // The Room window opens on THIS project, and its core draws the hub's Room read.
    const room = await waitFor(() => {
      const el = document.getElementById("surface-project-memory");
      expect(el).not.toBeNull();
      return el!;
    }, { timeout: 5000 });
    expect(useDesk.getState().windowsById["surface-project-memory"]?.scope).toBe(`project:${S17.pid}`);
    const headline = await within(room).findByTestId("room-headline", undefined, { timeout: 5000 });
    expect(headline.textContent).toBe("Clear here");
    expect(room.textContent).toContain("Ledger cutover");
    expect(apiFetch.mock.calls.map(([url]) => String(url))).toContain(`/api/projects/${S17.pid}/room`);
    // Never a drawer: no drawer window in the store or on the page.
    expect(Object.keys(useDesk.getState().windowsById).filter((id) => id.includes("drawer"))).toEqual([]);
    expect(document.querySelector(".drawer-window")).toBeNull();
  });
});

describe("HS-169-02: the Streamlined Door with GitHub and Jira", () => {
  // replaces: tests/e2e/test_hs169_door_glass.py::test_door_connected (the Jira pick, its counts, the receipt and the
  //   Create with both sources; the GitHub picker and counts are room.app.test.tsx and DoorCore.test.tsx; the 393
  //   unpicked Door is the sweep's surface-project-setup case)
  type Call = { method: string; path: string; request: Record<string, unknown>; status: number; answer: unknown };

  function replay169() {
    misses.length = 0;
    const room = D169.room as Record<string, unknown>;
    const counts = D169.counts as Record<string, Call>;
    apiFetch.mockImplementation((url: string, init: { method?: string; json?: Record<string, unknown> } = {}) => {
      const method = init.method ?? "GET";
      const clone = (v: unknown) => Promise.resolve(JSON.parse(JSON.stringify(v)));
      if (method === "GET" && url in D169.gets) return clone((D169.gets as Record<string, unknown>)[url]);
      if (method === "POST" && url === "/api/projects/door/count") {
        const call = counts[String(init.json?.provider)];
        if (call) return clone(call.answer);
      }
      if (method === "POST" && url === "/api/projects/door") return clone(D169.create.answer);
      if (method === "POST" && url === D169.register.path) return clone(D169.register.answer);
      const key = method === "GET" ? url : `${method} ${url}`;
      if (key in room) return clone(room[key]);
      misses.push(`${method} ${url}`);
      return Promise.reject(new ApiError(404, `not recorded: ${method} ${url}`, {}));
    });
  }

  const countPosts = () => apiFetch.mock.calls
    .filter(([url, init]) => String(url) === "/api/projects/door/count" && (init as { method?: string })?.method === "POST")
    .map(([, init]) => (init as { json: unknown }).json);

  it("Jira: pick KAN, its counts arrive, the receipt names sources and watches; Create sends both sources, closes the Door, opens the Room", async () => {
    replay169();
    await openTheDoor();
    fireEvent.change(screen.getByTestId("door-outcome-input"), { target: { value: D169.create.request.outcome } });

    fireEvent.click(await screen.findByTestId("door-trigger-github"));
    fireEvent.click(await screen.findByTestId("door-pick-karolswdev/HoldSpeak", undefined, { timeout: 5000 }));
    await screen.findByTestId("door-counts-github", undefined, { timeout: 5000 });

    fireEvent.click(screen.getByTestId("door-trigger-jira"));
    await screen.findByTestId("door-picker-jira", undefined, { timeout: 5000 });
    fireEvent.click(await screen.findByTestId("door-pick-KAN", undefined, { timeout: 5000 }));
    // The Jira count lands: the row leaves CHECKING and names the hub's host. The
    // recorded answer is live with an empty plain line (0 overdue, 0 due this
    // week), so the row draws no count line, as the hub says.
    const jiraRow = screen.getByTestId("door-row-jira");
    await waitFor(() => expect(jiraRow.textContent).toContain(D169.counts.jira.answer.host), { timeout: 5000 });
    expect(D169.counts.jira.answer.state).toBe("live");
    expect(jiraRow.textContent).not.toContain("CHECKING");
    expect(jiraRow.textContent).not.toContain("CAN'T CHECK");
    expect(screen.getByTestId("door-trigger-jira").textContent).toContain("KAN");
    if (D169.counts.jira.answer.plain) expect(within(jiraRow).getByTestId("door-counts-jira").textContent).toBe(D169.counts.jira.answer.plain);
    else expect(within(jiraRow).queryByTestId("door-counts-jira")).toBeNull();

    // The face sent the recorded count bodies, Jira scoped to the connected account and KAN.
    expect(countPosts()).toEqual([D169.counts.github.request, D169.counts.jira.request]);
    const receipt = screen.getByTestId("door-receipt").textContent?.toUpperCase() ?? "";
    expect(receipt).toContain("SOURCE");
    expect(receipt).toContain("WATCH");

    await act(async () => { fireEvent.click(screen.getByTestId("door-create")); });
    await waitFor(() => expect(screen.queryByTestId("door-root")).toBeNull(), { timeout: 5000 });
    expect(doorPosts()).toHaveLength(1);
    expect(doorPosts()[0][1].json).toEqual(D169.create.request);
    expect(useDesk.getState().windowsById[DOOR_WINDOW]).toBeUndefined();
    expect(useDesk.getState().windowsById["surface-project-memory"]?.scope).toBe(`project:${D169.pid}`);
  }, 20000);
});
