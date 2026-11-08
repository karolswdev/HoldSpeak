// Needs you on the hub's OWN answers (the test diet,
// 2026-10-11). The answers under ./wire were captured on a real hub where an
// agent's own credential held two calls outside its worktree through the real
// gate route (`ls /etc`, and a 198-char call the hook cut), and are fenced
// against the hub's shape on every run by
// tests/integration/test_desk_agents_wire.py. Only apiFetch is a double; the
// drawer, the gate store and the needs-you reader are the real ones. The
// shade's case is parked with SystemShade (web/src/desk/_parked/attention/).
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { hubWire } from "./wire/hubWire";

const api = vi.hoisted(() => ({ fetch: vi.fn() }));
vi.mock("../../lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../lib/api")>()),
  apiFetch: api.fetch,
}));
vi.mock("../shell", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../shell")>()),
  openCoderSession: vi.fn(),
  openSurfaceOr: vi.fn(),
}));
vi.mock("../components/MicButton", () => ({ MicButton: () => null }));
vi.mock("../programs/open", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../programs/open")>()),
  openProgram: vi.fn(),
}));
// The Send well species has its own app test (send.app.test.tsx); here it is
// the seat Nudge opens, named by the note it sends.
vi.mock("../documentSendsLazy", () => ({
  NoteSendWells: ({ id }: { id: string }) => <div data-testid="note-send-wells" data-note={id} />,
}));

import { openCoderSession } from "../shell";
import { useAgentFlights } from "../agentFlights";
import { NeedsDrawer } from "../needs/NeedsDrawer";

const NEEDS = hubWire("needs-you.gate");
const HELD = hubWire("gate-proposals.held");
const LONG_CMD = (() => {
  const base = "psql -h staging-ledger -U ops -d payments -c 'select count(*) from entries where ledger_id = ";
  return base + "7".repeat(198 - base.length - 1) + "'";
})();

let decided: Array<{ url: string; json: unknown }> = [];

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(new Date(NEEDS.captured_at));
  decided = [];
  vi.mocked(openCoderSession).mockClear();
  (globalThis as { __resetNeedsYou?: () => void }).__resetNeedsYou?.();
  useAgentFlights.setState({ flights: [], sessions: [], loaded: true } as never);
  api.fetch.mockReset();
  api.fetch.mockImplementation(async (url: string, init?: { json?: unknown }) => {
    const path = String(url);
    if (path.startsWith("/api/desk/needs-you")) return NEEDS.wire;
    if (path.startsWith("/api/gate/proposals?state=held")) return HELD.wire;
    if (path.endsWith("/decide")) {
      decided.push({ url: path, json: init?.json });
      return { state: (init?.json as { decision?: string })?.decision };
    }
    if (path === "/api/door") return hubWire("door.empty").wire;
    if (path.startsWith("/api/desk/projections")) return hubWire("desk-projections.attention").wire;
    if (path === "/api/dictation/corrections") return hubWire("dictation-corrections.empty").wire;
    if (path === "/api/brief/latest") return hubWire("brief-latest.empty").wire;
    throw new Error(`no captured hub answer for ${path}`);
  });
});
afterEach(() => {
  vi.useRealTimers();
});

function rowWith(text: string): HTMLElement {
  const rows = [...document.querySelectorAll<HTMLElement>("[data-testid='needs-drawer'] [data-testid='needs-row']")];
  const hit = rows.find((li) => (li.textContent ?? "").includes(text));
  if (!hit) throw new Error(`no row with ${text}`);
  return hit;
}

