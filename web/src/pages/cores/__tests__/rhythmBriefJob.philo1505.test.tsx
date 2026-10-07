// PHILO-15 05, ruling 2: the morning Brief makes itself at its own hour
// (cadence.brief_hour, 06:00 by default), not at the end of quiet hours. The
// Rhythm row's DAILY token reads that hour from /api/cadence/status, OFF when
// the Brief job is off; an older hub without `brief_job` keeps the old token.
import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { CadenceCore } from "../CadenceCore";

function json(body: unknown) {
  return new Response(JSON.stringify(body), { status: 200, headers: { "content-type": "application/json" } });
}

function hub(status: Record<string, unknown>) {
  vi.stubGlobal("fetch", vi.fn(async (input: string) => {
    const url = String(input);
    if (url.includes("/api/settings/heartbeat"))
      return json({
        sweep_every_minutes: 15, quiet_hours: { start: 22, end: 8 }, notify: "edge",
        muted_projects: [], last_sweep_at: null, next_sweep_at: null, runs_on: null, last_remote_run_at: null,
      });
    if (url.includes("/api/brief/latest")) return json(null);
    if (url.includes("/api/projects")) return json({ projects: [] });
    if (url.includes("/api/cadence/status")) return json(status);
    if (url.includes("/api/cadence/loops")) return json({ loops: [] });
    if (url.includes("/api/cadence/history")) return json({ nudges: [] });
    return json({});
  }));
}

afterEach(() => vi.unstubAllGlobals());

describe("the Rhythm brief row's DAILY token", () => {
  it("reads the Brief job's own hour", async () => {
    hub({ enabled: false, brief_job: { enabled: true, hour: 6 } });
    render(<CadenceCore />);
    await waitFor(() => expect(screen.getByTestId("rhythm-brief-cadence").textContent).toBe("DAILY 06:00"));
  });

  it("reads OFF when the Brief job is off", async () => {
    hub({ enabled: false, brief_job: { enabled: false, hour: 6 } });
    render(<CadenceCore />);
    await waitFor(() => expect(screen.getByTestId("rhythm-brief-cadence").textContent).toBe("OFF"));
  });

  it("an older hub without brief_job keeps the quiet-hours end", async () => {
    hub({ enabled: false });
    render(<CadenceCore />);
    await waitFor(() => expect(screen.getByTestId("rhythm-brief-cadence").textContent).toBe("DAILY 08:00"));
  });
});
