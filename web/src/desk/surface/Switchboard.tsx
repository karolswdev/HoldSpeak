// PHILO-16 (C) — SurfaceSwitchboard: the picture of what runs on what.
//
// COMPOSITOR.md §12 ("The exemplar: Runs on"), canvas Board 2. Three columns:
// the jobs (left; each with a plug on its right edge coloured by one of five
// states), the wires (an SVG of cubic curves; solid = first, dashed =
// fallbacks), and the engines (right; a raised steel plate with an emblem, a
// token line, a live lamp, a plug on its left edge, a download bar that fills
// in place). Below the engines, FOUND: what the machine found but the owner
// has not accepted, each with one verb. Drag an engine plate onto a job to
// patch it; hold ⌥ (Alt) on the drop to add it as a fallback. The species
// decides nothing: `accepts` answers accept/refuse, `onPatch` writes.
//
// At phone width (`layout="list"`) the board becomes the job list: the
// selected job opens to its engine and the alternatives; a tap patches.

import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  type KeyboardEvent,
  type PointerEvent,
  type ReactNode,
  type RefObject,
} from "react";
import { Button } from "../../components/signal/Signal";
import { plugPoint, wirePath, type Box } from "./switchboardGeometry";
import "./switchboard.css";

/** The five state words, and nothing else (§12 rule 6). */
export type SwitchState = "ready" | "limited" | "broken" | "waiting" | "off";
export type SwitchLamp = "ok" | "busy" | "warn" | "broken" | "off";

export interface SwitchJob {
  id: string;
  name: string;
  /** The job's tasks, as one token line. */
  tasks: string;
  state: SwitchState;
  /** The global head: every job with no wire of its own follows it. */
  isDefault?: boolean;
  /** The job's verb (Try it). */
  verb?: ReactNode;
  /** The answer of the last Try it, on the job. */
  result?: ReactNode;
  /** Phone: the line under the job's name (its engine, or its tasks). */
  runsOn?: string;
}

export interface SwitchEngine {
  id: string;
  /** MAC · LAN · API. */
  emblem: string;
  name: string;
  tokens: string[];
  lamp: SwitchLamp;
  /** 0..100 while a download fills the bar on the plate; null otherwise. */
  progress?: number | null;
  /** The engine's one verb (Download · Fix address · Key · Use it). */
  verb?: ReactNode;
  /** The egress chip beside the verb (the host the verb reaches). */
  egress?: ReactNode;
  /** Only an engine with a model record can be dragged onto a job. */
  draggable?: boolean;
}

export interface SwitchWire {
  job: string;
  engine: string;
  /** 0 = the job's engine (solid); 1.. = its fallbacks (dashed), in order. */
  order: number;
  tone?: "limited" | "broken";
}

export interface SwitchAccept {
  ok: boolean;
  /** The refusal, as a token (`SPEECH ENGINES ONLY`). */
  reason?: string;
}

export type SwitchLayout = "board" | "list";

/** The board needs room for three columns; below this the job list. */
export const SWITCHBOARD_LIST_BELOW = 720;

/** The layout for a container: measured, never the viewport. */
export function useSwitchboardLayout(ref: RefObject<HTMLElement | null>): SwitchLayout {
  const [layout, setLayout] = useState<SwitchLayout>("board");
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    const read = () => {
      const width = el.getBoundingClientRect().width;
      if (width > 0) setLayout(width < SWITCHBOARD_LIST_BELOW ? "list" : "board");
    };
    read();
    if (typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(read);
    observer.observe(el);
    return () => observer.disconnect();
  }, [ref]);
  return layout;
}

