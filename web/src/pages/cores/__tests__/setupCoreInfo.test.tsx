// The Conductor K1 (Astra r1 finding 6): an INFO doctor check stays neutral on
// the Setup core. It renders the existing lamp species unlit, never the
// warning tone.
import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { SetupCore } from "../SetupCore";
import { closeFirstRun, useFirstRunOpen } from "../../../desk/firstrun/reopen";

function json(body: unknown) {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "content-type": "application/json" },
  });
}

afterEach(() => vi.unstubAllGlobals());

describe("SetupCore info lamp", () => {
  it("renders an info check with the neutral unlit lamp", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        json({
          overall: "ready",
          first_run: false,
          sections: [
            { id: "coding-agents", label: "Coding agents", status: "info", detail: "no coding agent" },
            { id: "ffmpeg", label: "ffmpeg", status: "warn", detail: "Not found" },
          ],
        }),
      ),
    );
    render(<SetupCore />);
    const info = await screen.findByTitle("info");
    expect(info.getAttribute("data-on")).toBe("false");
    const warn = screen.getByTitle("warn");
    expect(warn.getAttribute("data-on")).toBe("true");
    expect(warn.getAttribute("data-tone")).toBe("warn");
  });
});

describe("PHILO-17 U17: Setup opens the same Get ready cards", () => {
  it.each([true, false])("first_run=%s: Get ready opens first run; no 'arrival' word, no /welcome", async (firstRun) => {
    closeFirstRun();
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => json({ overall: "ready", first_run: firstRun, sections: [] })),
    );
    render(<SetupCore />);
    const verb = await screen.findByRole("button", { name: "Get ready" });
    expect(document.body.textContent?.toLowerCase()).not.toContain("arrival");
    expect(screen.queryByRole("button", { name: "Open Desk" })).toBeNull();
    fireEvent.click(verb);
    expect(useFirstRunOpen.getState().open).toBe(true);
    closeFirstRun();
  });
});

describe("PHILO-17 U19: Setup leads with the failing check", () => {
  it("puts a failing check first, then a warning, then the rest in order", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        json({
          overall: "blocked",
          first_run: false,
          sections: [
            { id: "python", label: "Python", status: "pass" },
            { id: "ffmpeg", label: "ffmpeg", status: "warn" },
            { id: "db", label: "Database", status: "pass" },
            { id: "speech-model", label: "Speech model", status: "fail" },
          ],
        }),
      ),
    );
    render(<SetupCore />);
    await screen.findByText("Speech model");
    const titles = Array.from(document.querySelectorAll(".surface-row-text > strong")).map((n) => n.textContent);
    expect(titles).toEqual(["Speech model", "ffmpeg", "Python", "Database"]);
  });
});
