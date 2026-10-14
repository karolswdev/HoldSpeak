import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { ChainPullout } from "../pullouts/ChainPullout";
import { openSurfaceOr } from "../shell";
import type { WorldObject } from "../world";

vi.mock("../shell", () => ({ openSurfaceOr: vi.fn() }));
vi.mock("../pullouts/shared/CapabilitySection", () => ({ CapabilitySection: () => null }));
vi.mock("../components/DeskFilingStrip", () => ({ DeskFilingStrip: () => null }));

function object(steps: string[]): WorldObject {
  return { kind: "chain", id: "c-1", title: "Morning review", ref: { kind: "chain", id: "c-1", name: "Morning review", steps, capability: null } } as WorldObject;
}

describe("Sequence actions", () => {
  it.each([{ state: "empty", steps: [] }, { state: "populated", steps: ["recipe-1"] }])("withholds unsupported Edit for a $state Sequence", ({ steps }) => {
    render(<ChainPullout object={object(steps)} onClose={() => {}} />);
    expect(screen.queryByRole("button", { name: /^Edit/ })).toBeNull();
  });

  it("keeps Dictate as a library action that opens the real surface with its source", () => {
    render(<ChainPullout object={object([])} onClose={() => {}} />);
    expect(screen.getByText("No steps")).toBeTruthy();
    const dictate = screen.getByRole("button", { name: "Dictate about this" });
    expect(dictate.classList.contains("btn")).toBe(true);
    fireEvent.click(dictate);
    expect(openSurfaceOr).toHaveBeenCalledWith("dictate", "/dictation", "sequence:c-1");
  });
});
