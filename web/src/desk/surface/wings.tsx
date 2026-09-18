// HS-100-07 — wings: an application window's few faces, in the HEAD.
//
// The thesis's posture rule (APPLICATION_LAYER_THESIS.md §2): an
// application opens on its headline, carries at most two more wings as
// segments in the window head, and folds configuration behind one gear
// door. No tab walls inside window bodies.
//
// The core owns which wing is active; the window frame owns the head.
// `useWindowWings` bridges them: the core publishes its wing bar into
// the head slot the SurfaceWindows host provides.
import {
  createContext,
  useContext,
  useLayoutEffect,
  useRef,
  type ReactNode,
} from "react";

export interface WingSpec {
  id: string;
  label: string;
}

export const WingSlotContext = createContext<
  ((node: ReactNode) => void) | null
>(null);

/** Publish a wing bar into the hosting window's head. Pass null to
 * clear. `deps` gates republishing (typically [active]).
 *
 * HS-200-42: this is a LAYOUT effect, and that is the whole point. The
 * strip lives in the window HEAD (`SurfaceWindows` holds it in `useState`)
 * while the body it labels lives in the core, so a wing change is two
 * commits: one paints the new body, the effect then schedules a second that
 * repaints the head. With a passive `useEffect` the browser paints in
 * between, and the head shows the OLD wing selected over the NEW body --
 * a strip that disagrees with the thing it names. Measured at up to 600ms
 * on a loaded machine at 393 (the Speak loop's `Review` verb crosses to the
 * Journal wing; `tests/e2e/test_hs176_loop_glass.py:324` reads the strip the
 * instant the body arrives). `useLayoutEffect` runs before paint and React
 * flushes the resulting head update synchronously, so head and body land in
 * the SAME paint at every width. The desk is client-only; there is no SSR
 * pass for this to warn in.
 */
export function useWindowWings(node: ReactNode, deps: unknown[]) {
  const setSlot = useContext(WingSlotContext);
  useLayoutEffect(() => {
    if (!setSlot) return;
    setSlot(node);
    return () => setSlot(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [setSlot, ...deps]);
}

/** The segmented wing control + the one configuration door (gear). */
export function SurfaceWings({
  wings,
  active,
  onChange,
  door,
  doorOpen,
  onDoor,
}: {
  wings: WingSpec[];
  active: string;
  onChange: (id: string) => void;
  /** Label for the configuration door; omit for doorless windows. */
  door?: string;
  doorOpen?: boolean;
  onDoor?: () => void;
}) {
  // HS-111-08 — the tablist walks with arrows (roving tabindex, the
  // same grammar the in-body Tabs species carried before it retired).
  const refs = useRef<Array<HTMLButtonElement | null>>([]);
  const move = (to: number) => {
    const index = (to + wings.length) % wings.length;
    onChange(wings[index].id);
    refs.current[index]?.focus();
  };
  // When no wing is active (the door face rules), the first wing keeps
  // the Tab stop so the strip stays reachable.
  const hasActive = wings.some((w) => w.id === active);
  return (
    <span className="desk-wings">
      {/* The tablist wraps ONLY the tabs — the gear door is a pressed
          gadget, not a tab (aria-required-children). display:contents
          keeps the strip one flex row. */}
      <span
        className="desk-wings-tabs"
        role="tablist"
        aria-label="Window faces"
      >
      {wings.map((w, index) => (
        <button
          key={w.id}
          ref={(element) => {
            refs.current[index] = element;
          }}
          type="button"
          role="tab"
          aria-selected={active === w.id}
          tabIndex={active === w.id || (!hasActive && index === 0) ? 0 : -1}
          className={`desk-wing${active === w.id ? " is-on" : ""}`}
          onClick={() => onChange(w.id)}
          onKeyDown={(event) => {
            if (event.key === "ArrowRight") {
              event.preventDefault();
              move(index + 1);
            } else if (event.key === "ArrowLeft") {
              event.preventDefault();
              move(index - 1);
            } else if (event.key === "Home") {
              event.preventDefault();
              move(0);
            } else if (event.key === "End") {
              event.preventDefault();
              move(wings.length - 1);
            }
          }}
        >
          {w.label}
        </button>
      ))}
      </span>
      {door ? (
        <button
          type="button"
          className={`desk-wing desk-wing-door${doorOpen ? " is-on" : ""}`}
          aria-label={door}
          title={door}
          aria-pressed={doorOpen}
          onClick={onDoor}
        >
          <span aria-hidden="true">⚙︎</span>
        </button>
      ) : null}
    </span>
  );
}
