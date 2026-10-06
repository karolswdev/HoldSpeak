// The Conductor K1 (Astra r1 finding 6): an INFO doctor check stays neutral on
// the Setup core. It renders the existing lamp species unlit, never the
// warning tone.
import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { SetupCore } from "../SetupCore";

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
