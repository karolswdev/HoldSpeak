import { afterEach, expect, it, vi } from "vitest";
import { cancelRowLayout, scheduleRowLayout } from "./rowLayout";
afterEach(() => vi.unstubAllGlobals());
it("reads every queued seat before writing and does no work while idle", () => {
  let frame: FrameRequestCallback | undefined;
  const request = vi.fn((callback: FrameRequestCallback) => { frame = callback; return 1; });
  vi.stubGlobal("requestAnimationFrame", request);
  const work: string[] = [];
  const first = () => { work.push("read first"); return () => work.push("write first"); };
  const second = () => { work.push("read second"); return () => work.push("write second"); };
  scheduleRowLayout(first); scheduleRowLayout(first); scheduleRowLayout(second);
  expect(request).toHaveBeenCalledOnce();
  frame!(0);
  expect(work).toEqual(["read first", "read second", "write first", "write second"]);
  expect(request).toHaveBeenCalledOnce();
});
it("cancels a removed list without cancelling another list's frame", () => {
  let frame: FrameRequestCallback | undefined;
  vi.stubGlobal("requestAnimationFrame", (callback: FrameRequestCallback) => { frame = callback; return 2; });
  const cancel = vi.fn(); vi.stubGlobal("cancelAnimationFrame", cancel);
  const removed = vi.fn(), retained = vi.fn();
  scheduleRowLayout(removed); scheduleRowLayout(retained); cancelRowLayout(removed);
  expect(cancel).not.toHaveBeenCalled(); frame!(0);
  expect(removed).not.toHaveBeenCalled(); expect(retained).toHaveBeenCalledOnce();
});
