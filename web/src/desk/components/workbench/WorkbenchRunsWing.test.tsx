import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { WorkbenchRun } from "../../detail-types";
import { WorkbenchRunsWing } from "./WorkbenchRunsWing";

const RUN: WorkbenchRun = {
  id: "run1",
  started_at: "2026-08-29T12:00:00Z",
  completed_at: "2026-08-29T12:01:00Z",
  items_attempted: 2,
  items_completed: 1,
  items_failed: 1,
  mint_failures: 0,
  total_tokens: 480,
  egress_boundary: "this_device",
  model: "local-model",
  status: "completed",
};

describe("WorkbenchRunsWing", () => {
  it("keeps the empty-state action honest", async () => {
    const onRun = vi.fn();
    render(
      <WorkbenchRunsWing
        runs={[]}
        configured
        running={false}
        openRunId={null}
        onToggleRun={vi.fn()}
        onRun={onRun}
        onBindAgent={vi.fn()}
      />,
    );

    await userEvent.setup().click(screen.getByRole("button", { name: "Run now" }));
    expect(onRun).toHaveBeenCalledOnce();
  });

  it("renders the run ledger and delegates disclosure state", async () => {
    const onToggleRun = vi.fn();
    const { rerender } = render(
      <WorkbenchRunsWing
        runs={[RUN]}
        configured
        running={false}
        openRunId={null}
        onToggleRun={onToggleRun}
        onRun={vi.fn()}
        onBindAgent={vi.fn()}
      />,
    );

    const runRow = screen.getByRole("button", {
      name: /1\/2 done.*1 failed.*local-model.*completed/i,
    });
    expect(runRow).toBeInTheDocument();
    await userEvent.setup().click(runRow);
    expect(onToggleRun).toHaveBeenCalledWith("run1");

    rerender(
      <WorkbenchRunsWing
        runs={[RUN]}
        configured
        running={false}
        openRunId="run1"
        onToggleRun={onToggleRun}
        onRun={vi.fn()}
        onBindAgent={vi.fn()}
      />,
    );
    expect(screen.getByText("480")).toBeInTheDocument();
  });
});
