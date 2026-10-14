import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { EngineLine } from "../EngineLine";
import { RunLine } from "../RunLine";

describe("engine and run lines", () => {
  it("shows the selected model and place", () => {
    render(<EngineLine engine={{ state: "set", model: "Qwen", place: "LAN" }} />);
    expect(screen.getByTestId("engine-line")).toHaveTextContent("Qwen · LAN");
  });

  it("offers a choice when no engine is set", () => {
    const onChoose = vi.fn();
    render(<EngineLine engine={{ state: "none", model: "", place: "" }} onChoose={onChoose} />);
    screen.getByRole("button", { name: "Choose engine" }).click();
    expect(onChoose).toHaveBeenCalledOnce();
  });

  it("leaves the engine slot empty while the shared roster is unread", () => {
    render(<EngineLine engine={{ state: "unread", model: "", place: "" }} />);
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
});
