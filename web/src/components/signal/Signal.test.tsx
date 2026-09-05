// HS-111-08 — the legacy dialect's specs retired with the species
// (Switch/Tabs/InlineMessage died; wings and FoldGadget carry the
// keyboard grammar now — see desk/surface tests). What survives here
// is the surviving roster: Field association and Button semantics.
import { createRef } from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Button, Field, TextInput } from "./Signal";

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

  it("forwards the native button ref for focus restoration", () => {
    const ref = createRef<HTMLButtonElement>();
    render(<Button ref={ref}>Return</Button>);
    ref.current?.focus();
    expect(screen.getByRole("button", { name: "Return" })).toHaveFocus();
  });

  it("exposes semantic busy and disabled states", () => {
    render(<Button loading>Save</Button>);
    expect(screen.getByRole("button", { name: "Save" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Save" })).toHaveAttribute(
      "aria-busy",
      "true",
    );
  });
});
