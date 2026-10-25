/* Window grammar 2026-10-24 (docs/internal/betterment/native-experience/
 * WINDOW-GRAMMAR-2026-10-24.md): the native preference window.
 *
 *   rail (32 px rows, glyph + label, selection blue) | pane (label/control grid)
 *   status bar (24 px, sans 12 muted: the save state, then the facts)
 *
 * Settings and the Components Forms specimen compose these three pieces; the
 * specimen supplies a fixture writer, Settings the production one. At a
 * content width of 520 px or less the rail is the first view and a pane opens
 * with a Back verb. `PrefStatus` composes the kit `StatusBar`: the one status
 * bar in the product. */
import { useEffect, useRef, useState, type KeyboardEvent, type ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import { StatusBar, type StatusBarItem } from "../../desk/surface/kit";
import { FootSlotContext } from "../../desk/surface/foot";
import { useHasWindowBack, useWindowBack } from "../../desk/surface/back";
import { useWindowTitle } from "../../desk/surface/title";
import { useCompactViewport } from "../../desk/useCompactViewport";
import "./settingsWindow.css";

export type PrefRailItem = {
  id: string;
  label: string;
  glyph?: ReactNode;
  disabled?: boolean;
};

export function PrefWindow({
  items,
  selected,
  onSelect,
  paneOpen,
  onBack,
  label = "Settings sections",
  testId,
  railTestIdPrefix = "settings-index-",
  frameBack = false,
  children,
}: {
  items: readonly PrefRailItem[];
  selected: string;
  onSelect: (id: string) => void;
  /** Narrow only: true shows the pane with Back, false the rail. */
  paneOpen: boolean;
  onBack: () => void;
  label?: string;
  testId?: string;
  railTestIdPrefix?: string;
  /** The hosting window's compact title-bar Back returns the pane to the
   *  rail; the pane then draws no Back of its own at a compact viewport. */
  frameBack?: boolean;
  children: ReactNode;
}) {
  const railRef = useRef<HTMLElement>(null);
  const compact = useCompactViewport();
  const hosted = useHasWindowBack();
  const viaFrame = frameBack && hosted && compact;
  useWindowBack(
    frameBack && paneOpen ? { onBack, testId: "settings-back" } : null,
    [frameBack, paneOpen],
  );
  const onKeyDown = (event: KeyboardEvent<HTMLElement>) => {
    if (event.key !== "ArrowDown" && event.key !== "ArrowUp" && event.key !== "Home" && event.key !== "End") return;
    const rows = Array.from(railRef.current?.querySelectorAll<HTMLButtonElement>(".pref-rail-row:not(:disabled)") ?? []);
    if (!rows.length) return;
    const at = rows.indexOf(document.activeElement as HTMLButtonElement);
    const next = event.key === "Home" ? 0
      : event.key === "End" ? rows.length - 1
        : event.key === "ArrowDown" ? Math.min(rows.length - 1, at + 1)
          : Math.max(0, at < 0 ? 0 : at - 1);
    event.preventDefault();
    rows[next].focus();
    rows[next].click();
  };
  const current = items.find((item) => item.id === selected);
  return (
    <div className="settings-page pref-window" data-testid={testId} data-pane-open={paneOpen || undefined}>
      {frameBack ? <PaneTitle label={viaFrame && paneOpen && current ? current.label : null} /> : null}
      <nav ref={railRef} className="settings-page-index pref-rail" aria-label={label} onKeyDown={onKeyDown}>
        {items.map((item) => {
          const active = item.id === selected;
          return (
            <Button
              key={item.id}
              variant="ghost"
              dense
              className={`pref-rail-row${active ? " is-active" : ""}`}
              aria-current={active ? "location" : undefined}
              aria-pressed={active}
              disabled={item.disabled}
              tabIndex={active ? 0 : -1}
              onClick={() => onSelect(item.id)}
              data-testid={`${railTestIdPrefix}${item.id}`}
            >
              {item.glyph ? <span className="pref-rail-glyph" aria-hidden="true">{item.glyph}</span> : null}
              <span className="pref-rail-label">{item.label}</span>
              <span className="pref-rail-chevron" aria-hidden="true">›</span>
            </Button>
          );
        })}
      </nav>
      <div className="settings-page-sections pref-pane">
        {/* A narrow window off the phone (or a specimen) keeps its own Back;
            on the phone the window's title-bar Back is the one Back. */}
        {viaFrame ? null : (
          <div className="pref-pane-back">
            <Button variant="ghost" dense onClick={onBack} data-testid="settings-back">
              <span aria-hidden="true">‹</span> Settings
            </Button>
            {current ? <span className="pref-pane-back-name">{current.label}</span> : null}
          </div>
        )}
        {children}
      </div>
    </div>
  );
}

/** On the phone the title bar names the open pane (‹ Back · Speak), as a
 *  native settings list does; the rail view keeps the window's name. Only a
 *  window that owns the frame's Back publishes it. */
function PaneTitle({ label }: { label: string | null }) {
  useWindowTitle(label, [label]);
  return null;
}

/** A pane section: a sans 12/600 sentence-case caption over a hairline. */
export function PrefSection({ id, label, hidden, quiet, children }: {
  id: string;
  label: string;
  hidden?: boolean;
  /** The caption is said by the first group inside (You, Agents). */
  quiet?: boolean;
  children: ReactNode;
}) {
  return (
    <section
      id={`settings-section-${id}`}
      data-settings-section={id}
      className="settings-page-section"
      hidden={hidden}
      aria-hidden={hidden}
      aria-labelledby={`settings-section-title-${id}`}
    >
      <h2 id={`settings-section-title-${id}`} className={`settings-page-section-title${quiet ? " settings-page-section-title-quiet" : ""}`}>{label}</h2>
      <div className="settings-page-section-body">{children}</div>
    </section>
  );
}

export type PrefSaveState = {
  tone: "ok" | "busy" | "edited" | "danger";
  text: string;
  /** When it was saved: the bar says "just now", "4 min ago", then the clock. */
  at?: Date;
  /** The plain reason, kept for the tooltip and assistive technology. */
  reason?: string;
};

/** The status bar: save state, then facts, then (only on a refusal) Retry.
 *  `inline` keeps it inside its host (a Components specimen) instead of
 *  publishing into the window frame's foot. */
export function PrefStatus({
  save,
  facts = [],
  extra,
  onRetry,
  retryDisabled,
  verbs,
  inline,
  failureTestId = "settings-save-failure",
}: {
  save: PrefSaveState | null;
  /** Where the reason lives: the bar, unless the face shows it in its body. */
  failureTestId?: string | null;
  facts?: ReactNode[];
  extra?: ReactNode;
  onRetry?: () => void;
  retryDisabled?: boolean;
  verbs?: ReactNode;
  inline?: boolean;
}) {
  const now = useMinuteTick(Boolean(save?.at));
  const items: Array<StatusBarItem | null> = [
    save ? {
      key: "save",
      lamp: SAVE_LAMP[save.tone],
      text: (
        <span
          className="pref-status-save prefs-receipt"
          data-tone={save.tone}
          role={save.tone === "danger" ? "alert" : undefined}
          title={save.reason || undefined}
          data-testid={save.tone === "danger" && failureTestId ? failureTestId : undefined}
        >
          {save.at ? `${save.text} ${sinceWord(save.at, now)}` : save.text}
          {/* The bar stays short; the plain reason is the tooltip and is read aloud. */}
          {save.reason ? <span className="pref-status-reason"> · {save.reason}</span> : null}
        </span>
      ),
    } : null,
    ...facts.filter(Boolean).map((fact, index) => ({ key: `fact-${index}`, text: fact })),
    extra ? { key: "extra", text: extra } : null,
  ];
  const retry = onRetry ? <Button variant="primary" dense disabled={retryDisabled} onClick={onRetry}>Retry</Button> : null;
  const bar = (
    <StatusBar
      className="pref-status-bar"
      data-testid="settings-status"
      items={items}
      verbs={retry || verbs ? <>{retry}{verbs}</> : undefined}
    />
  );
  return inline ? <FootSlotContext.Provider value={null}>{bar}</FootSlotContext.Provider> : bar;
}

/** The save state's lamp: green saved, amber saving, blue edited, red not saved. */
const SAVE_LAMP = { ok: "ok", busy: "warn", edited: "info", danger: "fail" } as const;

/** Re-render once a minute while a relative time is on show. */
function useMinuteTick(active: boolean): number {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (!active) return;
    setNow(Date.now());
    const timer = window.setInterval(() => setNow(Date.now()), 30_000);
    return () => window.clearInterval(timer);
  }, [active]);
  return now;
}

