import { useState } from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import {
  hub,
  mocks,
  todoFixture,
  todoDoneFixture,
  proposalsFixture,
  proposalsAddedFixture,
  auditSecureFixture,
  auditFiledFixture,
  auditBoardFixture,
  auditFixFixture,
  lessonProgramFixture,
  lessonKeptFixture,
  deliveryMergeFixture,
  deliveryMergedFixture,
  deliveryCheckFixture,
  deliveryCheckedOpenFixture,
  deliveryUnknownFixture,
  deliveryQueuedFixture,
  deliveryLegacyFixture,
  type Program,
} from "./programs.seats.test-setup";
import { ProgramNow } from "../ProgramWindow";
import type { YourTurnItem } from "../types";
const program = (wire: unknown) =>
  ((wire as { program?: Program }).program ?? wire) as Program;
function Now({ initial }: { initial: Program }) {
  const [p, setP] = useState(initial);
  return (
    <ProgramNow
      program={p}
      onApplied={(next) => {
        if (next) setP(next);
      }}
      onError={() => {}}
    />
  );
}
describe("Every answer kind in Now keeps its note and custody", () => {
  for (const [label, before, after, kind, choice] of [
    ["walk", todoFixture, todoDoneFixture, "todo", "done"],
    [
      "proposal",
      proposalsFixture,
      proposalsAddedFixture,
      "requirement_proposed",
      "add",
    ],
    [
      "file findings",
      auditSecureFixture,
      auditFiledFixture,
      "audit_file",
      "file",
    ],
    ["fix program", auditBoardFixture, auditFixFixture, "fix_program", "make"],
    ["lesson", lessonProgramFixture, lessonKeptFixture, "lesson", "program"],
    [
      "delivery",
      deliveryMergeFixture,
      deliveryMergedFixture,
      "delivery",
      "merge",
    ],
    [
      "check delivery",
      deliveryCheckFixture,
      deliveryCheckedOpenFixture,
      "delivery",
      "check",
    ],
  ] as const) {
    it(`${label}: sends the shown question and renders the acknowledged result`, async () => {
      const p = program(before),
        next = program(after),
        item =
          p.your_turn_items.find((x) => x.kind === kind) ??
          p.your_turn_items[0];
      hub({
        [item.requirement_id
          ? `POST /api/programs/${p.id}/requirements/${item.requirement_id}/decide`
          : `POST /api/programs/${p.id}/steps/${item.step_id || "program"}/decide`]:
          after,
      });
      render(<Now initial={p} />);
      const questions = screen.queryByRole("combobox", { name: "Question" });
      if (questions)
        fireEvent.change(questions, { target: { value: item.id } });
      const answer = screen.queryByRole("combobox", { name: "Answer" });
      const chosen = item.choices.includes(choice)
        ? choice
        : item.choices.find((x) => x !== "park")!;
      if (answer) fireEvent.change(answer, { target: { value: chosen } });
      fireEvent.change(screen.getByLabelText("Answer note"), {
        target: { value: "I read this result." },
      });
      fireEvent.click(screen.getByTestId("program-go-on"));
      await waitFor(() =>
        expect(mocks.apiFetch).toHaveBeenCalledWith(
          expect.any(String),
          expect.objectContaining({
            json: expect.objectContaining({
              ...(item.requirement_id
                ? { line: "I read this result." }
                : { kind: item.kind, reason: "I read this result." }),
              choice: chosen,
              binding: expect.objectContaining({
                program_id: p.id,
                step_id: item.step_id || "",
              }),
            }),
          }),
        ),
      );
      await waitFor(() =>
        expect(
          document.querySelector('[data-testid="program-question"]')
            ?.textContent || "",
        ).not.toContain(item.brief?.question || item.title),
      );
      expect(next.your_turn_items.some((x) => x.id === item.id)).toBe(false);
    });
  }
  it.each([
    deliveryUnknownFixture,
    deliveryQueuedFixture,
    deliveryLegacyFixture,
  ])(
    "uncertain or old deliveries expose only the choices returned by the hub",
    (wire) => {
      const p = program(wire);
      render(<Now initial={p} />);
      const item = p.your_turn_items.find((x) => x.kind === "delivery")!;
      const answer = screen.queryByRole("combobox", { name: "Answer" });
      const options = answer
        ? [...answer.querySelectorAll("option")].map((x) => x.value)
        : [];
      expect(options).toEqual(
        item.choices.filter((x) => x !== "park").length > 1
          ? item.choices.filter((x) => x !== "park")
          : [],
      );
      expect(options).not.toContain("retry");
      expect(options).not.toContain("merge");
    },
  );
});
