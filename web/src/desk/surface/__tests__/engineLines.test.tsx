import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { EngineLine } from "../EngineLine";
import { RunLine } from "../RunLine";

describe("engine and run lines", () => {
  it("names the selected model by name only (owner ruling 2026-10-25)", () => {
    render(<EngineLine engine={{ state: "set", model: "Qwen" }} />);
    expect(screen.getByTestId("engine-line").textContent).toBe("Qwen");
  });

  it("offers a choice when no engine is set", () => {
    const onChoose = vi.fn();
    render(<EngineLine engine={{ state: "none", model: "" }} onChoose={onChoose} />);
    screen.getByRole("button", { name: "Choose engine" }).click();
    expect(onChoose).toHaveBeenCalledOnce();
  });

  it("leaves the engine slot empty while the shared roster is unread", () => {
    render(<EngineLine engine={{ state: "unread", model: "" }} />);
    expect(screen.queryByTestId("engine-line")).toBeNull();
    expect(screen.queryByText("Reading engine")).toBeNull();
  });

  it("keeps a closed failure reason and retry verb", () => {
    const onRetry = vi.fn();
    render(<RunLine phase="failure" reason="did_not_answer" model="Qwen" onRetry={onRetry} />);
    expect(screen.getByTestId("run-line")).toHaveTextContent("Qwen did not answer");
    screen.getByRole("button", { name: "Try again" }).click();
    expect(onRetry).toHaveBeenCalledOnce();
  });

  it("names source change without offering a retry of that stale request", () => {
    render(<RunLine phase="failure" reason="source_changed" model="Qwen" />);
    expect(screen.getByTestId("run-line")).toHaveTextContent("Source changed. Select it again");
    expect(screen.queryByRole("button", { name: "Ask again" })).toBeNull();
  });
});
