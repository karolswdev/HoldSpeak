// HS-167-04 — activation review recomposed on the surface library (D4).
// WHAT WILL RUN = SurfaceLedger (one row per watch: provider emblem, name,
// cadence token, ProvenanceChip, CheckGadget trailing).
// THE BRIEF = SurfaceFacts. Baseline = ProgressPlan per provider.
// Footer: EgressChips per host · Back · Activate primary.

import { useEffect, useState } from "react";
import { SurfaceFooter } from "../../../desk/surface/SurfaceFooter";
import {
  SurfaceSection,
  SurfaceFacts,
  SurfaceLedger,
  SurfaceLedgerRow,
} from "../../../desk/surface/Surface";
import {
  EgressChip,
  CheckGadget,
} from "../../../desk/surface/gadgets";
import { ProvenanceChip, Receipt } from "../../../desk/surface/patterns/ProvenanceChip";
import { StateChip } from "../../../desk/surface/patterns/StateChip";
import { ProgressPlan, type PlanStep } from "../../../desk/surface/patterns/ProgressPlan";
import { Button } from "../../../components/signal/Signal";
import {
  cadenceLabel,
  conditionPlainWords,
  inferProjectName,
  ACTION_LABELS,
  STAGE_META,
  STAGE_COUNT,
  type SetupAnswer,
  type SetupProposal,
} from "./model";

const PROVIDER_EMBLEM: Record<string, string> = {
  github: "⌁",
  jira: "⌁",
  native: "◉",
};

const PROVIDER_SOURCE: Record<string, string> = {
  github: "gh",
  jira: "acli",
};

function providerHost(proposal: SetupProposal): string {
  if (proposal.providerId === "github") return "github.com";
  const ref = proposal.spec.subject.scope?.connection_ref;
  if (ref) {
    const site = String(ref).split("|")[0];
    if (site) return site;
  }
  if (proposal.providerId === "jira") return "atlassian.net";
  return "";
}

