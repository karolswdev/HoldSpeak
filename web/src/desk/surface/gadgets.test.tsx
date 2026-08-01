// HS-111-01 — the gadget kit: every gadget wraps a REAL input and the
// interaction contracts hold (checkbox species, cycle select, stepper
// arrows, mx radio reveal, secret armed replace).
import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import {
  CheckGadget,
  CycleGadget,
  GadgetRow,
  MxRadio,
  SecretRow,
  StepperGadget,
} from "./gadgets";

describe("gadget kit", () => {
  it("CheckGadget is a real checkbox", async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(<CheckGadget label="Enabled" checked={false} onChange={onChange} />);
    const box = screen.getByRole("checkbox", { name: "Enabled" });
    await user.click(box);
    expect(onChange).toHaveBeenCalledWith(true);
  });

  it("CycleGadget is a real select and keeps an off-roster value visible", () => {
    const onChange = vi.fn();
    render(
      <CycleGadget
        label="Theme"
        value="weird"
        options={[{ value: "dark" }, { value: "light" }]}
        onChange={onChange}
      />,
    );
    const select = screen.getByRole("combobox", { name: "Theme" });
    expect(select).toHaveValue("weird");
    fireEvent.change(select, { target: { value: "light" } });
    expect(onChange).toHaveBeenCalledWith("light");
  });

  it("StepperGadget arrows step and clamp", async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(
      <StepperGadget
        label="History lines"
        value={10}
        min={1}
        max={10}
        onChange={onChange}
      />,
    );
    await user.click(
      screen.getByRole("button", { name: "Increase History lines" }),
    );
    expect(onChange).toHaveBeenCalledWith(10); // clamped at max
    await user.click(
      screen.getByRole("button", { name: "Decrease History lines" }),
    );
    expect(onChange).toHaveBeenCalledWith(9);
  });

  it("MxRadio reveals only the selected option's gadgets", () => {
    const onChange = vi.fn();
    const { rerender } = render(
      <MxRadio
        label="Runs on"
        value="a"
        onChange={onChange}
        options={[
          { value: "a", label: "Alpha", children: <span>alpha-deps</span> },
          { value: "b", label: "Beta", children: <span>beta-deps</span> },
        ]}
      />,
    );
    expect(screen.getByText("alpha-deps")).toBeInTheDocument();
    expect(screen.queryByText("beta-deps")).toBeNull();
    fireEvent.click(screen.getByRole("radio", { name: "Beta" }));
    expect(onChange).toHaveBeenCalledWith("b");
    rerender(
      <MxRadio
        label="Runs on"
        value="b"
        onChange={onChange}
        options={[
          { value: "a", label: "Alpha", children: <span>alpha-deps</span> },
          { value: "b", label: "Beta", children: <span>beta-deps</span> },
        ]}
      />,
    );
    expect(screen.queryByText("alpha-deps")).toBeNull();
    expect(screen.getByText("beta-deps")).toBeInTheDocument();
  });

  it("SecretRow shows the chip, arms an in-row replace, Enter commits", async () => {
    const onReplace = vi.fn();
    const user = userEvent.setup();
    render(
      <SecretRow
        label="Web pairing token"
        configured
        rotatable={false}
        onReplace={onReplace}
      />,
    );
    expect(screen.getByText("SET")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Replace" }));
    const input = screen.getByLabelText("Replacement Web pairing token");
    await user.type(input, "new-secret{Enter}");
    expect(onReplace).toHaveBeenCalledWith("new-secret");
    // the chip returns after the commit
    expect(screen.getByText("SET")).toBeInTheDocument();
  });

  it("SecretRow Escape reverts the armed replace without committing", async () => {
    const onReplace = vi.fn();
    const user = userEvent.setup();
    render(
      <SecretRow label="Device audio key" configured={false} onReplace={onReplace} />,
    );
    expect(screen.getByText("—")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Replace" }));
    const input = screen.getByLabelText("Replacement Device audio key");
    await user.type(input, "draft{Escape}");
    expect(onReplace).not.toHaveBeenCalled();
    expect(screen.getByText("—")).toBeInTheDocument();
  });

  it("GadgetRow carries the label and a token fact", () => {
    render(
      <GadgetRow label="Latency budget" fact="ms">
        <span>gadget</span>
      </GadgetRow>,
    );
    expect(screen.getByText("Latency budget")).toBeInTheDocument();
    expect(screen.getByText("ms")).toBeInTheDocument();
  });
});
