// HS-111-01 — the gadget kit: every gadget wraps a REAL input and the
// interaction contracts hold (checkbox species, cycle select, stepper
// arrows, mx radio reveal, secret armed replace).
import { act, fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import {
  CheckGadget,
  CycleGadget,
  FoldGadget,
  GadgetRow,
  GadgetTable,
  LampGadget,
  LedMeter,
  MxRadio,
  PadGadget,
  SecretRow,
  StepperGadget,
  TransportKey,
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

  // HS-111-02 — the dictation-deck species.

  it("LedMeter is a labeled meter: lit segments follow the value, hot above 0.8", () => {
    const { container } = render(
      <LedMeter label="Level" value={0.5} segments={12} />,
    );
    const meter = screen.getByRole("meter", { name: "Level" });
    expect(meter).toHaveAttribute("aria-valuenow", "0.5");
    expect(container.querySelectorAll(".gadget-ledmeter-seg")).toHaveLength(12);
    expect(container.querySelectorAll("[data-lit]")).toHaveLength(6);
    expect(container.querySelectorAll("[data-hot]")).toHaveLength(0);
  });

  it("LedMeter scanning posture reads as scanning, not a level", () => {
    const { container } = render(<LedMeter label="Level" value={1} scanning />);
    const meter = screen.getByRole("meter", { name: "Level" });
    expect(meter).toHaveAttribute("aria-valuetext", "scanning");
    // no level lit while the tape winds — the walk is CSS-driven
    expect(container.querySelectorAll("[data-lit]")).toHaveLength(0);
  });

  it("LampGadget is never color-only: the axis label rides with the lamp", () => {
    render(<LampGadget label="Live" on tone="ok" />);
    const lamp = screen.getByText("Live");
    expect(lamp).toHaveAttribute("data-on", "true");
    expect(lamp).toHaveAttribute("data-tone", "ok");
  });

  // HS-135-02 L6 — lamp overflow regression: truncation + title affordance.
  it("LampGadget carries a title tooltip with the full label text", () => {
    const longMsg =
      "DESTINATION SELECTION IGNORED · OPENAICOMPATIBLE-KIND DECIDES";
    render(<LampGadget label={longMsg} on tone="fail" />);
    const lamp = screen.getByText(longMsg);
    expect(lamp).toHaveAttribute("title", longMsg);
  });

  it("LampGadget default (inline) truncates via CSS class contract", () => {
    render(<LampGadget label="Short" on tone="ok" />);
    const lamp = screen.getByText("Short");
    expect(lamp.className).toBe("gadget-lamp");
    // the CSS contract: gadget-lamp has overflow:hidden + text-overflow:ellipsis
    // the class is the DOM proof; the CSS raw-text assertion below covers the rules.
  });

  it("LampGadget block variant adds is-block for wrap behavior", () => {
    const longMsg = "PROVIDER SELECTION IGNORED · DESTINATION HUB DECIDES";
    render(<LampGadget label={longMsg} on tone="fail" block />);
    const lamp = screen.getByText(longMsg);
    expect(lamp.className).toContain("is-block");
    expect(lamp).toHaveAttribute("title", longMsg);
  });

  it("TransportKey: held = pressed (inverted video is the CSS contract)", () => {
    const onClick = vi.fn();
    const { rerender } = render(
      <TransportKey label="Talk" glyph="🎙" onClick={onClick} />,
    );
    const key = screen.getByRole("button", { name: "Talk" });
    expect(key).not.toHaveAttribute("aria-pressed");
    fireEvent.click(key);
    expect(onClick).toHaveBeenCalled();
    rerender(<TransportKey label="Talk" glyph="🎙" active onClick={onClick} />);
    expect(screen.getByRole("button", { name: "Talk" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });

  it("GadgetTable verbs slot renders per-row verbs in place of the bare ×", async () => {
    const onForget = vi.fn();
    const user = userEvent.setup();
    render(
      <GadgetTable
        head={["Kind", "Gist"]}
        rows={[["intent", "send the launch checklist"]]}
        verbs={(index) => (
          <button type="button" onClick={() => onForget(index)}>
            Forget?
          </button>
        )}
      />,
    );
    expect(
      screen.queryByRole("button", { name: "Delete row 1" }),
    ).toBeNull();
    await user.click(screen.getByRole("button", { name: "Forget?" }));
    expect(onForget).toHaveBeenCalledWith(0);
  });

  // HS-111-08 — arming is the KIT DEFAULT (doctrine P0 F4): the bare
  // × never fires on the first press.
  it("GadgetTable default delete ARMS: × → DELETE? → gone", () => {
    vi.useFakeTimers();
    try {
      const onDelete = vi.fn();
      render(
        <GadgetTable
          head={["Kind"]}
          rows={[["intent"]]}
          onDelete={onDelete}
        />,
      );
      const x = screen.getByRole("button", { name: "Delete row 1" });
      fireEvent.click(x);
      expect(onDelete).not.toHaveBeenCalled();
      expect(x).toHaveTextContent("DELETE?");
      fireEvent.click(x);
      expect(onDelete).toHaveBeenCalledWith(0);
    } finally {
      vi.useRealTimers();
    }
  });

  it("the armed face self-disarms after 3s (a late press only re-arms)", () => {
    vi.useFakeTimers();
    try {
      const onDelete = vi.fn();
      render(
        <GadgetTable
          head={["Kind"]}
          rows={[["intent"]]}
          deleteLabel="FORGET?"
          onDelete={onDelete}
        />,
      );
      const x = screen.getByRole("button", { name: "Delete row 1" });
      fireEvent.click(x);
      expect(x).toHaveTextContent("FORGET?");
      act(() => {
        vi.advanceTimersByTime(3100);
      });
      expect(x).toHaveTextContent("×");
      fireEvent.click(x);
      expect(onDelete).not.toHaveBeenCalled();
    } finally {
      vi.useRealTimers();
    }
  });

  it("PadGadget is a real textarea", () => {
    const onChange = vi.fn();
    render(<PadGadget label="Notes" value="" onChange={onChange} mic={false} />);
    const pad = screen.getByRole("textbox", { name: "Notes" });
    fireEvent.change(pad, { target: { value: "spoken words" } });
    expect(onChange).toHaveBeenCalledWith("spoken words");
  });

  it("FoldGadget keeps details semantics and carries the token slot", () => {
    const onToggle = vi.fn();
    const { container } = render(
      <FoldGadget title="RAW · DIFF" token="1.2k tok" onToggle={onToggle}>
        <p>body</p>
      </FoldGadget>,
    );
    expect(screen.getByText("RAW · DIFF")).toBeInTheDocument();
    expect(screen.getByText("1.2k tok")).toBeInTheDocument();
    const details = container.querySelector("details.gadget-fold");
    expect(details).not.toBeNull();
    fireEvent(details!, new Event("toggle"));
    expect(onToggle).toHaveBeenCalled();
  });
});

// HS-135-02 L6 — lamp CSS contract: the raw stylesheet proves overflow
// handling exists on the base class and the block variant.
import gadgetsCss from "./gadgets.css?raw";

describe("HS-135-02 lamp overflow CSS contract", () => {
  it("gadget-lamp base truncates: overflow hidden + text-overflow ellipsis + max-width", () => {
    // The gadget-lamp block in the raw CSS must contain the overflow rules.
    const lampBlock = gadgetsCss.slice(
      gadgetsCss.indexOf(".gadget-lamp {"),
      gadgetsCss.indexOf("}", gadgetsCss.indexOf(".gadget-lamp {")) + 1,
    );
    expect(lampBlock).toContain("overflow: hidden");
    expect(lampBlock).toContain("text-overflow: ellipsis");
    expect(lampBlock).toContain("max-width: 100%");
    expect(lampBlock).toContain("white-space: nowrap");
  });

  it("gadget-lamp.is-block wraps instead of truncating", () => {
    expect(gadgetsCss).toContain(".gadget-lamp.is-block");
    const blockStart = gadgetsCss.indexOf(".gadget-lamp.is-block");
    const blockRule = gadgetsCss.slice(
      blockStart,
      gadgetsCss.indexOf("}", blockStart) + 1,
    );
    expect(blockRule).toContain("white-space: normal");
    expect(blockRule).toContain("word-break: break-word");
    expect(blockRule).toContain("text-overflow: clip");
  });
});