export interface SurfaceSwitchboardProps {
  jobs: SwitchJob[];
  engines: SwitchEngine[];
  found?: SwitchEngine[];
  wires: SwitchWire[];
  selected?: string | null;
  onSelect?: (jobId: string | null) => void;
  /** The job whose first wire pulses (a Try it in flight). */
  pulse?: string | null;
  accepts?: (jobId: string, engineId: string) => SwitchAccept;
  onPatch?: (jobId: string, engineId: string, asFallback: boolean) => void;
  onRefuse?: (jobId: string, engineId: string, reason: string) => void;
  layout?: SwitchLayout;
  captions?: { jobs?: string; engines?: string; found?: string; or?: string; others?: string };
  /** The row at the bottom of the engines column (Add an engine). */
  engineFoot?: ReactNode;
}

const STATE_CLASS: Record<SwitchState, string> = {
  ready: "is-ready",
  limited: "is-limited",
  broken: "is-broken",
  waiting: "is-waiting",
  off: "is-off",
};

function EnginePlate({
  engine,
  found,
  inline,
  dragging,
  plugRef,
  onPointerDown,
  onKeyDown,
}: {
  engine: SwitchEngine;
  found?: boolean;
  /** Inside a phone tap verb: a span, so the button holds phrasing only. */
  inline?: boolean;
  dragging?: boolean;
  plugRef?: (el: HTMLSpanElement | null) => void;
  onPointerDown?: (event: PointerEvent<HTMLDivElement>) => void;
  onKeyDown?: (event: KeyboardEvent<HTMLDivElement>) => void;
}) {
  const downloading = engine.progress != null;
  const Tag = inline ? "span" : "div";
  return (
    <Tag
      className={
        "switchboard-engine" +
        (found ? " is-found" : "") +
        (engine.draggable ? " is-draggable" : "") +
        (dragging ? " is-dragging" : "") +
        (downloading ? " is-downloading" : "")
      }
      data-testid={`switchboard-engine-${engine.id}`}
      data-engine-id={engine.id}
      tabIndex={engine.draggable && !found ? 0 : undefined}
      aria-label={engine.name}
      onPointerDown={onPointerDown}
      onKeyDown={onKeyDown}
    >
      {found ? null : <span className="switchboard-plug" ref={plugRef} aria-hidden="true" />}
      <span className="switchboard-emblem">{engine.emblem}</span>
      <span className="switchboard-engine-name">{engine.name}</span>
      <span
        className={`switchboard-lamp is-${engine.lamp}`}
        data-testid={`switchboard-lamp-${engine.id}`}
        data-lamp={engine.lamp}
        aria-hidden="true"
      />
      <span className="switchboard-engine-tokens">
        {engine.tokens.filter(Boolean).map((token) => (
          <span key={token}>{token}</span>
        ))}
      </span>
      {downloading ? (
        <span
          className="switchboard-bar"
          role="progressbar"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={Math.round(engine.progress ?? 0)}
          data-testid={`switchboard-bar-${engine.id}`}
        >
          <i style={{ width: `${Math.max(0, Math.min(100, engine.progress ?? 0))}%` }} />
        </span>
      ) : null}
      {engine.verb || engine.egress ? (
        <span className="switchboard-engine-verb">
          {engine.egress}
          {engine.verb}
        </span>
      ) : null}
    </Tag>
  );
}

export function SurfaceSwitchboard({
  jobs,
  engines,
  found = [],
  wires,
  selected = null,
  onSelect,
  pulse = null,
  accepts,
  onPatch,
  onRefuse,
  layout = "board",
  captions = {},
  engineFoot,
}: SurfaceSwitchboardProps) {
  if (layout === "list") {
    return (
      <SwitchboardList
        jobs={jobs}
        engines={engines}
        found={found}
        wires={wires}
        selected={selected}
        onSelect={onSelect}
        accepts={accepts}
        onPatch={onPatch}
        captions={captions}
        engineFoot={engineFoot}
      />
    );
  }
  return (
    <SwitchboardBoard
      jobs={jobs}
      engines={engines}
      found={found}
      wires={wires}
      selected={selected}
      onSelect={onSelect}
      pulse={pulse}
      accepts={accepts}
      onPatch={onPatch}
      onRefuse={onRefuse}
      captions={captions}
      engineFoot={engineFoot}
    />
  );
}

