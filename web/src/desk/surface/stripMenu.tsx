/* PHILO-13-11 (C1, §3a) — strips of choices: nothing clips, nothing scrolls
 * sideways (HS-200-12 stands).
 *
 * At the phone width a strip of choices that does not fit its row (window
 * wings, FilterTokens) becomes ONE library menu Button that shows the
 * current choice and ▾. It opens the existing DeskMenu species (WorkMenu)
 * with every choice and a check on the current one; a window's gear door
 * joins after a separator. A strip that fits stays a strip.
 *
 * "Does not fit" is MEASURED (useStripFit), never a fixed count: the strip
 * renders, and if one row cannot hold it (its content runs past its box, or
 * its choices wrap to a second line) it folds. A folded strip unfolds when
 * its row grows wide enough for the width it measured. Where nothing can be
 * measured (jsdom, a zero box) the strip stays a strip.
 */
import { useLayoutEffect, useRef, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { WorkMenu, type WorkMenuEntry } from "../components/DeskMenu";

/** Measures whether the strip in `ref` fits one row. `enabled` false (the
 * desktop width) always reports a fit. `key` re-measures when the choices
 * change. */
export function useStripFit<T extends HTMLElement>(enabled: boolean, key: string) {
  const ref = useRef<T | null>(null);
  const [fits, setFits] = useState(true);
  const natural = useRef(0);
  useLayoutEffect(() => {
    if (!enabled) {
      if (!fits) setFits(true);
      return;
    }
    const el = ref.current;
    if (!el) return;
    const measure = () => {
      const box = el.clientWidth;
      if (!box) return;
      if (fits) {
        const kids = Array.from(el.children) as HTMLElement[];
        const top = kids[0]?.offsetTop ?? 0;
        const wrapped = kids.some((k) => k.offsetTop > top + 2);
        const wide = el.scrollWidth > box + 1;
        if (wrapped || wide) {
          natural.current = Math.max(
            el.scrollWidth,
            kids.reduce((sum, k) => sum + k.getBoundingClientRect().width, 0),
          );
          setFits(false);
        }
      } else if (box >= natural.current + 1) {
        setFits(true);
      }
    };
    measure();
    if (typeof ResizeObserver !== "function") return;
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, [enabled, fits, key]);
  return { ref, fits };
}

export type StripChoice = { value: string; label: string };

/** The folded strip: ONE library Button (the current choice + ▾) that
 * opens the DeskMenu species. */
export function StripMenuButton({
  label,
  choices,
  value,
  onChange,
  door,
  doorOpen,
  onDoor,
  variant,
  className,
  disabled,
}: {
  /** The strip's accessible name ("Window faces", "Ranking"). */
  label: string;
  choices: StripChoice[];
  value: string;
  onChange(next: string): void;
  door?: string;
  doorOpen?: boolean;
  onDoor?: () => void;
  variant: "chrome" | "secondary";
  className?: string;
  /** The library Button's disabled state (FilterTokens' `disabled`). */
  disabled?: boolean;
}) {
  const [at, setAt] = useState<{ x: number; y: number; keys: boolean } | null>(null);
  const buttonRef = useRef<HTMLButtonElement | null>(null);
  const current = choices.find((c) => c.value === value);
  const shown =
    doorOpen && door ? door : (current?.label ?? choices[0]?.label ?? "");
  const entries: WorkMenuEntry[] = choices.map((c) => ({
    type: "item" as const,
    id: `strip-${c.value || "all"}`,
    label: c.label,
    checked: !doorOpen && c.value === value,
    onSelect: () => onChange(c.value),
  }));
  if (door && onDoor)
    entries.push(
      { type: "sep", id: "strip-sep" },
      {
        type: "item",
        id: "strip-door",
        label: door,
        checked: Boolean(doorOpen),
        onSelect: () => onDoor(),
      },
    );
  return (
    <>
      <Button
        ref={buttonRef}
        variant={variant}
        dense={variant !== "chrome"}
        className={["surface-strip-menu", className].filter(Boolean).join(" ")}
        aria-haspopup="menu"
        aria-expanded={Boolean(at)}
        aria-label={`${label}: ${shown}`}
        data-testid="surface-strip-menu"
        disabled={disabled}
        onClick={(e) => {
          const r = e.currentTarget.getBoundingClientRect();
          // A keyboard press (Enter/Space: a click with no pointer) puts focus
          // on the first row, so the arrows walk the choices at once.
          setAt(at ? null : { x: r.left, y: r.bottom, keys: e.detail === 0 });
        }}
        // PHILO-13-18: a pointer open leaves focus here, so Escape reaches this
        // Button first. It closes the menu and stops: the window does not close.
        onKeyDown={(e) => {
          if (e.key === "Escape" && at) { e.preventDefault(); e.stopPropagation(); setAt(null); }
        }}
      >
        {shown} ▾
      </Button>
      {at ? (
        <WorkMenu
          className="desk-head-menu"
          label={label}
          x={at.x}
          y={at.y}
          entries={entries}
          autoFocus={at.keys}
          returnFocus={() => buttonRef.current?.focus()}
          onClose={() => setAt(null)}
        />
      ) : null}
    </>
  );
}
