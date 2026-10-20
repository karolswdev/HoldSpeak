// ShortcutSheet — keyboard overlay portal.
// Extracted from DeskWindow.tsx (HS-117-04).
import { useEffect } from "react";
import { createPortal } from "react-dom";
import { VERBS, verbLabel } from "../../verbRegistry";
import { useSettleState } from "../../settleState";

/** HS-101 B8 — the shortcut sheet, drawn (never a doc link).
 * HS-111-07 — rows DERIVE from the registry's key fields (doctrine
 * P11): the hand-maintained list is gone; a verb that gains a key
 * appears here for free. Esc is grammar, not a verb; it stays a
 * fixed convention line. */
const SHEET_GROUPS: { title: string; include: (id: string, scope: string, menu?: string, group?: string) => boolean }[] = [
  { title: "Apps", include: (_id, scope) => scope === "go" },
  { title: "New", include: (_id, _scope, menu, group) => menu === "desk" && group === "new" },
  { title: "Windows", include: (_id, scope, menu) => scope === "window" || menu === "window" },
  { title: "Desk", include: (_id, scope, menu, group) =>
    scope !== "go" && !(menu === "desk" && group === "new") && scope !== "window" && menu !== "window" },
];

export function ShortcutSheet({ onClose }: { onClose: () => void }) {
  const settled = useSettleState((state) => state.settled);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);
  const ctx = { selectedRef: null };
  const rows: [string, [string, string][]][] = SHEET_GROUPS.map((group) => {
    const keys = VERBS.filter(
      (v) => v.key && group.include(v.id, v.scope, v.menu, v.group),
    ).map((v): [string, string] => [v.key as string, verbLabel(v, ctx)]);
    // The applications read in Cmd+1..Cmd+4 order, whatever the registry's
    // program-table order is.
    if (group.title === "Apps")
      keys.sort((a, b) => a[0].localeCompare(b[0]));
    return [group.title, keys];
  });
  rows[2][1].push([
    "Esc",
    settled ? "Back to Desk (keep work open)" : "Close / cancel",
  ]);
  return createPortal(
    <div
      className="desk-shortcut-sheet"
      role="group"
      aria-label="Keyboard shortcuts"
      onPointerDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="desk-shortcut-panel">
        {rows.map(([group, keys]) => (
          <section key={group}>
            <h4>{group}</h4>
            {keys.map(([cap, what]) => (
              <div className="desk-shortcut-row" key={cap}>
                <kbd>{cap}</kbd>
                <span>{what}</span>
              </div>
            ))}
          </section>
        ))}
      </div>
    </div>,
    document.body,
  );
}
