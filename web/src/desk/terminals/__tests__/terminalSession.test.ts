import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  armTerminal,
  disarmTerminal,
  readTerminalSubscription,
  sendTerminalCommand,
} from "../api";
import { createTerminalSession } from "../terminalSession";
import type { TerminalDescriptor } from "../types";

vi.mock("../api", () => ({
  armTerminal: vi.fn(),
  disarmTerminal: vi.fn(),
  readTerminalSubscription: vi.fn(),
  sendTerminalCommand: vi.fn(),
}));

const descriptor = (id: string): TerminalDescriptor => ({
  id,
  label: id,
  session: `session-${id}`,
  key: `pane:${id}`,
  agent: "pane",
  command: "zsh",
  current_path: "/isolated",
  state: "live",
  target: {
    node_id: "local",
    target_id: `target-${id}`,
    target_generation: "generation-1",
  },
  pane_id: `%${id}`,
});

const response = (body: Record<string, unknown>, status = 200) => ({
  response: { ok: status < 400, status } as Response,
  body,
});

const flush = async () => {
  await Promise.resolve();
  await Promise.resolve();
};

describe("per-instance terminal session", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.mocked(armTerminal).mockResolvedValue({ ok: true });
    vi.mocked(disarmTerminal).mockResolvedValue({ ok: true, status: "disarmed" });
    vi.mocked(sendTerminalCommand).mockResolvedValue({
      ok: true,
      receipt: { receipt_id: "receipt-1", state: "succeeded", outcome: "delivered" },
    });
    vi.mocked(readTerminalSubscription).mockResolvedValue(
      response({ status: "snapshot", raw: "initial", sequence: 1, hash: "h1" }),
    );
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it("keeps two controllers independent", async () => {
    const a = createTerminalSession(descriptor("a"));
    const b = createTerminalSession(descriptor("b"));
    a.getState().start();
    b.getState().start();
    await flush();
    expect(a.getState().raw).toBe("initial");
    expect(b.getState().raw).toBe("initial");
    expect(vi.mocked(readTerminalSubscription)).toHaveBeenCalledTimes(2);
    expect(vi.mocked(readTerminalSubscription).mock.calls[0][0].target_id).not.toBe(
      vi.mocked(readTerminalSubscription).mock.calls[1][0].target_id,
    );
    a.getState().stop();
    expect(b.getState().status).toBe("live");
  });

  it("replaces a screen delta when the producer marks it as a redraw", async () => {
    const session = createTerminalSession(descriptor("redraw"));
    session.getState().setActivity({ focused: true, visible: true });
    session.getState().start();
    await flush();
    vi.mocked(readTerminalSubscription).mockResolvedValueOnce(
      response({
        status: "deltas",
        sequence: 2,
        deltas: [{ sequence: 2, data: "new screen", kind: "replace" }],
      }),
    );
    vi.advanceTimersByTime(350);
    await flush();
    expect(session.getState().raw).toBe("new screen");
    expect(session.getState().lines).toEqual(["new screen"]);
  });

  it("does not paint a response after the controller is stopped", async () => {
    let resolve: ((value: ReturnType<typeof response>) => void) | undefined;
    vi.mocked(readTerminalSubscription).mockReturnValueOnce(
      new Promise((done) => { resolve = done; }),
    );
    const session = createTerminalSession(descriptor("late"));
    session.getState().start();
    session.getState().stop();
    resolve?.(response({ status: "snapshot", raw: "late output", sequence: 1 }));
    await flush();
    expect(session.getState().raw).toBeNull();
    expect(session.getState().status).toBe("idle");
  });

  it("requires focus for xterm data and keeps pasted text non-submitting", async () => {
    const session = createTerminalSession(descriptor("input"));
    session.getState().start();
    await flush();
    expect(await session.getState().enableTyping()).toBe(true);
    expect(session.getState().sendData("no focus")).toBe(false);
    session.getState().setActivity({ focused: true, visible: true });
    expect(session.getState().sendData("one\r\x1b[200~two\nthree\x1b[201~")).toBe(true);
    vi.advanceTimersByTime(30);
    await flush();
    expect(vi.mocked(sendTerminalCommand)).toHaveBeenCalledTimes(2);
    expect(vi.mocked(sendTerminalCommand).mock.calls[0][1]).toBe("terminal.keys");
    expect(vi.mocked(sendTerminalCommand).mock.calls[0][2]).toMatchObject({ keys: [{ literal: "one" }, "Enter"] });
    expect(vi.mocked(sendTerminalCommand).mock.calls[1][1]).toBe("terminal.text");
    expect(vi.mocked(sendTerminalCommand).mock.calls[1][2]).toMatchObject({ text: "two\nthree", submit: false });
  });

  it("makes a view-only key action explain how to enable typing", async () => {
    const session = createTerminalSession(descriptor("view-only-key"));
    session.getState().start();
    await flush();
    expect(await session.getState().sendKeys(["Enter"], "ENTER")).toBe(false);
    expect(session.getState().error).toBe("Enable typing first");
  });

  it("sends natural single-line keyboard text, including a standalone space, as literal keys", async () => {
    const session = createTerminalSession(descriptor("typing"));
    session.getState().start();
    await flush();
    expect(await session.getState().enableTyping()).toBe(true);
    session.getState().setActivity({ focused: true, visible: true });
    expect(session.getState().sendData("printf")).toBe(true);
    vi.advanceTimersByTime(30);
    await flush();
    expect(vi.mocked(sendTerminalCommand).mock.calls[0][1]).toBe("terminal.keys");
    expect(vi.mocked(sendTerminalCommand).mock.calls[0][2]).toMatchObject({ keys: [{ literal: "printf" }] });
    expect(session.getState().sendData(" ")).toBe(true);
    vi.advanceTimersByTime(30);
    await flush();
    expect(vi.mocked(sendTerminalCommand).mock.calls[1][2]).toMatchObject({ keys: [{ literal: " " }] });
  });

  it("cancels unsent input when disarmed and does not auto-retry refusal", async () => {
    const session = createTerminalSession(descriptor("refused"));
    session.getState().start();
    await flush();
    expect(await session.getState().enableTyping()).toBe(true);
    session.getState().setActivity({ focused: true, visible: true });
    const queued = session.getState().sendText("retain until queued", false);
    await session.getState().disableTyping();
    expect(await queued).toBe(false);
    vi.advanceTimersByTime(100);
    await flush();
    expect(sendTerminalCommand).not.toHaveBeenCalled();
    expect(session.getState().canType).toBe(false);
    expect(disarmTerminal).toHaveBeenCalledTimes(1);
  });

  it("keeps a disarm failure visible after local typing is disabled", async () => {
    const session = createTerminalSession(descriptor("disarm-failure"));
    session.getState().start();
    await flush();
    expect(await session.getState().enableTyping()).toBe(true);
    vi.mocked(disarmTerminal).mockResolvedValueOnce({ ok: false, error: "hub unreachable" });

    await session.getState().disableTyping();
    expect(session.getState().canType).toBe(false);
    expect(session.getState().error).toBe("Disarm failed: hub unreachable");

    vi.mocked(readTerminalSubscription).mockResolvedValueOnce(
      response({ status: "not_modified", sequence: 1, hash: "h1" }),
    );
    vi.advanceTimersByTime(1_200);
    await flush();
    expect(session.getState().status).toBe("live");
    expect(session.getState().error).toBe("Disarm failed: hub unreachable");
  });

  it("resolves text only after the receipt, so a draft cannot clear at enqueue", async () => {
    let resolveCommand: ((value: { ok: true; receipt: { receipt_id: string; state: string; outcome: string } }) => void) | undefined;
    vi.mocked(sendTerminalCommand).mockReturnValueOnce(
      new Promise((done) => { resolveCommand = done; }),
    );
    const session = createTerminalSession(descriptor("receipt"));
    session.getState().start();
    await flush();
    expect(await session.getState().enableTyping()).toBe(true);
    const pending = session.getState().sendText("until receipt", true);
    let settled = false;
    void pending.then(() => { settled = true; });
    vi.advanceTimersByTime(30);
    await flush();
    expect(settled).toBe(false);
    resolveCommand?.({ ok: true, receipt: { receipt_id: "receipt-2", state: "succeeded", outcome: "delivered" } });
    await flush();
    expect(await pending).toBe(true);
  });

  it("does not let an old in-flight send splice newly queued input after re-enable", async () => {
    let resolveOld: ((value: { ok: true; receipt: { receipt_id: string; state: string; outcome: string } }) => void) | undefined;
    vi.mocked(sendTerminalCommand).mockReturnValueOnce(
      new Promise((done) => { resolveOld = done; }),
    );
    const session = createTerminalSession(descriptor("queue-epoch"));
    session.getState().start();
    await flush();
    expect(await session.getState().enableTyping()).toBe(true);
    const oldPending = session.getState().sendText("old", true);
    vi.advanceTimersByTime(30);
    await flush();
    expect(vi.mocked(sendTerminalCommand)).toHaveBeenCalledTimes(1);

    await session.getState().disableTyping();
    expect(await oldPending).toBe(false);
    expect(await session.getState().enableTyping()).toBe(true);
    const newPending = session.getState().sendText("new", true);
    resolveOld?.({ ok: true, receipt: { receipt_id: "old-receipt", state: "succeeded", outcome: "delivered" } });
    await flush();
    expect(sendTerminalCommand).toHaveBeenCalledTimes(2);
    expect(vi.mocked(sendTerminalCommand).mock.calls[1][2]).toMatchObject({ text: "new", submit: true });
    await flush();
    expect(await newPending).toBe(true);
  });

  it("keeps a failed delivery visible through a successful screen poll", async () => {
    vi.mocked(sendTerminalCommand).mockResolvedValueOnce({
      ok: false,
      error: "Not sent: pane refused the command",
      receipt: { receipt_id: "refused-1", state: "failed", outcome: "refused" },
    });
    const session = createTerminalSession(descriptor("sticky-error"));
    session.getState().start();
    await flush();
    expect(await session.getState().enableTyping()).toBe(true);

    const pending = session.getState().sendText("will fail", true);
    vi.advanceTimersByTime(30);
    await flush();
    expect(await pending).toBe(false);
    expect(session.getState().error).toBe("Not sent: pane refused the command");

    vi.mocked(readTerminalSubscription).mockResolvedValueOnce(
      response({ status: "not_modified", sequence: 1, hash: "h1" }),
    );
    vi.advanceTimersByTime(1_200);
    await flush();
    expect(session.getState().status).toBe("live");
    expect(session.getState().error).toBe("Not sent: pane refused the command");
  });

  it("keeps an arm refusal visible through a successful screen poll", async () => {
    vi.mocked(armTerminal).mockResolvedValueOnce({
      ok: false,
      error: "Typing not armed: target changed",
    });
    const session = createTerminalSession(descriptor("sticky-arm-error"));
    session.getState().start();
    await flush();
    expect(await session.getState().enableTyping()).toBe(false);
    expect(session.getState().error).toBe("Typing not armed: target changed");

    vi.mocked(readTerminalSubscription).mockResolvedValueOnce(
      response({ status: "not_modified", sequence: 1, hash: "h1" }),
    );
    vi.advanceTimersByTime(1_200);
    await flush();
    expect(session.getState().status).toBe("live");
    expect(session.getState().error).toBe("Typing not armed: target changed");
  });
});
