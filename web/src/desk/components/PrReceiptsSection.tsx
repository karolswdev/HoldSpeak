// HS-104-04 — PR receipts beside the delivery list: needs-you-first
// rows (open failing CI above open green above draft above quiet
// merged/closed), each wearing its attribution and observed-at. Two
// verbs only: See diff (read-only, local; honest absence offers an
// explicit fetch) and Open on GitHub. The one egress badge is the
// whole privacy story.
import { useEffect, useState } from "react";
import {
  attributionLabel,
  prStateLabel,
  usePrReceipts,
  type PrDiff,
  type PrRow,
} from "../prReceipts";

export function PrReceiptsSection() {
  const store = usePrReceipts();
  const [openDiff, setOpenDiff] = useState<{
    key: string;
    diff: PrDiff | null;
  } | null>(null);

  useEffect(() => {
    void usePrReceipts.getState().load();
  }, []);

  const sources = store.sources.filter((s) => s.prs !== null || s.status !== "unavailable");
  if (sources.length === 0) return null;

  const seeDiff = async (row: PrRow) => {
    const key = `${row.source_id}:${row.number}`;
    if (openDiff?.key === key) {
      setOpenDiff(null);
      return;
    }
    setOpenDiff({ key, diff: null });
    const diff = await store.diff(row.source_id, row.number);
    setOpenDiff({ key, diff });
  };

  const fetchAndRetry = async (row: PrRow) => {
    await store.fetchShas(row.source_id, row.number);
    const diff = await store.diff(row.source_id, row.number);
    setOpenDiff({ key: `${row.source_id}:${row.number}`, diff });
  };

  return (
    <section aria-labelledby="desk-pr-receipts-title" className="desk-dlv-list desk-pr-receipts">
      <h2 id="desk-pr-receipts-title">
        Pull requests{" "}
        <span
          className="egress-badge is-cloud"
          title="Refresh asks GitHub through the gh CLI; nothing else leaves this device."
        >
          ☁ GitHub on refresh
        </span>
        <button
          type="button"
          className="desk-list-open desk-pr-refresh"
          disabled={store.busy}
          onClick={() => void store.refresh()}
        >
          {store.busy ? "Refreshing" : "Refresh"}
        </button>
      </h2>
      {sources.map((source) => (
        <div key={source.source_id} className="desk-pr-source">
          <h3>
            {source.label}
            <small>
              {source.status === "live"
                ? `observed ${source.observed_at}`
                : source.status === "stale"
                  ? `stale · last observed ${source.observed_at} · ${source.detail}`
                  : source.detail}
            </small>
          </h3>
          {source.prs && source.prs.length === 0 ? (
            <p className="desk-shade-quiet">No pull requests</p>
          ) : null}
          {source.prs ? (
            <div className="desk-list-scroll">
              <table className="desk-list-table">
                <thead>
                  <tr>
                    <th scope="col">PR</th>
                    <th scope="col">State</th>
                    <th scope="col">Match</th>
                    <th scope="col">Author</th>
                    <th scope="col">Verbs</th>
                  </tr>
                </thead>
                <tbody>
                  {source.prs.map((row) => {
                    const key = `${row.source_id}:${row.number}`;
                    return (
                      <>
                        <tr
                          key={key}
                          className={row.state === "open" && row.ci === "failing" ? "is-needs-you" : undefined}
                        >
                          <th scope="row">
                            #{row.number} {row.title}
                          </th>
                          <td>{prStateLabel(row)}</td>
                          <td>
                            <span
                              className={`desk-pr-attmeans is-${row.attribution}`}
                              title={row.basis}
                            >
                              {attributionLabel(row)}
                            </span>
                          </td>
                          <td>{row.author}</td>
                          <td>
                            <span className="desk-shade-do">
                              <button type="button" onClick={() => void seeDiff(row)}>
                                See diff
                              </button>
                              <a href={row.url} target="_blank" rel="noreferrer">
                                Open on GitHub
                              </a>
                            </span>
                          </td>
                        </tr>
                        {openDiff?.key === key ? (
                          <tr key={`${key}-diff`} className="desk-pr-diffrow">
                            <td colSpan={5}>
                              {openDiff.diff === null ? (
                                <p className="desk-shade-quiet">Reading the local diff</p>
                              ) : openDiff.diff.status === "ok" ? (
                                <pre className="desk-pr-diff">{openDiff.diff.diff}</pre>
                              ) : openDiff.diff.offer_fetch ? (
                                <p className="desk-shade-quiet">
                                  Commits are not in the local checkout.{" "}
                                  <button
                                    type="button"
                                    className="desk-list-open"
                                    onClick={() => void fetchAndRetry(row)}
                                  >
                                    Fetch them (network)
                                  </button>
                                </p>
                              ) : (
                                <p className="desk-shade-quiet">
                                  {openDiff.diff.detail || "No local diff"}
                                </p>
                              )}
                            </td>
                          </tr>
                        ) : null}
                      </>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="desk-shade-quiet">Not observed yet</p>
          )}
        </div>
      ))}
    </section>
  );
}
