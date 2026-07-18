// The Delivery board (HS-94-08) — delivery work through familiar Desk
// objects, not a new dashboard. Sources with honest freshness, Projects and
// Stories over the one read model, active Work attempts naming their Story,
// agent, node, worktree/branch, lifecycle, freshness and target, and Coder
// sessions as node-issued terminal targets. A Story opens its dossier IN a
// window; a target opens the immutable-target terminal. Launch is a typed
// operation with a voice-fillable label and its destination shown up front.
import { useEffect, useMemo, useState } from "react";
import { MicButton } from "./MicButton";
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
import { DeskWindowFrame } from "./DeskWindow";

const STATE_LABEL: Record<string, string> = {
  starting: "starting",
  working: "working",
  waiting: "waiting",
  idle: "idle",
  ended: "ended",
  abandoned: "abandoned",
  unknown: "unknown",
};

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

function AttemptRow({
  attempt,
  branch,
  target,
}: {
  attempt: WorkAttempt;
  branch: string | null;
  target: DiscoveredTarget | null;
}) {
  return (
    <div className="desk-dlv-attempt">
      <span className="desk-dlv-attempt-story">{attempt.storyRef.storyId}</span>
      <span className={"desk-dlv-state is-" + attempt.state}>
        {STATE_LABEL[attempt.state] || attempt.state}
      </span>
      <span className="quiet desk-dlv-attempt-meta">
        {attempt.claimedBy || attempt.association}
        {attempt.nodeId ? ` · node ${attempt.nodeId}` : ""}
        {branch ? ` · ${branch}` : ""}
        {attempt.worktreeId ? ` · wt ${attempt.worktreeId.slice(0, 8)}` : ""}
        {!attempt.exact ? " · inexact" : ""}
      </span>
      {target ? (
        <button
          type="button"
          className="desk-chip"
          title={`watch and steer ${target.paneId} on ${target.nodeId}`}
          onClick={() =>
            useDeliveryTerminal.getState().open(targetHandle(target))
          }
        >
          Open terminal
        </button>
      ) : attempt.targetId ? (
        <span className="quiet desk-dlv-hint">
          target {attempt.targetId.slice(0, 10)} · offline
        </span>
      ) : null}
    </div>
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
  // worktree are the destination shown before the button.
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
      <p className="quiet desk-dlv-hint">No live source to launch on.</p>
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
      <span className="desk-dlv-launch-label">Launch</span>
      <div className="desk-dlv-launch-row">
        <select
          className="desk-classify-input"
          value={profileId}
          aria-label="Persona"
          onChange={(e) => setProfileId(e.target.value)}
        >
          {profiles.map((p) => (
            <option key={p.profileId} value={p.profileId}>
              {p.label}
            </option>
          ))}
        </select>
        <MicButton
          label="Story id"
          draftScope={`dlv-launch-story`}
          onText={(t) => setStoryId(t.trim())}
        />
        <input
          className="desk-classify-input"
          value={storyId}
          placeholder="story id"
          aria-label="Story id"
          onChange={(e) => setStoryId(e.target.value)}
        />
        <MicButton
          label="Session label"
          draftScope={`dlv-launch-label`}
          onText={(t) => setLabel(t.trim())}
        />
        <input
          className="desk-classify-input"
          value={label}
          placeholder="session label"
          aria-label="Session label"
          onChange={(e) => setLabel(e.target.value)}
        />
        <button
          type="button"
          className="desk-chip"
          disabled={!profileId || !storyId.trim() || launchState === "working"}
          onClick={() => void doLaunch()}
        >
          Launch Coder session
        </button>
      </div>
      <p className="quiet desk-dlv-consequence">
        → {site.source.label} · {site.worktree.branch} ·{" "}
        {site.source.nodeId || "local"} · spawns the Coder session and binds a
        Work attempt
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

  if (!open) {
    const awaiting = attempts.filter((a) => a.state === "waiting").length;
    return (
      <button
        className="desk-mc-tab desk-dlv-tab"
        onClick={() => setOpen(true)}
        title="Delivery work"
      >
        ▤ Delivery{awaiting > 0 ? ` 🙋${awaiting}` : ""}
      </button>
    );
  }

  return (
    <DeskWindowFrame
      id="delivery-board"
      minW={460}
      label="Delivery"
      className="desk-dlv-board"
      title={<span className="desk-mc-title">▤ Delivery</span>}
      entrance={false}
      actions={
        <button
          type="button"
          className="desk-mc-btn"
          onClick={() => void useDelivery.getState().refresh()}
          title="Refresh from hub"
        >
          ↻
        </button>
      }
      open={open}
      onClose={() => setOpen(false)}
    >

      {updatedAt === null ? <p className="quiet">…</p> : null}

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
          <h3 className="desk-dlv-h3">Active work</h3>
          {active.map((a) => (
            <AttemptRow
              key={a.attemptId}
              attempt={a}
              branch={branchFor(a.worktreeId)}
              target={targetFor(a)}
            />
          ))}
        </section>
      ) : null}

      {looseTargets.length > 0 ? (
        <section className="desk-dlv-sessions">
          <h3 className="desk-dlv-h3">Coder sessions</h3>
          {looseTargets.map((t) => (
            <button
              key={t.targetId}
              type="button"
              className="desk-dlv-session-open"
              onClick={() =>
                useDeliveryTerminal.getState().open(targetHandle(t))
              }
            >
              <span className="desk-dlv-session-glyph">▮</span>
              {t.storyRef ? t.storyRef.storyId : t.session || t.paneId}
              <small>
                {t.paneId} · {t.nodeId}
                {t.attemptState ? ` · ${t.attemptState}` : ""}
              </small>
            </button>
          ))}
        </section>
      ) : null}

      <LaunchComposer sources={sources} />
    </DeskWindowFrame>
  );
}
