import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { OwnerPreferencesReference } from "./OwnerPreferencesReference";

afterEach(() => vi.restoreAllMocks());

// Window grammar 2026-10-24: no pill per field. Each field keeps its true
// word as data; the specimen's status bar says the window's state.
const fieldState = (field: "name" | "aliases") => screen.getByTestId(`settings-owner-${field}`).getAttribute("data-save-state");
const status = () => screen.getByTestId("settings-status").textContent ?? "";
const nameBox = () => within(screen.getByTestId("settings-owner-name")).getByRole("textbox", { name: "Your name" });

describe("Settings You local reference", () => {
  it("renders the rail, the pane and the status bar of the Settings window", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("No fixture network"));
    const { container } = render(<OwnerPreferencesReference state="saved" />);
    await screen.findByTestId("settings-owner-name");
    const rail = container.querySelector(".pref-rail")!;
    expect(within(rail as HTMLElement).getAllByRole("button")).toHaveLength(9); // + Calls (2026-10-28)
    expect(screen.getByTestId("reference-settings-index-you")).toHaveClass("is-active");
    expect(container.querySelector(".pref-pane .gadget-row")).not.toBeNull();
    expect(container.querySelector(".surface-state-chip")?.textContent ?? "").not.toMatch(/SAVED|EDITED|SAVING/);
    expect(status()).toContain("Local specimen");
  });

  it("keeps an uncommitted alias draft Edited and never calls the settings API", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("No fixture network"));
    render(<OwnerPreferencesReference state="saved" />);

    const alias = within(await screen.findByTestId("settings-owner-aliases")).getByRole("textbox", { name: "Also called" });
    expect(fieldState("aliases")).toBe("Saved");
    fireEvent.change(alias, { target: { value: "Karel" } });
    expect(fieldState("aliases")).toBe("Edited");
    expect(status()).toContain("Edited");
    expect(status()).not.toContain("Saved");
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("keeps a refused name draft and retries the same writer with a local revision", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("No fixture network"));
    render(<OwnerPreferencesReference state="refused" />);

    await waitFor(() => expect(fieldState("name")).toBe("Not saved"));
    expect(status()).toContain("Not saved");
    expect(screen.getByTestId("settings-save-failure")).toHaveAttribute("role", "alert");
    expect(nameBox()).toHaveValue("Karol A");
    expect(fieldState("aliases")).toBe("Saved");
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await waitFor(() => {
      expect(nameBox()).toHaveValue("Karol A");
      expect(fieldState("name")).toBe("Saved");
      expect(status()).toMatch(/Saved just now/);
    });
    expect(screen.queryByRole("button", { name: "Retry" })).not.toBeInTheDocument();
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("shows a captured local write as Saving until the adapter acknowledges it", async () => {
    render(<OwnerPreferencesReference state="saving" />);

    const complete = await screen.findByRole("button", { name: "Complete local write" });
    expect(fieldState("name")).toBe("Saving");
    expect(status()).toContain("Saving…");
    fireEvent.click(complete);
    await waitFor(() => expect(fieldState("name")).toBe("Saved"));
    await waitFor(() => expect(status()).toMatch(/Saved just now/));
  });

  it("shows Saved after the local refusal is retried and acknowledged", async () => {
    render(<OwnerPreferencesReference state="retried" />);

    await waitFor(() => {
      expect(nameBox()).toHaveValue("Karol A");
      expect(fieldState("name")).toBe("Saved");
    });
    expect(screen.queryByRole("button", { name: "Retry" })).not.toBeInTheDocument();
  });

  it("retains a newer edit while an earlier local write is pending", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("No fixture network"));
    render(<OwnerPreferencesReference state="newer" />);

    const complete = await screen.findByRole("button", { name: "Complete local write" });
    expect(nameBox()).toHaveValue("Karol B");
    expect(fieldState("name")).toBe("Edited");
    expect(status()).toContain("Edited");
    expect(status()).not.toContain("Saved");
    fireEvent.click(complete);
    await waitFor(() => expect(fieldState("name")).toBe("Saved"));
    expect(nameBox()).toHaveValue("Karol B");
    expect(fetchSpy).not.toHaveBeenCalled();
  });
});
