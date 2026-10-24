import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { FiledNotesReference } from "./FiledNotesReference";

const wire = vi.hoisted(() => ({ apiFetch: vi.fn(), openRef: vi.fn() }));
vi.mock("../../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../../lib/api")>("../../../lib/api");
  return { ...actual, apiFetch: (...args: unknown[]) => wire.apiFetch(...args) };
});
vi.mock("../../../desk/openObject", async () => {
  const actual = await vi.importActual<typeof import("../../../desk/openObject")>("../../../desk/openObject");
  return { ...actual, openRef: (...args: unknown[]) => wire.openRef(...args) };
});
afterEach(() => { cleanup(); wire.apiFetch.mockReset(); wire.openRef.mockReset(); });

describe("Components filed Note specimen", () => {
  it("uses the Room Files controller and local read/Open callbacks", async () => {
    render(<FiledNotesReference preset="filed-notes" />);
    expect(wire.apiFetch).not.toHaveBeenCalled();
    fireEvent.click(screen.getByTestId("room-fold-files").querySelector("summary")!);
    fireEvent.click(await screen.findByRole("button", { name: /Review record, Note/i }));
    fireEvent.click(screen.getByTestId("room-files-open"));
    await waitFor(() => expect(screen.getByText(/OPENED LOCALLY/)).toBeInTheDocument());
    expect(wire.apiFetch).not.toHaveBeenCalled();
    expect(wire.openRef).not.toHaveBeenCalled();
  });

  it("keeps refusal, moved membership, and unavailable Note distinct with no real IO", async () => {
    const first = render(<FiledNotesReference preset="files-not-read" />);
    fireEvent.click(screen.getByTestId("room-fold-files").querySelector("summary")!);
    expect(screen.getByText("RESOURCES NOT READ")).toBeInTheDocument();
    fireEvent.click(screen.getByTestId("room-files-retry"));
    await screen.findByRole("button", { name: /Review record/i });
    first.unmount();
    const second = render(<FiledNotesReference preset="not-filed" />);
    await screen.findByText("NOT FILED HERE");
    second.unmount();
    render(<FiledNotesReference preset="unavailable" />);
    await screen.findByText("NOTE NOT AVAILABLE");
    expect(screen.getByTestId("room-files-open")).toBeDisabled();
    expect(wire.apiFetch).not.toHaveBeenCalled();
    expect(wire.openRef).not.toHaveBeenCalled();
  });
});
