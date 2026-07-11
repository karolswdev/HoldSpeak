import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import {
  Button,
  Field,
  InlineMessage,
  Switch,
  Tabs,
  TextInput,
} from "./Signal";

describe("Signal React controls", () => {
  it("associates field label, description and error", () => {
    render(
      <Field
        label="Server"
        description="Include the scheme."
        error="Could not connect."
      >
        {({ id, describedBy }) => (
          <TextInput id={id} aria-describedby={describedBy} />
        )}
      </Field>,
    );
    const input = screen.getByRole("textbox", { name: "Server" });
    expect(input).toHaveAccessibleDescription(
      "Include the scheme. Could not connect.",
    );
  });

  it("exposes semantic busy and disabled states", () => {
    render(<Button loading>Save</Button>);
    expect(screen.getByRole("button", { name: "Save" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Save" })).toHaveAttribute(
      "aria-busy",
      "true",
    );
  });

  it("changes tabs and switch state from the keyboard", async () => {
    const onTab = vi.fn();
    const onSwitch = vi.fn();
    const user = userEvent.setup();
    render(
      <>
        <Tabs
          label="Demo"
          tabs={[
            { id: "a", label: "Alpha" },
            { id: "blocked", label: "Blocked", disabled: true },
            { id: "b", label: "Beta" },
          ]}
          active="a"
          onChange={onTab}
        />
        <Switch label="Enabled" onChange={onSwitch} />
      </>,
    );
    await user.click(screen.getByRole("tab", { name: "Beta" }));
    await user.click(screen.getByRole("tab", { name: "Alpha" }));
    await user.keyboard("{ArrowRight}");
    expect(onTab).toHaveBeenCalledWith("b");
    expect(screen.getByRole("tab", { name: "Beta" })).toHaveFocus();
    expect(screen.getByRole("tab", { name: "Blocked" })).toBeDisabled();
    await user.click(screen.getByRole("switch", { name: "Enabled" }));
    expect(onSwitch).toHaveBeenCalled();
  });

  it("uses a live region for success and an alert for errors", () => {
    render(
      <>
        <InlineMessage tone="success">Saved</InlineMessage>
        <InlineMessage tone="error">Failed</InlineMessage>
      </>,
    );
    expect(screen.getByRole("status")).toHaveTextContent("Saved");
    expect(screen.getByRole("alert")).toHaveTextContent("Failed");
  });
});
