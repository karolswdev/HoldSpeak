/* Meaning search row: the state the server gives is the state on the face,
 * and the one verb issues the one request. */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../../../lib/api";
import { MeaningSearchRow, type MeaningSearchStatus } from "../MeaningSearchRow";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn() }));
vi.mock("../../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../../lib/api")>("../../../lib/api");
  return { ...actual, apiFetch: mocks.apiFetch };
});

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

  it("a failure the hub reports has a name, a reason and Try again", async () => {
    mocks.apiFetch
      .mockResolvedValueOnce(status({
        error: "The file was not correct. Press Try again to download it again.", error_code: "integrity",
      }))
      .mockResolvedValue(status({ state: "downloading", percent: 3 }));
    render(<ul><MeaningSearchRow /></ul>);
    expect((await screen.findByTestId("meaning-search-error")).textContent).toBe(
      "The file was not correct. Press Try again to download it again.",
    );
    expect(screen.getByTestId("meaning-search-state").textContent).toContain("WRONG FILE");
    expect(screen.getByTestId("meaning-search-verb").textContent).toBe("Try again");
    fireEvent.click(screen.getByTestId("meaning-search-verb"));
    await waitFor(() => expect(screen.getByTestId("meaning-search-state").textContent).toContain("DOWNLOADING 3%"));
    expect(mocks.apiFetch.mock.calls[1][0]).toBe("/api/memory/meaning-search/turn-on");
    expect(screen.queryByTestId("meaning-search-error")).toBeNull();
  });

  it.each([
    [new ApiError(401, "missing_right: owner", { missing_right: "owner" }), "NOT PERMITTED", "Only the owner can do this."],
    [new ApiError(403, "Owner access is required.", {}), "NOT PERMITTED", "Only the owner can do this."],
    [new ApiError(500, "boom", {}), "HUB ERROR", "The hub did not do this (error 500)."],
    [new TypeError("Failed to fetch"), "NO ANSWER", "The hub did not answer."],
  ])("a refused or failed press is never silent: %s", async (error, token, words) => {
    mocks.apiFetch
      .mockResolvedValueOnce(status({}))
      .mockImplementationOnce(async () => { throw error; })
      .mockResolvedValue(status({ state: "downloading", percent: 1 }));
    render(<ul><MeaningSearchRow /></ul>);
    fireEvent.click(await screen.findByTestId("meaning-search-verb"));
    const alert = await screen.findByTestId("meaning-search-error");
    expect(alert.getAttribute("role")).toBe("alert");
    expect(alert.textContent).toContain(words);
    expect(alert.textContent).toContain("Try again");
    expect(screen.getByTestId("meaning-search-state").textContent).toContain(token);
    // The recovery action repeats the press that failed.
    expect(screen.getByTestId("meaning-search-verb").textContent).toBe("Try again");
    fireEvent.click(screen.getByTestId("meaning-search-verb"));
    await waitFor(() => expect(screen.getByTestId("meaning-search-state").textContent).toContain("DOWNLOADING 1%"));
    expect(mocks.apiFetch.mock.calls[2]).toEqual(["/api/memory/meaning-search/turn-on", { method: "POST" }]);
  });

  it("a status read that fails says so and offers Try again", async () => {
    mocks.apiFetch
      .mockImplementationOnce(async () => { throw new TypeError("Failed to fetch"); })
      .mockResolvedValue(status({}));
    render(<ul><MeaningSearchRow /></ul>);
    expect((await screen.findByTestId("meaning-search-state")).textContent).toContain("NO ANSWER");
    fireEvent.click(screen.getByTestId("meaning-search-verb"));
    await waitFor(() => expect(screen.getByTestId("meaning-search-state").textContent).toContain("OFF"));
    expect(mocks.apiFetch.mock.calls[1][0]).toBe("/api/memory/meaning-search");
  });
});
