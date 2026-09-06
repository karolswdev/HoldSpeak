/* HS-176-05 — the `Learned` wing (settled design D2(c), boards `Learned` /
   `LearnedQuiet` / `LearnedPhone`): the kind emblem in the lead slot, the
   key -> LABEL row, the real `N APPLIED` count absent at zero, `Forget`,
   and the one-token empty state. */
import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { Learned, appliedToken, kindEmblem, valueLabel } from "../Learned";

const mocks = vi.hoisted(() => ({
  apiFetch: vi.fn(),
  listeners: new Map<string, (frame: { type: string; data: unknown }) => void>(),
}));

vi.mock("../../../../lib/api", () => ({
  apiFetch: mocks.apiFetch,
  readableError: (e: unknown) => (e instanceof Error ? e.message : "failed"),
}));

// `useRuntimeBus` throws outside its provider (RuntimeBus.tsx:106-111); the
// LiveCore.test.tsx pattern is to mock the module and drive the frames.
vi.mock("../../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({
    state: "connected",
    lastFrame: null,
    subscribe: (
      type: string,
      listener: (frame: { type: string; data: unknown }) => void,
    ) => {
      mocks.listeners.set(type, listener);
      return () => mocks.listeners.delete(type);
    },
  }),
}));

const OVERRIDES = [
  { id: "claude_code", label: "Claude Code" },
  { id: "terminal_shell", label: "Terminal shell" },
];
const BLOCKS = {
  document: { blocks: [{ id: "delivery", description: "Delivery" }] },
};

/** The three rows the 1440 board draws. */
const RULES = [
  { id: 3, kind: "text", key: "queue for", value: "Q4", applied: 1 },
  {
    id: 5,
    kind: "intent",
    key: "ship the q4 platform on schedule",
    value: "delivery",
    applied: 3,
  },
  {
    id: 7,
    kind: "target",
    key: "payments cut-over runbook",
    value: "terminal_shell",
    applied: 0,
  },
];

let items: Record<string, unknown>[] = [];
const deleted: string[] = [];

function mountRoutes() {
  mocks.apiFetch.mockImplementation(
    (url: string, init?: { method?: string }) => {
      const path = String(url);
      if (init?.method === "DELETE" && path.startsWith("/api/dictation/corrections/")) {
        deleted.push(path);
        items = [];
        return Promise.resolve({});
      }
      if (path.startsWith("/api/dictation/corrections"))
        return Promise.resolve({ items });
      if (path.startsWith("/api/dictation/readiness"))
        return Promise.resolve({ target: { overrides: OVERRIDES } });
      if (path.startsWith("/api/dictation/blocks")) return Promise.resolve(BLOCKS);
      return Promise.resolve({});
    },
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  mocks.listeners.clear();
  deleted.length = 0;
  items = RULES.map((rule) => ({ ...rule }));
  mountRoutes();
});

function rows(): HTMLElement[] {
  return Array.from(
    document.querySelectorAll<HTMLElement>(".speak-learned .surface-ledger-row"),
  );
}

describe("the Learned wing's rows", () => {
  it("draws one row per rule: the kind emblem, the key, the value, the count", async () => {
    render(<Learned />);
    await waitFor(() => expect(rows()).toHaveLength(3));

    const [text, intent, target] = rows();

    // the lead slot is the emblem (canon B), never a free-text column
    expect(
      within(text).getByText("TEXT", { selector: ".learned-kind" }),
    ).toBeTruthy();
    expect(
      within(intent).getByText("INTENT", { selector: ".learned-kind" }),
    ).toBeTruthy();
    expect(
      within(target).getByText("TARGET", { selector: ".learned-kind" }),
    ).toBeTruthy();

    // the primary is the key; the cells carry `-> value`
    expect(within(text).getByText("queue for")).toBeTruthy();
    expect(
      within(text).getByText("Q4", { selector: ".learned-value" }),
    ).toBeTruthy();
  });

  it("prints the routing value's LABEL, never its raw id (canon E.4, R12)", async () => {
    render(<Learned />);
    await waitFor(() => expect(rows()).toHaveLength(3));
    const body = document.querySelector(".speak-learned")!.textContent ?? "";
    expect(body).toContain("Delivery");
    expect(body).toContain("Terminal shell");
    expect(body).not.toContain("terminal_shell");
    expect(body).not.toContain("delivery");
  });

  it("`N APPLIED` is the real count, and is ABSENT at zero (rule A.8)", async () => {
    render(<Learned />);
    await waitFor(() => expect(rows()).toHaveLength(3));
    const [text, intent, target] = rows();
    expect(within(text).getByText("1 APPLIED")).toBeTruthy();
    expect(within(intent).getByText("3 APPLIED")).toBeTruthy();
    // the never-fired rule says nothing — no `0 APPLIED`
    expect(within(target).queryByText(/APPLIED/)).toBeNull();
    // ...but the slot is still there, so its neighbours never move
    expect(target.querySelector(".learned-applied")).toBeTruthy();
  });

  it("carries no caption count — the tab is the name (ruling N5b, A.7)", async () => {
    render(<Learned />);
    await waitFor(() => expect(rows()).toHaveLength(3));
    const caption = document.querySelector(".speak-learned .surface-ledger-count");
    expect((caption?.textContent ?? "").trim()).toBe("");
    // `LEARNED` is said once per face — on the wing tab, never in the body
    expect(document.querySelector(".speak-learned")!.textContent).not.toContain(
      "LEARNED",
    );
  });

  it("every verb is the library Button — no raw <button> in the wing", async () => {
    render(<Learned />);
    await waitFor(() => expect(rows()).toHaveLength(3));
    const raw = Array.from(
      document.querySelectorAll<HTMLButtonElement>(".speak-learned button"),
    ).filter(
      (b) =>
        !b.classList.contains("btn") &&
        !b.classList.contains("surface-ledger-line"),
    );
    expect(raw.map((b) => b.className)).toEqual([]);
  });
});

