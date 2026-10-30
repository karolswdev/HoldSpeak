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
    expect(row.textContent).toContain("Off");
    expect(row.textContent).toContain("146 MB");
    expect(row.textContent).toContain("To download");
    expect(row.textContent).toContain("huggingface.co");
    expect(screen.getByTestId("meaning-search-verb").textContent).toBe("Turn on");
    // A read makes no command request.
    expect(mocks.apiFetch.mock.calls.map((call) => call[0])).toEqual(["/api/memory/meaning-search"]);
  });

  it("OFF with the file on this device shows no download", async () => {
    mocks.apiFetch.mockResolvedValue(status({ egress: null, model: { ...status({}).model, on_device: true } }));
    render(<ul><MeaningSearchRow /></ul>);
    const row = await screen.findByTestId("concierge-meaning-search");
    expect(row.textContent).not.toContain("THIS DEVICE");
    expect(row.textContent).not.toContain("huggingface.co");
    expect(row.textContent).not.toContain("To download");
  });

  it("Turn on issues one POST and draws the state the server returns", async () => {
    mocks.apiFetch
      .mockResolvedValueOnce(status({}))
      .mockResolvedValue(status({ state: "downloading", percent: 42 }));
    render(<ul><MeaningSearchRow /></ul>);
    fireEvent.click(await screen.findByTestId("meaning-search-verb"));
    await waitFor(() => expect(screen.getByTestId("meaning-search-state").textContent).toContain("Downloading 42%"));
    expect(mocks.apiFetch.mock.calls[1]).toEqual(["/api/memory/meaning-search/turn-on", { method: "POST" }]);
    expect(screen.getByTestId("meaning-search-verb").textContent).toBe("Turn off");
  });

  it("INDEXING and ON read from the index numbers; Turn off issues the clear", async () => {
    mocks.apiFetch
      .mockResolvedValueOnce(status({ state: "indexing", indexed: 32, total: 710, egress: null }))
      .mockResolvedValue(status({ state: "off", egress: null }));
    render(<ul><MeaningSearchRow /></ul>);
    const chip = await screen.findByTestId("meaning-search-state");
    expect(chip.textContent).toContain("Indexing 32 of 710");
    fireEvent.click(screen.getByTestId("meaning-search-verb"));
    await waitFor(() => expect(screen.getByTestId("meaning-search-state").textContent).toContain("Off"));
    expect(mocks.apiFetch.mock.calls[1]).toEqual(["/api/memory/meaning-search/turn-off", { method: "POST" }]);
  });

  it("a failure the hub reports has a name, a reason and Try again", async () => {
    // replaces: tests/e2e/test_meaning_search_row_glass.py::test_a_wrong_file_is_named_and_the_whole_reason_is_on_the_glass
    // (the hub's real hash refusal: tests/unit/test_meaning_search_turn_on.py::test_a_file_with_a_different_hash_is_refused;
    // the "not clipped" half is the generic sweep's, T3)
    mocks.apiFetch
      .mockResolvedValueOnce(status({
        error: "The file was not correct. Press Try again to download it again.", error_code: "integrity",
      }))
      .mockResolvedValue(status({ state: "downloading", percent: 3 }));
    render(<ul><MeaningSearchRow /></ul>);
    expect((await screen.findByTestId("meaning-search-error")).textContent).toBe(
      "The file was not correct. Press Try again to download it again.",
    );
    expect(screen.getByTestId("meaning-search-state").textContent).toContain("Wrong file");
    expect(screen.getByTestId("meaning-search-verb").textContent).toBe("Try again");
    fireEvent.click(screen.getByTestId("meaning-search-verb"));
    await waitFor(() => expect(screen.getByTestId("meaning-search-state").textContent).toContain("Downloading 3%"));
    expect(mocks.apiFetch.mock.calls[1][0]).toBe("/api/memory/meaning-search/turn-on");
    expect(screen.queryByTestId("meaning-search-error")).toBeNull();
  });

  it.each([
    [new ApiError(401, "missing_right: owner", { missing_right: "owner" }), "Not permitted", "Only the owner can do this."],
    [new ApiError(403, "Owner access is required.", {}), "Not permitted", "Only the owner can do this."],
    [new ApiError(500, "boom", {}), "Hub error", "The hub did not do this (error 500)."],
    [new TypeError("Failed to fetch"), "No answer", "The hub did not answer."],
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
    await waitFor(() => expect(screen.getByTestId("meaning-search-state").textContent).toContain("Downloading 1%"));
    expect(mocks.apiFetch.mock.calls[2]).toEqual(["/api/memory/meaning-search/turn-on", { method: "POST" }]);
  });

  it("Turn off stops a download in flight (one POST, the row reads OFF)", async () => {
    // replaces: tests/e2e/test_meaning_search_row_glass.py::test_off_and_downloading (the Turn off leg)
    mocks.apiFetch
      .mockResolvedValueOnce(status({ state: "downloading", percent: 37 }))
      .mockResolvedValue(status({}));
    render(<ul><MeaningSearchRow /></ul>);
    expect((await screen.findByTestId("meaning-search-state")).textContent).toContain("Downloading 37%");
    expect(screen.getByTestId("meaning-search-verb").textContent).toBe("Turn off");
    fireEvent.click(screen.getByTestId("meaning-search-verb"));
    await waitFor(() => expect(screen.getByTestId("meaning-search-state").getAttribute("data-state")).toBe("off"));
    expect(mocks.apiFetch.mock.calls[1]).toEqual(["/api/memory/meaning-search/turn-off", { method: "POST" }]);
  });

  it("the hub's 401 says the whole way forward", async () => {
    // replaces: tests/e2e/test_meaning_search_row_glass.py::test_a_refused_press_is_named_with_a_way_forward
    // (the page forgetting the refused token is fenced in lib/auth.test.ts)
    mocks.apiFetch
      .mockResolvedValueOnce(status({}))
      .mockImplementationOnce(async () => { throw new ApiError(401, "missing_right: owner", { missing_right: "owner" }); });
    render(<ul><MeaningSearchRow /></ul>);
    fireEvent.click(await screen.findByTestId("meaning-search-verb"));
    const alert = await screen.findByTestId("meaning-search-error");
    expect(alert.getAttribute("role")).toBe("alert");
    expect(alert.textContent).toBe("Only the owner can do this. Open this desk as the owner. Then press Try again.");
    expect(screen.getByTestId("meaning-search-state").textContent).toContain("Not permitted");
    expect(screen.getByTestId("meaning-search-verb").textContent).toBe("Try again");
  });

  it("a status read that fails says so and offers Try again", async () => {
    mocks.apiFetch
      .mockImplementationOnce(async () => { throw new TypeError("Failed to fetch"); })
      .mockResolvedValue(status({}));
    render(<ul><MeaningSearchRow /></ul>);
    expect((await screen.findByTestId("meaning-search-state")).textContent).toContain("No answer");
    fireEvent.click(screen.getByTestId("meaning-search-verb"));
    await waitFor(() => expect(screen.getByTestId("meaning-search-state").textContent).toContain("Off"));
    expect(mocks.apiFetch.mock.calls[1][0]).toBe("/api/memory/meaning-search");
  });
});
