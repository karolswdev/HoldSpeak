// PHILO-13-03 (A2-W) — ONE meaning of "needs you" on the Chair. The wire is
// the oracle week minted through the real producers
// (scripts/philo13_needs_you_fixture.py: Door, Room, roster, heartbeat mute,
// meetings), never a stub that returns a count. Red on d4765b97, green after:
//
//   1. The Chair head speaks the module's number (6), and R3 is the module's
//      bounded `summary_attention` read: a FAILED meeting that the desk store
//      does not hold still counts.
//   2. The Chair's list is narrower than "needs you" and says so: ACTIONS.
//   3. Done on A1 re-reads the one snapshot at once: the Chair head and every
//      other reader of the hook (the bell, the Dock) read 5 with no reload and
//      no minute poll.
import { execFileSync } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterAll, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../../lib/api";
import { useDesk } from "../../store";
import { ChairHome } from "../ChairHome";
import { useNeedsYou } from "../../needsYou";
import { openChairWindows } from "./fixtures/openChairWindows";

// PHILO-14 A1: the Chair is the screen; these specs read its windows, so they open them first.
beforeEach(() => openChairWindows());

vi.mock("../../../lib/api", async (original) => ({
  ...(await original<typeof import("../../../lib/api")>()),
  apiFetch: vi.fn(),
}));
vi.mock("../../thoughts", () => ({ unfinishedThoughts: async () => ({ items: [] }) }));
vi.mock("../../components/MicButton", () => ({ MicButton: () => null }));
vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe: () => () => undefined }),
  useRuntimeFrame: () => null,
}));

const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../../../../..");
const FIXTURE_PYTHON = resolve(REPO_ROOT, ".venv/bin/python");
const FIXTURE_SCRIPT = resolve(REPO_ROOT, "scripts/philo13_needs_you_fixture.py");

type Wire = Record<string, any>;

let home = "";
let before: Wire;
let after: Wire;

function runFixture(mode: "seed" | "export"): Wire {
  const db = join(home, ".local", "share", "holdspeak", "holdspeak.db");
  const text = execFileSync(FIXTURE_PYTHON, [FIXTURE_SCRIPT, mode, "--db", db, "--home", home], {
    cwd: REPO_ROOT,
    env: { ...process.env, HOME: home },
    encoding: "utf8",
    maxBuffer: 32 * 1024 * 1024,
  });
  return JSON.parse(text) as Wire;
}

beforeAll(() => {
  home = mkdtempSync(join(tmpdir(), "philo13-a2w-chair-"));
  runFixture("seed");
  const exported = runFixture("export");
  before = exported.before as Wire;
  after = exported.after as Wire;
}, 60_000);

afterAll(() => {
  if (home) rmSync(home, { recursive: true, force: true });
});

/** The hub as the fixture recorded it; `state.wire` flips to `after` when the
 * real Done route (`/api/follow-through/complete`) is pressed. */
function installHub() {
  const state = { wire: before, paths: [] as string[] };
  vi.mocked(apiFetch).mockImplementation(async (path: string, init?: unknown) => {
    const value = String(path);
    state.paths.push(value);
    const wire = state.wire;
    if (value === "/api/follow-through/complete") {
      const body = (init as { json?: { card_id?: string } } | undefined)?.json;
      if (body?.card_id === "philo13-a2-A1") state.wire = after;
      return { ok: true } as never;
    }
    if (value === "/api/door") return wire.door as never;
    if (value.startsWith("/api/desk/needs-you")) return wire.needsYou as never;
    if (value === "/api/inference/assignments") return wire.assignments as never;
    if (value === "/api/settings/heartbeat") return wire.heartbeat as never;
    if (value.startsWith("/api/meetings?summary_attention=true")) {
      // The route's own filter (FAILED/RETRYING, unparked) over the real rows.
      const rows = (wire.meetingsWire.meetings as Wire[]).filter(
        (row) => row.id === "philo13-a2-failed-meeting",
      );
      return { meetings: rows, total: rows.length } as never;
    }
    if (value.startsWith("/api/meetings/")) return null as never;
    return null as never;
  });
  return state;
}

/** Any other reader of the one snapshot (the bell and the Dock read it). */
function OtherReader() {
  const { count } = useNeedsYou();
  return <span data-testid="other-reader">{String(count)}</span>;
}

describe("PHILO-13-03 A2-W — the Chair reads the one needs-you number", () => {
  beforeEach(() => {
    vi.mocked(apiFetch).mockReset();
    // The desk store holds no meetings: R3 must come from the module's
    // bounded server read, not from the page the store happens to hold.
    useDesk.setState({ items: { ...useDesk.getState().items, meeting: [] } } as never);
  });

  it("speaks the module's six, counts R3 from the server read, and draws the six members as rows", async () => {
    installHub();
    render(<><ChairHome /><OtherReader /></>);
    await waitFor(
      () => expect(screen.getByTestId("arrival-display").textContent).toMatch(/^6 need you/),
      { timeout: 3000 },
    );
    expect(screen.getByTestId("other-reader").textContent).toBe("6");
    // PHILO-14 A5: the drawer's rows ARE the members: six rows under `6 need you`
    // (Phase 16: five drawn, the sixth behind `1 more · Show all`).
    fireEvent.click(screen.getByTestId("needs-show-all"));
    expect(document.querySelectorAll("[data-testid='needs-drawer'] [data-testid='needs-row']")).toHaveLength(6);
    // No "need(s) you" on the face carries a number other than the one.
    const said = (document.body.textContent ?? "").match(/\d+ needs? you/gi) ?? [];
    expect(said.every((token) => token.startsWith("6 "))).toBe(true);
  });

  it("re-reads the one snapshot on Done: the Chair and every other reader read 5 with no reload", async () => {
    const hub = installHub();
    render(<><ChairHome /><OtherReader /></>);
    await waitFor(
      () => expect(screen.getByTestId("arrival-display").textContent).toMatch(/^6 need you/),
      { timeout: 3000 },
    );
    const a1 = [...document.querySelectorAll<HTMLElement>(".needs-row")]
      .find((row) => row.textContent?.includes("A1 close the overdue release note"));
    expect(a1).toBeDefined();
    hub.paths.length = 0;
    fireEvent.click(within(a1!).getByRole("button", { name: /^Done: / }));
    await waitFor(
      () => expect(screen.getByTestId("arrival-display").textContent).toMatch(/^5 need you/),
      { timeout: 1000 },
    );
    expect(screen.getByTestId("other-reader").textContent).toBe("5");
    // The refresh is explicit and fresh, never the cached minute poll.
    expect(hub.paths).toContain("/api/desk/needs-you?fresh=1");
  });
});
