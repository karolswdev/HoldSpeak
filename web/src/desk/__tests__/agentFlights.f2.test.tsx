// Conductor F2: the agents store's pure parts (wire, labels, the item join,
// the live set, the merge receipt), the flight chip and verbs (K4a/K4b), and
// the `coder:<key>` open (K5a).
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import {
  flightForItem,
  flightLabel,
  fromWireFlight,
  fromWireSessionRow,
  itemOriginRefs,
  liveAgentSessions,
  mergeReceipt,
  useAgentFlights,
} from "../agentFlights";
import { FlightChip, FlightVerbs } from "../components/AgentFlight";
import { refOpener } from "../openObject";
import { openCoderSession } from "../shell";

vi.mock("../shell", async (original) => ({
  ...(await original<typeof import("../shell")>()),
  openCoderSession: vi.fn(),
}));

const wire = (over: Record<string, unknown> = {}) => ({
  origin_ref: "action:a1", kind: "action", id: "a1", title: "Write the rollback runbook",
  project_id: "p1", project_name: "Payments ledger cutover", agent: "claude", state: "waiting",
  session_key: "claude:s1", pr: null, close: null, merged_at: null, ...over,
});

describe("the flight's words", () => {
  it("names the agent in flight, then the PR once it exists", () => {
    expect(flightLabel(fromWireFlight(wire()))).toBe("CLAUDE CODE · WAITING");
    expect(flightLabel(fromWireFlight(wire({ agent: "codex", state: "working" })))).toBe("CODEX · WORKING");
    expect(flightLabel(fromWireFlight(wire({ state: "pr_open", pr: { number: 412, url: "u", state: "open" } })))).toBe("PR #412 · OPEN");
    expect(flightLabel(fromWireFlight(wire({ state: "merged", pr: { number: 413, url: "u", state: "merged" } })))).toBe("PR #413 · MERGED");
    // No session bound yet: STARTING. Ended or expired draws nothing.
    expect(flightLabel(fromWireFlight(wire({ state: "starting", session_key: null })))).toBe("CLAUDE CODE · STARTING");
    expect(flightLabel(fromWireFlight(wire({ state: "ended" })))).toBeNull();
    expect(flightLabel(fromWireFlight(wire({ state: "expired" })))).toBeNull();
  });
});

describe("the item join", () => {
  it("knows a row by its action item, its Door card or its decision ref", () => {
    expect(itemOriginRefs({ actionItemId: "a1" })).toEqual(["action:a1"]);
    expect(itemOriginRefs({ _doorCard: { target_ref: "action_item:a2" } })).toEqual(["action:a2"]);
    expect(itemOriginRefs({ ref: "decision:d1", openRef: "decision:d1" })).toEqual(["decision:d1"]);
    expect(itemOriginRefs({ ref: "Write the runbook" })).toEqual([]);
    // Conductor R4: a Room issue row is known by its Watch and entity.
    expect(itemOriginRefs({ kind: "issue", watchId: "w1", entityId: "PAY-418" })).toEqual(["issue:w1.PAY-418"]);
  });

  it("finds the row's flight and skips an ended one", () => {
    const flights = [fromWireFlight(wire()), fromWireFlight(wire({ origin_ref: "decision:d1", state: "ended" }))];
    expect(flightForItem(flights, { actionItemId: "a1" })?.state).toBe("waiting");
    expect(flightForItem(flights, { ref: "decision:d1" })).toBeNull();
  });
});

