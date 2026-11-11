import { useRef, useState } from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { it, expect, vi } from "vitest";
import { InspectorQuestion } from "./PreferencePane";
import { StringGadget } from "../gadgets";

it("keeps the question identity frozen while its answer fields can change", () => {
  const send = vi.fn(),
    cancel = vi.fn();
  function Question({ target }: { target: string }) {
    const [note, setNote] = useState("");
    const draft = useRef(note);
    draft.current = note;
    return (
      <InspectorQuestion
        actionId="answer"
        targetId={target}
        question="Go on?"
        cancel={cancel}
        rows={[
          {
            label: "Note",
            control: (
              <StringGadget
                label="Answer note"
                value={note}
                onChange={setNote}
              />
            ),
          },
        ]}
        verb={{
          label: "Go on",
          run: () => send({ target, note: draft.current }),
        }}
      />
    );
  }
  const view = render(<Question target="step:revision1" />);
  fireEvent.change(screen.getByLabelText("Answer note"), {
    target: { value: "Keep this reason." },
  });
  fireEvent.click(screen.getByRole("button", { name: "Go on" }));
  expect(send).toHaveBeenCalledWith({
    target: "step:revision1",
    note: "Keep this reason.",
  });
  view.rerender(<Question target="step:revision2" />);
  expect(screen.queryByRole("button", { name: "Go on" })).toBeNull();
  expect(cancel).toHaveBeenCalled();
  expect(send).toHaveBeenCalledTimes(1);
});