describe("a held call on Needs you (Conductor R1, PHILO-14 A5)", () => {
  /** replaces: tests/e2e/test_conductor_r1_gate_row_glass.py::test_a_held_call_row_opens_the_shade_and_approve_and_deny_decide_it */
  it("the row says why it waits, the whole command, HELD CALL; Approve and Deny decide the real proposal", async () => {
    render(<NeedsDrawer />);
    await waitFor(() => expect(rowWith("ls /etc")).toBeTruthy());
    const row = rowWith("ls /etc");
    expect(row.querySelector(".needs-row-fact")?.textContent).toBe("OUTSIDE THE WORKTREE\nls /etc");
    expect(row.querySelector(".needs-row-lamp")?.textContent).toContain("Held call");
    fireEvent.click(row.querySelector("[data-verb='approve']")!);
    await waitFor(() => expect(decided).toContainEqual(expect.objectContaining({
      url: "/api/gate/proposals/toolu_glass_approve/decide", json: expect.objectContaining({ decision: "approved" }),
    })));
    fireEvent.click(rowWith("ls /etc").querySelector("[data-verb='deny']")!);
    await waitFor(() => expect(decided.some((d) => (d.json as { decision?: string })?.decision === "denied")).toBe(true));
  });

  /** replaces: tests/e2e/test_conductor_r1_gate_row_glass.py::test_a_held_call_row_opens_the_shade_and_approve_and_deny_decide_it (the cut call) */
  it("a cut call reads `… +90 CHARS` and CUT · APPROVE IN RAW, with Deny and Open, never Approve", async () => {
    render(<NeedsDrawer />);
    await waitFor(() => expect(rowWith("psql -h staging-ledger")).toBeTruthy());
    const row = rowWith("psql -h staging-ledger");
    const [reason, fact] = (row.querySelector(".needs-row-fact")?.textContent ?? "").split("\n");
    expect(reason).toBe("OUTSIDE THE WORKTREE");
    expect(fact.endsWith("… +90 CHARS")).toBe(true);
    expect(LONG_CMD.startsWith(fact.replace(/… \+90 CHARS$/, ""))).toBe(true);
    expect(row.querySelector(".needs-row-lamp")?.textContent).toContain("Cut · Approve in raw");
    expect(row.querySelector("[data-verb='approve']")).toBeNull();
    expect(row.querySelectorAll("[data-verb='deny']")).toHaveLength(1);
    expect(row.querySelectorAll("[data-verb='open']")).toHaveLength(1);
    // PHILO-15 20 (B63): Open opens the lane on Raw, where the cut call is approved.
    fireEvent.click(row.querySelector("[data-verb='open']")!);
    expect(openCoderSession).toHaveBeenCalledWith("claude:glass-r1", { raw: true });
  });
});

// ── Betterment daily D2: the chips and one verb per row, on the recorded week ──
import dailyWeek from "./fixtures/daily-week/needs-you.json";
import madeFromAction from "../programs/__fixtures__/program.from_action.json";
import { recordedGet, type Gets } from "../../test/recordedHub";
import notesCreate from "../../test/wire/notes-create.wire.json";
import destinationsTwo from "./fixtures/destinations-wire/list-two.json";

function weekRows(): HTMLElement[] {
  return [...document.querySelectorAll<HTMLElement>("[data-testid='needs-drawer'] li.needs-row")];
}
const names = () => weekRows().map((li) => li.querySelector(".needs-row-name")?.textContent ?? "").sort();

