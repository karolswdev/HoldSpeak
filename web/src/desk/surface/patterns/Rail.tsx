import { useEffect, useRef, useState, type ReactNode } from "react";
import { Button } from "../../../components/signal/Signal";
import { useRovingRows } from "../roving";
import { useHasWindowBack, useWindowBack } from "../back";
import { useCompactViewport } from "../../useCompactViewport";
import { Spine, type SpineProps } from "./Spine";
import "./rail.css";

type RailData = { [key: `data-${string}`]: string | undefined };
export type RailItem = {
  id: string;
  label: ReactNode;
  accessibleLabel?: string;
  glyph?: ReactNode;
  facts?: ReactNode;
  state?: ReactNode;
  spine?: SpineProps;
  count?: number;
  disabled?: boolean;
  data?: RailData;
  rowData?: RailData;
};
export type RailGroup = {
  id: string;
  label?: string;
  items: readonly RailItem[];
  testId?: string;
  labelTestId?: string;
};
export type RailProps = {
  label: string;
  compact?: boolean;
  items?: readonly RailItem[];
  groups?: readonly RailGroup[];
  picked: string | null;
  onPick(id: string): void;
  head?: ReactNode;
  foot?: ReactNode;
  /** Loading, empty or failed content replaces the rows. */
  children?: ReactNode;
  /** Controlled phone navigation; otherwise a press opens the pane locally. */
  paneOpen?: boolean;
  onBack?(): void;
  /** The host already supplies the one Back path. */
  hostBack?: boolean;
  "data-testid"?: string;
};

/** One list beside a pane. On a narrow surface the list and pane take turns;
 *  names and state remain readable, and Back returns focus to the picked row. */
export function Rail({ label, compact = false, items = [], groups, picked, onPick, head, foot, children,
  paneOpen, onBack, hostBack = false, "data-testid": testId }: RailProps) {
  const ref = useRef<HTMLElement>(null);
  const lastPicked = useRef(picked);
  const [opened, setOpened] = useState(false);
  const open = paneOpen ?? opened;
  const compactViewport = useCompactViewport();
  const hosted = useHasWindowBack();
  const viaFrame = compactViewport && hosted;
  useRovingRows(ref, { selector: ".surface-rail-row:not(:disabled)" });
  useEffect(() => {
    if (picked) lastPicked.current = picked;
    // Anchor Tab to the picked item after an external selection too.
    const rows = [...(ref.current?.querySelectorAll<HTMLButtonElement>(".surface-rail-row:not(:disabled)") ?? [])];
    const active = rows.find((row) => row === document.activeElement)
      ?? rows.find((row) => row.dataset.railId === picked) ?? rows[0];
    rows.forEach((row) => { row.tabIndex = row === active ? 0 : -1; });
  });
  const back = () => {
    setOpened(false);
    onBack?.();
    requestAnimationFrame(() => {
      const rows = [...(ref.current?.querySelectorAll<HTMLButtonElement>(".surface-rail-row:not(:disabled)") ?? [])];
      (rows.find((row) => row.dataset.railId === lastPicked.current) ?? rows[0])?.focus();
    });
  };
  return <>
    {hostBack ? null : <RailFrameBack open={viaFrame && open} onBack={back} />}
    <nav ref={ref} className="surface-rail surface-rail--fold" aria-label={label}
      data-pane-open={open || undefined} data-compact={compact || undefined} data-testid={testId}>
      {head ? <div className="surface-rail-head">{head}</div> : null}
      {children ?? (groups ?? [{ id: "items", items }]).map((group) => group.items.length ? (
        <div key={group.id} className="surface-rail-group" role={group.label ? "group" : undefined}
          aria-label={group.label} data-section={group.id} data-testid={group.testId}>
          {group.label ? <h3 className="surface-rail-caption" data-testid={group.labelTestId}>{group.label}</h3> : null}
          <ul className="surface-rail-list">
            {group.items.map((item) => <li key={item.id} {...item.rowData}>
              <Button {...item.data} variant="chrome" className="surface-rail-row" data-rail-id={item.id}
                aria-current={picked === item.id ? "true" : undefined} aria-label={item.accessibleLabel} title={item.accessibleLabel}
                disabled={item.disabled} onClick={() => { lastPicked.current = item.id; setOpened(true); onPick(item.id); }}>
                {item.glyph ? <span className="surface-rail-glyph" aria-hidden="true">{item.glyph}</span> : null}
                <span className="surface-rail-words">
                  <span className="surface-rail-label" data-control-label>{item.label}</span>
                  {item.facts ? <span className="surface-rail-facts">{item.facts}</span> : null}
                  {item.spine ? <Spine {...item.spine} /> : null}
                </span>
                {"state" in item || "count" in item ? <span className="surface-rail-trailing">
                  {item.state ? <span className="surface-rail-state">{item.state}</span> : null}
                  {item.count != null && item.count > 0 ? <span className="surface-rail-count">{item.count}</span> : null}
                </span> : null}
              </Button>
            </li>)}
          </ul>
        </div>
      ) : null)}
      {foot ? <div className="surface-rail-foot">{foot}</div> : null}
    </nav>
    {hostBack || viaFrame ? null : <div className="surface-rail-back"><Button variant="chrome" onClick={back}>Back to {label.toLowerCase()}</Button></div>}
  </>;
}

/** Keep one Back on the phone. A narrow desktop window uses the in-flow one. */
function RailFrameBack({ open, onBack }: { open: boolean; onBack(): void }) {
  const back = useRef(onBack);
  back.current = onBack;
  useWindowBack(open ? { onBack: () => back.current(), testId: "rail-back" } : null, [open]);
  return null;
}