export function ActivationReview({
  outcomeAnswer,
  signalsAnswer,
  proposals,
  onFinalize,
  onBack,
  finalizing,
}: {
  outcomeAnswer: SetupAnswer;
  signalsAnswer: SetupAnswer;
  proposals: SetupProposal[];
  onFinalize: () => void;
  onBack: () => void;
  finalizing: boolean;
}) {
  const selected = proposals.filter((p) => p.state === "selected");
  const passed = selected.filter((p) => p.testState === "passed");

  const projectName = inferProjectName(outcomeAnswer.answer.normalized);
  const testedCount = passed.length;

  // Cmd/Ctrl+Enter activates (WEB-CMD-005)
  useEffect(() => {
    const handler = (e: globalThis.KeyboardEvent) => {
      if (e.key === "Enter" && (e.metaKey || e.ctrlKey) && !finalizing) {
        e.preventDefault();
        onFinalize();
      }
      if (e.key === "Escape") {
        e.preventDefault();
        onBack();
      }
    };
    const el = document.getElementById("setup-review");
    el?.addEventListener("keydown", handler as EventListener);
    return () => el?.removeEventListener("keydown", handler as EventListener);
  }, [onFinalize, onBack, finalizing]);

  // Collect unique provider hosts for footer EgressChips
  const hosts = [...new Set(selected.map(providerHost).filter(Boolean))];

  // Baseline steps: one per provider
  const providerIds = [...new Set(selected.map((p) => p.providerId))];
  const baselineSteps: PlanStep[] = providerIds
    .filter((pid) => pid !== "native")
    .map((pid) => {
      const host = selected.find((p) => p.providerId === pid);
      const h = host ? providerHost(host) : pid;
      const allTested = selected
        .filter((p) => p.providerId === pid)
        .every((p) => p.testState === "passed");
      return {
        id: `baseline-${pid}`,
        label: `Baseline ${h}`,
        status: allTested ? "done" as const : "queued" as const,
        rate: allTested
          ? `${selected.filter((p) => p.providerId === pid && p.testResult).reduce((n, p) => n + (p.testResult?.entityCount ?? 0), 0)} items`
          : undefined,
      };
    });

  return (
    <div
      id="setup-review"
      tabIndex={-1}
      data-testid="setup-review"
      role="region"
      aria-label="Activation review"
    >
      {/* Headline kept for glass: testid review-headline */}
      <h3 data-testid="review-headline" className="sr-only">
        {projectName} with {testedCount} tested {testedCount === 1 ? "Watch" : "Watches"}
      </h3>

      {/* WHAT WILL RUN — one row per watch */}
      <SurfaceSection label={`WHAT WILL RUN ${selected.length}`}>
        <div data-testid="review-watches">
          {selected.length === 0 ? (
            <div className="surface-fact-empty">
              No Watches selected.
            </div>
          ) : null}
          <SurfaceLedger count="" cols="room">
            <ul className="surface-ledger-rows">
              {selected.map((p) => (
                <WatchRow key={p.id} proposal={p} />
              ))}
            </ul>
          </SurfaceLedger>
        </div>
      </SurfaceSection>

      {/* THE BRIEF — SurfaceFacts for outcome + signals */}
      <SurfaceSection label="THE BRIEF">
        <div data-testid="review-outcome" data-value={outcomeAnswer.answer.normalized}>
          <div data-testid="review-signals" data-section="signals" data-value={signalsAnswer.answer.normalized}>
            <SurfaceFacts value={{
              OUTCOME: outcomeAnswer.answer.normalized,
              NOTICE: signalsAnswer.answer.normalized,
            }} />
          </div>
        </div>
      </SurfaceSection>

      {/* Baseline ProgressPlan per provider */}
      {baselineSteps.length > 0 ? (
        <SurfaceSection label="BASELINE">
          <ProgressPlan steps={baselineSteps} compact ariaLabel="Baseline progress" />
        </SurfaceSection>
      ) : null}

      {/* Footer: EgressChips per host · Back · Activate */}
      <SurfaceFooter
        egress={
          hosts.length > 0 ? (
            <span className="setup-review-egress-row">
              {hosts.map((host) => (
                <EgressChip key={host} label={host} scope="mixed" title={`This activation contacts ${host}.`} />
              ))}
            </span>
          ) : undefined
        }
        verbs={
          <>
            <Button
              dense
              variant="ghost"
              className="setup-review-back"
              onClick={onBack}
              disabled={finalizing}
            >
              Back
            </Button>
            <Button
              dense
              variant="primary"
              onClick={onFinalize}
              disabled={finalizing}
              loading={finalizing}
              data-testid="review-activate-btn"
            >
              Activate
            </Button>
          </>
        }
      />
    </div>
  );
}

/* ── WatchRow: one SurfaceLedgerRow per watch ── */

function WatchRow({ proposal }: { proposal: SetupProposal }) {
  const spec = proposal.spec;
  const [enabled, setEnabled] = useState(true);
  const source = PROVIDER_SOURCE[proposal.providerId];
  const host = providerHost(proposal);

  return (
    <SurfaceLedgerRow
      lead={PROVIDER_EMBLEM[proposal.providerId] ?? "◉"}
      primary={spec.name}
      data-testid={`review-watch-${proposal.id}`}
      cells={
        <>
          <span className="surface-token">{conditionPlainWords(spec)}</span>
          <span className="surface-token">{cadenceLabel(spec.trigger)}</span>
          <span className="surface-token">{ACTION_LABELS[spec.action.kind] ?? spec.action.kind}</span>
          {source && host ? <ProvenanceChip source={source} boundary={host} /> : null}
        </>
      }
      trailing={
        <CheckGadget
          label={`Include ${spec.name}`}
          checked={enabled}
          onChange={setEnabled}
        />
      }
      wrap
      expands={false}
    />
  );
}

function formatTime(iso: string): string {
  if (!iso) return "unknown";
  try {
    return new Date(iso).toLocaleTimeString();
  } catch {
    return iso;
  }
}
