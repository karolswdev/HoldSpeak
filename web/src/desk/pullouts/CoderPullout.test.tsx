import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { readDurableDraft } from "../../lib/durableDraft";
import { EMPTY_ITEMS } from "../api";
import { useDesk } from "../store";
import type { WorldObject } from "../world";
import { CoderPullout } from "./CoderPullout";

vi.mock("../components/MicButton", () => ({ MicButton: () => null }));
const speak = vi.fn();
const object: WorldObject = {
  kind: "coder", id: "session-1", title: "Migration review",
  ref: { kind: "coder", id: "session-1", sessionId: "session-1", agent: "claude", state: "waiting", question: "Who owns rollback?" },
};
const scope = "coder-reply:session-1";
const mount = () => render(<CoderPullout object={object} onClose={vi.fn()} />);

beforeEach(() => {
  localStorage.clear();
  speak.mockReset();
  useDesk.setState({ items: { ...EMPTY_ITEMS }, selectedIds: [], speakToCoder: speak });
});

describe("Coder reply custody", () => {
  it("sends once and retains newer text durably when the sent snapshot lands", async () => {
    let release!: (ok: boolean) => void;
    speak.mockImplementation(() => new Promise<boolean>((resolve) => { release = resolve; }));
    const view = mount();
    const field = screen.getByRole("textbox", { name: "Reply to the agent" });
    const send = screen.getByRole("button", { name: "Send reply" });
    fireEvent.change(field, { target: { value: "  Jordan owns rollback.  " } });
    fireEvent.click(send);
    fireEvent.click(send);
    expect(send).toBeDisabled();
    expect(speak).toHaveBeenCalledTimes(1);
    expect(speak).toHaveBeenCalledWith("claude", "session-1", "Jordan owns rollback.");
    fireEvent.change(field, { target: { value: "Avery reviews the plan." } });
    await act(async () => { release(true); });
    expect(field).toHaveValue("Avery reviews the plan.");
    expect(readDurableDraft(scope)?.text).toBe("Avery reviews the plan.");
    view.unmount();
    mount();
    expect(screen.getByRole("textbox", { name: "Reply to the agent" })).toHaveValue("Avery reviews the plan.");
  });

  it("retains a refused reply and clears only that snapshot after Retry succeeds", async () => {
    speak.mockResolvedValueOnce(false).mockResolvedValueOnce(true);
    mount();
    const field = screen.getByRole("textbox", { name: "Reply to the agent" });
    fireEvent.change(field, { target: { value: "Jordan owns rollback." } });
    fireEvent.click(screen.getByRole("button", { name: "Send reply" }));
    expect(await screen.findByText("REPLY FAILED · RETRY")).toBeVisible();
    expect(field).toHaveValue("Jordan owns rollback.");
    expect(readDurableDraft(scope)?.text).toBe("Jordan owns rollback.");
    fireEvent.click(screen.getByRole("button", { name: "Retry reply" }));
    await waitFor(() => expect(field).toHaveValue(""));
    expect(speak).toHaveBeenCalledTimes(2);
    expect(readDurableDraft(scope)).toBeNull();
    expect(screen.getByText("REPLY SENT")).toBeVisible();
  });

  it("names a rejected send and keeps the reply for Retry", async () => {
    speak.mockRejectedValueOnce(new Error("Unavailable"));
    mount();
    fireEvent.change(screen.getByRole("textbox", { name: "Reply to the agent" }), { target: { value: "Keep this reply" } });
    fireEvent.click(screen.getByRole("button", { name: "Send reply" }));
    expect(await screen.findByRole("button", { name: "Retry reply" })).toBeEnabled();
    expect(readDurableDraft(scope)?.text).toBe("Keep this reply");
  });
});
