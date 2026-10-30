// HS-106-08 — PR rows become actionable desk objects: state at rest,
// Info and four kernel operations in-world. Proposals expose their complete
// GitHub text before the owner approves or denies; no modal owns the loop.
import "./delivery.css";
import { Fragment, useEffect, useRef, useState } from "react";
import { Button } from "../../components/signal/Signal";
import {
  attributionLabel,
  prStateLabel,
  usePrReceipts,
  type PrActionResult,
  type PrDiff,
  type PrRow,
} from "../prReceipts";
import { DeskComposer } from "./DeskComposer";
import { WorkMenu, type WorkMenuEntry } from "./DeskMenu";
import { FoldGadget } from "../surface/gadgets";
import { SurfaceCode, SurfaceState, SurfaceWell } from "../surface/Surface";
import { humanizeWireValue } from "../../lib/productLanguage";

type Action = "send" | "comment" | "status" | null;
type VerbName = "send_agent" | "draft_review" | "post_comment" | "post_status";
type ResultAction = VerbName | "approve" | "deny";
interface RowWork {
  action: Action;
  text: string;
  busy: string;
  result: PrActionResult | null;
  resultAction: ResultAction | null;
  info: boolean;
}
const EMPTY: RowWork = { action: null, text: "", busy: "", result: null, resultAction: null, info: false };