function SwitchboardBoard({
  jobs,
  engines,
  found,
  wires,
  selected,
  onSelect,
  pulse,
  accepts,
  onPatch,
  onRefuse,
  captions,
  engineFoot,
}: Omit<SurfaceSwitchboardProps, "layout"> & { found: SwitchEngine[]; captions: NonNullable<SurfaceSwitchboardProps["captions"]> }) {
  const wiresRef = useRef<HTMLDivElement | null>(null);
  const jobPlugs = useRef(new Map<string, HTMLSpanElement>());
  const enginePlugs = useRef(new Map<string, HTMLSpanElement>());
  const [paths, setPaths] = useState<Record<string, string>>({});
  const [drag, setDrag] = useState<{ engine: string; pointer: number } | null>(null);
  const [over, setOver] = useState<{ job: string; ok: boolean } | null>(null);

  const wireKey = (wire: SwitchWire) => `${wire.job}|${wire.engine}|${wire.order}`;

  const measure = useCallback(() => {
    const layer = wiresRef.current;
    if (!layer) return;
    const origin = layer.getBoundingClientRect() as Box;
    const next: Record<string, string> = {};
    for (const wire of wires ?? []) {
      const from = jobPlugs.current.get(wire.job);
      const to = enginePlugs.current.get(wire.engine);
      if (!from || !to) continue;
      // A wire leaves the job's right edge and lands on the engine's left
      // edge (each plug straddles its edge; canvas Board 2 `draw()`).
      const jobBox = (from.parentElement ?? from).getBoundingClientRect() as Box;
      const engineBox = (to.parentElement ?? to).getBoundingClientRect() as Box;
      const a = plugPoint(jobBox, "right", origin);
      const b = plugPoint(engineBox, "left", origin);
      next[wireKey(wire)] = wirePath(a, b);
    }
    setPaths((prev) => (JSON.stringify(prev) === JSON.stringify(next) ? prev : next));
  }, [wires]);

  useLayoutEffect(() => {
    measure();
  });

  useEffect(() => {
    const layer = wiresRef.current?.parentElement;
    if (!layer || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(() => measure());
    observer.observe(layer);
    return () => observer.disconnect();
  }, [measure]);

  const jobAt = (x: number, y: number): string | null => {
    if (typeof document === "undefined" || typeof document.elementFromPoint !== "function") return null;
    const el = document.elementFromPoint(x, y);
    const job = el instanceof Element ? el.closest("[data-job-id]") : null;
    return job ? job.getAttribute("data-job-id") : null;
  };

  const hasWire = (jobId: string) => (wires ?? []).some((wire) => wire.job === jobId);

  const drop = (jobId: string, engineId: string, alt: boolean) => {
    const answer = accepts ? accepts(jobId, engineId) : { ok: true };
    if (!answer.ok) {
      onRefuse?.(jobId, engineId, answer.reason ?? "REFUSED");
      return;
    }
    onPatch?.(jobId, engineId, Boolean(alt) && hasWire(jobId));
  };

  const startDrag = (engine: SwitchEngine) => (event: PointerEvent<HTMLDivElement>) => {
    if (!engine.draggable) return;
    if ((event.target as Element).closest("button, a, input")) return;
    event.preventDefault();
    try {
      event.currentTarget.setPointerCapture?.(event.pointerId);
    } catch {
      /* a synthetic pointer has no capture */
    }
    setDrag({ engine: engine.id, pointer: event.pointerId });
  };

  const moveDrag = (event: PointerEvent<HTMLDivElement>) => {
    if (!drag) return;
    const job = jobAt(event.clientX, event.clientY);
    if (!job) {
      if (over) setOver(null);
      return;
    }
    const ok = accepts ? accepts(job, drag.engine).ok : true;
    if (!over || over.job !== job || over.ok !== ok) setOver({ job, ok });
  };

  const endDrag = (event: PointerEvent<HTMLDivElement>) => {
    if (!drag) return;
    const job = jobAt(event.clientX, event.clientY) ?? over?.job ?? null;
    const engine = drag.engine;
    setDrag(null);
    setOver(null);
    if (job) drop(job, engine, event.altKey);
  };

  // Keyboard: with a job selected, Enter on an engine patches it; ⌥Enter
  // adds it as a fallback. The drag's twin, for hands on keys.
  const keyPatch = (engine: SwitchEngine) => (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key !== "Enter" || !selected || !engine.draggable) return;
    event.preventDefault();
    drop(selected, engine.id, event.altKey);
  };

  return (
    <div
      className={"switchboard" + (drag ? " is-dragging" : "")}
      data-testid="switchboard"
      data-layout="board"
      onPointerMove={moveDrag}
      onPointerUp={endDrag}
      onPointerCancel={() => {
        setDrag(null);
        setOver(null);
      }}
    >
      <div className="switchboard-col switchboard-jobs" data-testid="switchboard-jobs">
        {captions.jobs ? <div className="switchboard-cap">{captions.jobs}</div> : null}
        {jobs.map((job) => {
          const hover = over && over.job === job.id ? (over.ok ? " is-over" : " is-over is-refused") : "";
          return (
            <div
              key={job.id}
              className={
                "switchboard-job " +
                STATE_CLASS[job.state] +
                (job.isDefault ? " is-default" : "") +
                (selected === job.id ? " is-selected" : "") +
                hover
              }
              data-testid={`switchboard-job-${job.id}`}
              data-job-id={job.id}
              data-state={job.state}
              onClick={(event) => {
                if ((event.target as Element).closest("button")) return;
                onSelect?.(selected === job.id ? null : job.id);
              }}
            >
              <span className="switchboard-job-name">{job.name}</span>
              {job.verb ? <span className="switchboard-job-verb">{job.verb}</span> : null}
              <span className="switchboard-job-tasks">{job.tasks}</span>
              {job.result ? (
                <span className="switchboard-job-result" data-testid={`switchboard-result-${job.id}`}>
                  {job.result}
                </span>
              ) : null}
              <span
                className="switchboard-plug"
                aria-hidden="true"
                ref={(el) => {
                  if (el) jobPlugs.current.set(job.id, el);
                  else jobPlugs.current.delete(job.id);
                }}
              />
            </div>
          );
        })}
      </div>
      <div className="switchboard-wires" ref={wiresRef} aria-hidden="true">
        <svg className="switchboard-wire-layer">
          {(wires ?? []).map((wire) => {
            const d = paths[wireKey(wire)] ?? "";
            const classes =
              "switchboard-wire" +
              (wire.order > 0 ? " is-fallback" : "") +
              (wire.tone === "limited" ? " is-limited" : "") +
              (wire.tone === "broken" ? " is-broken" : "") +
              (selected === wire.job ? " is-hot" : "") +
              (pulse === wire.job && wire.order === 0 ? " is-pulse" : "");
            return (
              <path
                key={wireKey(wire)}
                className={classes}
                d={d}
                data-testid="switchboard-wire"
                data-job={wire.job}
                data-engine={wire.engine}
                data-order={wire.order}
              />
            );
          })}
        </svg>
      </div>
      <div className="switchboard-col switchboard-engines" data-testid="switchboard-engines">
        {captions.engines ? <div className="switchboard-cap">{captions.engines}</div> : null}
        {engines.map((engine) => (
          <EnginePlate
            key={engine.id}
            engine={engine}
            dragging={drag?.engine === engine.id}
            plugRef={(el) => {
              if (el) enginePlugs.current.set(engine.id, el);
              else enginePlugs.current.delete(engine.id);
            }}
            onPointerDown={startDrag(engine)}
            onKeyDown={keyPatch(engine)}
          />
        ))}
        {found.length > 0 ? (
          <>
            <div className="switchboard-cap" data-testid="switchboard-found-cap">
              {`${captions.found ?? "Found"} · ${found.length}`}
            </div>
            {found.map((engine) => (
              <EnginePlate key={engine.id} engine={engine} found />
            ))}
          </>
        ) : null}
        {engineFoot}
      </div>
    </div>
  );
}

