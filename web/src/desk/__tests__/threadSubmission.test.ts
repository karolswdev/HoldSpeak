import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../lib/api";
import { useThreadStore, type TurnResult } from "../threads";

vi.mock("../../lib/api", () => ({ apiFetch: vi.fn() }));

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: Error) => void;
  const promise = new Promise<T>((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}

const ack: TurnResult = { thread_id: "t-1", user_message_id: "u-1", assistant_message_id: "a-1" };
const start = { thread_id: "t-1", user_message_id: "u-1", message_id: "a-1", model_id: "fixture", egress: null };
const empty = { id: "t-1", title: "Test", messages: [] };
const snapshot = {
  ...empty,
  messages: [
    { id: "u-1", thread_id: "t-1", role: "user", parts: [{ id: "p-u", ordinal: 0, kind: "text", text: "My exact words" }] },
    { id: "a-1", thread_id: "t-1", parent_id: "u-1", role: "assistant", streaming: 1, parts: [{ id: "p-a", ordinal: 0, kind: "text", text: "Saved answer" }] },
  ],
};

beforeEach(async () => {
  vi.resetAllMocks();
  useThreadStore.setState({ threads: {}, buffers: {}, loading: {}, toolRows: {}, draftAnnotations: {} });
  vi.mocked(apiFetch).mockResolvedValueOnce(empty);
  await useThreadStore.getState().loadThread("t-1");
  // Follow-up reconciliation is deliberately delayed unless a test supplies it.
  vi.mocked(apiFetch).mockImplementation(() => new Promise(() => {}));
});

describe("visible Thread submission", () => {
  it("shows the prompt before HTTP acknowledgement and creates the answer without a socket frame", async () => {
    const post = deferred<TurnResult>();
    vi.mocked(apiFetch).mockReturnValueOnce(post.promise);
    const pending = useThreadStore.getState().submitTurn("t-1", { text: "My exact words" });
    const local = useThreadStore.getState().threads["t-1"].messages;
    expect(local).toHaveLength(1);
    expect(local[0]).toMatchObject({ role: "user", pending: true, parts: [{ text: "My exact words" }] });
    post.resolve(ack);
    await pending;
    expect(useThreadStore.getState().threads["t-1"].messages.map((m) => m.id)).toEqual(["u-1", "a-1"]);
    expect(useThreadStore.getState().threads["t-1"].messages[0].pending).toBe(false);
    expect(useThreadStore.getState().threads["t-1"].messages[1]).toMatchObject({ streaming: true, parentId: "u-1" });
  });

  it("reconciles socket frames arriving before HTTP without duplicating rows or losing text", async () => {
    const post = deferred<TurnResult>();
    vi.mocked(apiFetch).mockReturnValueOnce(post.promise);
    const pending = useThreadStore.getState().submitTurn("t-1", { text: "My exact words" });
    useThreadStore.getState().applyTurnStarted(start);
    useThreadStore.getState().applyDelta({ thread_id: "t-1", message_id: "a-1", ordinal: 0, kind: "text", text: "Live answer", seq: 0 });
    post.resolve(ack);
    await pending;
    expect(useThreadStore.getState().threads["t-1"].messages.map((m) => m.id)).toEqual(["u-1", "a-1"]);
    expect(useThreadStore.getState().getBufferText("a-1")).toBe("Live answer");
  });

  it("does not let a GET started before Send erase the accepted turn", async () => {
    const stale = deferred<typeof empty>();
    vi.mocked(apiFetch).mockReturnValueOnce(stale.promise).mockResolvedValueOnce(ack);
    const oldLoad = useThreadStore.getState().loadThread("t-1");
    await useThreadStore.getState().submitTurn("t-1", { text: "My exact words" });
    stale.resolve(empty);
    await oldLoad;
    expect(useThreadStore.getState().threads["t-1"].messages.map((m) => m.id)).toEqual(["u-1", "a-1"]);
  });

  it("preserves an unacknowledged prompt through refresh and deduplicates once acknowledged", async () => {
    const post = deferred<TurnResult>();
    vi.mocked(apiFetch).mockReturnValueOnce(post.promise).mockResolvedValueOnce(empty).mockResolvedValueOnce(snapshot);
    const pending = useThreadStore.getState().submitTurn("t-1", { text: "My exact words" });
    await useThreadStore.getState().loadThread("t-1");
    expect(useThreadStore.getState().threads["t-1"].messages[0]).toMatchObject({ pending: true, parts: [{ text: "My exact words" }] });
    await useThreadStore.getState().loadThread("t-1");
    post.resolve(ack);
    await pending;
    expect(useThreadStore.getState().threads["t-1"].messages.map((m) => m.id)).toEqual(["u-1", "a-1"]);
    expect(useThreadStore.getState().threads["t-1"].messages[1].parts[0].text).toBe("Saved answer");
  });

  it("removes an unconfirmed echo on failure so the composer can retain the unsent draft", async () => {
    vi.mocked(apiFetch).mockRejectedValueOnce(new Error("Offline"));
    await expect(useThreadStore.getState().submitTurn("t-1", { text: "My exact words" })).rejects.toThrow("Offline");
    expect(useThreadStore.getState().threads["t-1"].messages).toEqual([]);
  });

  it("accepts a late start frame for a saved streaming row and retains its text at completion", async () => {
    vi.mocked(apiFetch).mockResolvedValueOnce(snapshot);
    await useThreadStore.getState().loadThread("t-1");
    useThreadStore.getState().applyTurnStarted(start);
    expect(useThreadStore.getState().applyDelta({ thread_id: "t-1", message_id: "a-1", ordinal: 0, kind: "text", text: " tail only", seq: 4 })).toBe(true);
    useThreadStore.getState().applyTurnDone({ thread_id: "t-1", message_id: "a-1", outcome: "succeeded", receipt_id: "r-1", egress: null, stats: null });
    const messages = useThreadStore.getState().threads["t-1"].messages;
    expect(messages).toHaveLength(2);
    expect(messages[1]).toMatchObject({ streaming: false, parts: [{ text: "Saved answer" }] });
  });
});
