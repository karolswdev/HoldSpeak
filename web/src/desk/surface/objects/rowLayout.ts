/** List seats and row wells share one frame: read all geometry, then write.
 * No frame runs while idle. A callback can request a later measurement. */
type ReadLayout = () => void | (() => void);
const pending = new Set<ReadLayout>();
let frame = 0;
export function scheduleRowLayout(read: ReadLayout) {
  pending.add(read);
  if (frame) return;
  frame = requestAnimationFrame(() => {
    frame = 0;
    const reads = [...pending];
    pending.clear();
    const writes = reads.map(read => read());
    for (const write of writes) write?.();
  });
}
export function cancelRowLayout(read: ReadLayout) {
  pending.delete(read);
  if (!pending.size && frame) { cancelAnimationFrame(frame); frame = 0; }
}
