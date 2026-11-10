import { useLayoutEffect, useState, type RefObject } from "react";

/** A single row carries its own name. Count rendered rows so fragments,
 * conditional rows and composed row components follow the same rule. */
export function useGroupHeading(ref: RefObject<HTMLElement | null>, label?: string) {
  const [single, setSingle] = useState(false);
  useLayoutEffect(() => {
    const group = ref.current;
    if (!group || !label) return;
    const update = () => {
      const rows = [...group.querySelectorAll(".gadget-row, .object-list-row")]
        .filter((row) => row.closest(".gadget-group, .surface-pane-group") === group);
      setSingle(rows.length === 1);
    };
    update();
    const observer = new MutationObserver(update);
    observer.observe(group, { childList: true, subtree: true });
    return () => observer.disconnect();
  }, [ref, label]);
  return Boolean(label) && !single;
}
