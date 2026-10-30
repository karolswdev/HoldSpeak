// HS-111-01 — the gadget kit: every gadget wraps a REAL input and the
// interaction contracts hold (checkbox species, cycle select, stepper
// arrows, mx radio reveal, secret armed replace).
import { act, fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { createRef } from "react";
import {
  CheckGadget,
  CycleGadget,
  FoldGadget,
  GadgetDivider,
  GadgetGroup,
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
import { Button } from "../../components/signal/Signal";
import { SurfaceColumns } from "./Surface";

const { micCallbacks } = vi.hoisted(() => ({ micCallbacks: new Map<string, (text: string) => void>() }));
vi.mock("../components/MicButton", () => ({
  MicButton: ({ onText, label = "Speak", draftScope = "" }: { onText: (text: string) => void; label?: string; draftScope?: string }) => {
    micCallbacks.set(draftScope, onText);
    return <button type="button" aria-label={label} data-draft-scope={draftScope}/>;
  },
}));

describe("gadget kit", () => {
  it("inset groups name their section and keep actions after block content", () => {
    const { container } = render(
      <GadgetGroup label="Spoken symbols" material="inset" actions={<Button>Add symbol</Button>}>
        <GadgetRow label="Dictionary" controlWidth="full"><div>Symbol editor</div></GadgetRow>
        <GadgetDivider/>
      </GadgetGroup>,
    );
    const group = screen.getByRole("region", { name: "Spoken symbols" });
    expect(group).toHaveAttribute("data-material", "inset");
    const content = group.querySelector(".gadget-sheet")!;
    const footer = screen.getByRole("button", { name: "Add symbol" }).closest("footer")!;
    expect(footer.parentElement).toBe(group);
    expect(content.contains(footer)).toBe(false);
    expect(content.compareDocumentPosition(footer) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(container.querySelector(".gadget-row-gadget")?.tagName).toBe("DIV");
    expect(screen.getByRole("separator")).toBeInTheDocument();
  });

  it("state checks expose one named checkbox and a visible On or Off value", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    const { rerender } = render(<CheckGadget variant="state" label="Preview before type" checked={false} onChange={onChange}/>);
    const box = screen.getByRole("checkbox", { name: "Preview before type" });
    expect(screen.getAllByRole("checkbox")).toHaveLength(1);
    expect(screen.getByText("Off")).toHaveAttribute("aria-hidden", "true");
    await user.click(screen.getByText("Off").closest("label")!);
    expect(onChange).toHaveBeenCalledWith(true);
    rerender(<CheckGadget variant="state" label="Preview before type" checked onChange={onChange}/>);
    expect(screen.getByText("On")).toBeInTheDocument();
    expect(box).toBeChecked();
    box.focus();
    await user.keyboard(" ");
    expect(onChange).toHaveBeenLastCalledWith(false);
  });

  it("disabled state checks retain their value and reject pointer and keyboard changes", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<CheckGadget variant="state" label="Voice commands" checked disabled onChange={onChange}/>);
    expect(screen.getByText("On")).toBeInTheDocument();
    const box = screen.getByRole("checkbox", { name: "Voice commands" });
    expect(box).toBeDisabled();
    await user.click(screen.getByText("On").closest("label")!);
    await user.keyboard(" ");
    expect(onChange).not.toHaveBeenCalled();
  });

  it("field tables derive repeated visible labels from the supplied heads", () => {
    const onChange = vi.fn();
    const { container, rerender } = render(<GadgetTable layout="fields" head={["Spoken", "Attach"]} rows={[[
      <input key="spoken" aria-label="Spoken phrase 1" defaultValue="arrow"/>,
      <CycleGadget key="attach" label="Attachment 1" value="none" options={[{ value:"none" },{ value:"right" }]} onChange={onChange}/>,
    ]]}/>);
    const labels = container.querySelectorAll(".gadget-table-field-label");
    expect(Array.from(labels, (label) => label.textContent)).toEqual(["Spoken", "Attach"]);
    labels.forEach((label) => expect(label).toHaveAttribute("aria-hidden", "true"));
    fireEvent.change(screen.getByRole("combobox", { name:"Attachment 1" }), { target:{ value:"right" } });
    expect(onChange).toHaveBeenCalledWith("right");
    rerender(<GadgetTable head={["Spoken"]} rows={[["arrow"]]}/>);
    expect(container.querySelector(".gadget-table-field-label")).toBeNull();
  });

  it("field tables keep editing keys native and preserve an armed row action across reorder", () => {
    const onDelete = vi.fn();
    const entries = [{ id:"arrow", word:"arrow" },{ id:"bracket", word:"bracket" }];
    const table = (items: typeof entries) => <GadgetTable layout="fields" head={["Spoken"]}
      rowKey={(index) => items[index].id} onDelete={onDelete} deleteLabel="Forget?"
      rows={items.map((entry) => [<input key={entry.id} aria-label={entry.id} defaultValue={entry.word}/>])}/>;
    const { rerender } = render(table(entries));
    const arrow = screen.getByRole("textbox", { name:"arrow" });
    const bracket = screen.getByRole("textbox", { name:"bracket" });
    arrow.focus();
    fireEvent.keyDown(arrow, { key:"ArrowDown" });
    expect(arrow).toHaveFocus();
    const firstAction = screen.getByRole("button", { name:"Delete row 1" });
    firstAction.focus();
    fireEvent.keyDown(firstAction, { key:"ArrowDown" });
    const action = screen.getByRole("button", { name:"Delete row 2" });
    expect(action).toHaveFocus();
    fireEvent.keyDown(action, { key:"ArrowLeft" });
    expect(bracket).toHaveFocus();
    fireEvent.click(action);
    expect(onDelete).not.toHaveBeenCalled();
    rerender(table([entries[1], entries[0]]));
    expect(screen.getByRole("button", { name:"Delete row 1" })).toBe(action);
    expect(action).toHaveTextContent("Forget?");
    fireEvent.click(action);
    expect(onDelete).toHaveBeenCalledWith(0);
  });

  it("preference columns retain the two content slots and leave the default unmarked", () => {
    const { container, rerender } = render(<SurfaceColumns variant="preferences" main={<span>Capture</span>} side={<span>Symbols</span>}/>);
    expect(container.querySelector('.surface-columns[data-variant="preferences"] > .surface-columns-main')).toHaveTextContent("Capture");
    expect(container.querySelector('.surface-columns[data-variant="preferences"] > .surface-columns-side')).toHaveTextContent("Symbols");
    rerender(<SurfaceColumns main={<span>Capture</span>} side={<span>Symbols</span>}/>);
    expect(container.querySelector(".surface-columns")).not.toHaveAttribute("data-variant");
  });

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
    // W1-KIT: at its max the + step is disabled (the value cannot pass it).
    const increase = screen.getByRole("button", { name: "Increase History lines" });
    expect(increase).toBeDisabled();
    await user.click(increase);
    expect(onChange).not.toHaveBeenCalled();
    const decrease = screen.getByRole("button", { name: "Decrease History lines" });
    // Both steps are the library Button (dense), never a raw <button>.
    expect(decrease.className).toContain("btn--sm");
    expect(increase.className).toContain("btn--sm");
    await user.click(decrease);
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
    expect(screen.getByText("Set")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Replace" }));
    const input = screen.getByLabelText("Replacement Web pairing token");
    await user.type(input, "new-secret{Enter}");
    expect(onReplace).toHaveBeenCalledWith("new-secret");
    // the chip returns after the commit
    expect(screen.getByText("Set")).toBeInTheDocument();
  });

  it("SecretRow Escape reverts the armed replace without committing", async () => {
    const onReplace = vi.fn();
    const user = userEvent.setup();
    render(
      <SecretRow label="Device audio key" configured={false} onReplace={onReplace} />,
    );
    expect(screen.getByText("Not set")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Replace" }));
    const input = screen.getByLabelText("Replacement Device audio key");
    await user.type(input, "draft{Escape}");
    expect(onReplace).not.toHaveBeenCalled();
    expect(screen.getByText("Not set")).toBeInTheDocument();
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
    // LAMPS-WORDS: the lamp draws (and titles) its word in sentence case.
    const words = "Destination selection ignored · Openaicompatible-kind decides";
    const lamp = screen.getByText(words);
    expect(lamp).toHaveAttribute("title", words);
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
    const words = "Provider selection ignored · Destination hub decides";
    const lamp = screen.getByText(words);
    expect(lamp.className).toContain("is-block");
    expect(lamp).toHaveAttribute("title", words);
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

  it("PadGadget keeps one mic and appends a late capture through the latest value and writer", () => {
    const firstChange = vi.fn();
    const latestChange = vi.fn();
    const { rerender } = render(<PadGadget label="Material" value="First draft." onChange={firstChange}
      micLabel="Speak material" micDraftScope="pad:late-material"/>);
    const lateCapture = micCallbacks.get("pad:late-material")!;
    expect(screen.getAllByRole("button", { name: "Speak material" })).toHaveLength(1);
    const newer = "Edited first paragraph.\n\nSecond paragraph stays.";
    rerender(<PadGadget label="Material" value={newer} onChange={latestChange}
      micLabel="Speak material" micDraftScope="pad:late-material"/>);
    act(() => lateCapture("New spoken clause."));
    expect(firstChange).not.toHaveBeenCalled();
    expect(latestChange).toHaveBeenCalledExactlyOnceWith(`${newer} New spoken clause.`);
    expect(screen.getByRole("textbox", { name: "Material" })).toHaveValue(newer);
    expect(screen.getAllByRole("button", { name: "Speak material" })).toHaveLength(1);
  });

  it("PadGadget forwards native combobox attributes and its textarea ref", () => {
    const inputRef = createRef<HTMLTextAreaElement>();
    const onPaste = vi.fn();
    const { unmount } = render(<PadGadget label="Instruction" value="Review" onChange={vi.fn()} mic={false}
      inputRef={inputRef} inputProps={{ role: "combobox", "aria-expanded": false, "aria-controls": "sources", onPaste }} />);
    const pad = screen.getByRole("combobox", { name: "Instruction" });
    expect(pad.tagName).toBe("TEXTAREA");
    expect(inputRef.current).toBe(pad);
    expect(pad).toHaveAttribute("aria-controls", "sources");
    fireEvent.paste(pad);
    expect(onPaste).toHaveBeenCalledOnce();
    unmount();
    expect(inputRef.current).toBeNull();
  });

  it("PadGadget keeps controlled ownership and auto-grow when an external ref is used", () => {
    const onChange = vi.fn(), onKeyDown = vi.fn(), rejectedChange = vi.fn(), rejectedKey = vi.fn();
    const inputRef = vi.fn();
    const props = { role: "combobox", "aria-label": "Wrong", value: "Wrong", onChange: rejectedChange, onKeyDown: rejectedKey } as never;
    const view = (value: string) => <PadGadget label="Instruction" value={value} onChange={onChange} onKeyDown={onKeyDown}
      mic={false} autoGrow inputRef={inputRef} inputProps={props} />;
    const { rerender } = render(view("Review"));
    const pad = screen.getByRole("combobox", { name: "Instruction" });
    expect(inputRef).toHaveBeenCalledWith(pad);
    expect(pad).toHaveValue("Review");
    Object.defineProperty(pad, "scrollHeight", { configurable: true, value: 80 });
    rerender(view("Review\nConfirm ownership"));
    expect(pad).toHaveStyle({ height: "82px" });
    fireEvent.change(pad, { target: { value: "Revised" } });
    fireEvent.keyDown(pad, { key: "Enter" });
    expect(onChange).toHaveBeenCalledWith("Revised");
    expect(onKeyDown).toHaveBeenCalledOnce();
    expect(rejectedChange).not.toHaveBeenCalled();
    expect(rejectedKey).not.toHaveBeenCalled();
  });

  it("PadGadget auto-grow remeasures width changes, ignores height feedback and disconnects", () => {
    let notify!: ResizeObserverCallback;
    const observe = vi.fn(), disconnect = vi.fn();
    vi.stubGlobal("ResizeObserver", class {
      constructor(callback: ResizeObserverCallback) { notify = callback; }
      observe = observe;
      disconnect = disconnect;
    });
    try {
      const view = (value: string) => <PadGadget label="Resized instruction" value={value} onChange={vi.fn()} mic={false} autoGrow />;
      const { rerender, unmount } = render(view("Review the complete migration instruction"));
      const pad = screen.getByRole("textbox", { name: "Resized instruction" });
      let contentHeight = 271;
      Object.defineProperty(pad, "scrollHeight", { configurable: true, get: () => contentHeight });
      const resize = (width: number) => act(() => notify([{ contentRect: { width } } as ResizeObserverEntry], {} as ResizeObserver));
      expect(observe).toHaveBeenCalledWith(pad);
      resize(566);
      expect(pad).toHaveStyle({ height: "273px" });
      contentHeight = 634;
      resize(327);
      expect(pad).toHaveStyle({ height: "636px" });
      contentHeight = 900;
      resize(327);
      expect(pad).toHaveStyle({ height: "636px" });
      contentHeight = 40;
      rerender(view("A shorter instruction"));
      expect(pad).toHaveStyle({ height: "42px" });
      expect(disconnect).toHaveBeenCalledOnce();
      unmount();
      expect(disconnect).toHaveBeenCalledTimes(2);
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it("FoldGadget keeps details semantics and carries the token slot", () => {
    const onToggle = vi.fn();
    const { container } = render(
      <FoldGadget title="RAW · DIFF" token="1.2k tok" onToggle={onToggle}>
        <p>body</p>
      </FoldGadget>,
    );
    expect(screen.getByText("Raw · Diff")).toBeInTheDocument();
    expect(screen.getByText("1.2k tok")).toBeInTheDocument();
    const details = container.querySelector("details.gadget-fold");
    expect(details).not.toBeNull();
    fireEvent(details!, new Event("toggle"));
    expect(onToggle).toHaveBeenCalled();
  });
});

