/** The Object menu, Betterment Q5 "Ask about this, from everywhere".
 *
 * One verb, Ask about this, on every object (a person: "Ask about Mira"). It
 * opens the one Ask window with the object in About and an empty question.
 * The Object menu acts on the front window's object, else the selected icon,
 * and shows only rows that work. The real store, the real menu bar and the
 * real Ask window; the hub's Ask answer is the recorded one
 * (ask.thread.wire.json, tests/unit/test_desk_ask.py). */
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../../runtime/RuntimeBus", () => {
  const value = { state: "connected", lastFrame: null, subscribe: () => () => undefined };
  return { useRuntimeBus: () => value, useOptionalRuntimeBus: () => value, useRuntimeFrame: () => null };
});

import { EMPTY_ITEMS } from "../api";
import type { Directory, Meeting, Note, Project } from "../../lib/primitives";
import { useDesk } from "../store";
import { objectMenuEntries } from "../objectMenu";
import type { WorkMenuEntry } from "../components/DeskMenu";
import { DeskMenuBar } from "../components/DeskMenuBar";
import { AskPanel } from "../components/AskPanel";
import { DeskWindowFrame } from "../components/DeskWindow";
import { retractWindow } from "../components/window/windowRegistry";
import { clearEngineCache } from "../hooks/useEngine";
import { useScreenMembersStore } from "../screen/members";
import THREAD from "../../test/wire/ask.thread.wire.json";

type Item = Extract<WorkMenuEntry, { type: "item" }>;
const labels = (ref: string) =>
  objectMenuEntries({ ref }).filter((e): e is Item => e.type === "item").map((e) => e.label);

let asked: Array<Record<string, unknown>> = [];
function reply(body: unknown, status = 200): Response {
  return { ok: status < 400, status, headers: { get: () => "application/json" }, json: () => Promise.resolve(body), text: () => Promise.resolve(JSON.stringify(body)) } as unknown as Response;
}

beforeEach(() => {
  Element.prototype.scrollIntoView = () => {};
  localStorage.clear();
  clearEngineCache();
  asked = [];
  vi.stubGlobal("fetch", vi.fn((input: string, init: RequestInit = {}) => {
    const url = String(input);
    if (String(init.method ?? "GET") === "POST" && url.endsWith("/api/ask")) {
      asked.push(JSON.parse(String(init.body)));
      return Promise.resolve(reply(THREAD.first));
    }
    return Promise.resolve(reply({}));
  }));
  useDesk.setState({
    items: {
      ...EMPTY_ITEMS,
      note: [{ kind: "note", id: "n-mira", title: "1:1 with Mira", bodyMarkdown: "", tags: [], createdAt: "" } as Note],
      meeting: [{ kind: "meeting", id: "m1", title: "Ledger migration review", startedAt: "" } as Meeting],
      project: [{ kind: "project", id: "p1", name: "Ledger migration" } as Project],
      directory: [
        { kind: "directory", id: "d1", name: "Cutover", memberIds: [] } as unknown as Directory,
        { kind: "directory", id: "hs-seed-desk", name: "Desk", memberIds: [] } as unknown as Directory,
      ],
    },
    selectedIds: [],
    askOpen: false,
    askThread: null,
    panelOrder: [],
    panelMin: [],
    pullouts: [],
    panelRects: {},
    panelSaved: [],
  } as never);
  useScreenMembersStore.setState({
    people: { state: "ready", persons: [{ id: "mira", name: "Mira Kovacs" }] },
  });
});

afterEach(() => {
  cleanup();
  retractWindow("pullout:people:mira");
  vi.unstubAllGlobals();
});

function Desk() {
  const open = useDesk((s) => s.askOpen);
  return <><DeskMenuBar />{open ? <AskPanel /> : null}</>;
}

describe("Betterment Q5: Ask about this, on every object", () => {
  it.each([
    ["note:n-mira", "a note"],
    ["meeting:m1", "a meeting"],
    ["project:p1", "a project"],
    ["zone:d1", "a drawer"],
  ])("%s (%s) offers Ask about this, and none of the old three", (ref) => {
    const rows = labels(ref);
    expect(rows).toContain("Ask about this");
    expect(rows).not.toContain("Ask AI");
    expect(rows).not.toContain("Ask this project");
    expect(rows).not.toContain("Continue in thread");
  });

  it("no row is greyed with an excuse: every row the menu shows can run", () => {
    for (const ref of ["note:n-mira", "meeting:m1", "project:p1", "zone:d1"])
      for (const entry of objectMenuEntries({ ref })) if (entry.type === "item") expect(entry.ghost, `${ref} ${entry.label}`).toBeNull();
  });

  it("from the menu bar: the selected note, one press, Ask opens with the note in About and an empty question", async () => {
    useDesk.setState({ selectedIds: ["note:n-mira"] });
    render(<Desk />);
    fireEvent.click(screen.getByRole("button", { name: /^Note$/ }), { detail: 0 });
    const menu = screen.getByRole("menu", { name: "Note menu" });
    fireEvent.click(within(menu).getByRole("menuitem", { name: /Ask about this/ }));
    const about = await screen.findByTestId("ask-context");
    expect(about).toHaveTextContent("About1:1 with Mira");
    expect(screen.getByRole("textbox", { name: "Ask about your work" })).toHaveValue("");
    expect(asked).toEqual([]);
  });

  it("with Mira's window in front, the Person menu carries live open, ask, prep and keep verbs", async () => {
    useDesk.setState({ panelOrder: ["pullout:people:mira"] });
    render(
      <>
        <DeskWindowFrame
          id="pullout:people:mira"
          title="Mira Kovacs"
          label="Mira Kovacs"
          open
          entrance={false}
          onClose={() => {}}
        >
          Mira Kovacs
        </DeskWindowFrame>
        <Desk />
      </>,
    );
    fireEvent.click(screen.getByRole("button", { name: /^Person$/ }), { detail: 0 });
    const menu = screen.getByRole("menu", { name: "Person menu" });
    const rows = Array.from(menu.querySelectorAll("[role^=menuitem] .desk-menu-label"), (e) => e.textContent?.trim());
    expect(rows).toEqual(["Open", "Ask about Mira", "Prep 1:1", "Keep on desk"]);
    fireEvent.click(within(menu).getByRole("menuitem", { name: /Ask about Mira/ }));

    expect(await screen.findByTestId("ask-context")).toHaveTextContent("AboutMira Kovacs");
    fireEvent.change(screen.getByRole("textbox", { name: "Ask about your work" }), { target: { value: "What do I owe Mira this week?" } });
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));
    expect(await screen.findByText(THREAD.first.output)).toBeInTheDocument();
    expect(asked[0].context).toEqual([{ id: "mira", kind: "people", title: "Mira Kovacs", ref: "people:mira" }]);
  });
});
