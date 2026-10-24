import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import axe from "axe-core";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { ComponentsCore } from "./cores/ComponentsCore";

describe("Signal component gallery", () => {
  it.each(["Forms", "Editing", "Reading", "Lists", "Resources", "Conversation", "Progress", "Controls"])("%s has no automatically detectable accessibility violations", async (pattern) => {
    const { container } = render(
      <MemoryRouter initialEntries={["/design/components"]}>
        <ComponentsCore />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByRole("button", { name: pattern }));
    const result = await axe.run(container, {
      rules: { "color-contrast": { enabled: false } },
    });
    expect(result.violations).toEqual([]);
  });

  it("keeps the pattern selector and the controls catalogue in one window", () => {
    render(<ComponentsCore />);

    expect(screen.getByTestId("design-reference")).toBeInTheDocument();
    expect(screen.getByTestId("reference-owner-preferences")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Controls" }));
    expect(screen.getByTestId("reference-controls")).toBeInTheDocument();
    expect(screen.getByTestId("object-species-gallery")).toBeInTheDocument();
  });

  it("shows the Thought editing states and retains the other production specimens", () => {
    render(<ComponentsCore />);

    fireEvent.click(screen.getByRole("button", { name: "Editing" }));
    const editing = screen.getByTestId("reference-editing");
    expect(within(editing).getByRole("textbox", { name: "Note body" })).toBeInTheDocument();
    expect(within(editing).getByRole("button", { name: "Capture target" })).toBeEnabled();
    expect(within(editing).queryByRole("button", { name: "Speak the note" })).not.toBeInTheDocument();

    const preset = screen.getByRole("combobox", { name: "Example state" });
    fireEvent.change(preset, { target: { value: "retained" } });
    expect(within(screen.getByTestId("reference-editing")).getByText("NOT INSERTED")).toBeInTheDocument();
    fireEvent.change(preset, { target: { value: "newer" } });
    expect(within(screen.getByTestId("reference-editing")).getByText("NOT INSERTED")).toBeInTheDocument();
    expect(screen.getByTestId("reference-editing")).toHaveTextContent("Newer local edit.");
    fireEvent.change(preset, { target: { value: "read-only" } });
    expect(within(screen.getByTestId("reference-editing")).getByRole("button", { name: "Insert at caret" })).toBeDisabled();

    fireEvent.click(screen.getByRole("button", { name: "Forms" }));
    expect(screen.getByTestId("reference-owner-preferences")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Resources" }));
    expect(screen.getByTestId("reference-resource")).toBeInTheDocument();
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
    expect(within(conversation).queryByRole("button", { name: /Speak/i })).not.toBeInTheDocument();
    expect(conversation.querySelector(".desk-mic")).toBeNull();
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

  it("keeps the local Thought return outside a closed source fold and keeps the source after Clear quote", async () => {
    render(<ComponentsCore />);
    fireEvent.click(screen.getByRole("button", { name: "Conversation" }));

    const source = screen.getByTestId("reference-conversation-source");
    const frame = within(source).getByTestId("ask-selected-passage");
    const fold = frame.querySelector("details");
    expect(fold).toHaveAttribute("open");
    fireEvent.click(within(frame).getByText("Selected text"));
    await waitFor(() => expect(fold).not.toHaveAttribute("open"));
    fireEvent.click(within(frame).getByRole("button", { name: "Back to Thought" }));
    expect(within(source).getByRole("status")).toHaveTextContent("LOCAL RETURN");

    fireEvent.click(within(frame).getByText("Selected text"));
    await waitFor(() => expect(fold).toHaveAttribute("open"));
    fireEvent.click(within(frame).getByRole("button", { name: "Clear quote" }));
    expect(within(frame).getByText("Source")).toBeInTheDocument();
    expect(within(frame).queryByText("The source stays beside the decision.")).not.toBeInTheDocument();
    expect(within(frame).getByRole("button", { name: "Back to Thought" })).toBeInTheDocument();
    expect(screen.getByTestId("reference-conversation")).toHaveTextContent("Yes. Keep the source beside the decision.");
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
