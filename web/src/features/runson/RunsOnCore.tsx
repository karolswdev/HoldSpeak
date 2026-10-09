// PHILO-16 (C) — Runs on: the Models window as a Switchboard.
//
// COMPOSITOR.md §12 "The exemplar: Runs on", canvas Board 2. Composed from
// the kit: the AppHead (the one fact `N jobs · M engines` with its status
// strip), the Switchboard (the app's one species), and the Foot (the
// receipt `PATCHED <time> · <job> → <engine>`, the egress chip of the last
// engine used, Undo). A change applies on the drop; there is no Save.

import { useContext, useEffect, useMemo, useRef, type ReactNode } from "react";
import {
  CheckGadget,
  EgressChip,
  StateChip,
  StringGadget,
  SurfaceFooter,
  SurfaceSwitchboard,
  useSwitchboardLayout,
  wireDate,
  type SwitchEngine,
  type SwitchJob,
  type SwitchLamp,
  type SwitchWire,
} from "../../desk/surface";
import { TitleSlotContext } from "../../desk/surface/title";
import { Button } from "../../components/signal/Signal";
import type { CoreProps } from "../../pages/cores/core-types";
import { endpointHostPort, isLanAddress } from "../concierge/endpointDraft";
import { MeaningSearchRow } from "../concierge/MeaningSearchRow";
import {
  DEFAULT_JOB,
  JOB_ORDER,
  SPEECH_JOB,
  jobState,
  jobOf,
  limitTokens,
  ownEntries,
  splitEngines,
  taskLine,
  type BoardEngine,
} from "./model";
import { stateClass, stateWord } from "./stateWord";
import { useRunsOn, type RunsOnController } from "./useRunsOn";
// The Meaning search row draws with the Concierge's ledger cells.
import "../concierge/concierge.css";
import "./runson.css";

function lampFor(engine: BoardEngine, busy: boolean): SwitchLamp {
  if (busy) return "busy";
  if (engine.kind === "preset") return "warn";
  const word = stateWord(engine.state);
  if (word === "READY") return "ok";
  if (word === "BROKEN") return "broken";
  if (word === "OFF") return "off";
  return engine.state === "unknown" ? "off" : "warn";
}

function hardwareToken(det: RunsOnController["detection"]): string | null {
  const cap = det?.hardware?.capability;
  if (!cap) return null;
  const parts = ["THIS MAC"];
  if (cap.apple_silicon) parts.push("M‑SERIES");
  const gb = cap.ram_gb ?? (cap.total_memory_bytes ? Math.round(cap.total_memory_bytes / 1024 ** 3) : null);
  if (gb) parts.push(`${gb} GB`);
  return parts.join(" · ");
}

function AddEngineRow({ ctrl }: { ctrl: RunsOnController }) {
  const a = ctrl.add;
  const host = endpointHostPort(a.url).toUpperCase();
  return (
    <div className="runson-add" data-testid="concierge-add-engine-row">
      <StringGadget
        label="Server address"
        caption
        value={a.url}
        onChange={a.setUrl}
        placeholder="http://<host>:<port>/v1"
        autoFocus
      />
      <span className="runson-add-key" data-testid="concierge-add-key">
        <StringGadget label="Key" caption type="password" mic={false} value={a.key} onChange={a.setKey} placeholder="optional" />
      </span>
      <span data-testid="concierge-add-my-server">
        <CheckGadget variant="token" label="MY SERVER" checked={a.mine} onChange={a.setMine} />
      </span>
      <span className="runson-add-verbs">
        {host ? (
          <span data-testid="concierge-add-egress">
            <EgressChip label={host} scope={isLanAddress(a.url) ? "local" : "cloud"} />
          </span>
        ) : null}
        <Button
          dense
          variant="ghost"
          onClick={() => void a.check()}
          disabled={!a.url.trim() || a.state === "CHECKING"}
          loading={a.state === "CHECKING"}
          data-testid="concierge-add-check"
        >
          Check
        </Button>
        <Button
          dense
          variant="primary"
          onClick={() => void a.submit()}
          disabled={a.state !== "READY" || ctrl.busy}
          data-testid="concierge-add-submit"
        >
          Add
        </Button>
      </span>
      {a.state === "READY" ? (
        <span className="runson-add-answer">
          <StateChip state="success" label="READY" icon="●" />
          <span className="surface-token" data-testid="concierge-add-model">{a.model}</span>
          {a.tools ? (
            <span className="surface-token" data-testid="concierge-add-tools">
              {a.tools === "yes" ? "TOOLS" : a.tools === "no" ? "NO TOOLS" : "TOOLS UNKNOWN"}
            </span>
          ) : null}
        </span>
      ) : null}
      {a.state === "KEY_REQUIRED" ? (
        <span className="runson-add-answer" role="alert" data-testid="concierge-add-key-answer">
          <StateChip state="failure" label="KEY REQUIRED" />
        </span>
      ) : null}
      {a.state === "KEY_INVALID" ? (
        <span className="runson-add-answer" role="alert" data-testid="concierge-add-key-answer">
          <StateChip state="failure" label="KEY INVALID" />
          <span className="surface-token">BAD CHARACTERS</span>
        </span>
      ) : null}
      {/* A.3: the answer is tokens (the word and the host), never the
          server's sentence. */}
      {a.state === "UNREACHABLE" ? (
        <span className="runson-add-answer" role="alert">
          <StateChip state="failure" label="UNREACHABLE" />
          <span className="surface-token" data-testid="concierge-add-reason">{host || "NO ADDRESS"}</span>
        </span>
      ) : null}
      {a.state === "NOT_ADDED" ? (
        <span className="runson-add-answer" role="alert">
          <StateChip state="failure" label="NOT ADDED" />
          <span className="surface-token" data-testid="concierge-add-reason">{a.reason}</span>
        </span>
      ) : null}
    </div>
  );
}

