// HS-132-06 — with the hub refusing, every wired write verb names its
// failure in flow. No verb may look like a no-op.
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { Note } from "../../../lib/primitives";
import { EMPTY_ITEMS } from "../../api";
import { verbById } from "../../verbRegistry";
import type { WorkMenuEntry } from "../DeskMenu";
import { useDesk } from "../../store";
import { clearWriteFailure } from "../../hooks/useWriteReceipt";
import { DeskChrome } from "../DeskChrome";

// Query helper scoped to the render root (testing-library renders into
// document.body, so this equals baseElement.querySelector).
const q = (sel: string): HTMLElement | null => document.body.querySelector(sel);
const qa = (sel: string) => document.body.querySelectorAll(sel);


vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({
    state: "connected",
    lastFrame: null,
    subscribe: () => () => undefined,
  }),
  // Recordings (2026-10-28): the menu-bar lamp reads the optional bus.
  useOptionalRuntimeBus: () => null,
}));


describe("HS-132-06 desk-floor write receipts", () => {
  beforeEach(() => {
    localStorage.clear();
    clearWriteFailure();
    useDesk.setState({ items: { ...EMPTY_ITEMS }, setup: null, error: "" });
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("keeps a landed create quiet", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response(JSON.stringify({ note: { id: "n1" } }), {
            status: 200,
            headers: { "content-type": "application/json" },
          }),
      ),
    );
    await useDesk.getState().createPrimitive("note");
    expect(q(".write-receipt")).toBeNull();
    expect(useDesk.getState().error).not.toContain("FAILED");
  });
});

/** Desk ▸ New Note: the registry verb every New menu runs. PHILO-17: the
 * Floor's right-click (floorMenu.ts) and the empty Floor (EmptyDesk) are
 * parked, with the receipts only they drew. */
function floorNewNote() {
  const verb = verbById("desk.new-note")!;
  return { onSelect: () => verb.run({ selectedRef: null }) };
}

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

describe("HS-132-06 populated-floor write receipts", () => {
  beforeEach(() => {
    localStorage.clear();
    clearWriteFailure();
    useDesk.setState({
      items: {
        ...EMPTY_ITEMS,
        note: [{ kind: "note", id: "n1", title: "Release checklist" } as Note],
      },
      updatedAt: Date.now(),
      setup: null,
      error: "",
      // No editor of an earlier case is open: a New press while the window
      // it just opened is still new puts that window in front, by design.
      editingId: null,
      newIds: [],
    });
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("names a refused floor-menu create in the system bar, and retries", async () => {
    let refuse = true;
    const fetchMock = vi.fn(async (_input: RequestInfo | URL, init?: RequestInit) => {
      const method = (init?.method || "GET").toUpperCase();
      if (method === "POST") return refuse ? json({}, 500) : json({ note: { id: "n2" } });
      return json({});
    });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <DeskChrome />
      </MemoryRouter>,
    );
    expect(q(".write-receipt")).toBeNull();

    await act(async () => {
      floorNewNote().onSelect();
    });
    await waitFor(() =>
      expect(q(".write-receipt-label")?.textContent).toBe(
        "Could not make the note",
      ),
    );
    // In flow inside the system bar — not a floating overlay.
    expect(
      q(".desk-menubar .desk-chrome-receipt .write-receipt"),
    ).toBeTruthy();

    const posts = () =>
      fetchMock.mock.calls.filter(
        ([, init]) => (init as RequestInit | undefined)?.method === "POST",
      ).length;
    const before = posts();
    await user.click(screen.getByRole("button", { name: "Try again" }));
    await waitFor(() => expect(posts()).toBe(before + 1));
    expect(q(".write-receipt-label")?.textContent).toBe(
      "Could not make the note",
    );

    // A landed retry clears the line: success is quiet.
    refuse = false;
    await user.click(screen.getByRole("button", { name: "Try again" }));
    await waitFor(() =>
      expect(q(".write-receipt")).toBeNull(),
    );
  });

});
