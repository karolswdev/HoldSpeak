import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { OwnerPreferencesReference } from "./OwnerPreferencesReference";

afterEach(() => vi.restoreAllMocks());

function nameRow() {
  const row = screen.getByTestId("settings-owner-name").closest(".gadget-row");
  if (!row) throw new Error("Your name row missing");
  return within(row as HTMLElement);
}

function aliasesRow() {
  const row = screen.getByTestId("settings-owner-aliases").closest(".gadget-row");
  if (!row) throw new Error("Also called row missing");
  return within(row as HTMLElement);
}

describe("Settings You local reference", () => {
  it("keeps an uncommitted alias draft Edited and never calls the settings API", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("No fixture network"));
    render(<OwnerPreferencesReference state="saved" />);

    const alias = within(await screen.findByTestId("settings-owner-aliases")).getByRole("textbox", { name: "Also called" });
    expect(aliasesRow().getByText("SAVED")).toBeInTheDocument();
    fireEvent.change(alias, { target: { value: "Karel" } });
    expect(aliasesRow().getByText("EDITED")).toBeInTheDocument();
    expect(aliasesRow().queryByText("SAVED")).not.toBeInTheDocument();
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("keeps a refused name draft and retries the same writer with a local revision", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("No fixture network"));
    render(<OwnerPreferencesReference state="refused" />);

    await waitFor(() => expect(nameRow().getByText("NOT SAVED")).toBeInTheDocument());
    expect(nameRow().getByRole("textbox", { name: "Your name" })).toHaveValue("Karol A");
    expect(aliasesRow().getByText("SAVED")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await waitFor(() => {
      expect(nameRow().getByRole("textbox", { name: "Your name" })).toHaveValue("Karol A");
      expect(nameRow().getByText("SAVED")).toBeInTheDocument();
    });
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("shows a captured local write as Saving until the adapter acknowledges it", async () => {
    render(<OwnerPreferencesReference state="saving" />);

    const complete = await screen.findByRole("button", { name: "Complete local write" });
    expect(nameRow().getByText("SAVING")).toBeInTheDocument();
    fireEvent.click(complete);
    await waitFor(() => expect(nameRow().getByText("SAVED")).toBeInTheDocument());
  });

  it("shows Saved after the local refusal is retried and acknowledged", async () => {
    render(<OwnerPreferencesReference state="retried" />);

    await waitFor(() => {
      expect(nameRow().getByRole("textbox", { name: "Your name" })).toHaveValue("Karol A");
      expect(nameRow().getByText("SAVED")).toBeInTheDocument();
    });
    expect(screen.queryByRole("button", { name: "Retry" })).not.toBeInTheDocument();
  });

  it("retains a newer edit while an earlier local write is pending", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("No fixture network"));
    render(<OwnerPreferencesReference state="newer" />);

    const complete = await screen.findByRole("button", { name: "Complete local write" });
    expect(nameRow().getByRole("textbox", { name: "Your name" })).toHaveValue("Karol B");
    expect(nameRow().getByText("EDITED")).toBeInTheDocument();
    fireEvent.click(complete);
    await waitFor(() => expect(nameRow().getByText("SAVED")).toBeInTheDocument());
    expect(nameRow().getByRole("textbox", { name: "Your name" })).toHaveValue("Karol B");
    expect(fetchSpy).not.toHaveBeenCalled();
  });
});