describe("Needs you on the daily week: the chips and one verb per row (Betterment D2)", () => {
  let posts: Array<{ url: string; json: unknown }>;
  beforeEach(() => {
    vi.setSystemTime(new Date(String(dailyWeek.needsYou.computedAt)));
    posts = [];
    const gets: Gets = {
      "/api/desk/needs-you?fresh=1": dailyWeek.needsYou,
      "/api/door": hubWire("door.empty").wire,
      "/api/channels/destinations": destinationsTwo,
    };
    api.fetch.mockImplementation(async (url: string, init?: { method?: string; json?: unknown }) => {
      if (init?.method === "POST") {
        posts.push({ url: String(url), json: init.json });
        if (url === "/api/notes") return structuredClone(notesCreate.wire);
        if (url === "/api/programs/from-action") return structuredClone(madeFromAction);
        return {};
      }
      return recordedGet(gets, String(url));
    });
  });

  it("People shows what each person owes, each with Nudge, named by the person", async () => {
    render(<NeedsDrawer />);
    // Owner walk 2026-11-08: Mine (his own and his decisions) is the scope
    // the window opens on; People is what people owe him. The bold face
    // (2026-11-08) dropped the narrowing chips: the mast's verbs are Mine ·
    // People.
    await waitFor(() => expect(weekRows().length).toBe(4));
    expect(screen.queryByTestId("needs-filter")).toBeNull();
    const scope = screen.getByTestId("needs-scope");
    expect(within(scope).getByRole("button", { name: "Mine" }).getAttribute("aria-pressed")).toBe("true");
    fireEvent.click(within(scope).getByTestId("needs-open-people"));
    await waitFor(() => expect(weekRows().length).toBe(5));
    const theo = weekRows().filter((row) => row.querySelector("[data-testid=needs-row-state]")?.textContent === "Theo Park");
    expect(theo.map((row) => row.querySelector(".needs-row-name")?.textContent).sort())
      .toEqual(["Profile the reconciliation job", "Write up alert rule changes"]);
    for (const row of theo) {
      const verbs = [...row.querySelectorAll<HTMLElement>("[data-testid='needs-row-verb']")].map((b) => b.dataset.verb);
      expect(verbs).toEqual(["nudge"]);
    }
    expect(screen.getByTestId("arrival-display").textContent).toBe("4 need you");
    fireEvent.click(within(scope).getByTestId("needs-chip-mine"));
    await waitFor(() => expect(weekRows().length).toBe(4));
  });

  // One verb, one name (2026-11-08, #1882): the row menu's Program entry is
  // the one Run as a program; it makes the Program from the row's action.
  it("the row's context menu ▸ Run as a program makes the Program from the row's action and opens it", async () => {
    const { openProgram } = await import("../programs/open");
    render(<NeedsDrawer />);
    await waitFor(() => expect(weekRows().length).toBe(4));
    const row = weekRows().find((li) => li.textContent?.includes("Email Dana about the cutover window"))!;
    fireEvent.contextMenu(row, { clientX: 40, clientY: 40 });
    fireEvent.click(await screen.findByRole("menuitem", { name: "Run as a program" }));
    const card = (dailyWeek.needsYou.items as Array<{ title: string; actionItemId?: string }>)
      .find((i) => i.title === "Email Dana about the cutover window")!.actionItemId;
    await waitFor(() => expect(posts).toContainEqual({ url: "/api/programs/from-action", json: { action_id: card } }));
    await waitFor(() => expect(openProgram).toHaveBeenCalledWith(String((madeFromAction as { id?: string }).id)));
  });

  // Betterment AG4: one agent session on the action (the launch sheet) is a
  // different thing from a Program; the row keeps it under its honest name.
  it("the row's context menu ▸ Hand to an agent session opens the launch sheet on the row's action (Betterment AG4)", async () => {
    const { useAgentHand } = await import("../agentHand");
    useAgentHand.setState({ origin: null });
    render(<NeedsDrawer />);
    await waitFor(() => expect(weekRows().length).toBe(4));
    const row = weekRows().find((li) => li.textContent?.includes("Email Dana about the cutover window"))!;
    fireEvent.contextMenu(row, { clientX: 40, clientY: 40 });
    fireEvent.click(await screen.findByRole("menuitem", { name: "Hand to an agent session" }));
    const card = (dailyWeek.needsYou.items as Array<{ title: string; actionItemId?: string }>)
      .find((i) => i.title === "Email Dana about the cutover window")!.actionItemId;
    expect(useAgentHand.getState().origin).toEqual({ kind: "action", id: card, title: "Email Dana about the cutover window" });
  });

  it("Mine shows his two rows with Done, and Done closes the item through follow-through", async () => {
    render(<NeedsDrawer />);
    await waitFor(() => expect(names()).toEqual([
      "Do it", "Email Dana about the cutover window", "Review design doc on settlement retries",
      "Talk about the staff path in our next one-on-one"]));
    const done = weekRows().find((li) => li.textContent?.includes("Email Dana"))!.querySelector<HTMLElement>("[data-verb='done']")!;
    expect(done.textContent).toBe("Done");
    fireEvent.click(done);
    await waitFor(() => expect(posts).toContainEqual(expect.objectContaining({
      url: "/api/follow-through/complete", json: expect.objectContaining({ verb: "done" }),
    })));
  });

  it("Nudge prepares a message in the Send well and sends nothing", async () => {
    render(<NeedsDrawer />);
    await waitFor(() => expect(weekRows().length).toBe(4));
    fireEvent.click(screen.getByTestId("needs-open-people"));
    await waitFor(() => expect(weekRows().length).toBe(5));
    const row = weekRows().find((li) => li.textContent?.includes("Write up alert rule changes"))!;
    fireEvent.click(row.querySelector<HTMLElement>("[data-verb='nudge']")!);
    const well = await screen.findByTestId("needs-nudge");
    expect(within(well).getByTestId("needs-nudge-text").textContent)
      .toMatch(/^Theo, is "Write up alert rule changes" on track for \w{3} \d{1,2} \w{3}\? Tell me if you need help\.$/);
    const seat = await within(well).findByTestId("note-send-wells");
    expect(seat.dataset.note).toBe(notesCreate.wire.note.id);
    expect(posts.map((p) => p.url)).toEqual(["/api/notes"]);
    expect(posts.some((p) => p.url.startsWith("/api/channels"))).toBe(false);
  });

  it("a decision waits for Decide; Accept, Not now and Drop are in place", async () => {
    render(<NeedsDrawer />);
    await waitFor(() => expect(weekRows().length).toBe(4));
    const row = weekRows().find((li) => li.textContent?.includes("Do it"))!;
    fireEvent.click(row.querySelector<HTMLElement>("[data-verb='decide']")!);
    const well = await screen.findByTestId("needs-decide");
    expect(within(well).getAllByRole("button").map((b) => b.textContent)).toEqual(["Accept", "Not now", "Drop", "Open item"]);
    fireEvent.click(within(well).getByRole("button", { name: "Drop: Do it" }));
    await waitFor(() => expect(posts.some((p) => /\/api\/proposals\/prop-[^/]+\/dismiss$/.test(p.url))).toBe(true));
  });
});

