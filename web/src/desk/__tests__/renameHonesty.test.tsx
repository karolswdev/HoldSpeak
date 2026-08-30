// HS-132-07 — Rename works or is absent. No kind keeps a Rename that
// types itself into a dead end.
//
// Get Info always offered Rename while the store's update-URL map covered
// seven kinds, so meeting/artifact/chain/workbench renames fell through
// `if (!url) return;` in silence. The matrix below is the fence: every
// PrimitiveKind either has a REAL update path or a named lock.
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { PRIMITIVES, type PrimitiveKind } from "../../lib/primitives";
import { EMPTY_ITEMS } from "../api";
import { renameLock } from "../infoContract";
import { primitiveUpdateUrl } from "../store/dataSlice";
import { useDesk } from "../store";
import {
  clearWriteFailure,
  currentWriteFailure,
} from "../hooks/useWriteReceipt";
import { InfoWindow } from "../components/InfoWindow";

const KINDS = Object.keys(PRIMITIVES) as PrimitiveKind[];

/** The recorded decision per kind: a path, or the reason there is none. */
const EXPECTED: Record<PrimitiveKind, string | null> = {
  note: null,
  decision: null,
  kb: null,
  directory: null,
  recipe: null,
  workflow: null,
  project: null,
  chain: null,
  workbench: null,
  meeting: null,
  artifact: "Named by the run that minted it",
  repository: "Named by its git remote",
  roadmap: "Named by its roadmap file",
  story: "Named by its story file",
  coder: "Named by the live coder session",
  game: "Named by the game",
  layout: "Named by the desk layout",
  intelligence: "Named by the desk",
  people: "Named by the People surface",
  thread: null,
};

describe("HS-132-07 rename honesty", () => {
  it("decides every primitive kind: a real path, or a named lock", () => {
    for (const kind of KINDS) {
      const lock = renameLock(kind);
      expect([kind, lock]).toEqual([kind, EXPECTED[kind]]);
      // No third state: a kind without a lock must have a real update path
      // (zones rename through renameZone).
      if (!lock)
        expect(kind === "directory" || !!primitiveUpdateUrl(kind, "x")).toBe(true);
    }
  });

  it("carries the routes the hub already served but the map had lost", () => {
    expect(primitiveUpdateUrl("chain", "c1")).toBe("/api/chains/c1");
    expect(primitiveUpdateUrl("workbench", "w1")).toBe("/api/workbenches/w1");
    // The route this story added to the hub.
    expect(primitiveUpdateUrl("meeting", "m1")).toBe("/api/meetings/m1");
    expect(primitiveUpdateUrl("artifact", "a1")).toBeNull();
  });
});

function seed(kind: string, id: string, row: Record<string, unknown>) {
  useDesk.setState({
    items: { ...EMPTY_ITEMS, [kind]: [{ kind, id, ...row }] } as never,
  });
}

describe("HS-132-07 Get Info identity", () => {
  beforeEach(() => {
    localStorage.clear();
    clearWriteFailure();
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("renames a meeting through the hub's new route", async () => {
    const fetchMock = vi.fn(
      async (_input: RequestInfo | URL, _init?: RequestInit) =>
        new Response(JSON.stringify({ meeting: {} }), {
          status: 200,
          headers: { "content-type": "application/json" },
        }),
    );
    vi.stubGlobal("fetch", fetchMock);
    seed("meeting", "m1", { title: "Standup" });
    render(<InfoWindow refId="meeting:m1" />);

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "Standup" }));
    const well = screen.getByLabelText("Name");
    await user.clear(well);
    await user.type(well, "Quarter review{Enter}");

    const put = () =>
      fetchMock.mock.calls.find(([, init]) => init?.method === "PUT");
    await waitFor(() => expect(put()).toBeTruthy());
    const [url, init] = put()!;
    expect(String(url)).toBe("/api/meetings/m1");
    expect(JSON.parse(String(init!.body))).toEqual({
      title: "Quarter review",
    });
    expect(currentWriteFailure()).toBeNull();
  });

  it("names a refused rename in the desk's write-receipt channel", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (_input: RequestInfo | URL, init?: RequestInit) =>
        (init?.method || "GET").toUpperCase() === "PUT"
          ? new Response(JSON.stringify({}), { status: 500 })
          : new Response(JSON.stringify({}), {
              status: 200,
              headers: { "content-type": "application/json" },
            }),
      ),
    );
    seed("meeting", "m1", { title: "Standup" });
    render(<InfoWindow refId="meeting:m1" />);

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "Standup" }));
    const well = screen.getByLabelText("Name");
    await user.clear(well);
    await user.type(well, "Quarter review{Enter}");

    await waitFor(() => {
      const failure = currentWriteFailure();
      expect(failure?.verb).toBe("RENAME");
      expect(failure?.reason).toBe("HTTP 500");
    });
  });

  it("presents a locked name where no rename path exists", () => {
    seed("artifact", "a1", { title: "Summary", artifactType: "summary" });
    const { baseElement } = render(<InfoWindow refId="artifact:a1" />);
    expect(screen.queryByRole("button", { name: "Summary" })).toBeNull();
    const fixed = baseElement.querySelector(".info-name-fixed") as HTMLElement;
    expect(fixed).toBeTruthy();
    expect(fixed.textContent).toBe("Summary");
    expect(fixed.getAttribute("title")).toBe("Named by the run that minted it");
  });
});
