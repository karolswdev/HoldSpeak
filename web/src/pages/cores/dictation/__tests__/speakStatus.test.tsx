// Window grammar (2026-10-24): Speak's status bar words — the elapsed m:ss
// that ticks while he talks, and the speech engine in words.
import { act, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { speechEngineName, useElapsed } from "../SpeakFace";

function Clock({ since }: { since: number | null }) {
  return <span data-testid="clock">{useElapsed(since) ?? "none"}</span>;
}

afterEach(() => vi.useRealTimers());

describe("Speak status bar words", () => {
  it("the elapsed time is a tabular m:ss that ticks once a second, and nothing at rest", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-10-24T23:00:00Z"));
    const view = render(<Clock since={Date.now()} />);
    expect(screen.getByTestId("clock").textContent).toBe("0:00");
    act(() => { vi.advanceTimersByTime(42_000); });
    expect(screen.getByTestId("clock").textContent).toBe("0:42");
    act(() => { vi.advanceTimersByTime(30_000); });
    expect(screen.getByTestId("clock").textContent).toBe("1:12");
    view.rerender(<Clock since={null} />);
    expect(screen.getByTestId("clock").textContent).toBe("none");
  });

  it("names the speech engine from the hub's speech read", () => {
    expect(speechEngineName({ status: { speech: { model: "base", backend: "mlx", state: "on_device" } } as never })).toBe("whisper-base-mlx");
    expect(speechEngineName({ status: { speech: { model: "small", backend: "auto", state: "on_device" } } as never })).toBe("whisper-small");
    expect(speechEngineName({ status: null })).toBeNull();
  });
});
