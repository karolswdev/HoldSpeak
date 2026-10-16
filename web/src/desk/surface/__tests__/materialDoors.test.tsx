// PHILO-17 U18: a door link in a note is the library Button that opens a
// real door; an unknown door is bold text (no dead verbs).
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({ open: vi.fn(), needs: vi.fn() }));
vi.mock("../../shell", () => ({ openSurfaceOr: mocks.open }));
vi.mock("../../screen/open", () => ({ openNeedsYouDrawer: mocks.needs }));

import { Material, hasNoteDoor } from "../Material";
import START_HERE_WIRE from "../../../test/wire/note.start-here.wire.json";

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

// The fresh desk's Start here note as the hub serves it (holdspeak/seeds/fresh-desk.yaml,
// recorded by tests/integration/test_face_wire_fences.py::test_start_here_note).
const START_HERE = START_HERE_WIRE.wire.note.body_markdown;

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
    expect(screen.getByText("Nowhere").closest("strong")).not.toBeNull();
    expect(screen.getByText("door:nowhere")).toBeTruthy();
    expect(hasNoteDoor("[Nowhere](door:nowhere) [Proto](door:constructor)")).toBe(false);
    expect(hasNoteDoor(START_HERE)).toBe(true);
  });
});