// ── Betterment daily D3: promises from a meeting are kept on arrival ─────────
import dailyArrival from "./fixtures/daily-week/needs-you-arrival.json";
import { useDropped } from "../needs/NeedsDrawer";

describe("Needs you after the week's summaries: kept on arrival, Drop and Undo (Betterment D3)", () => {
  let posts: Array<{ url: string; json: unknown }>;
  let needsReads: string[];
  beforeEach(() => {
    vi.setSystemTime(new Date(String(dailyArrival.needsYou.computedAt)));
    posts = [];
    needsReads = [];
    useDropped.getState().set(null);
    const gets: Gets = {
      "/api/desk/needs-you?fresh=1": dailyArrival.needsYou,
      "/api/door": hubWire("door.empty").wire,
    };
    api.fetch.mockImplementation(async (url: string, init?: { method?: string; json?: unknown }) => {
      if (init?.method === "POST") {
        posts.push({ url: String(url), json: init.json });
        return {};
      }
      if (String(url).startsWith("/api/desk/needs-you")) needsReads.push(String(url));
      return recordedGet(gets, String(url));
    });
  });

  const groups = () => [...document.querySelectorAll<HTMLElement>("[data-testid='needs-arrival']")];
  const groupNames = (g: HTMLElement) => [...g.querySelectorAll(".needs-row-name")].map((n) => n.textContent ?? "").sort();

  it("each meeting's promises are NEW under it, kept with no press; its decisions wait for Decide", async () => {
    render(<NeedsDrawer />);
    await waitFor(() => expect(groups()).toHaveLength(3));
    expect(groups().map((g) => g.querySelector("h3")?.textContent?.split(" · ")[0]).sort()).toEqual([
      "New from 1:1 with Theo", "New from Architecture review", "New from Payments platform sync",
    ]);
    // Every row of the week is in a group: nothing is left ungrouped.
    expect(document.querySelectorAll("li.needs-row").length).toBe(
      groups().reduce((n, g) => n + g.querySelectorAll("li.needs-row").length, 0));
    // Mine: his own promises and his decisions; People: what people owe him.
    const sync = groups().find((g) => g.querySelector("h3")?.textContent?.startsWith("New from Payments platform sync"))!;
    expect(groupNames(sync)).toEqual(["Email Dana about the cutover window", "Freeze ledger writes during the cutover"]);
    // No Confirm anywhere: the promises are kept; each has its one verb
    // (Drop is in the row's context menu, owner walk 2026-11-08).
    expect(document.querySelectorAll("[data-verb='confirm']")).toHaveLength(0);
    const dana = [...sync.querySelectorAll<HTMLElement>("li.needs-row")].find((li) => li.textContent?.includes("Email Dana"))!;
    expect([...dana.querySelectorAll<HTMLElement>("[data-testid='needs-row-verb']")].map((b) => b.dataset.verb))
      .toEqual(["done"]);
    const freeze = [...sync.querySelectorAll<HTMLElement>("li.needs-row")].find((li) => li.textContent?.includes("Freeze ledger"))!;
    expect(freeze.querySelector("[data-verb='decide']")).toBeTruthy();
    fireEvent.click(screen.getByTestId("needs-open-people"));
    await waitFor(() => expect(groupNames(groups().find((g) => g.querySelector("h3")?.textContent?.startsWith("New from Payments platform sync"))!))
      .toEqual(["Confirm the vendor freeze dates", "Draft the rollback runbook", "Profile the reconciliation job"]));
    // Drawn once: the hub is told these meetings were seen.
    await waitFor(() => expect(posts.find((p) => p.url === "/api/desk/needs-you/seen")).toBeTruthy());
    const seen = posts.find((p) => p.url === "/api/desk/needs-you/seen")!.json as { meeting_ids: string[] };
    expect(seen.meeting_ids.sort()).toEqual(["m-daily-architecture-review", "m-daily-platform-sync", "m-daily-theo-1on1"]);
  });

  it("Drop on a kept promise posts dismiss; Undo posts reopen", async () => {
    render(<NeedsDrawer />);
    await waitFor(() => expect(groups()).toHaveLength(3));
    fireEvent.click(screen.getByTestId("needs-open-people"));
    const row = await waitFor(() => {
      const hit = [...document.querySelectorAll<HTMLElement>("li.needs-row")].find((li) => li.textContent?.includes("Write up alert rule changes"));
      if (!hit) throw new Error("no row yet");
      return hit;
    });
    fireEvent.contextMenu(row, { clientX: 40, clientY: 40 });
    fireEvent.click(await screen.findByRole("menuitem", { name: "Drop" }));
    await waitFor(() => expect(screen.getByTestId("needs-dropped").textContent).toContain("Dropped · Write up alert rule changes"));
    const card = (dailyArrival.needsYou.items as Array<{ title: string; actionItemId?: string }>)
      .find((i) => i.title === "Write up alert rule changes")!.actionItemId;
    expect(posts).toContainEqual({ url: "/api/follow-through/complete", json: { card_id: card, verb: "dismiss", payload: {} } });
    fireEvent.click(screen.getByRole("button", { name: "Undo: Write up alert rule changes" }));
    await waitFor(() => expect(posts).toContainEqual({ url: "/api/follow-through/complete", json: { card_id: card, verb: "reopen", payload: {} } }));
    await waitFor(() => expect(needsReads.at(-1)).toBe("/api/desk/needs-you"));
  });

  it("Drop on \"Do it\" dismisses the decision; Undo restores it", async () => {
    render(<NeedsDrawer />);
    await waitFor(() => expect(groups()).toHaveLength(3));
    const row = [...document.querySelectorAll<HTMLElement>("li.needs-row")].find((li) => li.querySelector(".needs-row-name")?.textContent === "Do it")!;
    fireEvent.click(row.querySelector<HTMLElement>("[data-verb='decide']")!);
    fireEvent.click(await screen.findByRole("button", { name: "Drop: Do it" }));
    await waitFor(() => expect(screen.getByTestId("needs-dropped").textContent).toContain("Dropped · Do it"));
    expect(posts.some((p) => /\/api\/proposals\/prop-[^/]+\/dismiss$/.test(p.url))).toBe(true);
    fireEvent.click(screen.getByRole("button", { name: "Undo: Do it" }));
    await waitFor(() => expect(posts.some((p) => /\/api\/proposals\/prop-[^/]+\/restore$/.test(p.url))).toBe(true));
  });
});

