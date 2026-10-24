import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../../../lib/api";
import { OwnerAliasField } from "../OwnerAliasField";
import { useOwnerName, type OwnerNameAdapter, type OwnerSetting } from "../ownerName";

let owner: ReturnType<typeof useOwnerName>;
function Probe({ adapter, aliasDraft }: { adapter: OwnerNameAdapter; aliasDraft?: (dirty: boolean) => void }) {
  owner = useOwnerName(adapter);
  return aliasDraft ? <OwnerAliasField owner={owner} onDraftChange={aliasDraft} mic={false} /> : null;
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: unknown) => void;
  const promise = new Promise<T>((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}

type WriteResult = Awaited<ReturnType<OwnerNameAdapter["write"]>>;
const result = (owner: OwnerSetting, revision: string): WriteResult => ({ settings: { owner, _revision: revision } });
const initial: OwnerSetting = { name: "Karl", aliases: ["K"] };
const read = () => Promise.resolve({ owner: initial, _revision: "r1" });

afterEach(() => { cleanup(); vi.unstubAllGlobals(); vi.useRealTimers(); });

describe("Settings You field receipts", () => {
  it("shows Edited during debounce, Saving only for the captured value, and Saved only after its ACK", async () => {
    const first = deferred<WriteResult>();
    const second = deferred<WriteResult>();
    const write = vi.fn().mockReturnValueOnce(first.promise).mockReturnValueOnce(second.promise);
    const adapter: OwnerNameAdapter = { read, write };
    render(<Probe adapter={adapter} />);
    await act(async () => { await Promise.resolve(); });
    expect(owner.fieldStatus("name")).toBe("Saved");
    expect(owner.fieldStatus("aliases")).toBe("Saved");

    act(() => owner.setName("One"));
    expect(owner.fieldStatus("name")).toBe("Edited");
    expect(write).not.toHaveBeenCalled();
    act(() => { void owner.flush(); });
    expect(owner.fieldStatus("name")).toBe("Saving");
    expect(write).toHaveBeenCalledWith({ name: "One", aliases: ["K"] }, "r1");

    act(() => owner.setName("Two"));
    expect(owner.fieldStatus("name")).toBe("Edited");
    await act(async () => { first.resolve(result({ name: "One", aliases: ["K"] }, "r2")); await first.promise; });
    expect(owner.name).toBe("Two");
    expect(owner.fieldStatus("name")).toBe("Edited");
    act(() => { void owner.flush(); });
    expect(owner.fieldStatus("name")).toBe("Saving");
    expect(write).toHaveBeenLastCalledWith({ name: "Two", aliases: ["K"] }, "r2");
    await act(async () => { second.resolve(result({ name: "Two", aliases: ["K"] }, "r3")); await second.promise; });
    expect(owner.fieldStatus("name")).toBe("Saved");
  });

  it("keeps the current field Not saved after refusal and retries with the newest revision", async () => {
    const writes: Array<{ owner: OwnerSetting; revision?: string }> = [];
    let attempt = 0;
    const adapter: OwnerNameAdapter = {
      read,
      write: async (next, revision) => {
        writes.push({ owner: next, revision });
        attempt += 1;
        if (attempt === 1) throw new ApiError(409, "Conflict", { revision: "r2" });
        if (attempt === 2) throw new ApiError(409, "Conflict", { revision: "r3" });
        return result(next, "r4");
      },
    };
    render(<Probe adapter={adapter} />);
    await act(async () => { await Promise.resolve(); });
    act(() => owner.setName("Karol"));
    await act(async () => { await owner.flush(); });
    expect(writes.map(({ revision }) => revision)).toEqual(["r1", "r2"]);
    expect(owner.name).toBe("Karol");
    expect(owner.fieldStatus("name")).toBe("Not saved");
    expect(owner.fieldStatus("aliases")).toBe("Saved");
    act(() => owner.setName("Karol S"));
    expect(owner.fieldStatus("name")).toBe("Edited");
    await act(async () => { await owner.flush(); });
    expect(writes[2]).toEqual({ owner: { name: "Karol S", aliases: ["K"] }, revision: "r3" });
    expect(owner.fieldStatus("name")).toBe("Saved");
  });

  it("uses only its injected adapter and observes a keepalive ACK", async () => {
    const fetch = vi.fn();
    vi.stubGlobal("fetch", fetch);
    const writes: Array<{ owner: OwnerSetting; revision?: string; keepalive?: boolean }> = [];
    const adapter: OwnerNameAdapter = {
      read,
      write: async (next, revision, options) => {
        writes.push({ owner: next, revision, keepalive: options?.keepalive });
        return result(next, "r2");
      },
    };
    render(<Probe adapter={adapter} />);
    await act(async () => { await Promise.resolve(); });
    act(() => owner.addAliases("Carol"));
    expect(owner.fieldStatus("aliases")).toBe("Edited");
    await act(async () => { window.dispatchEvent(new Event("pagehide")); await Promise.resolve(); });
    expect(writes).toEqual([{ owner: { name: "Karl", aliases: ["K", "Carol"] }, revision: undefined, keepalive: true }]);
    expect(owner.fieldStatus("aliases")).toBe("Saved");
    expect(fetch).not.toHaveBeenCalled();
  });

  it("keeps the later keepalive ACK when a guarded older response resolves last", async () => {
    const oldResponse = deferred<WriteResult>();
    const writes: Array<{ owner: OwnerSetting; revision?: string; keepalive?: boolean }> = [];
    let reads = 0;
    const adapter: OwnerNameAdapter = {
      read: async () => { reads += 1; return { owner: initial, _revision: "r1" }; },
      write: (next, revision, options) => {
        writes.push({ owner: next, revision, keepalive: options?.keepalive });
        if (writes.length === 1) return oldResponse.promise;
        return Promise.resolve(result(next, "r3"));
      },
    };
    render(<Probe adapter={adapter} />);
    await act(async () => { await Promise.resolve(); });
    act(() => owner.setName("A"));
    act(() => { void owner.flush(); });
    act(() => owner.setName("B"));
    await act(async () => { window.dispatchEvent(new Event("pagehide")); await Promise.resolve(); });
    expect(owner.fieldStatus("name")).toBe("Saved");
    await act(async () => { oldResponse.resolve(result({ name: "A", aliases: ["K"] }, "r2")); await oldResponse.promise; });
    expect(owner.name).toBe("B");
    expect(owner.fieldStatus("name")).toBe("Saved");
    expect(reads).toBe(1); // A used a revision, so it could not apply after B.
    act(() => owner.setName("C"));
    await act(async () => { await owner.flush(); });
    expect(writes[2].revision).toBe("r3");
  });

  it("ignores a late stale 409 from the earlier write after keepalive has advanced the revision", async () => {
    const oldResponse = deferred<WriteResult>();
    const revisions: Array<string | undefined> = [];
    const adapter: OwnerNameAdapter = {
      read,
      write: (next, revision) => {
        revisions.push(revision);
        return revisions.length === 1 ? oldResponse.promise : Promise.resolve(result(next, "r3"));
      },
    };
    render(<Probe adapter={adapter} />);
    await act(async () => { await Promise.resolve(); });
    act(() => owner.setName("A"));
    act(() => { void owner.flush(); });
    act(() => owner.setName("B"));
    await act(async () => { window.dispatchEvent(new Event("pagehide")); await Promise.resolve(); });
    await act(async () => {
      oldResponse.reject(new ApiError(409, "Conflict", { revision: "r2" }));
      await oldResponse.promise.catch(() => undefined);
    });
    expect(owner.fieldStatus("name")).toBe("Saved");
    act(() => owner.setName("C"));
    await act(async () => { await owner.flush(); });
    expect(revisions).toEqual(["r1", undefined, "r3"]);
  });

  it("reads back two revisionless keepalives applied in reverse order before claiming Saved", async () => {
    const oldResponse = deferred<WriteResult>();
    const readback = deferred<{ owner?: Partial<OwnerSetting>; _revision?: string }>();
    let remote: OwnerSetting = initial;
    let writes = 0;
    const adapter: OwnerNameAdapter = {
      read: vi.fn().mockResolvedValueOnce({ owner: initial }).mockImplementationOnce(() => readback.promise),
      write: (next) => {
        writes += 1;
        if (writes === 1) return oldResponse.promise;
        remote = next;
        return Promise.resolve(result(next, `r${writes}`));
      },
    };
    render(<Probe adapter={adapter} />);
    await act(async () => { await Promise.resolve(); });
    act(() => owner.setName("A"));
    await act(async () => { window.dispatchEvent(new Event("pagehide")); await Promise.resolve(); });
    act(() => owner.setName("B"));
    await act(async () => { window.dispatchEvent(new Event("pagehide")); await Promise.resolve(); });
    expect(remote.name).toBe("B");
    expect(owner.fieldStatus("name")).toBe("Not saved"); // A may still apply after B.
    remote = { name: "A", aliases: ["K"] }; // older unguarded PUT reaches the hub last
    await act(async () => { oldResponse.resolve(result(remote, "r3")); await oldResponse.promise; });
    expect(owner.fieldStatus("name")).toBe("Not saved");
    await act(async () => { readback.resolve({ owner: remote, _revision: "r3" }); await readback.promise; });
    expect(owner.name).toBe("B");
    expect(owner.fieldStatus("name")).toBe("Not saved");
    await act(async () => { await owner.flush(); });
    expect(remote.name).toBe("B");
    expect(owner.fieldStatus("name")).toBe("Saved");
  });
});

describe("Also called composition", () => {
  it("retains an IME comma and composition Enter, then accepts a deliberate later Enter", async () => {
    const draft = vi.fn();
    const write = vi.fn(async (next: OwnerSetting) => result(next, "r2"));
    const adapter: OwnerNameAdapter = { read, write };
    render(<Probe adapter={adapter} aliasDraft={draft} />);
    await act(async () => { await Promise.resolve(); });
    const input = screen.getByRole("textbox", { name: "Also called" });
    fireEvent.compositionStart(input);
    fireEvent.change(input, { target: { value: "あ," } });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(owner.aliases).toEqual(["K"]);
    fireEvent.compositionEnd(input);
    fireEvent.change(input, { target: { value: "あ," } });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(owner.aliases).toEqual(["K"]);
    expect(draft).toHaveBeenCalledWith(true);
    await act(async () => { await Promise.resolve(); });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(owner.aliases).toEqual(["K", "あ"]);
    expect(draft).toHaveBeenLastCalledWith(false);
    expect(write).not.toHaveBeenCalled();
  });

  it("flushes an unfinished alias draft on section unmount", async () => {
    const writes: Array<{ owner: OwnerSetting; keepalive?: boolean }> = [];
    const adapter: OwnerNameAdapter = {
      read,
      write: async (next, _revision, options) => {
        writes.push({ owner: next, keepalive: options?.keepalive });
        return result(next, "r2");
      },
    };
    const view = render(<Probe adapter={adapter} aliasDraft={vi.fn()} />);
    await act(async () => { await Promise.resolve(); });
    await userEvent.type(screen.getByRole("textbox", { name: "Also called" }), "Carol");
    expect(owner.aliases).toEqual(["K"]);
    view.unmount();
    await act(async () => { await Promise.resolve(); });
    expect(writes).toEqual([{ owner: { name: "Karl", aliases: ["K", "Carol"] }, keepalive: true }]);
  });

  it("clears the raw draft indicator when pagehide commits it in the mounted section", async () => {
    const draft = vi.fn();
    const adapter: OwnerNameAdapter = { read, write: async (next) => result(next, "r2") };
    render(<Probe adapter={adapter} aliasDraft={draft} />);
    await act(async () => { await Promise.resolve(); });
    fireEvent.change(screen.getByRole("textbox", { name: "Also called" }), { target: { value: "Carol" } });
    expect(draft).toHaveBeenLastCalledWith(true);
    await act(async () => { window.dispatchEvent(new Event("pagehide")); await Promise.resolve(); });
    expect(owner.aliases).toEqual(["K", "Carol"]);
    expect(owner.aliasDraft).toBe("");
    expect(draft).toHaveBeenLastCalledWith(false);
  });
});
