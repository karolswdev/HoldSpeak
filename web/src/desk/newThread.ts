/* New Thread — the thread window opens at once.
 *
 * Every door made the thread, asked the store to open `thread:<id>`, and
 * then started a desk read. The window is drawn from the store's object,
 * and the store did not hold the thread until that read ended (2 to 5 s on
 * a desk with a roadmap): the press showed nothing and the thread was made
 * unseen. The create answer carries the whole thread, so the store takes it
 * first and the window opens with no wait. */
import { useDesk } from "./store";
import { createThread, type ThreadWire } from "./threads";

export async function openNewThread(
  opts: Parameters<typeof createThread>[0] = {},
): Promise<ThreadWire> {
  const thread = await createThread(opts);
  const desk = useDesk.getState();
  desk.adoptCreated("thread", thread);
  desk.openPullout(`thread:${thread.id}`);
  void desk.refresh();
  return thread;
}