function resultLabel(result: PrActionResult, action: ResultAction | null): string {
  if (result.error) return "REFUSED";
  if (action === "draft_review" && result.output?.trim()) return "Review ready";
  return humanizeWireValue(result.proposal?.status || result.state || "accepted");
}

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

  const run = async (key: string, action: ResultAction, label: string, act: () => Promise<PrActionResult>) => {
    patch(key, { busy: label, result: null, resultAction: action });
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
        <Button dense variant="ghost" disabled={store.busy} onClick={() => void store.refresh()}>
          {store.busy ? "Refreshing" : "Refresh"}
        </Button>
      </h2>
      {sources.map((source) => {
        const observedAt = source.observed_at;
        return (
        <div key={source.source_id} className="desk-pr-source">
          <h3>{source.label}<small>{source.status === "live" ? `OBSERVED ${observedAt}` : source.status === "stale" ? `STALE · ${observedAt}` : source.detail}</small></h3>
          {source.prs && source.prs.length === 0 ? <SurfaceState empty emptyLabel="Empty" /> : null}
          {source.prs ? (
            <div className="desk-list-scroll">
              <table className="desk-list-table desk-pr-object-table">
                <thead><tr><th scope="col">PR</th><th scope="col">State</th><th scope="col">Match</th><th scope="col">Verbs</th></tr></thead>
                <tbody>
                  {source.prs.map((row) => {
                    const key = `${row.source_id}:${row.number}`;
                    const w = rowWork(key);
                    const proposalId = w.result?.proposal_id;
                    const proposal = proposalId ? w.result : null;
                    const gateWord = String(row.agent_gate || "ungated").replace(/_/g, " ");
                    const gateLabel = gateWord.charAt(0).toUpperCase() + gateWord.slice(1);
                    const headRef = row.head_ref;
                    const rowObserved = row.observed_at;
                    const rowGate = row.agent_gate;
                    const rawReceipt = [
                      w.result?.operation_id ? `Operation · ${w.result.operation_id}` : null,
                      w.result?.artifact_id ? `Artifact · ${w.result.artifact_id}` : null,
                    ].filter(Boolean).join("\n");
                    const rawResult = [w.result?.output, rawReceipt ? `Receipt\n${rawReceipt}` : null].filter(Boolean).join("\n\n");
                    return (
                      <Fragment key={key}>
                        <tr className={row.needs_you ? "is-needs-you" : undefined} data-desk-object="pr">
                          <th scope="row"><span className="desk-pr-number">#{row.number}</span> {row.title}</th>
                          <td>{prStateLabel(row)} <span className={`desk-pr-gate is-${rowGate || "ungated"}`}>{gateLabel}</span></td>
                          <td><span className={`desk-pr-attmeans is-${row.attribution}`} title={row.basis}>{attributionLabel(row)}</span></td>
                          <td>
                            {/* PHILO-17 THE REFIT: one verb per row (Open PR); the
                                rest live in the row's ⋯ menu (the library menu);
                                an unavailable verb is withheld (UX-CANON A.11,
                                betterment shell S0). */}
                            <span className="desk-shade-do desk-pr-verbs">
                              <Button dense variant="ghost" onClick={() => window.open(row.url, "_blank", "noopener,noreferrer")}>Open PR</Button>
                              <RowMenu
                                label={`More for #${row.number}`}
                                entries={[
                                  { type: "item", id: "diff", label: "Diff", onSelect: () => void seeDiff(row) },
                                  { type: "item", id: "info", label: w.info ? "Hide info" : "Info", onSelect: () => patch(key, { info: !w.info }) },
                                  { type: "sep", id: "sep" },
                                  ...(["send_agent", "draft_review", "post_comment", "post_status"] as const).map((name): WorkMenuEntry => {
                                    const a = availability(row, name);
                                    const labels = { send_agent: "Send agent", draft_review: "Draft review", post_comment: "Post comment", post_status: "Post status" };
                                    const click = name === "draft_review"
                                      ? () => void run(key, "draft_review", "Drafting", () => store.draftReview(row))
                                      : () => patch(key, { action: name === "send_agent" ? "send" : name === "post_comment" ? "comment" : "status", text: name === "post_status" ? "Review in progress" : w.text, result: null });
                                    return { type: "item", id: name, label: labels[name], ghost: !a.available ? a.reason || "unavailable" : w.busy ? w.busy : null, onSelect: click };
                                  }),
                                ]}
                              />
                            </span>
                          </td>
                        </tr>
                        {w.info ? (
                          <tr className="desk-pr-detail"><td colSpan={4}><dl><div><dt>Author</dt><dd>{row.author}</dd></div><div><dt>Branch</dt><dd>{headRef}</dd></div><div><dt>Observed</dt><dd>{rowObserved}</dd></div><div><dt>CI</dt><dd>{row.ci}</dd></div><div><dt>Agent</dt><dd>{gateLabel}</dd></div></dl></td></tr>
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
                                    w.action === "send" ? "send_agent" : w.action === "status" ? "post_status" : "post_comment",
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
                                <Button dense variant="ghost" onClick={() => patch(key, { action: null })}>Cancel</Button>
                              </span>
                            </div>
                          </td></tr>
                        ) : null}
                        {proposal ? (
                          <tr className="desk-pr-proposal"><td colSpan={4}>
                            <div className="desk-pr-proposal-head"><strong>Proposed</strong><span className="egress-badge is-cloud">GitHub</span></div>
                            {/* HS-111-07 — RAW pattern, default-open:
                                the complete text IS the consent surface. */}
                            <FoldGadget title="RAW · PROPOSAL" open>
                              <SurfaceWell head="RAW · PROPOSAL">
                                <SurfaceCode>{proposal.preview}</SurfaceCode>
                              </SurfaceWell>
                            </FoldGadget>
                            <span className="desk-pr-compose-actions">
                              <Button dense variant="ghost" onClick={() => void run(key, "deny", "Denying", () => store.decide(proposalId!, "reject"))}>Deny</Button>
                              <Button dense variant="ghost" onClick={() => void run(key, "approve", "Posting", () => store.decide(proposalId!, "approve"))}>Post to GitHub</Button>
                            </span>
                          </td></tr>
                        ) : null}
                        {w.busy ? <tr className="desk-pr-result"><td colSpan={4}>{w.busy}</td></tr> : null}
                        {w.result && !proposal ? (
                          <tr className={`desk-pr-result ${w.result.error ? "is-error" : "is-ok"}`}><td colSpan={4}>
                            <strong>{resultLabel(w.result, w.resultAction)}</strong>
                            {w.result.reason || w.result.error}
                            {rawResult ? (
                              <FoldGadget title={w.result.output ? "RAW · OUTPUT" : "RAW · RECEIPT"}>
                                <SurfaceWell head={w.result.output ? "RAW · OUTPUT" : "RAW · RECEIPT"}>
                                  <SurfaceCode>{rawResult}</SurfaceCode>
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
                              <Button dense variant="ghost" onClick={() => void fetchAndRetry(row)}>Fetch</Button>
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
        );
      })}
    </section>
  );
}

/** The row's ⋯ menu: the library menu Button and the WorkMenu species. */
function RowMenu({ label, entries }: { label: string; entries: WorkMenuEntry[] }) {
  const [at, setAt] = useState<{ x: number; y: number; keys: boolean } | null>(null);
  const ref = useRef<HTMLButtonElement | null>(null);
  return (
    <>
      <Button
        ref={ref}
        dense
        variant="ghost"
        aria-haspopup="menu"
        aria-expanded={Boolean(at)}
        aria-label={label}
        data-testid="pr-row-menu"
        onClick={(e) => {
          const r = e.currentTarget.getBoundingClientRect();
          setAt(at ? null : { x: r.left, y: r.bottom, keys: e.detail === 0 });
        }}
      >
        ⋯
      </Button>
      {at ? (
        <WorkMenu
          className="desk-head-menu"
          label={label}
          x={at.x}
          y={at.y}
          entries={entries}
          autoFocus={at.keys}
          returnFocus={() => ref.current?.focus()}
          onClose={() => setAt(null)}
        />
      ) : null}
    </>
  );
}
