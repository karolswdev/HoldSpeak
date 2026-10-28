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
  writeFailurePhrase,
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
    expect(screen.getByText("Could not add the item")).toBeInTheDocument();
    // The reason is the hover title, never the face.
    expect(q(".write-receipt-label")?.getAttribute("title")).toBe("Could not add the item · HTTP 500");

    // Retry re-issues the exact same call; a landed retry clears the receipt.
    await user.click(screen.getByRole("button", { name: "Try again" }));
    expect(run).toHaveBeenCalledTimes(2);
    expect(q(".write-receipt")).toBeNull();
  });

  it("treats a refused Response as a failure without a throw", async () => {
    const user = userEvent.setup();
    render(<Harness run={async () => new Response("", { status: 422 })} />);
    await user.click(screen.getByText("GO"));
    expect(screen.getByText("Could not add the item")).toBeInTheDocument();
  });

  it("dismisses on OK without re-issuing anything", async () => {
    const user = userEvent.setup();
    const run = vi.fn().mockRejectedValue(new TypeError("Failed to fetch"));
    render(<Harness run={run} />);
    await user.click(screen.getByText("GO"));
    expect(screen.getByText("Could not add the item")).toBeInTheDocument();
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
    expect(screen.getByText("Could not set up the desk")).toBeInTheDocument();
    expect(writeFailureLabel(currentWriteFailure()!)).toBe("Could not set up the desk");

    await userEvent.setup().click(screen.getByRole("button", { name: "Try again" }));
    expect(retry).toHaveBeenCalledTimes(1);

    act(() => clearWriteFailure());
    expect(q(".write-receipt")).toBeNull();
  });

  it("draws every failure as one sans sentence with Try again (atlas pass 3, defect 16; W6-E)", async () => {
    render(<DeskHarness />);
    const retry = vi.fn();
    act(() => {
      reportWriteFailure("Mark seen", new Response("", { status: 404 }), retry, "agent:l1");
    });
    const band = q(".write-receipt") as HTMLElement;
    expect(band.classList.contains("write-receipt-plain")).toBe(true);
    expect(band.classList.contains("write-receipt-mono")).toBe(false);
    expect(band.textContent).toContain("Could not mark it seen");
    expect(band.textContent).not.toMatch(/MARK SEEN|FAILED|HTTP 404/);
    // The reason stays reachable as the hover title, never on the face.
    expect(q(".write-receipt-label")?.getAttribute("title")).toBe("Could not mark it seen · HTTP 404");
    await userEvent.setup().click(screen.getByRole("button", { name: "Try again" }));
    expect(retry).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole("button", { name: "Retry" })).toBeNull();
  });

  it("says each verb in its own words, with the noun from the subject (W6-E)", () => {
    expect(writeFailurePhrase("SAVE", "note:n1")).toBe("save the note");
    expect(writeFailurePhrase("SAVE", "knowledge:k1")).toBe("save the drawer");
    expect(writeFailurePhrase("SAVE")).toBe("save it");
    expect(writeFailurePhrase("RENAME", "zone:z1")).toBe("rename the zone");
    expect(writeFailurePhrase("DELETE", "decision:d1")).toBe("delete the decision");
    expect(writeFailurePhrase("CREATE note")).toBe("make the note");
    expect(writeFailurePhrase("CREATE kb")).toBe("make the drawer");
    expect(writeFailurePhrase("READ Meetings")).toBe("load the meetings");
    expect(writeFailurePhrase("Send")).toBe("send it");
    expect(writeFailurePhrase("New Note")).toBe("make the note");
    // A verb with no phrase of its own is said in lower case.
    expect(writeFailurePhrase("Hold as source")).toBe("hold as source");
  });

  it("keeps the parked mono caps face behind the opt-in (W6-E)", () => {
    render(<DeskHarness />);
    act(() => {
      reportWriteFailure("SEED DESK", new Response("", { status: 500 }), vi.fn(), undefined, undefined, { mono: true });
    });
    const band = q(".write-receipt") as HTMLElement;
    expect(band.classList.contains("write-receipt-mono")).toBe(true);
    expect(band.textContent).toContain("SEED DESK FAILED · HTTP 500");
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
  });
});
