// HS-132-06 — the write-receipt channel itself: a refused write is named,
// carries a retry that re-issues the exact call, and a landed write is quiet.
import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  clearWriteFailure,
  currentWriteFailure,
  reportWriteFailure,
  useDeskWriteReceipt,
  useWriteReceipt,
  writeFailureLabel,
  writeFailureReason,
} from "../useWriteReceipt";

// Query helper scoped to the render root (testing-library renders into
// document.body, so this equals baseElement.querySelector).
const q = (sel: string): HTMLElement | null => document.body.querySelector(sel);
const qa = (sel: string) => document.body.querySelectorAll(sel);

function Harness({ run }: { run: () => Promise<unknown> }) {
  const { attempt, receipt } = useWriteReceipt();
  return (
    <div>
      <button type="button" onClick={() => void attempt("ADD ITEM", run)}>
        GO
      </button>
      {receipt}
    </div>
  );
}

function DeskHarness() {
  const { receipt } = useDeskWriteReceipt();
  return <div>{receipt}</div>;
}

describe("HS-132-06 write-receipt channel", () => {
  beforeEach(() => clearWriteFailure());

  it("names the cause in label grammar", () => {
    expect(writeFailureReason(new Response("", { status: 503 }))).toBe("HTTP 503");
    expect(writeFailureReason(Object.assign(new Error("nope"), { status: 422 }))).toBe(
      "HTTP 422",
    );
    expect(writeFailureReason(new TypeError("Failed to fetch"))).toBe("HUB UNREACHABLE");
    expect(writeFailureReason("bad payload")).toBe("BAD PAYLOAD");
    expect(writeFailureReason(new Error("weird"))).toBe("WRITE REFUSED");
  });

  it("stays quiet when the write lands", async () => {
    const user = userEvent.setup();
    render(<Harness run={async () => "ok"} />);
    await user.click(screen.getByText("GO"));
    expect(q(".write-receipt")).toBeNull();
  });

  it("seats a named receipt with retry when the write is refused", async () => {
    const user = userEvent.setup();
    const run = vi
      .fn()
      .mockRejectedValueOnce(Object.assign(new Error("boom"), { status: 500 }))
      .mockResolvedValueOnce("ok");
    render(<Harness run={run} />);

    await user.click(screen.getByText("GO"));
    expect(screen.getByText("ADD ITEM FAILED · HTTP 500")).toBeInTheDocument();

    // Retry re-issues the exact same call; a landed retry clears the receipt.
    await user.click(screen.getByRole("button", { name: "Retry" }));
    expect(run).toHaveBeenCalledTimes(2);
    expect(q(".write-receipt")).toBeNull();
  });

  it("treats a refused Response as a failure without a throw", async () => {
    const user = userEvent.setup();
    render(<Harness run={async () => new Response("", { status: 422 })} />);
    await user.click(screen.getByText("GO"));
    expect(screen.getByText("ADD ITEM FAILED · HTTP 422")).toBeInTheDocument();
  });

  it("dismisses on OK without re-issuing anything", async () => {
    const user = userEvent.setup();
    const run = vi.fn().mockRejectedValue(new TypeError("Failed to fetch"));
    render(<Harness run={run} />);
    await user.click(screen.getByText("GO"));
    expect(screen.getByText("ADD ITEM FAILED · HUB UNREACHABLE")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "OK" }));
    expect(q(".write-receipt")).toBeNull();
    expect(run).toHaveBeenCalledTimes(1);
  });

  it("carries module-channel failures to any mounted receipt line", async () => {
    render(<DeskHarness />);
    expect(q(".write-receipt")).toBeNull();

    const retry = vi.fn();
    act(() => {
      reportWriteFailure("SEED DESK", new Response("", { status: 500 }), retry);
    });
    expect(screen.getByText("SEED DESK FAILED · HTTP 500")).toBeInTheDocument();
    expect(writeFailureLabel(currentWriteFailure()!)).toBe("SEED DESK FAILED · HTTP 500");

    await userEvent.setup().click(screen.getByRole("button", { name: "Retry" }));
    expect(retry).toHaveBeenCalledTimes(1);

    act(() => clearWriteFailure());
    expect(q(".write-receipt")).toBeNull();
  });
});