// ── Betterment daily D6: a People read that failed is one line in place ──
import peopleLocked from "./fixtures/daily-week/needs-you-people-locked.json";

describe("Needs you when People could not be read (Betterment D6)", () => {
  it("says it in one line with Try again; the rows stay", async () => {
    vi.setSystemTime(new Date(String(peopleLocked.recordedAt)));
    const gets: Gets = { ...(peopleLocked.gets as Gets), "/api/door": hubWire("door.empty").wire };
    const reads: string[] = [];
    api.fetch.mockImplementation(async (url: string) => { reads.push(String(url)); return recordedGet(gets, String(url)); });
    render(<NeedsDrawer />);
    const line = await screen.findByTestId("needs-people-read-failed");
    expect(line.textContent).toContain("People could not be read");
    await waitFor(() => expect(weekRows().length).toBeGreaterThan(0));
    const before = reads.filter((u) => u.startsWith("/api/desk/needs-you")).length;
    fireEvent.click(within(line).getByRole("button", { name: "Try again" }));
    await waitFor(() => expect(reads.filter((u) => u.startsWith("/api/desk/needs-you")).length).toBe(before + 1));
    expect(reads.at(-1)).toBe("/api/desk/needs-you?fresh=1");
  });

  it("the week with People readable draws no such line", async () => {
    vi.setSystemTime(new Date(String(dailyWeek.needsYou.computedAt)));
    api.fetch.mockImplementation(async (url: string) => recordedGet({
      "/api/desk/needs-you?fresh=1": dailyWeek.needsYou, "/api/door": hubWire("door.empty").wire,
    }, String(url)));
    render(<NeedsDrawer />);
    await waitFor(() => expect(weekRows().length).toBe(4));
    expect(screen.queryByTestId("needs-people-read-failed")).toBeNull();
  });
});

// ── Send S3: the recorded channel row is a Needs-you object ───────────────
import sendNeeds from "./fixtures/send-needs/needs-send.json";
import sendNeedsUnknown from "./fixtures/send-needs/needs-send-unknown.json";
import { resetSendStore } from "../surface/send";

