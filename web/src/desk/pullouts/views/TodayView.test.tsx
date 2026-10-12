import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { TodayView, countdown, currentStep, toFinish } from "./TodayView";

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

const inMinutes = (n: number) => new Date(Date.now() + n * 60_000).toISOString();

function hub(routes: Record<string, (init?: RequestInit) => Response>) {
  const calls: Array<[string, RequestInit | undefined]> = [];
  vi.stubGlobal("fetch", vi.fn(async (input: string, init?: RequestInit) => {
    const key = String(input);
    calls.push([key, init]);
    const handler = routes[key];
    return handler ? handler(init) : json({}, 404);
  }));
  return calls;
}

afterEach(() => vi.unstubAllGlobals());

describe("PHILO-17 Today: the day as a timeline", () => {
  it("counts down in minutes, then hours, then now", () => {
    const now = new Date("2026-10-12T09:00:00");
    expect(countdown(new Date("2026-10-12T10:08:00"), now)).toBe("in 1 h 08 min");
    expect(countdown(new Date("2026-10-12T09:20:00"), now)).toBe("in 20 min");
    expect(countdown(new Date("2026-10-12T08:59:00"), now)).toBe("now");
  });

  it("lights Prep before the meeting, Record once it is armed or started", () => {
    const now = new Date("2026-10-12T09:00:00");
    expect(currentStep({ id: "e", source: "calendar_event", starts_at: "2026-10-12T10:00:00" }, now)).toBe(0);
    expect(currentStep({ id: "e", source: "calendar_event", starts_at: "2026-10-12T10:00:00", armed: { recording_id: "r" } }, now)).toBe(1);
    expect(currentStep({ id: "e", source: "calendar_event", starts_at: "2026-10-12T08:30:00" }, now)).toBe(1);
  });

  it("finishes only recent meetings whose summary is not made", () => {
    const now = new Date();
    const rows = [
      { id: "a", started_at: inMinutes(-60), transcriptWords: 40, intel_status: "disabled" },
      { id: "b", started_at: inMinutes(-60), transcriptWords: 40, intel_status: "ready", has_summary: true },
      { id: "c", started_at: inMinutes(-60 * 24 * 9), transcriptWords: 40, intel_status: "disabled" },
    ];
    expect(toFinish(rows, now).map((row) => row.id)).toEqual(["a"]);
  });

  it("draws the next meeting with its steps, later meetings, the owed and the decision", async () => {
    const calls = hub({
      "/api/door": () => json({ calendar_configured: true, upcoming: [
        { id: "ev1", source: "calendar_event", title: "1:1 Priya", starts_at: inMinutes(50), ends_at: inMinutes(80), person_label: "Priya Nair", person_relationship_id: "r1" },
        { id: "ev2", source: "calendar_event", title: "Ledger cutover sync", starts_at: inMinutes(120), ends_at: inMinutes(150), project_id: "p1", project_name: "Payments" },
      ] }),
      "/api/meetings?limit=40": () => json({ meetings: [] }),
      "/api/desk/needs-you": () => json({ items: [{ proposalId: "pr1", title: "Freeze the ledger on Nov 12", meetingTitle: "Ledger cutover sync" }] }),
      "/api/people/relationships": () => json({ relationships: [{ id: "r1" }] }),
      "/api/people/relationships/r1": () => json({ relationship: { commitments: [{ state: "open" }, { state: "done" }], owed_to_you: [{ state: "open" }] } }),
      "/api/proposals/pr1/confirm": () => json({ ok: true }),
    });
    render(<TodayView header={null} />);
    const next = await screen.findByTestId("today-next");
    expect(within(next).getByText("1:1 Priya")).toBeTruthy();
    expect(within(next).getByTestId("today-countdown").textContent).toMatch(/^in (49|50|51) min$/);
    expect(within(next).getByText("Prep").closest("li")?.getAttribute("aria-current")).toBe("step");
    expect(within(next).getByRole("button", { name: "Open prep" })).toBeTruthy();
    expect(within(next).getByRole("button", { name: "Record when it starts" }).className).toContain("btn--primary");
    expect(screen.getAllByTestId("today-later")).toHaveLength(1);
    expect(screen.getByTestId("today-now")).toBeTruthy();
    const owed = await screen.findByTestId("today-owed");
    await waitFor(() => expect(owed.textContent).toContain("1you owe"));
    expect(owed.textContent).toContain("1owed to you");
    const decide = screen.getByTestId("today-decide");
    fireEvent.click(within(decide).getByRole("button", { name: "Confirm" }));
    await waitFor(() => expect(calls.some(([url, init]) => url === "/api/proposals/pr1/confirm" && init?.method === "POST")).toBe(true));
    // One filled primary in the window.
    expect(document.querySelectorAll(".btn--primary")).toHaveLength(1);
  });

  it("an empty day with no calendar names the next step", async () => {
    hub({
      "/api/door": () => json({ calendar_configured: false, upcoming: [] }),
      "/api/meetings?limit=40": () => json({ meetings: [] }),
      "/api/desk/needs-you": () => json({ items: [] }),
      "/api/people/relationships": () => json({ relationships: [] }),
    });
    render(<TodayView header={null} />);
    const empty = await screen.findByTestId("today-empty");
    expect(within(empty).getByText("No calendar yet")).toBeTruthy();
    expect(within(empty).getByRole("button", { name: "Connect calendar" }).className).toContain("btn--primary");
    expect(screen.getByRole("button", { name: "Record now" }).className).not.toContain("btn--primary");
    expect(screen.queryByTestId("today-owed")).toBeNull();
  });
});
