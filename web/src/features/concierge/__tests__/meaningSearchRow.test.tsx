/* Meaning search row: the state the server gives is the state on the face,
 * and the one verb issues the one request. */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { MeaningSearchRow, type MeaningSearchStatus } from "../MeaningSearchRow";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn() }));
vi.mock("../../../lib/api", () => ({ apiFetch: mocks.apiFetch }));

function status(over: Partial<MeaningSearchStatus>): MeaningSearchStatus {
  return {
    state: "off", percent: 0, indexed: 0, total: 0, error: "",
    model: { label: "nomic-embed-text v1.5", size_bytes: 146_146_432, on_device: false, source: "huggingface.co" },
    egress: { destination: "huggingface.co", what: "model file request" },
    ...over,
  };
}

describe("MeaningSearchRow", () => {
  beforeEach(() => mocks.apiFetch.mockReset());

  it("OFF with no file on this device names the download and its destination", async () => {
    mocks.apiFetch.mockResolvedValue(status({}));
    render(<ul><MeaningSearchRow /></ul>);
    const row = await screen.findByTestId("concierge-meaning-search");
    expect(row.textContent).toContain("Meaning search");
    expect(row.textContent).toContain("OFF");
    expect(row.textContent).toContain("139 MB");
    expect(row.textContent).toContain("DOWNLOAD");
    expect(row.textContent).toContain("HUGGINGFACE.CO");
    expect(screen.getByTestId("meaning-search-verb").textContent).toBe("Turn on");
    // A read makes no command request.
    expect(mocks.apiFetch.mock.calls.map((call) => call[0])).toEqual(["/api/memory/meaning-search"]);
  });

  it("OFF with the file on this device shows no download", async () => {
    mocks.apiFetch.mockResolvedValue(status({ egress: null, model: { ...status({}).model, on_device: true } }));
    render(<ul><MeaningSearchRow /></ul>);
    const row = await screen.findByTestId("concierge-meaning-search");
    expect(row.textContent).toContain("THIS DEVICE");
    expect(row.textContent).not.toContain("HUGGINGFACE.CO");
    expect(row.textContent).not.toContain("DOWNLOAD");
  });

  it("Turn on issues one POST and draws the state the server returns", async () => {
    mocks.apiFetch
      .mockResolvedValueOnce(status({}))
      .mockResolvedValue(status({ state: "downloading", percent: 42 }));
    render(<ul><MeaningSearchRow /></ul>);
    fireEvent.click(await screen.findByTestId("meaning-search-verb"));
    await waitFor(() => expect(screen.getByTestId("meaning-search-state").textContent).toContain("DOWNLOADING 42%"));
    expect(mocks.apiFetch.mock.calls[1]).toEqual(["/api/memory/meaning-search/turn-on", { method: "POST" }]);
    expect(screen.getByTestId("meaning-search-verb").textContent).toBe("Turn off");
  });

  it("INDEXING and ON read from the index numbers; Turn off issues the clear", async () => {
    mocks.apiFetch
      .mockResolvedValueOnce(status({ state: "indexing", indexed: 32, total: 710, egress: null }))
      .mockResolvedValue(status({ state: "off", egress: null }));
    render(<ul><MeaningSearchRow /></ul>);
    const chip = await screen.findByTestId("meaning-search-state");
    expect(chip.textContent).toContain("INDEXING 32 OF 710");
    fireEvent.click(screen.getByTestId("meaning-search-verb"));
    await waitFor(() => expect(screen.getByTestId("meaning-search-state").textContent).toContain("OFF"));
    expect(mocks.apiFetch.mock.calls[1]).toEqual(["/api/memory/meaning-search/turn-off", { method: "POST" }]);
  });

  it("shows the server's error text", async () => {
    mocks.apiFetch.mockResolvedValue(status({ error: "The download stopped. Press Turn on to continue." }));
    render(<ul><MeaningSearchRow /></ul>);
    expect((await screen.findByTestId("meaning-search-error")).textContent).toBe(
      "The download stopped. Press Turn on to continue.",
    );
  });

  it("draws nothing when no status is read", async () => {
    mocks.apiFetch.mockResolvedValue({ code: "meaning_search_unavailable" });
    render(<ul><MeaningSearchRow /></ul>);
    await waitFor(() => expect(mocks.apiFetch).toHaveBeenCalled());
    await Promise.resolve();
    expect(screen.queryByTestId("concierge-meaning-search")).toBeNull();
  });
});