describe("Needs you with a prepared Send row (Send S3)", () => {
  let current: any;
  let posts: Array<{ url: string; json: any }>;
  let needsReads: string[];

  beforeEach(() => {
    resetSendStore();
    current = structuredClone(sendNeeds.needsYou);
    posts = [];
    needsReads = [];
    vi.setSystemTime(new Date(String(current.computedAt)));
    api.fetch.mockImplementation(async (url: string, init?: { method?: string; json?: unknown }) => {
      const path = String(url);
      if (init?.method === "POST") {
        posts.push({ url: path, json: init.json });
        if (path === "/api/channels/send") {
          const item = current.items[0];
          current = { ...current, count: 0, items: [], members: [] };
          return { send: { ...item.send, state: "sent", settled_at: current.computedAt } };
        }
        if (path.startsWith("/api/channels/sends/") && path.endsWith("/discard")) {
          const item = current.items[0];
          current = { ...current, count: 0, items: [], members: [] };
          return { send: { ...item.send, state: "discarded" } };
        }
        return {};
      }
      if (path.startsWith("/api/desk/needs-you")) { needsReads.push(path); return current; }
      if (path === "/api/door") return hubWire("door.empty").wire;
      if (path.startsWith("/api/channels/sends?send_id=")) return { sends: [current.items[0]?.send].filter(Boolean) };
      throw new Error(`no recorded answer for ${path}`);
    });
  });

  it("shows the frozen document, destination, producer and owner verbs; Send leaves the row", async () => {
    render(<NeedsDrawer />);
    const row = await screen.findByText("S3 private delivery — update r1 (2026-10-20)");
    const li = row.closest("li.needs-row") as HTMLElement;
    // The one rule (owner walk 2026-11-08): the revision, where, who, when.
    expect(li.querySelector(".needs-row-fact")?.textContent).toMatch(/^REV 1 · To Private team folder · by Claude Code · \d{2}:\d{2}$/);
    expect(li.textContent).toMatch(/\d{2}:\d{2}/);
    expect([...li.querySelectorAll<HTMLElement>("[data-testid='needs-row-verb']")].map((button) => button.dataset.verb))
      .toEqual(["send", "look"]);
    expect(li.querySelector("[data-testid='needs-send-discard']")).toBeTruthy();

    fireEvent.click(li.querySelector("[data-verb='look']")!);
    const preview = await screen.findByTestId("needs-send-preview");
    expect(preview.textContent).toContain("The ledger cutover is on track.");
    expect(preview.textContent).toContain("private-team-folder");

    fireEvent.click(li.querySelector("[data-verb='send']")!);
    await waitFor(() => expect(posts.some((post) => post.url === "/api/channels/send")).toBe(true));
    await waitFor(() => expect(screen.queryByText("S3 private delivery — update r1 (2026-10-20)")).toBeNull());
    expect(needsReads.at(-1)).toBe("/api/desk/needs-you");
    const sendPost = posts.find((post) => post.url === "/api/channels/send")!;
    expect(sendPost.json).toEqual(expect.objectContaining({ send_id: expect.any(String), command_id: expect.any(String) }));
  });

  it("arms Discard once and sends no request until the second press", async () => {
    render(<NeedsDrawer />);
    const row = (await screen.findByText("S3 private delivery — update r1 (2026-10-20)")).closest("li.needs-row") as HTMLElement;
    const discard = row.querySelector("[data-testid='needs-send-discard']") as HTMLElement;
    fireEvent.click(discard);
    expect(discard.textContent).toBe("Discard?");
    expect(posts).toEqual([]);
    fireEvent.click(discard);
    await waitFor(() => expect(posts.some((post) => post.url.endsWith("/discard"))).toBe(true));
    expect(posts.filter((post) => post.url.endsWith("/discard"))).toHaveLength(1);
  });
});

