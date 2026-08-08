import { SurfaceFooter } from "../surface/SurfaceFooter";
// The Delivery board (HS-94-08) — delivery work through familiar Desk
// objects, not a new dashboard. Sources with honest freshness, Projects and
// Stories over the one read model, active Work attempts naming their Story,
// agent, node, worktree/branch, lifecycle, freshness and target, and Coder
// sessions as node-issued terminal targets. A Story opens its dossier IN a
// window; a target opens the immutable-target terminal. Launch is a typed
// operation with a voice-fillable label and its destination shown up front.
//
// HS-111-06 (audit §3.3): active work and Coder sessions are SurfaceLedger
// tables; the launch composer is ONE GadgetGroup with an axis-named token
// consequence line; the footer receipt bar carries the freshness fact the
// wire already held. The delivery wires are untouched.
import "./delivery.css";
import { useEffect, useMemo, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { ReceiptLine } from "./ReceiptLine";
import {
  activeAttempts,
  sourceRecovery,
  useDelivery,
  POLL_MS,
  type DeliverySource,
  type WorkAttempt,
} from "../delivery";
import {
  targetHandle,
  useDeliveryFactory,
  type DiscoveredTarget,
} from "../deliveryFactory";
import { useDeliveryDossier } from "../deliveryDossier";
import { useDeliveryTerminal } from "../deliveryTerminal";
import {
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceState,
} from "../surface/Surface";
import {
  CycleGadget,
  GadgetGroup,
  GadgetRow,
  StringGadget,
  TransportKey,
} from "../surface/gadgets";
import {
  DeskWindowFrame,
  announceLauncher,
  retractLauncher,
} from "./DeskWindow";

function stateTone(state: string): "warn" | "danger" | undefined {
  if (state === "waiting") return "warn";
  if (state === "abandoned" || state === "unknown") return "danger";
  return undefined;
}

function clockToken(ms: number | null): string {
  if (!ms) return "";
  const date = new Date(ms);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
}

function FreshnessChip({ source }: { source: DeliverySource }) {
  const recovery = sourceRecovery(source);
  if (!recovery) {
    return (
      <span className="desk-chip quiet desk-dlv-fresh is-live" title="live">
        live
      </span>
    );
  }
  return (
    <span className="desk-dlv-recovery" role="status">
      <span className={"desk-dlv-fresh is-" + recovery.state}>
        {recovery.state}
      </span>
      <span className="quiet desk-dlv-hint">{recovery.hint}</span>
      <button
        type="button"
        className="desk-chip quiet"
        onClick={() => void useDelivery.getState().refresh()}
      >
        {recovery.label}
      </button>
    </span>
  );
}

/** One active attempt as a ledger row: STORY · STATE · AGENT · NODE ·
 * BR · WT · TARGET. Open-in-place is the terminal (bound target) or
 * the receipt line. */
function AttemptLedgerRow({
  attempt,
  branch,
  target,
}: {
  attempt: WorkAttempt;
  branch: string | null;
  target: DiscoveredTarget | null;
}) {
  const [open, setOpen] = useState(false);
  return (
    <SurfaceLedgerRow
      primary={attempt.storyRef.storyId}
      open={open}
      onToggle={() => {
        if (target) useDeliveryTerminal.getState().open(targetHandle(target));
        else setOpen((v) => !v);
      }}
      cells={
        <>
          <span className="surface-ledger-cell">
            <span className="surface-token" data-tone={stateTone(attempt.state)}>
              {attempt.state.toUpperCase()}
            </span>
          </span>
          <span className="surface-ledger-cell">
            {[
              attempt.claimedBy || attempt.association,
              attempt.nodeId ? `NODE ${attempt.nodeId}` : "",
              branch ? `BR ${branch}` : "",
              attempt.worktreeId ? `WT ${attempt.worktreeId.slice(0, 8)}` : "",
              !attempt.exact ? "INEXACT" : "",
            ]
              .filter(Boolean)
              .join(" · ")}
          </span>
          {target ? (
            <span className="surface-ledger-cell">
              <span className="surface-token">
                {target.gate === "gated" ? "GATED" : "UNGATED"}
              </span>
            </span>
          ) : attempt.targetId ? (
            <span className="surface-ledger-cell">
              <span className="surface-token">
                {`TARGET ${attempt.targetId.slice(0, 10)} · OFFLINE`}
              </span>
            </span>
          ) : null}
        </>
      }
    >
      {attempt.sessionId ? (
        <ReceiptLine sessionKey={`claude:${attempt.sessionId}`} />
      ) : (
        <span className="surface-token">NO SESSION BOUND</span>
      )}
    </SurfaceLedgerRow>
  );
}

function LaunchComposer({ sources }: { sources: DeliverySource[] }) {
  const profiles = useDeliveryFactory((s) => s.profiles);
  const launchState = useDeliveryFactory((s) => s.launchState);
  const launchDetail = useDeliveryFactory((s) => s.launchDetail);
  const [profileId, setProfileId] = useState("");
  const [storyId, setStoryId] = useState("");
  const [label, setLabel] = useState("");

  useEffect(() => {
    void useDeliveryFactory.getState().loadProfiles();
  }, []);
  useEffect(() => {
    if (!profileId && profiles.length) setProfileId(profiles[0].profileId);
  }, [profiles]);

  // The launch targets the first live source with a worktree — its node and
  // worktree are the destination shown before the key.
  const site = useMemo(() => {
    const live = sources.find(
      (s) => s.status === "live" && s.worktrees.length && s.projects.length,
    );
    if (!live) return null;
    return {
      source: live,
      worktree: live.worktrees[0],
      project: live.projects[0].slug,
    };
  }, [sources]);

  if (!site) {
    return (
      <p className="desk-dlv-hint">
        <span className="surface-token">✕ NO LIVE SOURCE TO LAUNCH ON</span>
      </p>
    );
  }

  const doLaunch = async () => {
    const story = storyId.trim();
    if (!profileId || !story) return;
    const ok = await useDeliveryFactory.getState().launch({
      profileId,
      sourceId: site.source.sourceId,
      worktreeId: site.worktree.worktreeId,
      project: site.project,
      storyId: story,
      sessionLabel: label.trim() || story,
    });
    if (ok) {
      setStoryId("");
      setLabel("");
    }
  };

  return (
    <div className="desk-dlv-launch">
      <GadgetGroup label="LAUNCH">
        <GadgetRow label="AGENT">
          <CycleGadget
            label="Agent"
            value={profileId}
            options={profiles.map((p) => ({
              value: p.profileId,
              label: p.label,
            }))}
            onChange={setProfileId}
          />
        </GadgetRow>
        <GadgetRow label="STORY">
          <StringGadget label="Story id" value={storyId} onChange={setStoryId} />
        </GadgetRow>
        <GadgetRow label="LABEL">
          <StringGadget
            label="Session label"
            value={label}
            onChange={setLabel}
          />
        </GadgetRow>
        <GadgetRow label="">
          <TransportKey
            compact
            label="LAUNCH"
            glyph="▸"
            disabled={!profileId || !storyId.trim() || launchState === "working"}
            onClick={() => void doLaunch()}
          />
        </GadgetRow>
      </GadgetGroup>
      <p className="desk-dlv-consequence">
        <span className="surface-token">{`→ SRC ${site.source.label}`}</span>
        <span className="surface-token">{`WT ${site.worktree.branch}`}</span>
        <span className="surface-token">{`NODE ${site.source.nodeId || "local"}`}</span>
        <span className="surface-token">SPAWNS SESSION</span>
        <span className="surface-token">BINDS ATTEMPT</span>
      </p>
      {launchState === "failed" ? (
        <span className="desk-arm-refusal">✕ {launchDetail}</span>
      ) : null}
    </div>
  );
}

export function DeliveryBoard() {
  const sources = useDelivery((s) => s.sources);
  const attempts = useDelivery((s) => s.attempts);
  const updatedAt = useDelivery((s) => s.updatedAt);
  const [open, setOpen] = useState(false);
  const targets = useDeliveryFactory((s) => s.targets);

  useEffect(() => {
    const tick = () => {
      void useDelivery.getState().refresh();
      if (open) void useDeliveryFactory.getState().discover();
    };
    tick();
    const timer = setInterval(tick, POLL_MS);
    return () => clearInterval(timer);
  }, [open]);

  const branchFor = (worktreeId: string): string | null => {
    for (const s of sources)
      for (const w of s.worktrees)
        if (w.worktreeId === worktreeId) return w.branch;
    return null;
  };
  const targetFor = (attempt: WorkAttempt): DiscoveredTarget | null =>
    attempt.targetId
      ? targets.find((t) => t.targetId === attempt.targetId) || null
      : null;
  const boundTargetIds = new Set(attempts.map((a) => a.targetId).filter(Boolean));
  const looseTargets = targets.filter((t) => !boundTargetIds.has(t.targetId));
  const active = activeAttempts(attempts);

  // HS-97-07 — one shelf: the floating tab is gone; the dock carries
  // the launcher (with the awaiting badge) instead.
  const awaiting = attempts.filter((a) => a.state === "waiting").length;
  useEffect(() => {
    announceLauncher({
      id: "delivery-board",
      label: "Delivery",
      glyph: "▤",
      open,
      badge: awaiting > 0 ? awaiting : undefined,
      activate: () => setOpen(true),
    });
    return () => retractLauncher("delivery-board");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, awaiting]);

  if (!open) return null;

  return (
    <DeskWindowFrame
      id="delivery-board"
      glyph="▦"
      minW={460}
      label="Delivery"
      className="desk-dlv-board"
      title={<span className="desk-mc-title">▤ Delivery</span>}
      entrance={false}
      actions={
        <Button
          dense
          variant="ghost"
          aria-label="Refresh"
          title="Refresh from hub"
          onClick={() => void useDelivery.getState().refresh()}
        >
          ↻
        </Button>
      }
      open={open}
      onClose={() => setOpen(false)}
    >
      {/* HS-129-04 — body owns scroll; head and receipt stay on the frame. */}
      <div className="desk-pullout-body desk-surface-body desk-dlv-board-body">
      {updatedAt === null ? <SurfaceState loading /> : null}

      {sources.map((source) => (
        <div key={source.sourceId} className="desk-dlv-source">
          <div className="desk-dlv-source-head">
            <span className="desk-mc-slug">{source.label}</span>
            <FreshnessChip source={source} />
          </div>
          {source.projects.map((p) => (
            <div key={p.slug} className="desk-dlv-project">
              <div className="desk-dlv-project-head">
                <span className="desk-mc-slug">{p.slug}</span>
                {p.currentPhase ? (
                  <button
                    type="button"
                    className="desk-chip quiet"
                    title="open the phase dossier"
                    onClick={() =>
                      void useDeliveryDossier
                        .getState()
                        .openPhase(p.slug, p.currentPhase!.number, source.sourceId)
                    }
                  >
                    Phase {p.currentPhase.number} dossier
                  </button>
                ) : null}
                {p.warnings > 0 ? (
                  <span className="desk-mc-warn">⚠ {p.warnings}</span>
                ) : null}
              </div>
              <div className="desk-dlv-stories">
                {p.stories
                  .filter(
                    (s) =>
                      p.currentPhase && s.phase === p.currentPhase.number,
                  )
                  .map((s) => (
                    <span
                      key={s.storyId}
                      className={"desk-mc-story st-" + s.status.replace(/[^a-z-]/g, "")}
                    >
                      <button
                        type="button"
                        className="desk-mc-story-pick"
                        title={`${s.title} [${s.status}]`}
                        onClick={() =>
                          void useDeliveryDossier
                            .getState()
                            .openStory(p.slug, s.storyId, source.sourceId)
                        }
                      >
                        {s.storyId}
                      </button>
                      {s.evidenceExists ? (
                        <span className="desk-dlv-evidence" title="has evidence">
                          ✓
                        </span>
                      ) : null}
                    </span>
                  ))}
              </div>
            </div>
          ))}
        </div>
      ))}

      {active.length > 0 ? (
        <section className="desk-dlv-active">
          <SurfaceLedger cols="facts" count={`WORK ${active.length}`}>
            <ul className="surface-ledger-rows">
              {active.map((a) => (
                <AttemptLedgerRow
                  key={a.attemptId}
                  attempt={a}
                  branch={branchFor(a.worktreeId)}
                  target={targetFor(a)}
                />
              ))}
            </ul>
          </SurfaceLedger>
        </section>
      ) : null}

      {looseTargets.length > 0 ? (
        <section className="desk-dlv-sessions">
          <SurfaceLedger cols="facts" count={`SESSIONS ${looseTargets.length}`}>
            <ul className="surface-ledger-rows">
              {looseTargets.map((t) => (
                <SurfaceLedgerRow
                  key={t.targetId}
                  primary={
                    t.storyRef ? t.storyRef.storyId : t.session || t.paneId
                  }
                  onToggle={() =>
                    useDeliveryTerminal.getState().open(targetHandle(t))
                  }
                  cells={
                    <>
                      <span className="surface-ledger-cell">
                        {`${t.paneId} · ${t.nodeId}`}
                      </span>
                      {t.attemptState ? (
                        <span className="surface-ledger-cell">
                          <span
                            className="surface-token"
                            data-tone={stateTone(t.attemptState)}
                          >
                            {t.attemptState.toUpperCase()}
                          </span>
                        </span>
                      ) : null}
                      <span className="surface-ledger-cell">
                        <span className="surface-token">
                          {t.gate === "gated" ? "GATED" : "UNGATED"}
                        </span>
                      </span>
                    </>
                  }
                />
              ))}
            </ul>
          </SurfaceLedger>
        </section>
      ) : null}

      <LaunchComposer sources={sources} />
      </div>

      <SurfaceFooter verbs={<>
        <span className="surface-receiptbar-receipt" role="status">
          {`SOURCES ${sources.length} · WORK ${active.length}` +
            (updatedAt ? ` · READ ${clockToken(updatedAt)}` : "")}
        </span>
      </>} />
    </DeskWindowFrame>
  );
}