describe("Forget", () => {
  it("confirms in-world, then DELETEs the rule and re-reads", async () => {
    render(<Learned />);
    await waitFor(() => expect(rows()).toHaveLength(3));

    const forget = within(rows()[0]).getByRole("button", { name: "Forget" });
    await userEvent.click(forget);
    // one step, in-world (no modal)
    expect(screen.queryByRole("dialog")).toBeNull();
    await userEvent.click(
      within(rows()[0]).getByRole("button", { name: "Forget?" }),
    );

    // the verb is the WORD, never the `x` glyph (rule A.1 / HS-176-02)
    expect(screen.queryByRole("button", { name: "×" })).toBeNull();
    await waitFor(() => expect(deleted).toEqual(["/api/dictation/corrections/3"]));
    // the wing re-read and now stands quiet
    await waitFor(() => expect(screen.getByText("NOTHING LEARNED")).toBeTruthy());
  });
});

describe("the quiet wing", () => {
  it("says ONE token and no zero: NOTHING LEARNED", async () => {
    items = [];
    render(<Learned />);
    await waitFor(() => expect(screen.getByText("NOTHING LEARNED")).toBeTruthy());
    expect(rows()).toHaveLength(0);
    const body = document.querySelector(".speak-learned")!.textContent ?? "";
    expect(body).not.toContain("0 ");
    expect(body).not.toContain(".");
  });
});

describe("the live refresh", () => {
  it("re-reads on a `learning_event` frame", async () => {
    items = [];
    render(<Learned />);
    await waitFor(() => expect(screen.getByText("NOTHING LEARNED")).toBeTruthy());

    items = [{ id: 9, kind: "text", key: "queue for", value: "Q4", applied: 0 }];
    const listener = mocks.listeners.get("learning_event");
    expect(listener).toBeTruthy();
    act(() => listener!({ type: "learning_event", data: {} }));

    await waitFor(() => expect(rows()).toHaveLength(1));
    expect(screen.getByText("queue for")).toBeTruthy();
  });
});

describe("the pure helpers", () => {
  it("kindEmblem renders human tokens, never snake_case", () => {
    expect(kindEmblem("text")).toBe("TEXT");
    expect(kindEmblem("intent")).toBe("INTENT");
    expect(kindEmblem("target")).toBe("TARGET");
    expect(kindEmblem("some_new_kind")).toBe("SOME NEW KIND");
    expect(kindEmblem(undefined)).toBe("");
  });

  it("valueLabel resolves through the two label sources", () => {
    const blocks = { delivery: "Delivery" };
    const targets = { terminal_shell: "Terminal shell" };
    expect(valueLabel({ kind: "text", value: "Q4" }, blocks, targets)).toBe("Q4");
    expect(
      valueLabel({ kind: "intent", value: "delivery" }, blocks, targets),
    ).toBe("Delivery");
    expect(
      valueLabel({ kind: "target", value: "terminal_shell" }, blocks, targets),
    ).toBe("Terminal shell");
    // an id neither map carries still reads as words, never snake_case
    expect(valueLabel({ kind: "target", value: "new_thing" }, blocks, targets)).toBe(
      "new thing",
    );
  });

  it("appliedToken is absent at zero", () => {
    expect(appliedToken({ applied: 4 })).toBe("4 APPLIED");
    expect(appliedToken({ applied: 0 })).toBe("");
    expect(appliedToken({})).toBe("");
  });
});
