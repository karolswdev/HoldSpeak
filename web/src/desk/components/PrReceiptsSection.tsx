// HS-106-08 — PR rows become actionable desk objects: state at rest,
// Info and four kernel operations in-world. Proposals expose their complete
// GitHub text before the owner approves or denies; no modal owns the loop.
import { Fragment, useEffect, useState } from "react";
import {
  attributionLabel,
  prStateLabel,
  usePrReceipts,
  type PrActionResult,
  type PrDiff,
  type PrRow,
} from "../prReceipts";
import { DeskComposer } from "./DeskComposer";
import { FoldGadget } from "../surface/gadgets";
import { SurfaceCode, SurfaceState, SurfaceWell } from "../surface/Surface";

type Action = "send" | "comment" | "status" | null;
type VerbName = "send_agent" | "draft_review" | "post_comment" | "post_status";
interface RowWork {
  action: Action;
  text: string;
  busy: string;
  result: PrActionResult | null;
  info: boolean;
}
const EMPTY: RowWork = { action: null, text: "", busy: "", result: null, info: false };

export function PrReceiptsSection() {
  const store = usePrReceipts();
  const [openDiff, setOpenDiff] = useState<{ key: string; diff: PrDiff | null } | null>(null);
  const [work, setWork] = useState<Record<string, RowWork>>({});

  useEffect(() => {
    void usePrReceipts.getState().load();
  }, []);

  const sources = store.sources.filter((s) => s.prs !== null || s.status !== "unavailable");
  if (sources.length === 0) return null;

  const rowWork = (key: string) => work[key] ?? EMPTY;
  const patch = (key: string, value: Partial<RowWork>) =>
    setWork((now) => ({ ...now, [key]: { ...(now[key] ?? EMPTY), ...value } }));

  const seeDiff = async (row: PrRow) => {
    const key = `${row.source_id}:${row.number}`;
    if (openDiff?.key === key) return setOpenDiff(null);
    setOpenDiff({ key, diff: null });
    setOpenDiff({ key, diff: await store.diff(row.source_id, row.number) });
  };

  const fetchAndRetry = async (row: PrRow) => {
    await store.fetchShas(row.source_id, row.number);
    setOpenDiff({ key: `${row.source_id}:${row.number}`, diff: await store.diff(row.source_id, row.number) });
  };

  const run = async (key: string, label: string, act: () => Promise<PrActionResult>) => {
    patch(key, { busy: label, result: null });
    try {
      patch(key, { busy: "", result: await act(), action: null });
    } catch (error) {
      patch(key, { busy: "", result: { error: error instanceof Error ? error.message : "failed" } });
    }
  };

  const availability = (row: PrRow, name: VerbName) =>
    row.verbs?.[name] ?? { available: false, reason: "unavailable" };

  return (
    <section aria-labelledby="desk-pr-receipts-title" className="desk-dlv-list desk-pr-receipts">
      <h2 id="desk-pr-receipts-title">
        Pull requests <span className="egress-badge is-cloud" title="GitHub">GitHub</span>
        <button type="button" className="desk-list-open desk-pr-refresh" disabled={store.busy} onClick={() => void store.refresh()}>
          {store.busy ? "Refreshing" : "Refresh"}
        </button>
      </h2>
      {sources.map((source) => (
        <div key={source.source_id} className="desk-pr-source">
          <h3>{source.label}<small>{source.status === "live" ? `observed ${source.observed_at}` : source.status === "stale" ? `stale · ${source.observed_at} · ${source.detail}` : source.detail}</small></h3>
          {source.prs && source.prs.length === 0 ? <SurfaceState empty emptyLabel="Empty" /> : null}
          {source.prs ? (
            <div className="desk-list-scroll">
              <table className="desk-list-table desk-pr-object-table">
                <thead><tr><th scope="col">PR</th><th scope="col">State</th><th scope="col">Match</th><th scope="col">Verbs</th></tr></thead>
                <tbody>
                  {source.prs.map((row) => {
                    const key = `${row.source_id}:${row.number}`;
                    const w = rowWork(key);
                    const proposal = w.result?.proposal_id ? w.result : null;
                    return (
                      <Fragment key={key}>
                        <tr className={row.needs_you ? "is-needs-you" : undefined} data-desk-object="pr">
                          <th scope="row"><span className="desk-pr-number">#{row.number}</span> {row.title}</th>
                          <td>{prStateLabel(row)} <span className={`desk-pr-gate is-${row.agent_gate || "ungated"}`}>{(row.agent_gate || "ungated").toUpperCase()}</span></td>
                          <td><span className={`desk-pr-attmeans is-${row.attribution}`} title={row.basis}>{attributionLabel(row)}</span></td>
                          <td>
                            <span className="desk-shade-do desk-pr-verbs">
                              <button type="button" onClick={() => void seeDiff(row)}>Diff</button>
                              <button type="button" onClick={() => patch(key, { info: !w.info })}>Info</button>
                              {(["send_agent", "draft_review", "post_comment", "post_status"] as const).map((name) => {
                                const a = availability(row, name);
                                const labels = { send_agent: "Send agent", draft_review: "Draft review", post_comment: "Post comment", post_status: "Post status" };
                                const click = name === "draft_review"
                                  ? () => void run(key, "Drafting", () => store.draftReview(row))
                                  : () => patch(key, { action: name === "send_agent" ? "send" : name === "post_comment" ? "comment" : "status", text: name === "post_status" ? "Review in progress" : w.text, result: null });
                                return <button key={name} type="button" disabled={!a.available || Boolean(w.busy)} title={a.available ? labels[name] : a.reason} onClick={click}>{labels[name]}</button>;
                              })}
                              {Array.from(new Set((Object.values(row.verbs ?? {}) as Array<{ available: boolean; reason: string }>).filter((item) => !item.available && item.reason).map((item) => item.reason))).map((reason) => <small key={reason} className="desk-pr-refusal">{reason}</small>)}
                            </span>
                          </td>
                        </tr>
                        {w.info ? (
                          <tr className="desk-pr-detail"><td colSpan={4}><dl><div><dt>Author</dt><dd>{row.author}</dd></div><div><dt>Branch</dt><dd>{row.head_ref}</dd></div><div><dt>Observed</dt><dd>{row.observed_at}</dd></div><div><dt>CI</dt><dd>{row.ci}</dd></div><div><dt>Agent</dt><dd>{(row.agent_gate || "ungated").toUpperCase()}</dd></div></dl></td></tr>
                        ) : null}
                        {w.action ? (
                          <tr className="desk-pr-action"><td colSpan={4}>
                            <div className="desk-pr-compose">
                              <label htmlFor={`pr-action-${key}`}>{w.action === "send" ? "Instruction" : w.action === "comment" ? "Comment" : "Status"}</label>
                              <DeskComposer
                                className="desk-mic-row"
                                value={w.text}
                                onChange={(text) => patch(key, { text })}
                                placeholder={w.action === "send" ? "Instruction" : w.action === "comment" ? "Comment" : "Status"}
                                multiline
                                rows={w.action === "comment" ? 7 : 3}
                                micDraftScope={`pr-${key}-${w.action}`}
                                actionLabel={w.action === "send" ? "Send agent" : "Propose"}
                                actionDisabled={!w.text.trim()}
                                actionBusy={Boolean(w.busy)}
                                onAction={() =>
                                  void run(
                                    key,
                                    w.action === "send" ? "Sending" : "Proposing",
                                    () =>
                                      w.action === "send"
                                        ? store.sendAgent(row, w.text)
                                        : store.propose(
                                            row,
                                            w.text,
                                            w.action === "status" ? "status" : "comment",
                                          ),
                                  )
                                }
                              />
                              <span className="desk-pr-compose-actions">
                                <button type="button" onClick={() => patch(key, { action: null })}>Cancel</button>
                              </span>
                            </div>
                          </td></tr>
                        ) : null}
                        {proposal ? (
                          <tr className="desk-pr-proposal"><td colSpan={4}>
                            <div className="desk-pr-proposal-head"><strong>PROPOSED</strong><span className="egress-badge is-cloud">GitHub</span></div>
                            {/* HS-111-07 — RAW pattern, default-open:
                                the complete text IS the consent surface. */}
                            <FoldGadget title="RAW · PROPOSAL" open>
                              <SurfaceWell head="RAW · PROPOSAL">
                                <SurfaceCode>{proposal.preview}</SurfaceCode>
                              </SurfaceWell>
                            </FoldGadget>
                            <span className="desk-pr-compose-actions">
                              <button type="button" onClick={() => void run(key, "Denying", () => store.decide(proposal.proposal_id!, "reject"))}>Deny</button>
                              <button type="button" onClick={() => void run(key, "Posting", () => store.decide(proposal.proposal_id!, "approve"))}>Approve</button>
                            </span>
                          </td></tr>
                        ) : null}
                        {w.busy ? <tr className="desk-pr-result"><td colSpan={4}>{w.busy}</td></tr> : null}
                        {w.result && !proposal ? (
                          <tr className={`desk-pr-result ${w.result.error ? "is-error" : "is-ok"}`}><td colSpan={4}>
                            <strong>{w.result.error ? "REFUSED" : w.result.proposal?.status?.toUpperCase() || "RECEIPT"}</strong>
                            {w.result.reason || w.result.error || w.result.operation_id || w.result.artifact_id}
                            {w.result.output ? (
                              <FoldGadget title="RAW · OUTPUT">
                                <SurfaceWell head="RAW · OUTPUT">
                                  <SurfaceCode>{w.result.output}</SurfaceCode>
                                </SurfaceWell>
                              </FoldGadget>
                            ) : null}
                          </td></tr>
                        ) : null}
                        {openDiff?.key === key ? (
                          <tr className="desk-pr-diffrow"><td colSpan={4}>
                            {openDiff.diff === null ? (
                              <p className="desk-shade-quiet">Reading</p>
                            ) : openDiff.diff.status === "ok" ? (
                              /* HS-111-07 — the diff wears the RAW well,
                                 default-open (the owner asked for it). */
                              <FoldGadget title="RAW · DIFF" open>
                                <SurfaceWell head={`RAW · DIFF #${row.number}`}>
                                  <SurfaceCode>{openDiff.diff.diff}</SurfaceCode>
                                </SurfaceWell>
                              </FoldGadget>
                            ) : openDiff.diff.offer_fetch ? (
                              <button type="button" className="desk-list-open" onClick={() => void fetchAndRetry(row)}>Fetch</button>
                            ) : (
                              <p className="desk-shade-quiet">{openDiff.diff.detail || "Unavailable"}</p>
                            )}
                          </td></tr>
                        ) : null}
                      </Fragment>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : <p className="desk-shade-quiet">Unobserved</p>}
        </div>
      ))}
    </section>
  );
}
