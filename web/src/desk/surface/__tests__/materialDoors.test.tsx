// PHILO-17 U18: a door link in a note is the library Button that opens a
// real door; an unknown door is bold text (no dead verbs).
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({ open: vi.fn(), needs: vi.fn() }));
vi.mock("../../shell", () => ({ openSurfaceOr: mocks.open }));
vi.mock("../../screen/open", () => ({ openNeedsYouDrawer: mocks.needs }));

import { Material, hasNoteDoor } from "../Material";

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

const START_HERE = `HoldSpeak does three jobs for you.

- [Record a meeting](door:record-live) HoldSpeak writes the summary, the decisions and the actions.
- [Dictate](door:dictate) Speak, and HoldSpeak types your words.
- [Review what needs you](door:needs) See the actions and decisions that wait for you.`;

describe("Material door links", () => {
  it("renders the three jobs as library Buttons that open their doors", async () => {
    render(<Material>{START_HERE}</Material>);
    const record = screen.getByRole("button", { name: "Record a meeting" });
    expect(record.className).toContain("btn");
    fireEvent.click(record);
    expect(mocks.open).toHaveBeenCalledWith("record-live", "/live");
    fireEvent.click(screen.getByRole("button", { name: "Dictate" }));
    expect(mocks.open).toHaveBeenCalledWith("dictate", "/dictation");
    fireEvent.click(screen.getByRole("button", { name: "Review what needs you" }));
    await waitFor(() => expect(mocks.needs).toHaveBeenCalled());
    expect(screen.getByText(/HoldSpeak writes the summary/)).toBeTruthy();
  });

  it("an unknown door is bold text, never a dead button", () => {
    render(<Material>{"[Nowhere](door:nowhere) and [Proto](door:constructor)"}</Material>);
    expect(screen.queryByRole("button")).toBeNull();
    expect(screen.getByText("Nowhere").tagName).toBe("STRONG");
    expect(hasNoteDoor("[Nowhere](door:nowhere) [Proto](door:constructor)")).toBe(false);
    expect(hasNoteDoor(START_HERE)).toBe(true);
  });
});
