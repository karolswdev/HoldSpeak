// The evidence dossier window (HS-94-08) — a past Story or Phase and its
// evidence open IN a desk window, no route change to a separate app. Members,
// captured runs (pass/fail explicit), and the trace come manifest-bound from
// the hub; asset bytes download through the authorized asset route. A changed
// source, offline source, or missing story each render their own recovery.
//
// HS-111-06 (audit §3.3): the facts head is a token row, captured runs and
// assets are ledger rows (an empty command is a NAMED token, never a bare
// mark), and the record's markdown bodies fold behind the RAW well species
// (Disclosure → SurfaceWell) — 07's law, consumed early.
import { useEffect } from "react";
import { Button } from "../../components/signal/Signal";
import { EgressChip, FoldGadget } from "../surface/gadgets";
import { humanizeWireValue } from "../../lib/productLanguage";
import {
  assetHref,
  useDeliveryDossier,
  type DossierRefusalCode,
} from "../deliveryDossier";
import {
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceState,
  SurfaceWell,
} from "../surface/Surface";
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
      <Button dense variant="ghost" onClick={close}>
        {recovery.label}
      </Button>
    </div>
  );
}

export function DeliveryDossierWindow() {
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
        {loading ? <SurfaceState loading /> : null}
        <RefusalPanel />

        {dossier?.kind === "story" ? (
          <>
            <p className="desk-dlv-facts-line">
              <span className="surface-token">{humanizeWireValue(String(dossier.status || "unknown"))}</span>
              <span className="surface-token">{humanizeWireValue(String(dossier.freshness || "unknown"))}</span>
              <span className="surface-token">
                {`HEAD ${dossier.headSha.slice(0, 12) || "uncommitted"}`}
              </span>
              <span className="surface-token">
                {`RUNS ${dossier.summary.passing}✓ ${dossier.summary.failing}✕`}
              </span>
            </p>
            {dossier.bundleChanged ? (
              <p className="desk-arm-refusal" role="status">
                ✕ BUNDLE CHANGED
              </p>
            ) : null}

            <section>
              <SurfaceLedger
                cols="facts"
                count={`CAPTURED RUNS ${dossier.capturedRuns.length}`}
              >
                {dossier.capturedRuns.length ? (
                  <ul className="surface-ledger-rows">
                    {dossier.capturedRuns.map((r, i) => (
                      <SurfaceLedgerRow
                        key={`${r.timestamp}:${i}`}
                        primary={
                          <>
                            <span
                              className="surface-token"
                              data-tone={r.passed ? "ok" : "danger"}
                            >
                              {r.passed ? "✓" : "✕"}
                            </span>{" "}
                            {r.command ? (
                              <code>{r.command}</code>
                            ) : (
                              <span className="surface-token">
                                NO COMMAND RECORDED
                              </span>
                            )}
                          </>
                        }
                        cells={
                          <span className="surface-ledger-cell">
                            <span className="surface-token">
                              {`EXIT ${r.exitCode ?? "?"}`}
                            </span>
                          </span>
                        }
                      />
                    ))}
                  </ul>
                ) : null}
              </SurfaceLedger>
            </section>

            <section>
              <SurfaceLedger cols="facts" count={`ASSETS ${dossier.members.length}`}>
                {dossier.members.length ? (
                  <ul className="surface-ledger-rows">
                    {dossier.members.map((m) => (
                      <li key={m.assetId} className="surface-ledger-row">
                        <a
                          className="surface-ledger-line"
                          href={assetHref(dossier.bundleId, m.assetId)}
                          target="_blank"
                          rel="noreferrer"
                        >
                          <span className="surface-ledger-primary">
                            {m.label}
                          </span>
                          <span className="surface-ledger-cell">
                            {m.mediaType}
                          </span>
                          <span className="surface-ledger-cell">
                            {`${m.bytes} B`}
                          </span>
                          <EgressChip
                            label="↗ Download"
                            title="Opens this captured asset in a new tab."
                            scope="local"
                          />
                        </a>
                      </li>
                    ))}
                  </ul>
                ) : null}
              </SurfaceLedger>
            </section>

            {dossier.storyMarkdown ? (
              <FoldGadget title="RAW · STORY">
                <SurfaceWell
                  head={<span className="surface-token">{`STORY ${dossier.storyId}`}</span>}
                >
                  <pre className="desk-pullout-md">{dossier.storyMarkdown}</pre>
                </SurfaceWell>
              </FoldGadget>
            ) : null}
            {dossier.evidenceMarkdown ? (
              <FoldGadget title="RAW · EVIDENCE LOG">
                <SurfaceWell
                  head={<span className="surface-token">{`EVIDENCE ${dossier.storyId}`}</span>}
                >
                  <pre className="desk-pullout-md">
                    {dossier.evidenceMarkdown}
                  </pre>
                </SurfaceWell>
              </FoldGadget>
            ) : null}
          </>
        ) : null}

        {dossier?.kind === "phase" ? (
          <>
            <p className="desk-dlv-facts-line">
              <span className="surface-token">
                {dossier.title || `Phase ${dossier.phase}`}
              </span>
              <span className="surface-token">
                {(dossier.status || "open").toUpperCase()}
              </span>
              <span className="surface-token">
                {`${dossier.storiesDone ?? "?"}/${dossier.storiesTotal ?? "?"}`}
              </span>
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
