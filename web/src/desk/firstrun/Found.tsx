/* First run C1 — FOUND: the network and cloud engines HoldSpeak found and
 * did NOT assign by itself (owner ruling 2026-10-05, PR #855). Each is a
 * stored proposal (`GET /api/inference/defaults` -> `proposals`); "Use it"
 * is the owner's press (`POST /api/inference/defaults/use-proposal`), which
 * makes it the Default for AI work (`made_by: owner`, so memory follows).
 *
 * No proposals -> no section (UX-CANON A8: no empty section). */
import { useCallback, useEffect, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { EgressChip, StateChip, SurfaceLedgerRow, SurfaceSection } from "../surface";
import { egressFor } from "../surface/egress";
import { apiFetch, readableError } from "../../lib/api";

export interface DefaultProposal {
  id: string;
  label: string;
  host: string;
  lamp: "private_network" | "mesh" | "cloud";
  profile_id?: string;
  profile_revision?: number;
  verb?: string;
}

export const DEFAULTS_PATH = "/api/inference/defaults";
export const USE_PROPOSAL_PATH = "/api/inference/defaults/use-proposal";

type RowState = { kind: "open" } | { kind: "busy" } | { kind: "used" } | { kind: "refused"; reason: string };

/** The egress chip of a proposal: the host the work goes to. */
export function proposalEgress(proposal: DefaultProposal): { label: string; scope: "local" | "cloud" | "remote" | undefined } {
  if (proposal.lamp === "mesh") return { label: (proposal.host || "MESH").toUpperCase(), scope: "remote" };
  const egress = egressFor(proposal.host);
  return { label: egress.label.toUpperCase(), scope: egress.scope };
}

export function useProposals() {
  // The rows keep their place after "Use it": the hub closes a used
  // proposal, and the face says IN USE where the press happened.
  const [rows, setRows] = useState<DefaultProposal[]>([]);
  const [states, setStates] = useState<Record<string, RowState>>({});

  useEffect(() => {
    let live = true;
    void apiFetch<{ proposals?: DefaultProposal[] }>(DEFAULTS_PATH)
      .then((answer) => {
        if (live) setRows(Array.isArray(answer.proposals) ? answer.proposals : []);
      })
      // A hub without the defaults service has no proposals to offer.
      .catch(() => undefined);
    return () => {
      live = false;
    };
  }, []);

  const use = useCallback(async (id: string) => {
    setStates((prev) => ({ ...prev, [id]: { kind: "busy" } }));
    try {
      await apiFetch(USE_PROPOSAL_PATH, { method: "POST", json: { proposal_id: id } });
      setStates((prev) => ({ ...prev, [id]: { kind: "used" } }));
    } catch (error) {
      setStates((prev) => ({ ...prev, [id]: { kind: "refused", reason: readableError(error) } }));
    }
  }, []);

  return { rows, states, use };
}

export function Found({ proposals }: { proposals: ReturnType<typeof useProposals> }) {
  if (!proposals.rows.length) return null;
  return (
    <SurfaceSection label="FOUND" className="firstrun-found">
      <ul className="concierge-found-list firstrun-ledger" aria-label="Found engines" data-testid="firstrun-found">
        {proposals.rows.map((proposal) => {
          const state = proposals.states[proposal.id] ?? { kind: "open" };
          const egress = proposalEgress(proposal);
          const cloud = proposal.lamp === "cloud";
          return (
            <SurfaceLedgerRow
              key={proposal.id}
              lead={<span className="concierge-lead">{cloud ? "◇" : "▣"}</span>}
              primary={<span className="concierge-engine-name">{proposal.label}</span>}
              cells={
                <span className="concierge-found-cells" data-testid="firstrun-proposal">
                  {proposal.lamp === "private_network" ? <span className="concierge-token">LAN SERVER</span> : null}
                  {proposal.lamp === "mesh" ? <span className="concierge-token">MESH</span> : null}
                  {/* A cloud engine is proposed only when its key is set
                      (concierge_service.py: state READY iff keySet;
                      inference_default_service.py: READY engines only). */}
                  {cloud ? <span className="concierge-key-chip" data-set>KEY SET</span> : null}
                  {cloud ? <span className="concierge-cost-chip" title="Paid per use">$</span> : null}
                  <span className="concierge-cloud-actions">
                    {state.kind === "used" ? (
                      <StateChip state="success" label="IN USE · DEFAULT" icon="●" />
                    ) : (
                      <Button
                        dense
                        variant="secondary"
                        loading={state.kind === "busy"}
                        disabled={state.kind === "busy"}
                        aria-label={`Use ${proposal.label}`}
                        onClick={() => void proposals.use(proposal.id)}
                      >
                        Use it
                      </Button>
                    )}
                  </span>
                  {egress.label ? (
                    <span className="concierge-found-line2">
                      <EgressChip label={egress.label} scope={egress.scope} />
                    </span>
                  ) : null}
                  {state.kind === "refused" ? (
                    <span className="concierge-found-line2 firstrun-fail" role="alert">
                      <StateChip state="failure" label="NOT IN USE" />
                      <span className="firstrun-reason">{state.reason}</span>
                    </span>
                  ) : null}
                </span>
              }
              expands={false}
              wrap
            />
          );
        })}
      </ul>
    </SurfaceSection>
  );
}
