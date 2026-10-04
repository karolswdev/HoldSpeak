// Meaning search: one row in THE SET. OFF / DOWNLOADING n% / INDEXING n of m / ON,
// and one verb (Turn on / Turn off). Composes the species THE SET already
// uses: SurfaceLedgerRow, StateChip, EgressChip, the library Button.
// Server truth: GET /api/memory/meaning-search (MeaningSearchService.status).
//
// A failure is never silent. A refused press, a 4xx or 5xx answer, no answer,
// and a failure the hub reports all draw the window's failure species (the
// repair row's grammar): a failure chip that names it, one plain reason that
// wraps inside the row, and the verb "Try again".

import { useCallback, useEffect, useRef, useState } from "react";
import { SurfaceLedgerRow, StateChip, EgressChip } from "../../desk/surface";
import { Button } from "../../components/signal/Signal";
import { ApiError, apiFetch } from "../../lib/api";
import { GROUP_GLYPHS, humanSize } from "./useConciergeController";

export interface MeaningSearchStatus {
  state: "off" | "downloading" | "indexing" | "on";
  percent: number;
  indexed: number;
  total: number;
  error: string;
  error_code?: string;
  model: { label: string; size_bytes: number; on_device: boolean; source: string };
  egress: { destination: string; what: string } | null;
}

type Action = "read" | "turn-on" | "turn-off";

export interface MeaningSearchFailure {
  /** The name on the failure chip. */
  token: string;
  /** One or two short sentences: what happened and what to do. */
  reason: string;
  /** What "Try again" does. */
  retry: Action;
}

const PATH = "/api/memory/meaning-search";
const BUSY_POLL_MS = 1000;

/** The hub's own failure codes (MeaningSearchService) and their chip names. */
const SERVER_TOKENS: Record<string, string> = {
  network: "DOWNLOAD STOPPED",
  integrity: "WRONG FILE",
  refused: "NOT PERMITTED",
  unsafe: "LINK FOUND",
  runtime: "NOT INSTALLED",
  setup: "DID NOT START",
};

/** A request that did not succeed, in plain words with a way forward. */
export function requestFailure(error: unknown, retry: Action): MeaningSearchFailure {
  if (error instanceof ApiError) {
    if (error.status === 401 || error.status === 403) {
      return {
        token: "NOT PERMITTED",
        reason: "Only the owner can do this. Open this desk as the owner. Then press Try again.",
        retry,
      };
    }
    return {
      token: "HUB ERROR",
      reason: `The hub did not do this (error ${error.status}). Press Try again.`,
      retry,
    };
  }
  return {
    token: "NO ANSWER",
    reason: "The hub did not answer. Make sure the hub runs. Then press Try again.",
    retry,
  };
}

export function meaningSearchChip(status: MeaningSearchStatus) {
  if (status.state === "on") return <StateChip state="success" label="ON" icon="●" />;
  if (status.state === "downloading")
    return <StateChip state="working" label={`DOWNLOADING ${status.percent}%`} icon="○" />;
  if (status.state === "indexing")
    return <StateChip state="working" label={`INDEXING ${status.indexed} OF ${status.total}`} icon="○" />;
  return <StateChip state="idle" label="OFF" />;
}

function isStatus(value: unknown): value is MeaningSearchStatus {
  return Boolean(value) && typeof (value as MeaningSearchStatus).state === "string";
}

export function MeaningSearchRow() {
  const [status, setStatus] = useState<MeaningSearchStatus | null>(null);
  const [failed, setFailed] = useState<MeaningSearchFailure | null>(null);
  const [pressing, setPressing] = useState(false);
  const alive = useRef(true);

  const run = useCallback(async (action: Action) => {
    if (action !== "read") setPressing(true);
    try {
      const next = await apiFetch<MeaningSearchStatus>(
        action === "read" ? PATH : `${PATH}/${action}`,
        action === "read" ? {} : { method: "POST" },
      );
      if (!alive.current) return;
      if (isStatus(next)) {
        setStatus(next);
        setFailed(null);
      } else {
        setFailed(requestFailure(new ApiError(502, "no status", next), action));
      }
    } catch (error) {
      if (alive.current) setFailed(requestFailure(error, action));
    } finally {
      if (alive.current && action !== "read") setPressing(false);
    }
  }, []);

  useEffect(() => {
    alive.current = true;
    void run("read");
    return () => { alive.current = false; };
  }, [run]);

  const busy = !failed && (status?.state === "downloading" || status?.state === "indexing");
  useEffect(() => {
    if (!busy) return;
    const timer = window.setInterval(() => { void run("read"); }, BUSY_POLL_MS);
    return () => window.clearInterval(timer);
  }, [busy, run]);

  // A failure the hub reports (the download stopped, the wrong file...).
  const reported: MeaningSearchFailure | null =
    status && status.error && SERVER_TOKENS[status.error_code ?? ""]
      ? { token: SERVER_TOKENS[status.error_code ?? ""], reason: status.error, retry: "turn-on" }
      : null;
  const failure = failed ?? reported;
  if (!status && !failure) return null; // the first read is in progress

  const off = !status || status.state === "off";
  const leaves = Boolean(status) && (status!.state === "downloading" || (off && status!.egress !== null));
  const size = status ? humanSize(status.model.size_bytes) : null;
  const action: Action = failure ? failure.retry : off ? "turn-on" : "turn-off";
  const reason = failure?.reason ?? status?.error ?? "";

  return (
    <SurfaceLedgerRow
      lead={<span className="concierge-group-glyph">{GROUP_GLYPHS.background}</span>}
      primary={<span className="concierge-group-name">Meaning search</span>}
      cells={
        <span className="concierge-set-cells">
          <span className="concierge-cloud-actions">
            <Button
              dense
              variant={failure || off ? "secondary" : "ghost"}
              loading={pressing}
              disabled={pressing}
              onClick={(e: React.MouseEvent) => { e.stopPropagation(); void run(action); }}
              data-testid="meaning-search-verb"
            >
              {failure ? "Try again" : off ? "Turn on" : "Turn off"}
            </Button>
          </span>
          <span
            className="concierge-set-state"
            data-testid="meaning-search-state"
            data-state={failure ? "failed" : status!.state}
          >
            {failure ? <StateChip state="failure" label={failure.token} /> : meaningSearchChip(status!)}
          </span>
          {status ? (
            <span className="concierge-set-line2 concierge-meaning-line">
              {/* One short line at 393: the model name, or what the press downloads. */}
              {!leaves ? <span className="concierge-token">{status.model.label}</span> : null}
              {leaves && size ? <span className="concierge-token">{size}</span> : null}
              {off && leaves ? <span className="concierge-token">DOWNLOAD</span> : null}
              {leaves ? (
                <EgressChip
                  label={status.model.source.toUpperCase()}
                  scope="cloud"
                  title={`Turn on downloads the model file from ${status.model.source}`}
                />
              ) : (
                <EgressChip label="THIS DEVICE" scope="local" />
              )}
            </span>
          ) : null}
          {/* The reason has its own line and wraps inside the row. */}
          {reason ? (
            <span
              className="concierge-repair-reason concierge-meaning-reason"
              role="alert"
              data-testid="meaning-search-error"
            >
              {reason}
            </span>
          ) : null}
        </span>
      }
      expands={false}
      wrap
      data-testid="concierge-meaning-search"
    />
  );
}
