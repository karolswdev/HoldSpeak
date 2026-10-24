import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import axe from "axe-core";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { ComponentsCore } from "./cores/ComponentsCore";

describe("Signal component gallery", () => {
  it("has no automatically detectable accessibility violations", async () => {
    const { container } = render(
      <MemoryRouter initialEntries={["/design/components"]}>
        <ComponentsCore />
      </MemoryRouter>,
    );
    for (const pattern of ["Forms", "Reading", "Lists", "Resources", "Conversation", "Progress", "Controls"]) {
      fireEvent.click(screen.getByRole("button", { name: pattern }));
      const result = await axe.run(container, {
        rules: { "color-contrast": { enabled: false } },
      });
      expect(result.violations).toEqual([]);
    }
  });

  it("keeps the pattern selector and the controls catalogue in one window", () => {
    render(<ComponentsCore />);

    expect(screen.getByTestId("design-reference")).toBeInTheDocument();
    expect(screen.getByTestId("reference-owner-preferences")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Controls" }));
    expect(screen.getByTestId("reference-controls")).toBeInTheDocument();
    expect(screen.getByTestId("object-species-gallery")).toBeInTheDocument();
  });

  it("proves the Settings You field, list, conversation and progress behavior", async () => {
    render(<ComponentsCore />);

    const form = screen.getByTestId("reference-owner-preferences");
    const name = await within(form).findByRole("textbox", { name: "Your name" });
    fireEvent.change(name, { target: { value: "Karol A" } });
    expect(within(form).getByText("EDITED")).toBeInTheDocument();
    fireEvent.blur(name);
    await waitFor(() => expect(within(form).getAllByText("SAVED")).toHaveLength(2));

    fireEvent.click(screen.getByRole("button", { name: "Lists" }));
    const list = screen.getByTestId("reference-list");
    fireEvent.change(within(list).getByRole("textbox", { name: "Filter work items" }), { target: { value: "runtime" } });
    expect(within(list).getByText("Runtime plan")).toBeInTheDocument();
    fireEvent.click(within(list).getByRole("button", { name: /Runtime plan/ }));
    expect(within(list).getByText("Selected: Runtime plan")).toBeInTheDocument();
    fireEvent.click(within(list).getByRole("button", { name: "Clear selection" }));
    expect(within(list).queryByText("Selected: Runtime plan")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Conversation" }));
    const conversation = screen.getByTestId("reference-conversation");
    fireEvent.change(within(conversation).getByRole("textbox", { name: /Write a review note/ }), { target: { value: "Keep this local" } });
    fireEvent.click(within(conversation).getByRole("button", { name: "Send locally" }));
    expect(within(conversation).getByText("Keep this local")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Progress" }));
    const progress = screen.getByTestId("reference-progress");
    fireEvent.click(within(progress).getByRole("button", { name: "Fail locally" }));
    expect(within(progress).getByText("Needs retry")).toBeInTheDocument();
    fireEvent.click(within(progress).getByRole("button", { name: "Retry" }));
    expect(within(progress).getByRole("progressbar", { name: "Check source progress" })).toHaveAttribute("aria-valuenow", "55");
  });

  it("retries the captured failed request without replacing a newer draft", async () => {
    render(<ComponentsCore />);

    fireEvent.click(screen.getByRole("button", { name: "Conversation" }));
    const conversation = screen.getByTestId("reference-conversation");
    fireEvent.change(screen.getByRole("combobox", { name: "Example state" }), { target: { value: "failed" } });
    const failedRequest = "Can we keep the release note local while we review it?";
    expect(within(conversation).getAllByText(failedRequest, { exact: true })).toHaveLength(1);

    const draft = within(conversation).getByRole("textbox", { name: "Write a review note" });
    fireEvent.change(draft, { target: { value: "Newer draft" } });
    fireEvent.click(within(conversation).getAllByRole("button", { name: "Retry" })[0]);
    expect(within(conversation).getByRole("button", { name: "Retry…" })).toBeDisabled();
    fireEvent.change(draft, { target: { value: "Newer draft while retrying" } });

    await waitFor(() => expect(within(conversation).getByText("The reply is available locally for the captured request.", { exact: true })).toBeInTheDocument());
    expect(draft).toHaveValue("Newer draft while retrying");
    expect(within(conversation).getAllByText(failedRequest, { exact: true })).toHaveLength(1);
  });

  it("selects the real Settings writer refusal and keeps the draft for Retry", async () => {
    render(<ComponentsCore />);

    fireEvent.change(screen.getByRole("combobox", { name: "Example state" }), { target: { value: "refused" } });
    const form = screen.getByTestId("reference-owner-preferences");
    await waitFor(() => expect(within(form).getAllByText("NOT SAVED")).toHaveLength(2));
    expect(within(form).getByRole("textbox", { name: "Your name" })).toHaveValue("Karol A");
    fireEvent.click(within(form).getByRole("button", { name: "Retry" }));
    await waitFor(() => expect(within(form).getAllByText("SAVED")).toHaveLength(2));
  });

  it("keeps the reading source and excerpt actions truthful", () => {
    render(<ComponentsCore />);

    fireEvent.click(screen.getByRole("button", { name: "Reading" }));
    const reading = screen.getByTestId("reference-reading");
    const preset = screen.getByRole("combobox", { name: "Example state" });

    fireEvent.change(preset, { target: { value: "empty" } });
    expect(within(reading).queryByRole("button", { name: "Keep excerpt" })).not.toBeInTheDocument();
    const emptyOpenButtons = within(reading).getAllByRole("button", { name: "Open source" });
    expect(emptyOpenButtons).toHaveLength(1);
    fireEvent.click(emptyOpenButtons[emptyOpenButtons.length - 1]);
    expect(within(reading).getByTestId("reference-source-note")).toBeInTheDocument();
    fireEvent.click(within(reading).getByRole("button", { name: "Close source" }));
    expect(within(reading).queryByTestId("reference-source-note")).not.toBeInTheDocument();

    fireEvent.change(preset, { target: { value: "long" } });
    expect(within(reading).getByTestId("reference-reading-document")).toBeInTheDocument();
    expect(within(reading).getByRole("button", { name: "Keep excerpt" })).toBeInTheDocument();
  });

  it("resets the active specimen after local edits", async () => {
    render(<ComponentsCore />);

    const form = screen.getByTestId("reference-owner-preferences");
    fireEvent.change(await within(form).findByRole("textbox", { name: "Your name" }), { target: { value: "A local draft" } });
    fireEvent.click(screen.getByRole("button", { name: "Reset" }));
    expect(await within(screen.getByTestId("reference-owner-preferences")).findByRole("textbox", { name: "Your name" })).toHaveValue("Karol");

    fireEvent.click(screen.getByRole("button", { name: "Reading" }));
    fireEvent.change(screen.getByRole("combobox", { name: "Example state" }), { target: { value: "long" } });
    fireEvent.click(within(screen.getByTestId("reference-reading")).getByRole("button", { name: "Keep excerpt" }));
    expect(screen.getByTestId("reference-kept-excerpt")).toHaveTextContent("The team chose a local review pass for the next release.");

    fireEvent.click(screen.getByRole("button", { name: "Reset" }));
    expect(await within(screen.getByTestId("reference-owner-preferences")).findByRole("textbox", { name: "Your name" })).toHaveValue("Karol");
    expect(screen.queryByTestId("reference-kept-excerpt")).not.toBeInTheDocument();
  });
});