describe("Needs you with a recorded unknown Send (Send S3)", () => {
  it("keeps Check but withholds Try again when the hub has no replay command", async () => {
    const answer: any = structuredClone(sendNeedsUnknown.needsYou);
    delete answer.items[0].send.retry_command;
    const posts: Array<{ url: string; json: any }> = [];
    vi.setSystemTime(new Date(String(answer.computedAt)));
    api.fetch.mockImplementation(async (url: string, init?: { method?: string; json?: unknown }) => {
      const path = String(url);
      if (init?.method === "POST") {
        posts.push({ url: path, json: init.json });
        return {};
      }
      if (path.startsWith("/api/desk/needs-you")) return answer;
      if (path === "/api/door") return hubWire("door.empty").wire;
      throw new Error(`no recorded answer for ${path}`);
    });
    render(<NeedsDrawer />);
    const row = (await screen.findByText("S3 state transitions — update r1 (2026-10-20)")).closest("li.needs-row") as HTMLElement;
    expect(row.querySelector("[data-verb='check']")).toBeTruthy();
    expect(row.querySelector("[data-verb='try-again']")).toBeNull();
    expect(posts).toEqual([]);
  });

  it("reloads a settled UNKNOWN row and replays its recorded operation", async () => {
    const answer: any = structuredClone(sendNeedsUnknown.needsYou);
    const posts: Array<{ url: string; json: any }> = [];
    vi.setSystemTime(new Date(String(answer.computedAt)));
    api.fetch.mockImplementation(async (url: string, init?: { method?: string; json?: unknown }) => {
      const path = String(url);
      if (init?.method === "POST") {
        posts.push({ url: path, json: init.json });
        if (path === "/api/channels/send") return { send: answer.items[0].send };
        return {};
      }
      if (path.startsWith("/api/desk/needs-you")) return answer;
      if (path === "/api/door") return hubWire("door.empty").wire;
      throw new Error(`no recorded answer for ${path}`);
    });
    render(<NeedsDrawer />);
    const row = (await screen.findByText("S3 state transitions — update r1 (2026-10-20)")).closest("li.needs-row") as HTMLElement;
    fireEvent.click(row.querySelector("[data-verb='try-again']")!);
    await waitFor(() => expect(posts.filter((post) => post.url === "/api/channels/send")).toHaveLength(1));

    // The settled answer clears browser custody. A reload starts with the
    // recorded aggregate row and its owner-only kernel provenance.
    resetSendStore();
    fireEvent.click(row.querySelector("[data-verb='try-again']")!);
    await waitFor(() => expect(posts.filter((post) => post.url === "/api/channels/send")).toHaveLength(2));
    const attempts = posts.filter((post) => post.url === "/api/channels/send");
    expect(attempts[0].json).toEqual(answer.items[0].send.retry_command);
    expect(attempts[1].json).toEqual(answer.items[0].send.retry_command);
  });

  it("Check only rereads and a lost Try again reuses the same command id", async () => {
    resetSendStore();
    let answer: any = structuredClone(sendNeedsUnknown.needsYou);
    const posts: Array<{ url: string; json: any }> = [];
    const reads: string[] = [];
    const needsReads: string[] = [];
    let firstSend = true;
    vi.setSystemTime(new Date(String(answer.computedAt)));
    api.fetch.mockImplementation(async (url: string, init?: { method?: string; json?: unknown }) => {
      const path = String(url);
      if (init?.method === "POST") {
        posts.push({ url: path, json: init.json });
        if (path === "/api/channels/send" && firstSend) {
          firstSend = false;
          throw new Error("recording edge lost the answer");
        }
        if (path === "/api/channels/send") return { send: answer.items[0].send };
        return {};
      }
      if (path.startsWith("/api/desk/needs-you")) { needsReads.push(path); return answer; }
      if (path === "/api/door") return hubWire("door.empty").wire;
      if (path.startsWith("/api/channels/sends?send_id=")) { reads.push(path); return { sends: [answer.items[0].send] }; }
      throw new Error(`no recorded answer for ${path}`);
    });
    const opened = vi.spyOn(window, "open").mockImplementation(() => null);
    try {
      render(<NeedsDrawer />);
      const row = (await screen.findByText("S3 state transitions — update r1 (2026-10-20)")).closest("li.needs-row") as HTMLElement;
      const check = row.querySelector("[data-verb='check']") as HTMLElement;
      fireEvent.click(check);
      await waitFor(() => expect(reads.some((path) => path.startsWith("/api/channels/sends?send_id="))).toBe(true));
      expect(posts.some((post) => post.url === "/api/channels/send")).toBe(false);
      expect(opened).not.toHaveBeenCalled();

      const retry = row.querySelector("[data-verb='try-again']") as HTMLElement;
      fireEvent.click(retry);
      await waitFor(() => expect(posts.filter((post) => post.url === "/api/channels/send")).toHaveLength(1));
      await waitFor(() => expect(needsReads.at(-1)).toBe("/api/desk/needs-you"));
      fireEvent.click(row.querySelector("[data-verb='try-again']")!);
      await waitFor(() => expect(posts.filter((post) => post.url === "/api/channels/send")).toHaveLength(2));
      await waitFor(() => expect(needsReads.at(-1)).toBe("/api/desk/needs-you"));
      const attempts = posts.filter((post) => post.url === "/api/channels/send");
      expect(attempts[0].json).toEqual(attempts[1].json);
    } finally {
      opened.mockRestore();
    }
  });
});

