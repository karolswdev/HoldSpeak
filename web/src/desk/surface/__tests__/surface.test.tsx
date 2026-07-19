// HS-98-01 — the surface kit: honest formatters, the one state
// grammar, revealed row verbs, the inline two-step, and the reference
// core (Cadence) rendering with ZERO page grammar in its DOM.
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  ConfirmVerb,
  MetricStrip,
  SurfaceRow,
  SurfaceRows,
  SurfaceState,
} from "../Surface";
import { deSnake, humanTime, presentValue } from "../format";
import { CadenceCore } from "../../../pages/cores/CadenceCore";

afterEach(() => {
  vi.restoreAllMocks();
  vi.useRealTimers();
});

describe("honest formatters (idiom rule 4)", () => {
  it("humanTime: relative near, dated far, empty on junk", () => {
    expect(humanTime(new Date(Date.now() - 10_000).toISOString())).toBe(
      "just now",
    );
    expect(humanTime(new Date(Date.now() - 5 * 60_000).toISOString())).toBe(
      "5m ago",
    );
    expect(humanTime(new Date(Date.now() - 3 * 3_600_000).toISOString())).toBe(
      "3h ago",
    );
    expect(humanTime("2019-03-05T10:00:00Z")).toMatch(/Mar/);
    expect(humanTime("not a time")).toBe("");
    expect(humanTime(null)).toBe("");
    // Epoch seconds (the wire sends both).
    expect(humanTime(Math.floor(Date.now() / 1000) - 120)).toBe("2m ago");
  });

  it("deSnake reads identifiers as words", () => {
    expect(deSnake("agent_question")).toBe("agent question");
    expect(deSnake("live-transcript")).toBe("live transcript");
  });

  it("presentValue omits meaningless values instead of printing theater", () => {
    expect(presentValue("unknown")).toBe("");
    expect(presentValue("None")).toBe("");
    expect(presentValue("")).toBe("");
    expect(presentValue(null)).toBe("");
    expect(presentValue("ready")).toBe("ready");
    expect(presentValue(0)).toBe("0");
  });
});

describe("one state grammar (idiom rule 6)", () => {
  it("loading is a status, error an alert with retry, empty a quiet label", () => {
    const { rerender } = render(<SurfaceState loading />);
    expect(screen.getByRole("status")).toBeInTheDocument();
    const retry = vi.fn();
    rerender(<SurfaceState error="It broke" onRetry={retry} />);
    expect(screen.getByRole("alert")).toHaveTextContent("It broke");
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(retry).toHaveBeenCalled();
    rerender(<SurfaceState empty emptyLabel="No loops" />);
    expect(screen.getByText("No loops")).toBeInTheDocument();
    rerender(
      <SurfaceState>
        <p>content</p>
      </SurfaceState>,
    );
    expect(screen.getByText("content")).toBeInTheDocument();
  });
});

describe("rows and verbs (idiom rules 3–5)", () => {
  it("a row carries title, detail, meta, and a verb slot", () => {
    render(
      <SurfaceRows>
        <SurfaceRow
          title="Ship the phase"
          detail="agent question"
          meta="7d"
          verbs={<button type="button">Reply</button>}
        />
      </SurfaceRows>,
    );
    expect(screen.getByText("Ship the phase")).toBeInTheDocument();
    expect(screen.getByText("agent question")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reply" })).toBeInTheDocument();
  });

  it("onOpen makes the row body one press target", () => {
    const open = vi.fn();
    render(
      <SurfaceRows>
        <SurfaceRow title="A meeting" onOpen={open} />
      </SurfaceRows>,
    );
    fireEvent.click(screen.getByRole("button", { name: "A meeting" }));
    expect(open).toHaveBeenCalled();
  });

  it("MetricStrip omits empty figures (never zero-theater)", () => {
    const { container } = render(
      <MetricStrip
        items={[
          { label: "meetings", value: 12 },
          { label: "confidence", value: "unknown" },
          { label: "actions", value: "" },
        ]}
      />,
    );
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.queryByText("confidence")).toBeNull();
    expect(container.querySelectorAll(".surface-metrics > div")).toHaveLength(1);
  });

  it("ConfirmVerb: first press arms, second fires, arming self-disarms", () => {
    vi.useFakeTimers();
    const fire = vi.fn();
    render(<ConfirmVerb label="Kill loop" confirmLabel="Kill?" onConfirm={fire} />);
    const verb = screen.getByRole("button", { name: "Kill loop" });
    fireEvent.click(verb);
    expect(fire).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Kill?" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Kill?" }));
    expect(fire).toHaveBeenCalledTimes(1);
    // Re-arm and let it decay.
    fireEvent.click(screen.getByRole("button", { name: "Kill loop" }));
    act(() => {
      vi.advanceTimersByTime(3100);
    });
    expect(screen.getByRole("button", { name: "Kill loop" })).toBeInTheDocument();
    expect(fire).toHaveBeenCalledTimes(1);
  });
});

describe("the reference core (Cadence) is native", () => {
  it("renders loops as surface rows with zero page grammar in the DOM", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        const body = url.includes("/loops")
          ? {
              loops: [
                {
                  id: "l1",
                  title: "Answer the coder",
                  source_type: "agent_question",
                  stale_score: 12,
                },
              ],
            }
          : url.includes("/history")
            ? { nudges: [] }
            : { enabled: true, pressure: "steady" };
        return new Response(JSON.stringify(body), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }),
    );
    const { container } = render(<CadenceCore />);
    await waitFor(() =>
      expect(screen.getByText("Answer the coder")).toBeInTheDocument(),
    );
    for (const cls of [
      ".page-grid",
      ".span-8",
      ".span-4",
      ".data-list",
      ".data-row",
      ".signal-eyebrow",
      ".button-row",
    ]) {
      expect(container.querySelector(cls)).toBeNull();
    }
    expect(container.querySelector(".surface-verbs")).toBeTruthy();
    expect(container.querySelector(".surface-rows")).toBeTruthy();
    expect(screen.getByText("agent question")).toBeInTheDocument();
  });
});