/** "just now", "4 min ago", then the owner's clock (`4:22 PM`). */
export function sinceWord(at: Date, now: number = Date.now()): string {
  const diff = now - at.getTime();
  // A tick that predates the save is "just now"; a stamp far ahead of the
  // clock (yesterday's HH:MM read as today) says its clock.
  if (diff < 60_000 && diff > -60_000) return "just now";
  const minutes = Math.floor(diff / 60_000);
  if (minutes < 0 || minutes >= 60) return at.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
  return `${minutes} min ago`;
}

/** A writer's `16:22:54` / `16:22` stamp as today's Date (null when absent). */
export function stampDate(stamp: string | null | undefined): Date | undefined {
  const match = stamp ? /^(\d{1,2}):(\d{2})(?::(\d{2}))?/.exec(stamp) : null;
  if (!match) return undefined;
  const at = new Date();
  at.setHours(Number(match[1]), Number(match[2]), Number(match[3] ?? 0), 0);
  return at;
}

/** `16:22:54` or `16:22` (the writers' stamps) said as the owner's clock. */
export function clockWord(stamp: string | null | undefined): string {
  if (!stamp) return "";
  const match = /^(\d{1,2}):(\d{2})/.exec(stamp);
  if (!match) return stamp;
  const at = new Date();
  at.setHours(Number(match[1]), Number(match[2]), 0, 0);
  return at.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}