export function RunsOnCore({ scope }: CoreProps) {
  const ctrl = useRunsOn(scope);
  const setTitle = useContext(TitleSlotContext);
  const rootRef = useRef<HTMLDivElement | null>(null);
  const layout = useSwitchboardLayout(rootRef);

  useEffect(() => {
    setTitle?.("Runs on");
  }, [setTitle]);

  const { roster, detection, engines } = ctrl;
  const repairs = detection?.repairs ?? [];
  const { have, found } = useMemo(() => splitEngines(engines), [engines]);

  /* ── a repair's one verb (HS-200-04), on its engine; on its first job
     when the engine is not on the board ── */
  const repairButton = (repair: (typeof repairs)[number], testId: string): ReactNode => {
    const label =
      repair.control === "model_library" ? "Download" : repair.control === "endpoint_editor" ? "Fix address" : repair.control === "connections" ? "Key" : "Choose";
    return (
      <Button
        dense
        variant="secondary"
        data-testid={testId}
        onClick={() => {
          if (repair.control === "endpoint_editor") ctrl.add.openRow(repair.baseUrl);
          else if (repair.control === "model_library" && repair.presetId) {
            const preset = engines.find((e) => e.presetId === repair.presetId);
            if (preset) void ctrl.download(preset.key);
          } else if (repair.control === "connections") {
            void import("../../desk/shell").then(({ openSurfaceOr }) => openSurfaceOr("configure-integrations", "/settings"));
          } else if (repair.groups[0]) ctrl.select(repair.groups[0]);
        }}
      >
        {label}
      </Button>
    );
  };
  const onBoard = (engineId: string) => engines.some((e) => !e.found && e.detectId === engineId);

  /* ── the jobs ── */
  const jobs: SwitchJob[] = [];
  const wires: SwitchWire[] = [];
  const words: Record<string, ReturnType<typeof stateWord>> = {};
  for (const job of JOB_ORDER) {
    const row = roster?.rows.find((r) => jobOf(r.id) === job);
    if (!row) continue;
    const word = jobState(job, row, engines, repairs);
    words[job] = word;
    const effective = ctrl.engineForJob(job);
    const result = ctrl.results[job];
    const jobRepair = repairs.find((r) => r.groups.includes(job));
    const listening = job === SPEECH_JOB && ctrl.listening;
    // A Try it only where something runs (no verb that does nothing).
    const canTry = Boolean(effective) && (job === SPEECH_JOB || Boolean(effective?.detectId) || job === "thoughts_notes");
    const tryVerb: ReactNode = canTry ? (
      <Button
        dense
        variant="secondary"
        loading={ctrl.trying?.job === job && !listening}
        onClick={() => ctrl.tryJob(job)}
        data-testid={`runson-try-${job}`}
      >
        {listening ? "Stop" : "Try it"}
      </Button>
    ) : undefined;
    jobs.push({
      id: job,
      name: job === DEFAULT_JOB ? "Default for AI work" : job === SPEECH_JOB ? "Speech" : row.label,
      tasks: taskLine(job, roster, row),
      state: stateClass(word),
      isDefault: job === DEFAULT_JOB,
      verb: layout === "board" ? tryVerb : undefined,
      runsOn: effective ? effective.name : word,
      // C4: the engine the job runs on now, even when it follows the default.
      current: effective?.key,
      currentToken: effective && row.inherited_from === "global" && job !== DEFAULT_JOB ? "FOLLOWS DEFAULT" : undefined,
      // The limitation is a token on the job (§12 rule 6), until a Try
      // answers in its place; a repair names itself there too.
      result: result ? (
        <span data-tone={result.tone === "danger" ? "danger" : result.tone === "idle" ? "idle" : undefined}>{result.tokens.join(" · ")}</span>
      ) : jobRepair ? (
        <span data-tone="danger" data-testid={`runson-job-repair-${job}`}>
          {jobRepair.token}
          {jobRepair.groups[0] === job && !(jobRepair.engineId && onBoard(jobRepair.engineId))
            ? repairButton(jobRepair, `runson-repair-job-${job}`)
            : null}
        </span>
      ) : word === "LIMITED" && limitTokens(job, effective).length ? (
        <span data-tone="warn">{limitTokens(job, effective).join(" · ")}</span>
      ) : undefined,
    });
    ownEntries(row).forEach((entry, order) => {
      wires.push({
        job,
        engine: entry.profile_id,
        order,
        tone:
          entry.readiness === "missing"
            ? "broken"
            : order === 0 && word === "LIMITED"
              ? "limited"
              : order === 0 && word === "BROKEN"
                ? "broken"
                : undefined,
      });
    });
  }

  /* ── the engines ── */
  const repairVerb = (engine: BoardEngine): ReactNode => {
    const repair = repairs.find((r) => r.engineId && r.engineId === engine.detectId);
    return repair ? repairButton(repair, `runson-repair-${engine.key}`) : undefined;
  };

  const plate = (engine: BoardEngine): SwitchEngine => {
    const progress = ctrl.downloads[engine.key];
    const downloading = progress != null;
    let verb: ReactNode = repairVerb(engine);
    let egress: ReactNode;
    const tokens = [...engine.tokens];
    const stopped = ctrl.failedDownloads[engine.key];
    if (engine.kind === "preset") {
      if (stopped && !downloading) {
        // V3: a stopped download keeps its reason on the plate until retried.
        const at = tokens.indexOf("NOT DOWNLOADED");
        if (at >= 0) tokens[at] = `STOPPED · ${stopped}`;
      }
      if (downloading) {
        const at = tokens.indexOf("NOT DOWNLOADED");
        if (at >= 0) tokens[at] = `${Math.round(progress)} %`;
      } else {
        // The file comes from the internet: the chip names that host.
        egress = <EgressChip label={(engine.downloadHost ?? "huggingface.co").toUpperCase()} scope="cloud" />;
        verb = (
          <Button dense variant="secondary" data-testid={`runson-download-${engine.key}`} onClick={() => void ctrl.download(engine.key)}>
            Download
          </Button>
        );
      }
    }
    return {
      id: engine.key,
      emblem: engine.emblem,
      name: engine.name,
      tokens,
      lamp: stopped && !downloading ? "broken" : lampFor(engine, ctrl.trying?.engine === engine.key || downloading),
      progress: downloading ? progress : null,
      verb,
      egress,
      draggable: Boolean(engine.profileId),
    };
  };

  const haveEngines = have.map(plate);
  const foundEngines: SwitchEngine[] = found.map((engine) => ({
    id: engine.key,
    emblem: engine.emblem,
    name: engine.name,
    tokens: [engine.baseUrl ? endpointHostPort(engine.baseUrl).toUpperCase() : "", ...engine.tokens].filter(Boolean),
    lamp: lampFor(engine, false),
    verb: (
      <Button dense variant="secondary" disabled={ctrl.busy} data-testid={`runson-use-${engine.key}`} onClick={() => void ctrl.useFound(engine.key)}>
        Use it
      </Button>
    ),
  }));

  const engineFoot = ctrl.add.open ? (
    <AddEngineRow ctrl={ctrl} />
  ) : (
    <Button dense variant="ghost" className="runson-add-open" data-testid="concierge-add-engine" onClick={() => ctrl.add.openRow()}>
      Add an engine
    </Button>
  );

  /* ── the AppHead ── */
  const jobCount = jobs.length;
  const engineCount = have.filter((e) => e.profileId).length;
  const ready = Object.values(words).filter((w) => w === "READY").length;
  const limited = Object.values(words).filter((w) => w === "LIMITED").length;
  const broken = Object.values(words).filter((w) => w === "BROKEN").length;
  const waiting = Object.values(words).filter((w) => w === "WAITING").length;
  const fact = engineCount ? `${jobCount} jobs · ${engineCount} ${engineCount === 1 ? "engine" : "engines"}` : `${jobCount} jobs`;
  const checked = detection?.checkedAt
    ? wireDate(detection.checkedAt)?.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: false })
    : null;
  const hw = hardwareToken(detection);

  /* ── the foot ── */
  const selectedJob = ctrl.selected ?? (layout === "list" ? jobs[0]?.id ?? null : null);
  const footTry =
    layout === "list" && selectedJob
      ? jobs.find((j) => j.id === selectedJob)
      : undefined;

  return (
    <div className="runson-root" ref={rootRef} data-testid="runson-root">
      <div className="runson-apphead">
        <h1 className="surface-display runson-fact" data-testid="runson-fact">
          {roster ? fact : "Runs on"}
        </h1>
        <ul className="runson-strip" data-testid="runson-strip">
          {ready ? <li data-tone="ok"><span className="runson-sq" />{`${ready} ready`}</li> : null}
          {limited ? <li data-tone="warn"><span className="runson-sq" />{`${limited} limited`}</li> : null}
          {broken ? <li data-tone="danger"><span className="runson-sq" />{`${broken} broken`}</li> : null}
          {waiting ? <li data-tone="idle"><span className="runson-sq" />{`${waiting} waiting`}</li> : null}
          {hw ? <li>{hw}</li> : null}
          {checked ? <li>{`Checked ${checked}`}</li> : detection ? null : roster ? <li>Checking</li> : null}
        </ul>
      </div>

      {roster ? (
        <SurfaceSwitchboard
          layout={layout}
          jobs={jobs}
          engines={haveEngines}
          found={foundEngines}
          wires={wires}
          selected={ctrl.selected}
          onSelect={ctrl.select}
          pulse={ctrl.trying?.job ?? null}
          accepts={ctrl.accepts}
          onPatch={(job, key, fallback) => void ctrl.patch(job, key, fallback)}
          onRefuse={ctrl.refuse}
          captions={{ jobs: "What HoldSpeak does", engines: "What you have", found: "Found", or: "Or", others: "Other jobs" }}
          engineFoot={engineFoot}
        />
      ) : ctrl.error ? (
        <span className="surface-token" data-tone="danger" role="alert">NOT READ</span>
      ) : null}

      {roster ? (
        // The row keeps the ledger context it was built in (the Concierge's
        // set list), so its cells lay out exactly as before.
        <div className="concierge-root runson-meaning-host">
          <ul className="concierge-set-list runson-meaning">
            <MeaningSearchRow />
          </ul>
        </div>
      ) : null}

      <SurfaceFooter
        className="runson-foot"
        egress={
          ctrl.pending ? (
            <EgressChip label={ctrl.pending.host} scope={ctrl.pending.scope} />
          ) : ctrl.egress ? (
            <span data-testid="runson-egress">
              <EgressChip label={ctrl.egress.label} scope={ctrl.egress.scope} />
            </span>
          ) : undefined
        }
        receipt={
          ctrl.receipt ? (
            <span className="runson-receipt" data-testid="runson-receipt" data-tone={ctrl.receipt.tone}>
              {ctrl.receipt.text}
            </span>
          ) : undefined
        }
        verbs={
          <>
            {ctrl.pending ? (
              <Button dense variant="primary" data-testid="runson-try-confirm" onClick={ctrl.confirmTry}>
                {`Try on ${ctrl.pending.host}`}
              </Button>
            ) : footTry && footTry.verb === undefined && ctrl.engineForJob(footTry.id) ? (
              <Button dense variant="secondary" data-testid={`runson-try-${footTry.id}`} onClick={() => ctrl.tryJob(footTry.id)}>
                {footTry.id === SPEECH_JOB && ctrl.listening ? "Stop" : "Try it"}
              </Button>
            ) : null}
            {ctrl.canUndo ? (
              <Button dense variant="secondary" disabled={ctrl.busy} data-testid="runson-undo" onClick={() => void ctrl.undo()}>
                Undo
              </Button>
            ) : null}
          </>
        }
      />
    </div>
  );
}
