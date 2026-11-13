import { useId, useLayoutEffect, useRef, useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { activity } from "./activity";
import { WorkMenu } from "../../components/DeskMenu";
import { fitStrip } from "../fitStrip";
import "./step-track.css";
export type TrackStep = {
  id: string;
  name: string;
  /** Producer state: working, waiting, merged, planned, etc. */ state: string;
};
export type StepTrackProps = {
  steps: readonly TrackStep[];
  current: string | null;
  selected?: string | null;
  onSelect(id: string): void;
  label: string;
  /** The selected pane can own the step name while the track keeps its numbers. */
  showNames?: boolean;
};
/** Selection and running state are independent; every station fits the seat. */
export function StepTrack({
  steps,
  current,
  selected,
  onSelect,
  label,
  showNames = true,
}: StepTrackProps) {
  const ref = useRef<HTMLDivElement>(null),
    previous = useRef({ current, ids: steps.map((s) => s.id) });
  const [condensed, setCondensed] = useState(false);
  const [width, setWidth] = useState(0), [open, setOpen] = useState(false);
  const anchor = useRef<HTMLButtonElement>(null), pendingFocus = useRef<string | null>(null);
  const [ticked, setTicked] = useState<string | null>(null);
  const id = useId();
  const picked =
    steps.find((step) => step.id === selected)?.id ??
    steps.find((step) => step.id === current)?.id ??
    steps[0]?.id;
  useLayoutEffect(() => {
    const before = previous.current;
    if (before.current !== current) {
      const from = steps.findIndex((s) => s.id === before.current),
        to = steps.findIndex((s) => s.id === current);
      setTicked(
        !window.matchMedia?.("(prefers-reduced-motion: reduce)").matches &&
          from >= 0 &&
          to > from &&
          before.ids.join() === steps.map((s) => s.id).join()
          ? before.current
          : null,
      );
    }
    previous.current = { current, ids: steps.map((s) => s.id) };
    const show = () => {
      for (const station of ref.current?.querySelectorAll<HTMLElement>(
        "[data-step-id]",
      ) ?? []) {
        station.style.setProperty(
          "--surface-station-width",
          `${station.getBoundingClientRect().width}px`,
        );
      }
      const width = ref.current?.getBoundingClientRect().width || 0;
      setWidth(Math.max(0, width - 16));
      const narrowNames = [
        ...(ref.current?.querySelectorAll<HTMLElement>(".surface-step-name") ??
          []),
      ].some((name) => {
        const probe = name.cloneNode(true) as HTMLElement;
        const style = getComputedStyle(name);
        Object.assign(probe.style, {
          position: "absolute",
          visibility: "hidden",
          display: "block",
          height: "auto",
          overflow: "visible",
          webkitLineClamp: "unset",
          font: style.font,
          width: `${Math.max(1, name.parentElement!.getBoundingClientRect().width - 8)}px`,
        });
        ref.current!.append(probe);
        const long =
          probe.getBoundingClientRect().height >
          (parseFloat(style.lineHeight) || 16) * 2 + 1;
        probe.remove();
        return long;
      });
      setCondensed(narrowNames || (width > 0 && width < steps.length * 112));
    };
    show();
    const observer =
      typeof ResizeObserver === "undefined" ? null : new ResizeObserver(show);
    if (ref.current) observer?.observe(ref.current);
    return () => observer?.disconnect();
  }, [current, steps, showNames]);
  const currentStep = steps.find((s) => s.id === current);
  const shown = fitStrip(width, steps.map(() => 44), 84, 0, steps.findIndex(step => step.id === picked));
  const hidden = steps.filter((_, index) => !shown.includes(index));
  const rect = open ? anchor.current?.getBoundingClientRect() : null;
  useLayoutEffect(() => {
    if (!pendingFocus.current) return;
    [...ref.current?.querySelectorAll<HTMLButtonElement>('[data-step-id]') ?? []]
      .find(tab => tab.dataset.stepId === pendingFocus.current)?.focus();
    pendingFocus.current = null;
  }, [picked, width]);
  return (
    <div className="surface-step-track" data-condensed={condensed || !showNames || undefined}>
      <div
        ref={ref}
        className="surface-step-strip"
        role="tablist"
        aria-label={label}
        data-joined-controls
        onKeyDown={(event) => {
          if (event.altKey || event.metaKey || event.ctrlKey) return;
          const from = steps.findIndex(
            (s) =>
              s.id ===
              (event.target as HTMLElement).closest<HTMLElement>(
                "[data-step-id]",
              )?.dataset.stepId,
          );
          const delta =
            event.key === "ArrowRight" || event.key === "ArrowDown"
              ? 1
              : event.key === "ArrowLeft" || event.key === "ArrowUp"
                ? -1
                : 0;
          const to =
            event.key === "Home"
              ? 0
              : event.key === "End"
                ? steps.length - 1
                : delta
                  ? Math.max(0, Math.min(steps.length - 1, from + delta))
                  : -1;
          if (from < 0 || to < 0) return;
          event.preventDefault();
          pendingFocus.current = steps[to].id;
          onSelect(steps[to].id);
          ref.current
            ?.querySelectorAll<HTMLButtonElement>('[role="tab"]')
            [to]?.focus();
        }}
      >
        {steps.map((step, index) => {
          if (!shown.includes(index)) return null;
          const tone = activity(step.state),
            isCurrent = step.id === current;
          const word =
            step.state === "failed"
              ? "Failed"
              : step.state === "check_failed"
                ? "Check failed"
                : step.state === "limited"
                  ? "Limited"
                  : tone === "working"
                    ? "In work"
                    : tone === "waiting"
                      ? "Waits on you"
                      : tone === "parked"
                        ? "Parked"
                        : tone === "done"
                          ? "Done"
                          : "Not started";
          return (
            <Button
              key={step.id}
              variant="chrome"
              className="surface-step-station"
              role="tab"
              id={`${id}-${step.id}`}
              data-step-id={step.id}
              data-state={tone}
              data-complete={index > 0 && activity(steps[index-1].state) === "done" && (tone === "done" || isCurrent) || undefined}
              data-ticked={step.id === ticked || undefined}
              aria-label={`Step ${index + 1}: ${step.name}, ${word}`}
              aria-current={isCurrent ? "step" : undefined}
              aria-selected={step.id === picked}
              tabIndex={step.id === picked ? 0 : -1}
              onClick={() => onSelect(step.id)}
              onAnimationEnd={() => {
                if (step.id === ticked) setTicked(null);
              }}
            >
              {isCurrent && tone === "working" && index > 0 ? (
                <span className="surface-step-traveller" aria-hidden="true" />
              ) : null}
              <span className="surface-step-dot" aria-hidden="true">
                {tone === "done" ? "✓" : index + 1}
              </span>
              {showNames ? <span className="surface-step-name" aria-hidden="true">
                {step.name}
              </span> : null}
            </Button>
          );
        })}
        {hidden.length ? <Button ref={anchor} dense variant="secondary" className="surface-step-more" aria-haspopup="menu" aria-expanded={open} onClick={() => setOpen(!open)}>More ▾</Button> : null}
      </div>
      {rect ? <WorkMenu label={`${label} steps`} x={rect.left} y={rect.bottom} opener={anchor.current} autoFocus returnFocus={() => anchor.current?.focus()} onClose={() => setOpen(false)} entries={hidden.map(step => ({type:"item", id:step.id, label:`Step ${steps.indexOf(step) + 1}: ${step.name}`, checked:step.id === picked ? "exclusive" : undefined, onSelect:() => onSelect(step.id)}))} /> : null}
      {currentStep && showNames ? (
        <div className="surface-step-current-name" aria-hidden="true">
          Step {steps.indexOf(currentStep) + 1} · {currentStep.name}
        </div>
      ) : null}
    </div>
  );
}