describe("the live set (K4c, K6)", () => {
  it("drops ended sessions and sessions K4 cleaned up; keeps a merged one still awaiting confirm or cleanup", () => {
    const rows = [
      fromWireSessionRow({ session: { agent: "claude", session_id: "s1", state: "waiting", question: "Jordan or Avery?", hook_event_name: "Notification", repo_root: "/x/payments-ledger-runbook" }, flight: wire() }),
      fromWireSessionRow({ session: { agent: "codex", session_id: "x1", state: "working" } }),
      fromWireSessionRow({ session: { agent: "claude", session_id: "s2", state: "ended" } }),
      fromWireSessionRow({ session: { agent: "claude", session_id: "s3", state: "working" }, flight: wire({ state: "merged", close: "closed", session_cleanup: "killed" }) }),
      // Secure: merged, the close waits for the owner, the session is alive.
      fromWireSessionRow({ session: { agent: "claude", session_id: "s4", state: "working" }, flight: wire({ state: "merged", close: "awaiting_confirm" }) }),
      // Closed, cleanup still outstanding.
      fromWireSessionRow({ session: { agent: "claude", session_id: "s5", state: "working" }, flight: wire({ state: "merged", close: "closed" }) }),
    ];
    expect(rows[0]).toMatchObject({ key: "claude:s1", name: "payments-ledger-runbook", blocked: true });
    expect(rows[0].flight?.title).toBe("Write the rollback runbook");
    expect(liveAgentSessions(rows).map((r) => r.key)).toEqual(["claude:s1", "codex:x1", "claude:s4", "claude:s5"]);
  });

  it("the merge receipt: this Project's newest closed merge within a day", () => {
    const now = new Date("2026-10-06T16:00:00Z");
    const merged = (over: Record<string, unknown>) => fromWireFlight(wire({ state: "merged", close: "closed", pr: { number: 413, url: "u", state: "merged" }, ...over }));
    expect(mergeReceipt([merged({ merged_at: "2026-10-06T15:29:00Z" })], "p1", now)?.pr?.number).toBe(413);
    expect(mergeReceipt([merged({ merged_at: "2026-10-04T15:29:00Z" })], "p1", now)).toBeNull();
    expect(mergeReceipt([merged({ merged_at: "2026-10-06T15:29:00Z", close: "awaiting_confirm" })], "p1", now)).toBeNull();
    expect(mergeReceipt([merged({ merged_at: "2026-10-06T15:29:00Z" })], "p2", now)).toBeNull();
  });
});

describe("the store keeps a refresh that arrives mid-read (finding 5)", () => {
  it("one trailing read follows the outstanding GET, and its answer lands", async () => {
    const api = await import("../../lib/api");
    const spy = vi.spyOn(api, "apiFetch");
    let first!: (v: unknown) => void;
    spy.mockImplementationOnce(() => new Promise((r) => { first = r; }) as never);
    spy.mockImplementationOnce(async () => ({ sessions: [], flights: [wire({ state: "merged", close: "closed", session_cleanup: "killed", pr: { number: 413, url: "u", state: "merged" } })] }) as never);
    useAgentFlights.setState({ sessions: [], flights: [], loaded: false });
    const a = useAgentFlights.getState().load();
    void useAgentFlights.getState().load();       // the frame that arrives mid-read
    first({ sessions: [], flights: [wire()] });
    await a;
    await vi.waitFor(() => expect(useAgentFlights.getState().flights[0]?.state).toBe("merged"));
    expect(spy).toHaveBeenCalledTimes(2);
    spy.mockRestore();
  });
});

describe("FlightChip and FlightVerbs (K4a, K4b)", () => {
  it("in flight: the chip and Session, which opens the agent's session", () => {
    const flight = fromWireFlight(wire());
    render(<><FlightChip flight={flight} /><FlightVerbs flight={flight} title="Write the rollback runbook" /></>);
    expect(screen.getByTestId("flight-chip").textContent).toContain("CLAUDE CODE · WAITING");
    fireEvent.click(screen.getByRole("button", { name: "Open session: Write the rollback runbook" }));
    expect(openCoderSession).toHaveBeenCalledWith("claude:s1");
    expect(screen.queryByText("GITHUB.COM")).toBeNull();
  });

  it("PR open: the GITHUB.COM egress chip and Open PR", () => {
    const flight = fromWireFlight(wire({ state: "pr_open", session_key: null, pr: { number: 412, url: "https://github.com/a/b/pull/412", state: "open" } }));
    const open = vi.spyOn(window, "open").mockImplementation(() => null);
    render(<FlightVerbs flight={flight} title="Add the flag" />);
    expect(screen.getByText("GITHUB.COM")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Open PR #412: Add the flag" }));
    expect(open).toHaveBeenCalledWith("https://github.com/a/b/pull/412", "_blank", "noopener");
  });

  it("no flight draws nothing", () => {
    const { container } = render(<><FlightChip flight={null} /><FlightVerbs flight={null} title="x" /></>);
    expect(container.textContent).toBe("");
  });
});

describe("a coder ref opens (K5a)", () => {
  it("coder:<agent>:<session> opens the session window", () => {
    refOpener("coder:claude:s1")?.();
    expect(openCoderSession).toHaveBeenCalledWith("claude:s1");
    expect(refOpener("coder:")).toBeNull();
  });
});
