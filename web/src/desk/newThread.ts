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

/** One press, one thread: the creates in flight, by what was asked. */
const inFlight = new Map<string, Promise<ThreadWire>>();
/** The thread each ask made last, while its window is new. */
const fresh = new Map<string, { thread: ThreadWire; at: number }>();
const NEW_BEAT_MS = 4500;

async function make(key: string, opts: Parameters<typeof createThread>[0]): Promise<ThreadWire> {
  const thread = await createThread(opts);
  const desk = useDesk.getState();
  desk.adoptCreated("thread", thread);
  desk.openPullout(`thread:${thread.id}`);
  fresh.set(key, { thread, at: Date.now() });
  void desk.refresh();
  return thread;
}

/** A second press of the same ask while its create is in flight, or while
 * the window it just opened is still new and open, makes nothing: it puts
 * that window in front. Before, two quick presses made two threads. */
export function openNewThread(
  opts: Parameters<typeof createThread>[0] = {},
): Promise<ThreadWire> {
  const key = JSON.stringify(opts);
  const last = fresh.get(key);
  const desk = useDesk.getState();
  if (
    last &&
    Date.now() - last.at < NEW_BEAT_MS &&
    desk.pullouts.some((p) => p.id === `thread:${last.thread.id}`)
  ) {
    desk.openPullout(`thread:${last.thread.id}`);
    return Promise.resolve(last.thread);
  }
  const flying = inFlight.get(key);
  if (flying) return flying;
  const run = make(key, opts).finally(() => inFlight.delete(key));
  inFlight.set(key, run);
  return run;
}
