import { useId, useLayoutEffect, useRef, useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { activity } from "./activity";
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
};
/** Selection and the running station are independent. The strip owns overflow. */
export function StepTrack({
  steps,
  current,
  selected,
  onSelect,
  label,
}: StepTrackProps) {
  const ref = useRef<HTMLDivElement>(null),
    previous = useRef({ current, ids: steps.map((s) => s.id) });
  const [condensed, setCondensed] = useState(false);
  const [ticked, setTicked] = useState<string | null>(null);
  const id = useId();
  const picked =
    steps.find((step) => step.id === selected)?.id ??
    steps.find((step) => step.id === current)?.id ??
    steps[0]?.id;
  const reveal = (station: HTMLElement | null | undefined) => {
    const strip = ref.current;
    if (!strip || !station) return;
    const seat = strip.getBoundingClientRect(),
      box = station.getBoundingClientRect();
    if (box.left < seat.left) strip.scrollLeft -= seat.left - box.left;
    else if (box.right > seat.right) strip.scrollLeft += box.right - seat.right;
  };
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
      setCondensed(narrowNames);
      reveal(ref.current?.querySelector<HTMLElement>('[aria-current="step"]'));
    };
    show();
    const observer =
      typeof ResizeObserver === "undefined" ? null : new ResizeObserver(show);
    if (ref.current) observer?.observe(ref.current);
    return () => observer?.disconnect();
  }, [current, steps]);
  const currentStep = steps.find((s) => s.id === current);
  return (
    <div className="surface-step-track" data-condensed={condensed || undefined}>
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
          onSelect(steps[to].id);
          ref.current
            ?.querySelectorAll<HTMLButtonElement>('[role="tab"]')
            [to]?.focus();
          reveal(
            ref.current?.querySelectorAll<HTMLButtonElement>('[role="tab"]')[
              to
            ],
          );
        }}
      >
        {steps.map((step, index) => {
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
              <span className="surface-step-name" aria-hidden="true">
                {step.name}
              </span>
            </Button>
          );
        })}
      </div>
      {currentStep ? (
        <div className="surface-step-current-name" aria-hidden="true">
          Step {steps.indexOf(currentStep) + 1} · {currentStep.name}
        </div>
      ) : null}
    </div>
  );
}