// ── PG-LANG JRN9 to JRN11: an audit's rows and a lesson in Needs you ──────
// Recorded through the real engine (tests/integration/test_desk_program_audit.py,
// test_desk_program_lessons.py): the hub's needs-you answer (compute_needs_you).
import needsAudit from "../programs/__fixtures__/needs_you.audit.json";
import needsLesson from "../programs/__fixtures__/needs_you.lesson.json";

describe("Needs you: File, Make and a lesson are TO DECIDE rows that press the step's decide route", () => {
  let posts: Array<{ url: string; json: any }>;
  const serve = (answer: any) => {
    posts = [];
    const first = answer.items.find((row: any) => row.source === "program");
    vi.setSystemTime(new Date(String(first.since ?? first.ageToken)));
    api.fetch.mockImplementation(async (url: string, init?: { method?: string; json?: unknown }) => {
      const path = String(url);
      if (init?.method === "POST") { posts.push({ url: path, json: init.json }); return {}; }
      if (path.startsWith("/api/desk/needs-you")) return answer;
      if (path === "/api/door") return hubWire("door.empty").wire;
      if (path.startsWith("/api/gate/proposals")) return { proposals: [] };
      throw new Error(`no recorded answer for ${path}`);
    });
  };
  // Owner walk 2026-11-08: a Program row is named by its Program; the step's
  // question is the hover of its line. The row is found by its item.
  const rowOf = (item: any) => waitFor(() => {
    const li = document.querySelector<HTMLElement>(`li.needs-row[data-object-id="${item.id}"]`);
    if (!li) throw new Error(`no row ${item.id}`);
    return li;
  });
  const verbs = (li: HTMLElement) => [...li.querySelectorAll<HTMLElement>("[data-testid='needs-row-verb']")].map((b) => b.textContent);
  const menuOf = async (li: HTMLElement) => {
    fireEvent.contextMenu(li, { clientX: 40, clientY: 60 });
    return [...(await screen.findByRole("menu")).querySelectorAll<HTMLElement>("[role='menuitem']")];
  };

  it("File · Skip and Make · Skip, each sent to the step's decide route with its kind", async () => {
    serve(structuredClone(needsAudit));
    render(<NeedsDrawer />);
    const file = await rowOf((needsAudit.items as any[]).find((row) => row.program?.kind === "audit_file"));
    expect((needsAudit.items as any[]).filter((row) => row.source === "program" && row.program.kind !== "close").map((row) => row.why))
      .toEqual(["TO DECIDE", "TO DECIDE"]);
    // One verb, Decide; the choices, Later and Send are the row's menu.
    expect(verbs(file)).toEqual(["Decide"]);
    expect((await menuOf(file)).map((m) => m.textContent)).toEqual(["Open", "File", "Skip", "Later»", "Send»"]);
    fireEvent.keyDown(screen.getByRole("menu"), { key: "Escape" });
    const item = needsAudit.items.find((row: any) => row.program?.kind === "fix_program") as any;
    const make = await rowOf(item);
    expect(verbs(make)).toEqual(["Decide"]);
    fireEvent.click((await menuOf(make)).find((m) => m.textContent === "Make")!);
    await waitFor(() => expect(posts).toContainEqual({ url: item.program.decide, json: { kind: "fix_program", choice: "make" } }));
  });

  it("a lesson: Keep for this program · Keep for HoldSpeak · Skip; the press names its lesson", async () => {
    serve(structuredClone(needsLesson));
    const item = needsLesson.items.find((row: any) => row.program?.kind === "lesson") as any;
    render(<NeedsDrawer />);
    const li = await rowOf(item);
    expect(verbs(li)).toEqual(["Decide"]);
    const entries = await menuOf(li);
    expect(entries.map((m) => m.textContent).slice(1, 4)).toEqual(["Keep for this program", "Keep for HoldSpeak", "Skip"]);
    fireEvent.click(entries.find((m) => m.textContent === "Keep for HoldSpeak")!);
    await waitFor(() => expect(posts).toContainEqual({
      url: item.program.decide, json: { kind: "lesson", choice: "keep_repo", lesson_id: item.program.lessonId } }));
  });
});
