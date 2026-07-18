// The evidence dossier window (HS-94-08) — a past Story or Phase and its
// evidence open IN a desk window, no route change to a separate app. Members,
// captured runs (pass/fail explicit), and the trace come manifest-bound from
// the hub; asset bytes download through the authorized asset route. A changed
// source, offline source, or missing story each render their own recovery.
import { useEffect, useRef } from "react";
import { motion, useReducedMotion } from "motion/react";
import {
  assetHref,
  useDeliveryDossier,
  type DossierRefusalCode,
} from "../deliveryDossier";
import { DeskWindowFrame } from "./DeskWindow";

const REFUSAL_RECOVERY: Record<
  DossierRefusalCode,
  { label: string; hint: string }
> = {
  bundle_changed: {
    label: "Reload dossier",
    hint: "source changed since this bundle",
  },
  unavailable: { label: "Retry source", hint: "source offline" },
  not_found: { label: "Close", hint: "story not in any source" },
  error: { label: "Retry", hint: "dossier read failed" },
};

function RefusalPanel() {
  const refusal = useDeliveryDossier((s) => s.refusal);
  const { close } = useDeliveryDossier.getState();
  if (!refusal) return null;
  const recovery = REFUSAL_RECOVERY[refusal.code];
  return (
    <div className="desk-dlv-refusal" role="status">
      <span className="desk-arm-refusal">
        ✕ {refusal.code.replace(/_/g, " ")} · {refusal.detail || recovery.hint}
      </span>
      <button type="button" className="desk-chip quiet" onClick={close}>
        {recovery.label}
      </button>
    </div>
  );
}

export function DeliveryDossierWindow() {
  const reducedMotion = useReducedMotion();
  const dossier = useDeliveryDossier((s) => s.dossier);
  const loading = useDeliveryDossier((s) => s.loading);
  const refusal = useDeliveryDossier((s) => s.refusal);
  const { close } = useDeliveryDossier.getState();
  const open = Boolean(dossier || loading || refusal);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") close();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open]);

  if (!open) return null;

  const title =
    dossier?.kind === "story"
      ? dossier.storyId
      : dossier?.kind === "phase"
        ? `Phase ${dossier.phase}`
        : loading
          ? "Loading dossier"
          : "Evidence";

  return (
    <DeskWindowFrame
      id="delivery-dossier"
      glyph="▧"
      minW={420}
      label={`Dossier ${title}`}
      className="desk-pullout desk-dlv-dossier"
      eyebrow="Evidence"
      title={title}
      open={open}
      onClose={close}
    >

      <div className="desk-pullout-body desk-dlv-dossier-body">
        {loading ? <p className="quiet">…</p> : null}
        <RefusalPanel />

        {dossier?.kind === "story" ? (
          <>
            <dl className="desk-tool-facts">
              <div>
                <dt>Status</dt>
                <dd>{dossier.status}</dd>
              </div>
              <div>
                <dt>Freshness</dt>
                <dd>{dossier.freshness}</dd>
              </div>
              <div>
                <dt>Head</dt>
                <dd>{dossier.headSha.slice(0, 12) || "uncommitted"}</dd>
              </div>
              <div>
                <dt>Captures</dt>
                <dd>
                  {dossier.summary.passing} pass · {dossier.summary.failing}{" "}
                  fail
                </dd>
              </div>
            </dl>
            {dossier.bundleChanged ? (
              <p className="desk-arm-refusal" role="status">
                ✕ bundle changed · this evidence predates the current source
              </p>
            ) : null}

            <section>
              <h3 className="desk-dlv-h3">Captured runs</h3>
              {dossier.capturedRuns.length === 0 ? (
                <p className="quiet">No captured runs.</p>
              ) : (
                <ul className="desk-dlv-runs">
                  {dossier.capturedRuns.map((r, i) => (
                    <li
                      key={`${r.timestamp}:${i}`}
                      className={r.passed ? "is-pass" : "is-fail"}
                    >
                      <span className="desk-dlv-run-mark">
                        {r.passed ? "✓" : "✕"}
                      </span>
                      <code>{r.command}</code>
                      <small>exit {r.exitCode ?? "?"}</small>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <section>
              <h3 className="desk-dlv-h3">Evidence assets</h3>
              {dossier.members.length === 0 ? (
                <p className="quiet">No assets in this bundle.</p>
              ) : (
                <ul className="desk-dlv-members">
                  {dossier.members.map((m) => (
                    <li key={m.assetId}>
                      <a
                        className="desk-chip quiet"
                        href={assetHref(dossier.bundleId, m.assetId)}
                        target="_blank"
                        rel="noreferrer"
                      >
                        {m.label}
                      </a>
                      <small>
                        {m.mediaType} · {m.bytes} bytes
                      </small>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            {dossier.storyMarkdown ? (
              <details>
                <summary>Story</summary>
                <pre className="desk-pullout-md">{dossier.storyMarkdown}</pre>
              </details>
            ) : null}
            {dossier.evidenceMarkdown ? (
              <details>
                <summary>Evidence log</summary>
                <pre className="desk-pullout-md">
                  {dossier.evidenceMarkdown}
                </pre>
              </details>
            ) : null}
          </>
        ) : null}

        {dossier?.kind === "phase" ? (
          <>
            <p className="quiet">
              {dossier.title || `Phase ${dossier.phase}`} ·{" "}
              {dossier.status || "open"} · {dossier.storiesDone ?? "?"}/
              {dossier.storiesTotal ?? "?"}
            </p>
            <ul className="desk-dlv-phase-stories">
              {dossier.stories.map((s) => (
                <li key={s.storyId}>
                  {s.state === "ready" ? (
                    <button
                      type="button"
                      className="desk-dlv-story-open"
                      onClick={() =>
                        void useDeliveryDossier
                          .getState()
                          .openStory(dossier.project, s.storyId)
                      }
                    >
                      {s.storyId} {s.title ? `· ${s.title}` : ""}
                    </button>
                  ) : (
                    <span className="desk-dlv-story-unavail">
                      {s.storyId} · {s.state.replace(/_/g, " ")}
                    </span>
                  )}
                  {s.state === "ready" ? (
                    <small>
                      {s.passing} pass · {s.failing} fail
                    </small>
                  ) : null}
                </li>
              ))}
            </ul>
          </>
        ) : null}
      </div>
    </DeskWindowFrame>
  );
}