function SwitchboardList({
  jobs,
  engines,
  found,
  wires,
  selected,
  onSelect,
  accepts,
  onPatch,
  captions,
  engineFoot,
}: Omit<SurfaceSwitchboardProps, "layout" | "pulse" | "onRefuse"> & {
  found: SwitchEngine[];
  captions: NonNullable<SurfaceSwitchboardProps["captions"]>;
}) {
  const open = jobs.find((job) => job.id === selected) ?? jobs[0];
  const chain = (wires ?? [])
    .filter((wire) => open && wire.job === open.id)
    .sort((a, b) => a.order - b.order);
  const first = chain[0] ? engines.find((engine) => engine.id === chain[0].engine) : undefined;
  const alternatives = engines.filter(
    (engine) =>
      engine.draggable &&
      engine.id !== first?.id &&
      (!accepts || !open || accepts(open.id, engine.id).ok),
  );
  return (
    <div className="switchboard is-list" data-testid="switchboard" data-layout="list">
      {open ? (
        <>
          <div
            className={"switchboard-job is-open " + STATE_CLASS[open.state]}
            data-testid={`switchboard-job-${open.id}`}
            data-job-id={open.id}
            data-state={open.state}
          >
            <span className="switchboard-job-name">{`${open.name} · runs on`}</span>
            {open.result ? (
              <span className="switchboard-job-result" data-testid={`switchboard-result-${open.id}`}>
                {open.result}
              </span>
            ) : null}
          </div>
          {first ? <EnginePlate engine={first} /> : null}
          {alternatives.length > 0 ? (
            <>
              <div className="switchboard-cap">{captions.or ?? "Or"}</div>
              {alternatives.map((engine) => (
                <Button
                  key={engine.id}
                  variant="ghost"
                  className="switchboard-tap"
                  data-testid={`switchboard-tap-${engine.id}`}
                  onClick={() => onPatch?.(open.id, engine.id, false)}
                >
                  <EnginePlate inline engine={{ ...engine, verb: undefined, egress: undefined }} />
                </Button>
              ))}
            </>
          ) : null}
        </>
      ) : null}
      <div className="switchboard-cap">{captions.others ?? "Other jobs"}</div>
      {jobs
        .filter((job) => job.id !== open?.id)
        .map((job) => (
          <Button
            key={job.id}
            variant="ghost"
            className={"switchboard-tap switchboard-job " + STATE_CLASS[job.state]}
            data-testid={`switchboard-job-${job.id}`}
            data-job-id={job.id}
            data-state={job.state}
            onClick={() => onSelect?.(job.id)}
          >
            <span className="switchboard-job-name">{job.name}</span>
            <span className="switchboard-job-tasks">{job.runsOn ?? job.tasks}</span>
          </Button>
        ))}
      {found.length > 0 ? (
        <>
          <div className="switchboard-cap" data-testid="switchboard-found-cap">
            {`${captions.found ?? "Found"} · ${found.length}`}
          </div>
          {found.map((engine) => (
            <EnginePlate key={engine.id} engine={engine} found />
          ))}
        </>
      ) : null}
      {engines
        .filter((engine) => engine.progress != null || (!engine.draggable && engine.verb))
        .map((engine) => (
          <EnginePlate key={`more-${engine.id}`} engine={engine} />
        ))}
      {engineFoot}
    </div>
  );
}
