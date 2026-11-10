import { useId, useRef, type ReactNode, type HTMLAttributes } from "react";
import { Button } from "../../../components/signal/Signal";
import { useRovingRows } from "../roving";
import "./preferences.css";

/** A window-sized column. Only its list wells scroll. */
export function PreferencePane({
  children,
  label,
  testId,
  ...props
}: HTMLAttributes<HTMLDivElement> & {
  children: ReactNode;
  label: string;
  testId?: string;
}) {
  return (
    <div
      {...props}
      className="surface-preference-pane"
      aria-label={label}
      data-testid={testId}
    >
      {children}
    </div>
  );
}
export function PaneGroup({
  label,
  children,
  grow = true,
}: {
  label: string;
  children: ReactNode;
  grow?: boolean;
}) {
  return (
    <section
      className="surface-pane-group"
      data-grow={grow || undefined}
      aria-label={label}
    >
      <h3>{label}</h3>
      {children}
    </section>
  );
}
export function PaneInspector({
  label,
  children,
  onClose,
}: {
  label: string;
  children: ReactNode;
  onClose(): void;
}) {
  return (
    <section className="surface-pane-inspector" aria-label={label}>
      <div className="surface-pane-inspector-head">
        <strong>{label}</strong>
        <Button dense variant="ghost" onClick={onClose}>
          Close
        </Button>
      </div>
      {children}
    </section>
  );
}
export function PaneActions({ children }: { children: ReactNode }) {
  return <div className="surface-pane-actions">{children}</div>;
}
export function SegmentedTabs({
  label,
  value,
  onChange,
  tabs,
  children,
}: {
  label: string;
  value: string;
  onChange(id: string): void;
  tabs: readonly { id: string; label: string }[];
  children: ReactNode;
}) {
  const id = useId();
  const ref = useRef<HTMLDivElement>(null);
  useRovingRows(ref, { selector: "[role=tab]" });
  return (
    <>
      <div
        className="surface-segmented-tabs"
        role="tablist"
        data-joined-controls
        aria-label={label}
        ref={ref}
        onKeyDown={(event) => {
          if (!["ArrowLeft", "ArrowRight"].includes(event.key)) return;
          event.preventDefault();
          const at = tabs.findIndex((tab) => tab.id === value);
          const next =
            tabs[
              (at + (event.key === "ArrowRight" ? 1 : -1) + tabs.length) %
                tabs.length
            ];
          onChange(next.id);
          ref.current
            ?.querySelector<HTMLElement>(`[data-tab="${next.id}"]`)
            ?.focus();
        }}
      >
        {tabs.map((tab) => (
          <Button
            key={tab.id}
            variant="chrome"
            role="tab"
            id={`${id}-${tab.id}`}
            data-tab={tab.id}
            aria-selected={value === tab.id}
            aria-controls={`${id}-panel`}
            tabIndex={value === tab.id ? 0 : -1}
            onClick={() => onChange(tab.id)}
          >
            {tab.label}
          </Button>
        ))}
      </div>
      <div
        className="surface-tab-panel"
        id={`${id}-panel`}
        role="tabpanel"
        aria-labelledby={`${id}-${value}`}
      >
        {children}
      </div>
    </>
  );
}
